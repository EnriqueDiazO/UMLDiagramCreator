# Parselmouth Case Study

This case study probes Parselmouth, the Python wrapper around Praat built with C++, CMake, and pybind11.

The goal is not to claim full native-code understanding. The goal is to run the current UMLDiagramCreator outputs against a real hybrid project and document what is visible today.

## Run

```bash
python case_studies/parselmouth/run_parselmouth_probe.py /path/to/Parselmouth
```

Outputs are written to:

```text
results/case_studies/parselmouth/
```

## What This Probe Runs

Python-oriented graphs:

- `project-graph` without tests.
- `project-graph` with tests.
- `import-graph` without tests.
- `call-graph` without tests.

Experimental native architecture graphs:

- `repo-scan`.
- `cmake-graph`.
- `pybind11-graph`.

Optional comparison:

- `pyreverse`, if the optional `pyreverse` extra is installed.

## Interpretation

The Python AST graphs show Python files, imports, functions, classes, calls, tests, packaging helpers, and documentation helpers. They do not explain the native extension core.

For Parselmouth, the more relevant architecture views are experimental:

- repository scan;
- CMake target graph;
- pybind11 binding graph.

Those modes are intentionally lightweight. They use filesystem scanning and regular expressions rather than full CMake or C++ parsers.
