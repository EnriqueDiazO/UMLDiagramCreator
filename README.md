# UMLDiagramCreator

UMLDiagramCreator is a Python static-analysis tool for exploring Python source code as interactive graphs. It parses code with the standard `ast` module, builds normalized node/edge tables, exports CSV/JSON, and renders navigable HTML inspired by the MathMongo/MOFA2 controls from `renv-lab-mofa2`.

```text
Python source
-> static AST analysis
-> modules / classes / functions / methods / imports / calls
-> graph data
-> interactive HTML + CSV + JSON
```

The analyzer does not import or execute the project being analyzed.

## Instalacion del entorno

Este proyecto se recomienda usar dentro de un entorno virtual de Python.

### Crear entorno virtual

```bash
python3 -m venv .venv
```

### Activar entorno virtual

```bash
source .venv/bin/activate
```

### Actualizar pip

```bash
python -m pip install --upgrade pip
```

### Instalar el paquete en modo editable

```bash
python -m pip install -e .
```

### Instalar dependencias de desarrollo

```bash
python -m pip install -e ".[dev]"
```

El extra `dev` esta declarado en `pyproject.toml` e instala `pytest`.

## Flujo rapido

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest -q
umlgraph analyze examples/simple_project --graph project --output results/simple_project
xdg-open results/simple_project/project_graph.html
```

## Verificar instalacion

Despues de instalar el paquete en modo editable:

```bash
python -m compileall src tests examples
pytest -q
python -m uml_diagram_creator analyze examples/simple_project --graph project --output results/simple_project
```

Si el comando de consola esta disponible:

```bash
umlgraph analyze examples/simple_project --graph project --output results/simple_project
```

Para abrir el resultado:

```bash
xdg-open results/simple_project/project_graph.html
```

### Nota sobre PYTHONPATH

Durante desarrollo tambien puedes ejecutar comandos con `PYTHONPATH=src` si todavia no instalaste el paquete:

```bash
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 -m uml_diagram_creator analyze examples/simple_project --graph project --output results/simple_project
```

La ruta recomendada para trabajo normal es instalar en modo editable:

```bash
python -m pip install -e .
pytest -q
python -m uml_diagram_creator analyze examples/simple_project --graph project --output results/simple_project
```

## Basic usage

Analyze a project and write an interactive project graph:

```bash
umlgraph analyze examples/simple_project --graph project --output results/simple_project
```

Equivalent module execution:

```bash
python -m uml_diagram_creator analyze examples/simple_project --graph project --output results/simple_project
python -m uml_diagram_creator.cli analyze examples/simple_project --graph project --output results/simple_project
```

Analyze a single file:

```bash
umlgraph analyze examples/simple_project/services.py --graph call --output results/services_file
```

Open the HTML:

```bash
xdg-open results/simple_project/project_graph.html
```

## Que archivos subir al repositorio

Si subir:

- `src/`
- `tests/`
- `examples/`
- `docs/`
- `README.md`
- `LICENSE`
- `pyproject.toml`
- `.gitignore`
- `results/.gitkeep`

No subir normalmente:

- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `build/`
- `dist/`
- `*.egg-info/`
- resultados generados en `results/`
- ZIPs locales de referencia o adjuntos temporales

## Outputs

Each run writes:

```text
results/<project_name>/
  project_graph.html
  nodes.csv
  edges.csv
  graph.json
```

The HTML filename changes with `--graph`:

- `class_graph.html`
- `inheritance_graph.html`
- `call_graph.html`
- `import_graph.html`
- `project_graph.html`

## Graph types

- `class`: classes, methods, inheritance, class-to-method definitions, and simple class use.
- `inheritance`: class nodes and `Child -> Parent` inheritance edges.
- `call`: functions/methods and detected call edges.
- `import`: modules and import edges.
- `project`: combined modules, classes, functions, methods, imports, definitions, inheritance, calls, and uses.

## CLI options

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

Shortcut commands are also available:

```bash
umlgraph class-graph path/to/project
umlgraph inheritance-graph path/to/project
umlgraph call-graph path/to/project
umlgraph import-graph path/to/project
umlgraph project-graph path/to/project
```

## Interactive HTML

The generated HTML uses `vis-network` and includes:

- zoom, drag, hover tooltips, and keyboard interaction;
- MathMongo-style left panel with `nodeIdSelector`, `nodeTypeSelector`, dynamic legend, and node card;
- MathMongo-style right panel with `🧲 Physics Controls`, layout buttons, edge controls, text size controls, and state export/restore;
- node exploration for neighbors, incoming calls, outgoing calls, component, same type, and full graph;
- JSON state export, JSON copy, JSON restore, and current HTML download.

### Seleccion multiple y fijado de nodos

En el HTML interactivo puedes seleccionar varios nodos con `Ctrl + click` o `Shift + click`, segun soporte de `vis-network` en tu navegador. La seleccion multiple se conserva para los botones de organizacion:

- `📌 Fijar nodos seleccionados` fija todos los nodos seleccionados en sus posiciones actuales.
- `🔓 Liberar nodos seleccionados` libera todos los nodos seleccionados para que vuelvan a moverse con la fisica.
- `📌 Congelar posiciones` detiene la simulacion fisica global del grafo, pero no cambia la propiedad `fixed` de cada nodo.
- `▶ Activar física` reactiva la simulacion fisica.

Checklist manual recomendado:

1. Abre `results/simple_project/project_graph.html`.
2. Selecciona varios nodos con `Ctrl + click` o `Shift + click`.
3. Pulsa `📌 Fijar nodos seleccionados`.
4. Pulsa `▶ Activar física` y verifica que esos nodos no se muevan.
5. Selecciona esos nodos, pulsa `🔓 Liberar nodos seleccionados` y vuelve a activar la fisica.
6. Pulsa `📌 Congelar posiciones` para detener todo el grafo.

## Reference study

The first implementation was shaped by three local reference ZIPs provided during setup:

- `renv-lab-mofa2-main.zip`: main visual reference. The relevant scripts build node/edge tables, classify functions through profiles, compute graph metadata, write CSVs, render with `visNetwork`, and inject MathMongo-style controls for physics, filtering, legends, exploration, and state export.
- `UMLDiagramCreator-main.zip`: initial repository seed. It only contains the original README and MIT license, so this repository starts from a clean package structure.
- `6_Sesion_13_Junio_2026.zip`: source of Python OOP/UML examples. The new `examples/simple_project` mirrors those ideas with classes, inheritance, composition, imports, and method/function calls.

## Project structure

```text
src/uml_diagram_creator/
  cli.py
  analyzer/
    ast_parser.py
    model.py
    call_graph.py
    class_graph.py
    import_graph.py
    project_graph.py
  render/
    html_renderer.py
    mathmongo_controls.py
    palettes.py
  profiles/
    generic.py
  export/
    writers.py
examples/simple_project/
docs/
tests/
results/
```

## Static-analysis limits

Because analysis is static, some relationships can be missed or approximated:

- dynamic calls and dispatch;
- monkey patching;
- conditional imports;
- `getattr`, `setattr`, and `importlib`;
- decorators with complex runtime behavior;
- metaclasses;
- generated functions/classes;
- indirect calls through containers, callbacks, or dependency injection.

## Pyreverse comparison

Pyreverse is useful for UML-style class diagrams from Python projects. UMLDiagramCreator is intentionally different: it keeps the analyzer small and based on `ast`, exports reproducible graph tables, and prioritizes interactive exploration over static PNG/SVG diagrams. Future versions can compare or optionally integrate with Pyreverse, `networkx`, `pyvis`, `graphviz`, `libcst`, or `jedi`, but none are required for the current core.

## Roadmap

- Improve call resolution for imported modules, constructors, and inherited methods.
- Add richer composition/aggregation heuristics from annotations and assignments.
- Add package profiles beyond the generic Python profile.
- Add optional self-contained HTML assets.
- Add Graphviz/Pyreverse comparison output as optional integrations.
