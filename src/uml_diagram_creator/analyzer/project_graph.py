from __future__ import annotations

from .graph_utils import (
    class_node,
    external_node,
    finalize_graph,
    function_node,
    is_internal_target,
    make_edge,
    module_node,
)
from .import_graph import external_package_name, module_target
from .model import GraphData, ProjectAnalysis


def build_project_graph(
    analysis: ProjectAnalysis,
    *,
    include_private: bool = False,
    include_dunder: bool = False,
    include_external: bool = False,
) -> GraphData:
    graph = GraphData(name="Project Graph", graph_type="project")
    module_names = analysis.module_names
    class_ids = analysis.class_ids
    callable_ids = analysis.callable_ids

    for module in analysis.modules:
        graph.nodes.append(module_node(module))
        for cls in module.classes:
            if not _include_name(cls.name, include_private, include_dunder):
                continue
            graph.nodes.append(class_node(cls))
            graph.edges.append(make_edge(module.name, cls.qualname, "defines"))
            for method in cls.methods:
                if not _include_name(method.name, include_private, include_dunder):
                    continue
                graph.nodes.append(function_node(method))
                graph.edges.append(make_edge(cls.qualname, method.qualname, "defines"))
        for func in module.functions:
            if not _include_name(func.name, include_private, include_dunder):
                continue
            graph.nodes.append(function_node(func))
            graph.edges.append(make_edge(module.name, func.qualname, "defines"))

    included_nodes = {node.id for node in graph.nodes}
    for module in analysis.modules:
        for imp in module.imports:
            target = module_target(imp.resolved, module_names)
            if target in module_names:
                graph.edges.append(make_edge(module.name, target, "imports", imported=imp.resolved, alias=imp.alias or ""))
            elif include_external:
                external = external_package_name(imp.resolved)
                graph.nodes.append(external_node(external, kind="import"))
                graph.edges.append(make_edge(module.name, external, "imports", imported=imp.resolved, alias=imp.alias or ""))

        for cls in module.classes:
            if cls.qualname not in included_nodes:
                continue
            for base in cls.resolved_bases:
                if base in class_ids and base in included_nodes:
                    graph.edges.append(make_edge(cls.qualname, base, "inherits"))
                elif include_external:
                    graph.nodes.append(external_node(base))
                    graph.edges.append(make_edge(cls.qualname, base, "inherits"))

            for method in cls.methods:
                if method.qualname not in included_nodes:
                    continue
                _add_call_edges(graph, method.qualname, method.resolved_calls, callable_ids, included_nodes, analysis, include_external)
                for target in method.resolved_calls:
                    if target in class_ids and target in included_nodes:
                        graph.edges.append(make_edge(cls.qualname, target, "uses"))

        for func in module.functions:
            if func.qualname not in included_nodes:
                continue
            _add_call_edges(graph, func.qualname, func.resolved_calls, callable_ids, included_nodes, analysis, include_external)

    return finalize_graph(graph)


def _add_call_edges(
    graph: GraphData,
    source: str,
    targets: list[str],
    callable_ids: set[str],
    included_nodes: set[str],
    analysis: ProjectAnalysis,
    include_external: bool,
) -> None:
    for target in targets:
        if target in callable_ids and target in included_nodes:
            graph.edges.append(make_edge(source, target, "calls"))
        elif include_external and target and not is_internal_target(target, analysis):
            graph.nodes.append(external_node(target))
            graph.edges.append(make_edge(source, target, "calls"))


def _include_name(name: str, include_private: bool, include_dunder: bool) -> bool:
    if name.startswith("__") and name.endswith("__") and len(name) > 4:
        return include_dunder
    if name.startswith("_"):
        return include_private
    return True
