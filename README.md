# UMLDiagramCreator

UMLDiagramCreator is a Python package and CLI tool for generating UML-oriented visualizations from Python projects. It analyzes source code with the standard `ast` module, builds normalized graph data, and writes interactive HTML, JSON, and CSV outputs.

The analyzer does not import or execute the target project.

```text
Python source
-> static AST analysis
-> graph nodes and edges
-> interactive HTML + JSON + CSV
```

## Features

- AST-based analysis of Python source code.
- Class graphs.
- Inheritance graphs.
- Call graphs.
- Import graphs.
- Project-level dependency graphs.
- Interactive HTML visualization with `vis-network`.
- MathMongo-style graph controls for filtering, physics, layout, exploration, and state export/restore.
- Optional Pyreverse + Graphviz static UML output.
- JSON and CSV exports for generated graph data.

## Installation

UMLDiagramCreator is intended to be installed from this repository in editable mode during development. It is not currently documented as a published PyPI package.

### Recommended: virtual environment

Ubuntu/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Minimal editable install without development dependencies:

```bash
python -m pip install -e .
```

If your system Python cannot install editable packages because of permissions, use a virtual environment instead of installing into the global Python environment.

## Optional Pyreverse + Graphviz Support

UMLDiagramCreator can also generate classic static UML diagrams through Pyreverse and Graphviz. This is optional and does not replace the interactive `vis-network` HTML output.

Pyreverse is distributed with `pylint`. Graphviz is installed at the operating-system level because the `dot` executable is not a Python package dependency.

Ubuntu/Linux:

```bash
sudo apt update
sudo apt install graphviz
python -m pip install -e ".[pyreverse]"
dot -V
```

Windows PowerShell:

```powershell
winget install Graphviz.Graphviz
python -m pip install -e ".[pyreverse]"
dot -V
```

For development with tests and Pyreverse support:

```bash
python -m pip install -e ".[dev,pyreverse]"
```

## Command Line Usage

The examples below assume that the package has been installed and that the virtual environment is active.

The main CLI entry point is `umlgraph`:

```bash
umlgraph --help
```

The same CLI can also be executed as a module:

```bash
python -m uml_diagram_creator --help
```

If you have not activated the virtual environment, use the interpreter or script inside `.venv` directly, for example `.venv/bin/python -m uml_diagram_creator --help` or `.venv/bin/umlgraph --help` on Linux.

### Commands

```text
umlgraph analyze             Analyze a file or project.
umlgraph class-graph         Render a class graph.
umlgraph inheritance-graph   Render an inheritance graph.
umlgraph call-graph          Render a call graph.
umlgraph import-graph        Render an import graph.
umlgraph project-graph       Render a combined project graph.
umlgraph pyreverse           Generate classic UML diagrams with Pyreverse + Graphviz.
```

For the interactive graph commands, `--output` is an output directory. The HTML filename is selected from the graph type.

```bash
umlgraph analyze examples/simple_project --output results/simple_project
umlgraph class-graph examples/simple_project --output results/class_graph
umlgraph inheritance-graph examples/simple_project --output results/inheritance_graph
umlgraph call-graph examples/simple_project --output results/call_graph
umlgraph import-graph examples/simple_project --output results/import_graph
umlgraph project-graph examples/simple_project --output results/project_graph
```

Useful options:

```bash
umlgraph analyze path/to/project \
  --graph project \
  --output results/my_project \
  --max-nodes 300 \
  --include-private \
  --include-dunder \
  --include-external \
  --exclude-tests \
  --focus MyClass,my_function \
  --depth-in 1 \
  --depth-out 2
```

## Interactive HTML Output

A normal run writes graph data and an interactive HTML file:

```text
results/<project_name>/
  nodes.csv
  edges.csv
  graph.json
  project_graph.html
```

HTML filenames by graph type:

```text
class_graph.html
inheritance_graph.html
call_graph.html
import_graph.html
project_graph.html
```

The generated HTML includes:

- zoom, drag, hover tooltips, and keyboard interaction;
- a left navigation panel with node selector, type selector, dynamic legend, and node information;
- a right control panel for physics, layouts, edges, labels, and text size;
- node exploration controls for neighbors, incoming links, outgoing links, same type, component, and full graph;
- JSON state export, JSON copy, JSON restore, and current HTML download.

### Multiple Selection and Fixed Nodes

In the interactive HTML, use `Ctrl + click` or `Shift + click` to select multiple nodes when supported by your browser and `vis-network`.

- `Fijar nodos seleccionados` fixes selected nodes in their current positions.
- `Liberar nodos seleccionados` releases selected nodes.
- `Congelar posiciones` stops the global graph simulation.
- `Activar fisica` restarts the global graph simulation.

## Pyreverse Usage

Generate classic UML diagrams:

```bash
umlgraph pyreverse examples/simple_project \
  --project-name simple_project \
  --output results/pyreverse/simple_project \
  --formats dot,png,svg
```

Equivalent module execution:

```bash
python -m uml_diagram_creator pyreverse examples/simple_project \
  --project-name simple_project \
  --output results/pyreverse/simple_project \
  --formats dot,png,svg
```

Expected output:

```text
results/pyreverse/simple_project/
  classes_simple_project.dot
  packages_simple_project.dot
  classes_simple_project.png
  packages_simple_project.png
  classes_simple_project.svg
  packages_simple_project.svg
```

The `--formats` option accepts comma-separated combinations of:

```text
dot
png
svg
dot,png
dot,png,svg
```

## Demo Scripts

Pyreverse demos:

```bash
python scripts/pyreverse_demo/generar_pyreverse_simple_project.py
python scripts/pyreverse_demo/generar_pyreverse_numpy_polynomial.py
```

There are currently no separate demo scripts for the interactive HTML graphs. Use the CLI examples in this README with `examples/simple_project`.

## Python API

The Python API is still experimental. The recommended interface is currently the `umlgraph` CLI.

Internal modules are organized so they can become a public API later:

- `uml_diagram_creator.analyzer`: AST parsing and graph construction.
- `uml_diagram_creator.render`: interactive HTML rendering.
- `uml_diagram_creator.export`: JSON and CSV writers.
- `uml_diagram_creator.integrations`: optional external tool integrations.

## Development

Install development dependencies and run tests:

```bash
python -m pip install -e ".[dev,pyreverse]"
pytest -q
```

Recommended smoke test:

```bash
dot -V
pytest -q
python -m uml_diagram_creator --help
umlgraph --help
python scripts/pyreverse_demo/generar_pyreverse_simple_project.py
```

Repository layout:

```text
src/uml_diagram_creator/
  analyzer/
  export/
  integrations/
  profiles/
  render/
  __init__.py
  __main__.py
  cli.py

examples/
  simple_project/

scripts/
  pyreverse_demo/

docs/
tests/
results/
```

Files usually committed:

- `src/`
- `tests/`
- `examples/`
- `docs/`
- `scripts/`
- `README.md`
- `LICENSE`
- `pyproject.toml`
- `.gitignore`
- `results/.gitkeep`

Generated or local files usually not committed:

- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `build/`
- `dist/`
- `*.egg-info/`
- generated files in `results/`
- local ZIP references or temporary attachments

## Static Analysis Limits

Because analysis is static, some relationships can be missed or approximated:

- dynamic calls and dispatch;
- monkey patching;
- conditional imports;
- `getattr`, `setattr`, and `importlib`;
- decorators with complex runtime behavior;
- metaclasses;
- generated functions or classes;
- indirect calls through containers, callbacks, or dependency injection.

Pyreverse can provide complementary classic UML diagrams, but it is also a static-analysis tool and has its own limits.

## Troubleshooting

### `dot` not found

Graphviz is missing or the `dot` executable is not on `PATH`.

```bash
dot -V
```

Install Graphviz with your system package manager, then reopen the terminal if needed.

### `No module named pylint`

Install the optional Pyreverse dependency:

```bash
python -m pip install -e ".[pyreverse]"
```

For development:

```bash
python -m pip install -e ".[dev,pyreverse]"
```

### Permission problems with global `pip`

Create a virtual environment and install the package there:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,pyreverse]"
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,pyreverse]"
```

### CLI command not found

Make sure the environment where you installed the package is active:

```bash
source .venv/bin/activate
umlgraph --help
```

You can also run the module form:

```bash
python -m uml_diagram_creator --help
```

## License

This project includes a `LICENSE` file with the MIT license.
