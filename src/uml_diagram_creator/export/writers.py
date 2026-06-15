from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from uml_diagram_creator.analyzer.model import GraphData


def write_nodes_csv(graph: GraphData, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [node.to_record() for node in graph.nodes]
    write_csv_rows(rows, path)
    return path


def write_edges_csv(graph: GraphData, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [edge.to_record() for edge in graph.edges]
    write_csv_rows(rows, path)
    return path


def write_graph_json(graph: GraphData, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_graph_outputs(graph: GraphData, output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    return {
        "nodes_csv": write_nodes_csv(graph, output / "nodes.csv"),
        "edges_csv": write_edges_csv(graph, output / "edges.csv"),
        "graph_json": write_graph_json(graph, output / "graph.json"),
    }


def write_csv_rows(rows: list[dict[str, Any]], path: Path) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    if not fieldnames:
        fieldnames = ["id"]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
