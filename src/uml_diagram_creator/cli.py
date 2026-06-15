from __future__ import annotations

import argparse
from pathlib import Path

from uml_diagram_creator.analyzer.ast_parser import analyze_path
from uml_diagram_creator.analyzer.call_graph import build_call_graph
from uml_diagram_creator.analyzer.class_graph import build_class_graph, build_inheritance_graph
from uml_diagram_creator.analyzer.import_graph import build_import_graph
from uml_diagram_creator.analyzer.project_graph import build_project_graph
from uml_diagram_creator.export.writers import write_graph_outputs
from uml_diagram_creator.render.html_renderer import render_graph_html


GRAPH_BUILDERS = {
    "class": build_class_graph,
    "inheritance": build_inheritance_graph,
    "call": build_call_graph,
    "import": build_import_graph,
    "project": build_project_graph,
}

HTML_FILENAMES = {
    "class": "class_graph.html",
    "inheritance": "inheritance_graph.html",
    "call": "call_graph.html",
    "import": "import_graph.html",
    "project": "project_graph.html",
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="umlgraph",
        description="Analyze Python source statically and render interactive code graphs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_graph_command(subparsers, "analyze", default_graph="project", help_text="Analyze a file or project.")
    add_graph_command(subparsers, "class-graph", default_graph="class", help_text="Render a class graph.")
    add_graph_command(subparsers, "inheritance-graph", default_graph="inheritance", help_text="Render an inheritance graph.")
    add_graph_command(subparsers, "call-graph", default_graph="call", help_text="Render a call graph.")
    add_graph_command(subparsers, "import-graph", default_graph="import", help_text="Render an import graph.")
    add_graph_command(subparsers, "project-graph", default_graph="project", help_text="Render a combined project graph.")
    return parser


def add_graph_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    *,
    default_graph: str,
    help_text: str,
) -> None:
    command = subparsers.add_parser(name, help=help_text)
    command.add_argument("path", help="Python file or project directory to analyze.")
    command.add_argument(
        "--graph",
        choices=sorted(GRAPH_BUILDERS),
        default=default_graph,
        help=f"Graph type to build. Default: {default_graph}.",
    )
    command.add_argument("--output", default=None, help="Output directory. Default: results/<project_name>.")
    command.add_argument("--max-nodes", type=int, default=300, help="Maximum nodes to render in HTML.")
    command.add_argument("--include-private", action="store_true", help="Include names starting with a single underscore.")
    command.add_argument("--include-dunder", action="store_true", help="Include __dunder__ methods and functions.")
    command.add_argument("--include-external", action="store_true", help="Include external imports/calls as nodes.")
    command.add_argument("--exclude-tests", action="store_true", help="Skip test/test_* paths.")
    command.add_argument("--exclude-venv", action=argparse.BooleanOptionalAction, default=True, help="Skip virtualenv paths.")
    command.add_argument("--focus", default="", help="Comma-separated node ids or labels to keep around.")
    command.add_argument("--depth-in", type=int, default=1, help="Inbound focus depth. Reserved for growth.")
    command.add_argument("--depth-out", type=int, default=2, help="Outbound focus depth. Reserved for growth.")
    command.add_argument("--no-html", action="store_true", help="Skip HTML rendering.")
    command.add_argument("--csv", action="store_true", help="Write CSV outputs. Enabled by default.")
    command.add_argument("--json", action="store_true", help="Write JSON output. Enabled by default.")
    command.set_defaults(func=run_graph_command)


def run_graph_command(args: argparse.Namespace) -> int:
    target = Path(args.path)
    output_dir = Path(args.output) if args.output else Path("results") / project_name(target)
    analysis = analyze_path(target, exclude_tests=args.exclude_tests, exclude_venv=args.exclude_venv)
    builder = GRAPH_BUILDERS[args.graph]

    graph = builder(
        analysis,
        include_private=args.include_private,
        include_dunder=args.include_dunder,
        include_external=args.include_external,
    )
    graph = apply_focus(graph, args.focus, args.depth_in, args.depth_out)
    if args.max_nodes and args.max_nodes > 0 and len(graph.nodes) > args.max_nodes:
        graph = limit_graph_nodes(graph, args.max_nodes)

    outputs = write_graph_outputs(graph, output_dir)
    if not args.no_html:
        html_path = output_dir / HTML_FILENAMES[args.graph]
        render_graph_html(graph, html_path)
        outputs["html"] = html_path

    print(f"Analyzed: {target}")
    print(f"Graph: {args.graph}")
    print(f"Nodes: {len(graph.nodes)}")
    print(f"Edges: {len(graph.edges)}")
    for label, path in outputs.items():
        print(f"{label}: {path}")
    return 0


def project_name(path: Path) -> str:
    path = path.resolve()
    return path.stem if path.is_file() else path.name


def apply_focus(graph, focus: str, depth_in: int, depth_out: int):
    seeds = [item.strip() for item in focus.split(",") if item.strip()]
    if not seeds:
        return graph

    ids_by_label = {node.label: node.id for node in graph.nodes}
    seed_ids = {seed if any(node.id == seed for node in graph.nodes) else ids_by_label.get(seed, seed) for seed in seeds}
    node_ids = expand_focus(graph, seed_ids, depth_in=max(0, depth_in), depth_out=max(0, depth_out))
    return subgraph(graph, node_ids)


def expand_focus(graph, seeds: set[str], *, depth_in: int, depth_out: int) -> set[str]:
    incoming = {}
    outgoing = {}
    for edge in graph.edges:
        outgoing.setdefault(edge.source, set()).add(edge.target)
        incoming.setdefault(edge.target, set()).add(edge.source)

    visible = {seed for seed in seeds if any(node.id == seed for node in graph.nodes)}
    frontier = set(visible)
    for _ in range(depth_out):
        frontier = {target for node in frontier for target in outgoing.get(node, set())}
        visible.update(frontier)
    frontier = set(visible)
    for _ in range(depth_in):
        frontier = {source for node in frontier for source in incoming.get(node, set())}
        visible.update(frontier)
    return visible


def limit_graph_nodes(graph, max_nodes: int):
    ranked = sorted(graph.nodes, key=lambda node: (node.degree, node.out_degree, node.in_degree, node.id), reverse=True)
    keep = {node.id for node in ranked[:max_nodes]}
    return subgraph(graph, keep)


def subgraph(graph, node_ids: set[str]):
    from uml_diagram_creator.analyzer.graph_utils import finalize_graph
    from uml_diagram_creator.analyzer.model import GraphData

    selected = GraphData(name=graph.name, graph_type=graph.graph_type)
    selected.nodes = [node for node in graph.nodes if node.id in node_ids]
    selected.edges = [edge for edge in graph.edges if edge.source in node_ids and edge.target in node_ids]
    return finalize_graph(selected)


if __name__ == "__main__":
    raise SystemExit(main())
