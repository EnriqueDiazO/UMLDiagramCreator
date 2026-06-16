from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from uml_diagram_creator.analyzer.graph_utils import finalize_graph, make_edge, make_node
from uml_diagram_creator.analyzer.model import GraphData
from uml_diagram_creator.analyzer.repo_scan import ScanOptions, iter_project_files, relative_path


PYBIND_MODULE_RE = re.compile(r"PYBIND11_MODULE\s*\(\s*([^,\s\)]+)\s*,")
PY_CLASS_RE = re.compile(r"py::class_<\s*([^,>\)]+).*?\(\s*[^,]+,\s*\"([^\"]+)\"")
PY_ENUM_RE = re.compile(r"py::enum_<\s*([^,>\)]+).*?\(\s*[^,]+,\s*\"([^\"]+)\"")
PY_DEF_RE = re.compile(r"\.def(?:_property(?:_readonly)?|_readwrite|_readonly)?\s*\(\s*\"([^\"]+)\"")
MACRO_RE = re.compile(r"\b(PRAAT_(?:CLASS|ENUM|MODULE|EXCEPTION)_BINDING)\s*\(([^)]*)\)")


@dataclass(frozen=True)
class Pybind11Binding:
    kind: str
    name: str
    python_name: str
    file: Path
    lineno: int
    macro: str = ""


@dataclass(frozen=True)
class Pybind11Method:
    name: str
    file: Path
    lineno: int
    owner_python_name: str = ""


@dataclass
class Pybind11FileAnalysis:
    file: Path
    modules: list[Pybind11Binding]
    bindings: list[Pybind11Binding]
    methods: list[Pybind11Method]


def build_pybind11_graph(root: str | Path, options: ScanOptions | None = None) -> GraphData:
    root_path = Path(root).resolve()
    graph = GraphData(name=f"pybind11 graph: {root_path.name}", graph_type="pybind11")

    for source_file in find_cpp_header_files(root_path, options):
        analysis = analyze_pybind11_file(source_file)
        if not analysis.modules and not analysis.bindings and not analysis.methods:
            continue

        rel_file = relative_path(source_file, root_path)
        file_id = f"pybind_file:{rel_file}"
        graph.nodes.append(
            make_node(
                node_id=file_id,
                label=source_file.name,
                kind="binding_source_file",
                name=source_file.name,
                file=rel_file,
                metadata={"path": rel_file},
            )
        )

        module_ids: list[str] = []
        for module in analysis.modules:
            module_id = f"pybind_module:{module.python_name}"
            module_ids.append(module_id)
            graph.nodes.append(
                make_node(
                    node_id=module_id,
                    label=module.python_name,
                    kind="pybind11_module",
                    name=module.python_name,
                    file=rel_file,
                    lineno=module.lineno,
                    metadata={"cxx_name": module.name},
                )
            )
            graph.edges.append(make_edge(file_id, module_id, "defines", label="PYBIND11_MODULE"))

        default_parent = module_ids[0] if module_ids else file_id
        owner_by_python_name: dict[str, str] = {}
        for binding in analysis.bindings:
            binding_id = f"pybind_binding:{binding.kind}:{binding.python_name}:{binding.name}"
            owner_by_python_name[binding.python_name] = binding_id
            graph.nodes.append(
                make_node(
                    node_id=binding_id,
                    label=binding.python_name,
                    kind=binding.kind,
                    name=binding.python_name,
                    file=rel_file,
                    lineno=binding.lineno,
                    metadata={"cxx_name": binding.name, "macro": binding.macro},
                )
            )
            graph.edges.append(make_edge(file_id, binding_id, "defines", label=binding.kind))
            graph.edges.append(make_edge(default_parent, binding_id, "exposes", label="exposes"))

        current_owner = next(iter(owner_by_python_name.values()), default_parent)
        for method in analysis.methods:
            owner = owner_by_python_name.get(method.owner_python_name, current_owner)
            method_id = f"pybind_method:{rel_file}:{method.lineno}:{method.name}"
            graph.nodes.append(
                make_node(
                    node_id=method_id,
                    label=method.name,
                    kind="pybind11_method",
                    name=method.name,
                    file=rel_file,
                    lineno=method.lineno,
                    metadata={"owner": method.owner_python_name},
                )
            )
            graph.edges.append(make_edge(owner, method_id, "exposes", label="method"))

    return finalize_graph(graph)


def find_cpp_header_files(root: Path, options: ScanOptions | None = None) -> list[Path]:
    options = options or ScanOptions()
    suffixes = {".cpp", ".cc", ".cxx", ".h", ".hpp", ".hh", ".hxx"}
    return sorted(path for path in iter_project_files(root, options) if path.suffix.lower() in suffixes)


def analyze_pybind11_file(path: Path) -> Pybind11FileAnalysis:
    modules: list[Pybind11Binding] = []
    bindings: list[Pybind11Binding] = []
    methods: list[Pybind11Method] = []
    current_python_name = ""

    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        module_match = PYBIND_MODULE_RE.search(line)
        if module_match:
            name = clean_cpp_name(module_match.group(1))
            modules.append(Pybind11Binding(kind="pybind11_module", name=name, python_name=name, file=path, lineno=lineno))

        class_match = PY_CLASS_RE.search(line)
        if class_match:
            cxx_name = clean_cpp_name(class_match.group(1))
            py_name = class_match.group(2)
            current_python_name = py_name
            bindings.append(Pybind11Binding(kind="pybind11_class", name=cxx_name, python_name=py_name, file=path, lineno=lineno))

        enum_match = PY_ENUM_RE.search(line)
        if enum_match:
            cxx_name = clean_cpp_name(enum_match.group(1))
            py_name = enum_match.group(2)
            current_python_name = py_name
            bindings.append(Pybind11Binding(kind="pybind11_enum", name=cxx_name, python_name=py_name, file=path, lineno=lineno))

        macro_match = MACRO_RE.search(line)
        if macro_match:
            macro = macro_match.group(1)
            args = parse_macro_args(macro_match.group(2))
            cxx_name = args[0] if args else macro
            py_name = args[1].strip('"') if len(args) > 1 else cxx_name
            current_python_name = py_name
            bindings.append(
                Pybind11Binding(
                    kind="praat_binding_macro",
                    name=clean_cpp_name(cxx_name),
                    python_name=py_name,
                    file=path,
                    lineno=lineno,
                    macro=macro,
                )
            )

        for def_match in PY_DEF_RE.finditer(line):
            methods.append(Pybind11Method(name=def_match.group(1), file=path, lineno=lineno, owner_python_name=current_python_name))

    return Pybind11FileAnalysis(file=path, modules=modules, bindings=bindings, methods=methods)


def clean_cpp_name(value: str) -> str:
    return value.strip().replace("&", "").replace("*", "").strip()


def parse_macro_args(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]
