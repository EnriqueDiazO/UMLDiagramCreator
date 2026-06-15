from __future__ import annotations

import html
from collections import defaultdict, deque
from typing import Iterable

from uml_diagram_creator.profiles.generic import RELATION_COLORS, group_for_node, group_style

from .model import ClassInfo, FunctionInfo, GraphData, GraphEdge, GraphNode, ModuleInfo, ProjectAnalysis


def module_node(module: ModuleInfo) -> GraphNode:
    return make_node(
        node_id=module.name,
        label=module.name or "(root)",
        kind="module",
        name=module.name,
        module=module.name,
        file=module.file,
        metadata={"source": module.file},
    )


def class_node(cls: ClassInfo) -> GraphNode:
    return make_node(
        node_id=cls.qualname,
        label=cls.name,
        kind="class",
        name=cls.name,
        module=cls.module,
        file=cls.file,
        lineno=cls.lineno,
        metadata={
            "bases": cls.bases,
            "methods": len(cls.methods),
            "attributes": cls.attributes,
            "decorators": cls.decorators,
            "docstring": cls.docstring,
        },
    )


def function_node(func: FunctionInfo) -> GraphNode:
    kind = "method" if func.is_method else "function"
    return make_node(
        node_id=func.qualname,
        label=func.name,
        kind=kind,
        name=func.name,
        module=func.module,
        file=func.file,
        lineno=func.lineno,
        metadata={
            "args": func.args,
            "decorators": func.decorators,
            "docstring": func.docstring,
            "class": func.class_name or "",
            "method_type": func.method_type or kind,
            "out_calls": len([call for call in func.resolved_calls if call]),
        },
    )


def external_node(node_id: str, kind: str = "external") -> GraphNode:
    label = node_id.split(".")[-1] if node_id else "external"
    return make_node(
        node_id=node_id,
        label=label,
        kind=kind,
        name=label,
        metadata={"external": True},
    )


def make_node(
    *,
    node_id: str,
    label: str,
    kind: str,
    name: str,
    module: str = "",
    file: str = "",
    lineno: int | None = None,
    metadata: dict | None = None,
) -> GraphNode:
    metadata = metadata or {}
    group = group_for_node(kind, name, metadata)
    style = group_style(group)
    node = GraphNode(
        id=node_id,
        label=label,
        kind=kind,
        group=group,
        module=module,
        file=file,
        lineno=lineno,
        shape=style["shape"],
        color=style["color"],
        border_color=style["border"],
        metadata=metadata,
    )
    node.title = node_tooltip(node)
    return node


def make_edge(source: str, target: str, relation: str, *, label: str = "", **metadata: object) -> GraphEdge:
    color = RELATION_COLORS.get(relation, "#64748b")
    edge = GraphEdge(
        source=source,
        target=target,
        relation=relation,
        label=label,
        color=color,
        metadata={key: value for key, value in metadata.items() if value not in (None, "")},
    )
    edge.title = edge_tooltip(edge)
    return edge


def node_tooltip(node: GraphNode) -> str:
    rows = [
        ("Tipo", node.kind),
        ("Grupo", node.group),
        ("Modulo", node.module),
        ("Archivo", node.file),
        ("Linea", node.lineno or ""),
    ]
    for key in ("bases", "methods", "attributes", "args", "decorators", "class", "method_type", "out_calls", "docstring"):
        value = node.metadata.get(key)
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        rows.append((key.replace("_", " ").title(), value or ""))

    body = "<br>".join(
        f"{html.escape(label)}: {html.escape(str(value))}" for label, value in rows if value not in (None, "")
    )
    return f"<b>{html.escape(node.label)}</b><br>{body}"


def edge_tooltip(edge: GraphEdge) -> str:
    relation = html.escape(edge.relation)
    return f"<b>{html.escape(edge.source)}</b><br>{relation}<br><b>{html.escape(edge.target)}</b>"


def finalize_graph(graph: GraphData) -> GraphData:
    graph.nodes = unique_nodes(graph.nodes)
    graph.edges = unique_edges(graph.edges, {node.id for node in graph.nodes})
    node_map = {node.id: node for node in graph.nodes}

    outgoing: dict[str, set[str]] = defaultdict(set)
    incoming: dict[str, set[str]] = defaultdict(set)
    undirected: dict[str, set[str]] = defaultdict(set)
    for edge in graph.edges:
        outgoing[edge.source].add(edge.target)
        incoming[edge.target].add(edge.source)
        undirected[edge.source].add(edge.target)
        undirected[edge.target].add(edge.source)

    components = connected_components(node_map.keys(), undirected)
    for index, component in enumerate(components, start=1):
        label = f"component {index}"
        for node_id in component:
            node = node_map[node_id]
            node.in_degree = len(incoming[node_id])
            node.out_degree = len(outgoing[node_id])
            node.degree = len(incoming[node_id] | outgoing[node_id])
            node.component = label
            node.value = min(50, 12 + node.degree * 4)
            node.metadata.update(
                {
                    "degree": node.degree,
                    "in_degree": node.in_degree,
                    "out_degree": node.out_degree,
                    "component": node.component,
                }
            )
            node.title = node_tooltip(node)

    for idx, edge in enumerate(graph.edges, start=1):
        edge.id = f"e{idx}"
    return graph


def unique_nodes(nodes: Iterable[GraphNode]) -> list[GraphNode]:
    seen: dict[str, GraphNode] = {}
    for node in nodes:
        if node.id and node.id not in seen:
            seen[node.id] = node
    return list(seen.values())


def unique_edges(edges: Iterable[GraphEdge], node_ids: set[str]) -> list[GraphEdge]:
    seen: set[tuple[str, str, str]] = set()
    out: list[GraphEdge] = []
    for edge in edges:
        if not edge.source or not edge.target or edge.source == edge.target:
            continue
        if edge.source not in node_ids or edge.target not in node_ids:
            continue
        key = (edge.source, edge.target, edge.relation)
        if key in seen:
            continue
        seen.add(key)
        out.append(edge)
    return out


def connected_components(node_ids: Iterable[str], adjacency: dict[str, set[str]]) -> list[list[str]]:
    remaining = set(node_ids)
    components: list[list[str]] = []
    while remaining:
        start = min(remaining)
        queue: deque[str] = deque([start])
        remaining.remove(start)
        component: list[str] = []
        while queue:
            node_id = queue.popleft()
            component.append(node_id)
            for neighbor in adjacency.get(node_id, set()):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(component))
    return components


def known_internal_targets(analysis: ProjectAnalysis) -> set[str]:
    return analysis.module_names | analysis.class_ids | analysis.callable_ids


def is_internal_target(target: str, analysis: ProjectAnalysis) -> bool:
    if target in known_internal_targets(analysis):
        return True
    return any(target == name or target.startswith(name + ".") for name in analysis.module_names)
