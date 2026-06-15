from __future__ import annotations

from .graph_utils import class_node, external_node, finalize_graph, function_node, is_internal_target, make_edge
from .model import GraphData, ProjectAnalysis


def build_class_graph(
    analysis: ProjectAnalysis,
    *,
    include_private: bool = False,
    include_dunder: bool = False,
    include_external: bool = False,
) -> GraphData:
    graph = GraphData(name="Class Graph", graph_type="class")
    class_ids = analysis.class_ids

    for cls in analysis.classes:
        if not include_private and cls.name.startswith("_") and not _is_dunder(cls.name):
            continue
        graph.nodes.append(class_node(cls))
        for method in cls.methods:
            if not _include_member(method.name, include_private, include_dunder):
                continue
            graph.nodes.append(function_node(method))
            graph.edges.append(make_edge(cls.qualname, method.qualname, "defines"))

        for base in cls.resolved_bases:
            if base in class_ids:
                graph.edges.append(make_edge(cls.qualname, base, "inherits"))
            elif include_external:
                graph.nodes.append(external_node(base))
                graph.edges.append(make_edge(cls.qualname, base, "inherits"))

        for method in cls.methods:
            if not _include_member(method.name, include_private, include_dunder):
                continue
            for target in method.resolved_calls:
                if target in class_ids and target != cls.qualname:
                    graph.edges.append(make_edge(cls.qualname, target, "uses"))
                elif include_external and target and not is_internal_target(target, analysis):
                    graph.nodes.append(external_node(target))
                    graph.edges.append(make_edge(cls.qualname, target, "uses"))

    return finalize_graph(graph)


def build_inheritance_graph(
    analysis: ProjectAnalysis,
    *,
    include_private: bool = False,
    include_dunder: bool = False,
    include_external: bool = False,
) -> GraphData:
    graph = GraphData(name="Inheritance Graph", graph_type="inheritance")
    class_ids = analysis.class_ids
    for cls in analysis.classes:
        if not include_private and cls.name.startswith("_") and not _is_dunder(cls.name):
            continue
        graph.nodes.append(class_node(cls))
        for base in cls.resolved_bases:
            if base in class_ids:
                graph.edges.append(make_edge(cls.qualname, base, "inherits"))
            elif include_external:
                graph.nodes.append(external_node(base))
                graph.edges.append(make_edge(cls.qualname, base, "inherits"))
    return finalize_graph(graph)


def _include_member(name: str, include_private: bool, include_dunder: bool) -> bool:
    if _is_dunder(name):
        return include_dunder
    if name.startswith("_"):
        return include_private
    return True


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__") and len(name) > 4
