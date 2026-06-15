from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def short_docstring(text: str | None, limit: int = 160) -> str:
    if not text:
        return ""
    compact = " ".join(text.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


@dataclass
class ImportInfo:
    module: str
    name: str | None
    alias: str | None
    level: int = 0
    lineno: int = 0
    resolved: str = ""

    @property
    def local_name(self) -> str:
        return self.alias or self.name or self.module.split(".")[0]


@dataclass
class FunctionInfo:
    name: str
    qualname: str
    module: str
    file: str
    lineno: int
    args: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str = ""
    calls: list[str] = field(default_factory=list)
    resolved_calls: list[str] = field(default_factory=list)
    class_name: str | None = None
    method_type: str | None = None

    @property
    def is_method(self) -> bool:
        return self.class_name is not None


@dataclass
class ClassInfo:
    name: str
    qualname: str
    module: str
    file: str
    lineno: int
    bases: list[str] = field(default_factory=list)
    resolved_bases: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str = ""
    methods: list[FunctionInfo] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)


@dataclass
class ModuleInfo:
    name: str
    file: str
    imports: list[ImportInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)


@dataclass
class ProjectAnalysis:
    root: str
    modules: list[ModuleInfo] = field(default_factory=list)

    @property
    def module_names(self) -> set[str]:
        return {module.name for module in self.modules}

    @property
    def classes(self) -> list[ClassInfo]:
        return [item for module in self.modules for item in module.classes]

    @property
    def functions(self) -> list[FunctionInfo]:
        return [item for module in self.modules for item in module.functions]

    @property
    def methods(self) -> list[FunctionInfo]:
        return [method for cls in self.classes for method in cls.methods]

    @property
    def callables(self) -> list[FunctionInfo]:
        return self.functions + self.methods

    @property
    def class_ids(self) -> set[str]:
        return {cls.qualname for cls in self.classes}

    @property
    def callable_ids(self) -> set[str]:
        return {func.qualname for func in self.callables}

    @property
    def node_ids(self) -> set[str]:
        return self.module_names | self.class_ids | self.callable_ids


@dataclass
class GraphNode:
    id: str
    label: str
    kind: str
    group: str
    module: str = ""
    file: str = ""
    lineno: int | None = None
    title: str = ""
    shape: str = "dot"
    color: str = ""
    border_color: str = ""
    value: int = 12
    metadata: dict[str, Any] = field(default_factory=dict)
    degree: int = 0
    in_degree: int = 0
    out_degree: int = 0
    component: str = ""

    def to_vis(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "group": self.group,
            "kind": self.kind,
            "module": self.module,
            "file": self.file,
            "lineno": self.lineno,
            "title": self.title,
            "shape": self.shape,
            "value": self.value,
            "degree": self.degree,
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "component": self.component,
            "metadata": self.metadata,
        }
        if self.color or self.border_color:
            data["color"] = {
                "background": self.color or "#e5e7eb",
                "border": self.border_color or "#4b5563",
            }
        return data

    def to_record(self) -> dict[str, Any]:
        record = {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "group": self.group,
            "module": self.module,
            "file": self.file,
            "lineno": self.lineno or "",
            "degree": self.degree,
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "component": self.component,
            "shape": self.shape,
            "color": self.color,
        }
        for key, value in sorted(self.metadata.items()):
            if isinstance(value, (list, tuple, set)):
                record[key] = "; ".join(str(item) for item in value)
            else:
                record[key] = value
        return record


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    label: str = ""
    title: str = ""
    color: str = "#64748b"
    arrows: str = "to"
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = ""

    @property
    def from_id(self) -> str:
        return self.source

    @property
    def to_id(self) -> str:
        return self.target

    def to_vis(self) -> dict[str, Any]:
        return {
            "id": self.id or f"{self.source}::{self.relation}::{self.target}",
            "from": self.source,
            "to": self.target,
            "label": self.label,
            "title": self.title,
            "relation": self.relation,
            "arrows": self.arrows,
            "color": {"color": self.color, "highlight": "#dc2626", "hover": "#dc2626"},
            "metadata": self.metadata,
        }

    def to_record(self) -> dict[str, Any]:
        record = {
            "id": self.id,
            "from": self.source,
            "to": self.target,
            "relation": self.relation,
            "label": self.label,
            "color": self.color,
        }
        for key, value in sorted(self.metadata.items()):
            record[key] = value
        return record


@dataclass
class GraphData:
    name: str
    graph_type: str
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "graph_type": self.graph_type,
            "nodes": [node.to_record() for node in self.nodes],
            "edges": [edge.to_record() for edge in self.edges],
        }

    def to_vis_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "graph_type": self.graph_type,
            "nodes": [node.to_vis() for node in self.nodes],
            "edges": [edge.to_vis() for edge in self.edges],
        }


def as_posix(path: str | Path) -> str:
    return Path(path).as_posix()
