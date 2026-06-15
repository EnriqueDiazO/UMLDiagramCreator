from __future__ import annotations

import ast
from pathlib import Path

from .model import ClassInfo, FunctionInfo, ImportInfo, ModuleInfo, ProjectAnalysis, as_posix, short_docstring


DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "venv",
    ".venv",
    "env",
    ".env",
    "site-packages",
}


def analyze_path(
    target: str | Path,
    *,
    exclude_tests: bool = False,
    exclude_venv: bool = True,
) -> ProjectAnalysis:
    """Analyze a Python file or directory using only static AST parsing."""
    target_path = Path(target).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"Path does not exist: {target_path}")

    if target_path.is_file():
        if target_path.suffix != ".py":
            raise ValueError(f"Expected a .py file, got: {target_path}")
        root = target_path.parent
        files = [target_path]
    else:
        root = target_path
        files = list_python_files(root, exclude_tests=exclude_tests, exclude_venv=exclude_venv)

    modules = [_parse_module(path, root) for path in files]
    analysis = ProjectAnalysis(root=as_posix(root), modules=modules)
    _resolve_imports(analysis)
    _resolve_bases_and_calls(analysis)
    return analysis


def list_python_files(root: Path, *, exclude_tests: bool, exclude_venv: bool) -> list[Path]:
    excluded = set(DEFAULT_EXCLUDED_DIRS)
    if not exclude_venv:
        excluded -= {"venv", ".venv", "env", ".env", "site-packages"}

    files: list[Path] = []
    for path in sorted(root.rglob("*.py")):
        rel_parts = path.relative_to(root).parts
        if any(part in excluded for part in rel_parts):
            continue
        if exclude_tests and any(part in {"test", "tests"} or part.startswith("test_") for part in rel_parts):
            continue
        files.append(path)
    return files


def module_name_for_file(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        return path.stem
    return ".".join(parts)


def _parse_module(path: Path, root: Path) -> ModuleInfo:
    module_name = module_name_for_file(path, root)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    module = ModuleInfo(name=module_name, file=as_posix(path))

    for stmt in tree.body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            module.imports.extend(_parse_import(stmt))
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            module.functions.append(_parse_function(stmt, module_name, path))
        elif isinstance(stmt, ast.ClassDef):
            module.classes.append(_parse_class(stmt, module_name, path))

    return module


def _parse_import(stmt: ast.Import | ast.ImportFrom) -> list[ImportInfo]:
    imports: list[ImportInfo] = []
    if isinstance(stmt, ast.Import):
        for alias in stmt.names:
            imports.append(
                ImportInfo(
                    module=alias.name,
                    name=None,
                    alias=alias.asname,
                    level=0,
                    lineno=getattr(stmt, "lineno", 0),
                    resolved=alias.name,
                )
            )
        return imports

    module = stmt.module or ""
    for alias in stmt.names:
        imports.append(
            ImportInfo(
                module=module,
                name=alias.name,
                alias=alias.asname,
                level=stmt.level,
                lineno=getattr(stmt, "lineno", 0),
            )
        )
    return imports


def _parse_class(stmt: ast.ClassDef, module_name: str, path: Path) -> ClassInfo:
    cls = ClassInfo(
        name=stmt.name,
        qualname=f"{module_name}.{stmt.name}",
        module=module_name,
        file=as_posix(path),
        lineno=stmt.lineno,
        bases=[expr_to_name(base) for base in stmt.bases if expr_to_name(base)],
        decorators=[expr_to_name(item) for item in stmt.decorator_list if expr_to_name(item)],
        docstring=short_docstring(ast.get_docstring(stmt)),
    )

    attributes: set[str] = set()
    for item in stmt.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method = _parse_function(item, module_name, path, class_name=stmt.name)
            cls.methods.append(method)
            attributes.update(_self_attributes(item))
        elif isinstance(item, (ast.Assign, ast.AnnAssign)):
            attributes.update(_class_attributes(item))
    cls.attributes = sorted(attributes)
    return cls


def _parse_function(
    stmt: ast.FunctionDef | ast.AsyncFunctionDef,
    module_name: str,
    path: Path,
    *,
    class_name: str | None = None,
) -> FunctionInfo:
    decorators = [expr_to_name(item) for item in stmt.decorator_list if expr_to_name(item)]
    qualname = f"{module_name}.{stmt.name}" if class_name is None else f"{module_name}.{class_name}.{stmt.name}"
    visitor = CallVisitor()
    visitor.visit(stmt)
    return FunctionInfo(
        name=stmt.name,
        qualname=qualname,
        module=module_name,
        file=as_posix(path),
        lineno=stmt.lineno,
        args=_argument_names(stmt.args),
        decorators=decorators,
        docstring=short_docstring(ast.get_docstring(stmt)),
        calls=visitor.calls,
        class_name=class_name,
        method_type=_method_type(stmt.name, decorators) if class_name else None,
    )


def _argument_names(args: ast.arguments) -> list[str]:
    names: list[str] = []
    names.extend(arg.arg for arg in args.posonlyargs)
    names.extend(arg.arg for arg in args.args)
    if args.vararg:
        names.append("*" + args.vararg.arg)
    names.extend(arg.arg for arg in args.kwonlyargs)
    if args.kwarg:
        names.append("**" + args.kwarg.arg)
    return names


def _method_type(name: str, decorators: list[str]) -> str:
    decorator_names = {item.split(".")[-1] for item in decorators}
    if "classmethod" in decorator_names:
        return "classmethod"
    if "staticmethod" in decorator_names:
        return "staticmethod"
    if "property" in decorator_names:
        return "property"
    if any(item.endswith(".setter") for item in decorators):
        return "setter"
    if name.startswith("__") and name.endswith("__"):
        return "dunder"
    return "method"


class CallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        name = expr_to_name(node.func)
        if name:
            self.calls.append(name)
        self.generic_visit(node)


def expr_to_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = expr_to_name(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    if isinstance(node, ast.Call):
        inner = expr_to_name(node.func)
        if inner == "super":
            return "super"
        return inner
    if isinstance(node, ast.Subscript):
        return expr_to_name(node.value)
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return ""


def _self_attributes(node: ast.AST) -> set[str]:
    attrs: set[str] = set()
    for child in ast.walk(node):
        targets: list[ast.AST] = []
        if isinstance(child, ast.Assign):
            targets.extend(child.targets)
        elif isinstance(child, ast.AnnAssign):
            targets.append(child.target)
        elif isinstance(child, ast.AugAssign):
            targets.append(child.target)
        for target in targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id in {"self", "cls"}
            ):
                attrs.add(target.attr)
    return attrs


def _class_attributes(node: ast.Assign | ast.AnnAssign) -> set[str]:
    attrs: set[str] = set()
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for target in targets:
        if isinstance(target, ast.Name):
            attrs.add(target.id)
    return attrs


def _resolve_imports(analysis: ProjectAnalysis) -> None:
    for module in analysis.modules:
        for imp in module.imports:
            imp.resolved = resolve_import(module.name, imp)


def resolve_import(current_module: str, imp: ImportInfo) -> str:
    if imp.level <= 0:
        return f"{imp.module}.{imp.name}" if imp.name and imp.module else imp.name or imp.module

    current_parts = current_module.split(".") if current_module else []
    package_parts = current_parts[: max(0, len(current_parts) - imp.level)]
    module_parts = imp.module.split(".") if imp.module else []
    name_parts = [imp.name] if imp.name else []
    return ".".join(part for part in package_parts + module_parts + name_parts if part)


def _resolve_bases_and_calls(analysis: ProjectAnalysis) -> None:
    class_index = {cls.qualname: cls for cls in analysis.classes}
    class_short_by_module = {(cls.module, cls.name): cls.qualname for cls in analysis.classes}
    callable_short_by_module = {(func.module, func.name): func.qualname for func in analysis.callables}
    method_by_class = {(method.module, method.class_name, method.name): method.qualname for method in analysis.methods}

    for module in analysis.modules:
        aliases = import_aliases(module)
        for cls in module.classes:
            cls.resolved_bases = [
                resolve_symbol(base, module, aliases, class_short_by_module, callable_short_by_module)
                for base in cls.bases
            ]
            for method in cls.methods:
                method.resolved_calls = [
                    resolve_call(
                        call,
                        method,
                        module,
                        aliases,
                        class_short_by_module,
                        callable_short_by_module,
                        method_by_class,
                    )
                    for call in method.calls
                ]
        for func in module.functions:
            func.resolved_calls = [
                resolve_call(
                    call,
                    func,
                    module,
                    aliases,
                    class_short_by_module,
                    callable_short_by_module,
                    method_by_class,
                )
                for call in func.calls
            ]

    # Drop accidental references to missing local classes caused by stale indexes.
    for cls in analysis.classes:
        cls.resolved_bases = [base for base in cls.resolved_bases if base]


def import_aliases(module: ModuleInfo) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for imp in module.imports:
        local = imp.local_name
        if local:
            aliases[local] = imp.resolved
        if imp.name:
            aliases[imp.name] = imp.resolved
    return aliases


def resolve_symbol(
    name: str,
    module: ModuleInfo,
    aliases: dict[str, str],
    class_short_by_module: dict[tuple[str, str], str],
    callable_short_by_module: dict[tuple[str, str], str],
) -> str:
    if not name:
        return ""
    if name in aliases:
        return aliases[name]
    if (module.name, name) in class_short_by_module:
        return class_short_by_module[(module.name, name)]
    if (module.name, name) in callable_short_by_module:
        return callable_short_by_module[(module.name, name)]
    head, _, tail = name.partition(".")
    if head in aliases:
        return ".".join(part for part in [aliases[head], tail] if part)
    return name


def resolve_call(
    call: str,
    func: FunctionInfo,
    module: ModuleInfo,
    aliases: dict[str, str],
    class_short_by_module: dict[tuple[str, str], str],
    callable_short_by_module: dict[tuple[str, str], str],
    method_by_class: dict[tuple[str, str | None, str], str],
) -> str:
    if not call:
        return ""

    if call.startswith(("self.", "cls.")) and func.class_name:
        method_name = call.split(".", 1)[1].split(".", 1)[0]
        return method_by_class.get((func.module, func.class_name, method_name), f"{func.module}.{func.class_name}.{method_name}")

    if call.startswith("super.") and func.class_name:
        method_name = call.split(".", 1)[1].split(".", 1)[0]
        return f"super.{method_name}"

    if "." not in call:
        if (module.name, call) in callable_short_by_module:
            return callable_short_by_module[(module.name, call)]
        if (module.name, call) in class_short_by_module:
            return class_short_by_module[(module.name, call)]
        if call in aliases:
            return aliases[call]
        return call

    head, tail = call.split(".", 1)
    if head in aliases:
        return f"{aliases[head]}.{tail}"

    # Support ClassName.method() when ClassName is defined in the same module.
    class_id = class_short_by_module.get((module.name, head))
    if class_id:
        method_name = tail.split(".", 1)[0]
        return method_by_class.get((module.name, head, method_name), f"{class_id}.{tail}")

    return call
