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
}


RELATION_COLORS = {
    "imports": "#64748b",
    "defines": "#2563eb",
    "inherits": "#16a34a",
    "calls": "#7c3aed",
    "uses": "#d97706",
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
