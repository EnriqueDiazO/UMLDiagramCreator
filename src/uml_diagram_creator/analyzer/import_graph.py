from __future__ import annotations

from .graph_utils import external_node, finalize_graph, make_edge, module_node
from .model import GraphData, ProjectAnalysis


def build_import_graph(
    analysis: ProjectAnalysis,
    *,
    include_private: bool = False,
    include_dunder: bool = False,
    include_external: bool = False,
) -> GraphData:
    graph = GraphData(name="Import Graph", graph_type="import")
    module_names = analysis.module_names

    for module in analysis.modules:
        graph.nodes.append(module_node(module))

    for module in analysis.modules:
        for imp in module.imports:
            target = module_target(imp.resolved, module_names)
            if target in module_names:
                graph.edges.append(make_edge(module.name, target, "imports", imported=imp.resolved, alias=imp.alias or ""))
            elif include_external:
                external = external_package_name(imp.resolved)
                graph.nodes.append(external_node(external, kind="import"))
                graph.edges.append(make_edge(module.name, external, "imports", imported=imp.resolved, alias=imp.alias or ""))

    return finalize_graph(graph)


def module_target(resolved: str, module_names: set[str]) -> str:
    candidates = sorted(module_names, key=len, reverse=True)
    for module_name in candidates:
        if resolved == module_name or resolved.startswith(module_name + "."):
            return module_name
    return resolved


def external_package_name(resolved: str) -> str:
    return resolved.split(".")[0] if resolved else "external"
