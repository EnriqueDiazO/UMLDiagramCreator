from __future__ import annotations

from typing import Any


GROUPS: dict[str, dict[str, str]] = {
    "module": {"label": "module", "color": "#dbeafe", "border": "#2563eb", "shape": "box"},
    "class": {"label": "class", "color": "#dcfce7", "border": "#16a34a", "shape": "box"},
    "function": {"label": "function", "color": "#fef3c7", "border": "#d97706", "shape": "dot"},
    "method": {"label": "method", "color": "#e0e7ff", "border": "#4f46e5", "shape": "dot"},
    "classmethod": {"label": "classmethod", "color": "#ede9fe", "border": "#7c3aed", "shape": "dot"},
    "staticmethod": {"label": "staticmethod", "color": "#fae8ff", "border": "#c026d3", "shape": "dot"},
    "property": {"label": "property", "color": "#ccfbf1", "border": "#0f766e", "shape": "dot"},
    "import": {"label": "import", "color": "#e2e8f0", "border": "#475569", "shape": "box"},
    "external": {"label": "external", "color": "#f1f5f9", "border": "#64748b", "shape": "dot"},
    "internal": {"label": "internal", "color": "#dbeafe", "border": "#1d4ed8", "shape": "dot"},
    "private": {"label": "private", "color": "#fee2e2", "border": "#dc2626", "shape": "dot"},
    "dunder": {"label": "dunder", "color": "#ffedd5", "border": "#ea580c", "shape": "dot"},
    "repository": {"label": "repository", "color": "#fef9c3", "border": "#ca8a04", "shape": "box"},
    "repo_category": {"label": "repo category", "color": "#e5e7eb", "border": "#4b5563", "shape": "box"},
    "folder": {"label": "folder", "color": "#f1f5f9", "border": "#64748b", "shape": "box"},
    "source_folder": {"label": "source folder", "color": "#dbeafe", "border": "#2563eb", "shape": "box"},
    "python_package": {"label": "python package", "color": "#dbeafe", "border": "#2563eb", "shape": "box"},
    "cpp_source": {"label": "C++ source", "color": "#fee2e2", "border": "#dc2626", "shape": "box"},
    "c_source": {"label": "C source", "color": "#ffe4e6", "border": "#e11d48", "shape": "box"},
    "c_header": {"label": "C/C++ header", "color": "#ffedd5", "border": "#ea580c", "shape": "box"},
    "cmake_build": {"label": "CMake build", "color": "#ccfbf1", "border": "#0f766e", "shape": "box"},
    "cmake_file": {"label": "CMake file", "color": "#ccfbf1", "border": "#0f766e", "shape": "box"},
    "cmake_project": {"label": "CMake project", "color": "#cffafe", "border": "#0891b2", "shape": "box"},
    "cmake_target": {"label": "CMake target", "color": "#dcfce7", "border": "#16a34a", "shape": "box"},
    "cmake_subdirectory": {"label": "CMake subdirectory", "color": "#e0f2fe", "border": "#0284c7", "shape": "box"},
    "source_file": {"label": "source file", "color": "#fef3c7", "border": "#d97706", "shape": "dot"},
    "linked_library": {"label": "linked library", "color": "#ede9fe", "border": "#7c3aed", "shape": "dot"},
    "include_dir": {"label": "include directory", "color": "#f1f5f9", "border": "#475569", "shape": "dot"},
    "pybind11": {"label": "pybind11", "color": "#ddd6fe", "border": "#7c3aed", "shape": "box"},
    "pybind11_module": {"label": "pybind11 module", "color": "#ddd6fe", "border": "#7c3aed", "shape": "box"},
    "pybind11_class": {"label": "pybind11 class", "color": "#e0e7ff", "border": "#4f46e5", "shape": "box"},
    "pybind11_enum": {"label": "pybind11 enum", "color": "#f5d0fe", "border": "#c026d3", "shape": "box"},
    "pybind11_method": {"label": "pybind11 method", "color": "#ede9fe", "border": "#7c3aed", "shape": "dot"},
    "binding_source_file": {"label": "binding source file", "color": "#fef3c7", "border": "#d97706", "shape": "box"},
    "praat_binding_macro": {"label": "Praat binding macro", "color": "#fbcfe8", "border": "#db2777", "shape": "box"},
    "praat_source": {"label": "Praat source", "color": "#fecaca", "border": "#dc2626", "shape": "box"},
    "praat_script": {"label": "Praat script", "color": "#ffe4e6", "border": "#be123c", "shape": "dot"},
    "tests": {"label": "tests", "color": "#dcfce7", "border": "#16a34a", "shape": "box"},
    "docs": {"label": "docs", "color": "#e0f2fe", "border": "#0284c7", "shape": "box"},
    "build_artifact": {"label": "build artifact", "color": "#e5e7eb", "border": "#475569", "shape": "box"},
    "virtual_environment": {"label": "virtual environment", "color": "#fee2e2", "border": "#b91c1c", "shape": "box"},
    "compiled_extension": {"label": "compiled extension", "color": "#fae8ff", "border": "#a21caf", "shape": "box"},
}


RELATION_COLORS = {
    "imports": "#64748b",
    "defines": "#2563eb",
    "inherits": "#16a34a",
    "calls": "#7c3aed",
    "uses": "#d97706",
    "contains": "#2563eb",
    "links": "#7c3aed",
    "includes": "#0f766e",
    "exposes": "#db2777",
}


def is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__") and len(name) > 4


def is_private(name: str) -> bool:
    return name.startswith("_") and not is_dunder(name)


def group_for_node(kind: str, name: str, metadata: dict[str, Any] | None = None) -> str:
    metadata = metadata or {}
    if metadata.get("external"):
        return "external"
    if kind in {"module", "import"}:
        return kind
    if is_dunder(name):
        return "dunder"
    if is_private(name):
        return "private"
    if kind == "method":
        return metadata.get("method_type") or "method"
    return kind if kind in GROUPS else "internal"


def group_style(group: str) -> dict[str, str]:
    return GROUPS.get(group, {"label": group, "color": "#e5e7eb", "border": "#4b5563", "shape": "dot"})
