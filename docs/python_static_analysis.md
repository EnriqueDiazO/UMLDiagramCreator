# Python static analysis

UMLDiagramCreator analyzes Python code with the standard `ast` module. It reads source files, parses syntax trees, and never imports or executes the analyzed project.

## File discovery

For a directory target, the analyzer walks `*.py` files and skips common generated or environment directories such as `.git`, `__pycache__`, `.venv`, `venv`, `build`, and `dist`. `--exclude-tests` skips test paths.

For a file target, only that file is parsed.

## Module names

Module names are derived from the path relative to the analyzed root:

```text
examples/simple_project/services.py -> services
examples/simple_project/__init__.py -> simple_project root module
```

## Extracted entities

Modules:

- module name;
- file path;
- imports, relative imports, aliases, and best-effort resolved target.

Classes:

- name and qualified id;
- module, file, line;
- base classes;
- decorators;
- docstring summary;
- methods;
- detectable attributes from class assignments and `self.*`/`cls.*` assignments.

Functions and methods:

- name and qualified id;
- module, file, line;
- arguments;
- decorators;
- docstring summary;
- static call expressions found in `ast.Call`.

Methods also get a method type:

- `method`;
- `classmethod`;
- `staticmethod`;
- `property`;
- `setter`;
- `dunder`.

## Detected relationships

The first version detects:

- `module imports module`;
- `module defines class/function`;
- `class defines method`;
- `class inherits class`;
- `function calls function`;
- `method calls method/function`;
- `class uses class` when a method calls a known class constructor.

Calls are resolved with simple local rules:

- `foo()` resolves to a function/class in the same module when present;
- `self.foo()` and `cls.foo()` resolve to methods on the containing class;
- `from .models import User` lets `User()` resolve to `models.User`;
- unresolved calls can be included as external nodes with `--include-external`.

## Known limitations

Static analysis cannot fully model runtime Python. The current analyzer may miss or approximate:

- dynamic calls;
- monkey patching;
- conditional imports;
- `getattr` and `setattr`;
- `importlib`;
- decorators that replace functions/classes;
- dynamic dispatch through protocols or abstract base classes;
- metaclasses;
- generated functions/classes;
- indirect calls through callbacks, registries, containers, or dependency injection.

## Design decisions

The core keeps extraction and rendering separate:

- `ast_parser.py` produces `ProjectAnalysis`;
- graph builders convert analysis into `GraphData`;
- exporters write CSV/JSON;
- the renderer consumes `GraphData` and does not parse Python.

This mirrors the reference MOFA2 project: normalize graph data first, enrich nodes with metadata, then render and control the graph in HTML.
