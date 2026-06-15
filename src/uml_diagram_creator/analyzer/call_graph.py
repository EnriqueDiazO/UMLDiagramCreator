from __future__ import annotations

from .graph_utils import external_node, finalize_graph, function_node, is_internal_target, make_edge
from .model import GraphData, ProjectAnalysis


def build_call_graph(
    analysis: ProjectAnalysis,
    *,
    include_private: bool = False,
    include_dunder: bool = False,
    include_external: bool = False,
) -> GraphData:
    graph = GraphData(name="Call Graph", graph_type="call")
    callable_ids = analysis.callable_ids

    included_callables = [
        func for func in analysis.callables if _include_callable(func.name, include_private, include_dunder)
    ]
    for func in included_callables:
        graph.nodes.append(function_node(func))

    included_ids = {func.qualname for func in included_callables}
    for func in included_callables:
        for target in func.resolved_calls:
            if target in callable_ids and target in included_ids:
                graph.edges.append(make_edge(func.qualname, target, "calls"))
            elif include_external and target and not is_internal_target(target, analysis):
                graph.nodes.append(external_node(target))
                graph.edges.append(make_edge(func.qualname, target, "calls"))

    return finalize_graph(graph)


def _include_callable(name: str, include_private: bool, include_dunder: bool) -> bool:
    if name.startswith("__") and name.endswith("__") and len(name) > 4:
        return include_dunder
    if name.startswith("_"):
        return include_private
    return True
