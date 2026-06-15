from pathlib import Path

from uml_diagram_creator.analyzer.ast_parser import analyze_path
from uml_diagram_creator.analyzer.call_graph import build_call_graph
from uml_diagram_creator.analyzer.class_graph import build_class_graph, build_inheritance_graph
from uml_diagram_creator.analyzer.import_graph import build_import_graph
from uml_diagram_creator.analyzer.project_graph import build_project_graph
from uml_diagram_creator.export.writers import write_graph_outputs
from uml_diagram_creator.render.html_renderer import render_graph_html


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "simple_project"


def test_detects_classes_functions_methods_and_imports() -> None:
    analysis = analyze_path(EXAMPLE)
    class_names = {cls.name for cls in analysis.classes}
    function_names = {func.name for func in analysis.functions}
    method_names = {method.name for method in analysis.methods}
    imports = {imp.resolved for module in analysis.modules for imp in module.imports}

    assert {"User", "AdminUser", "Report", "ReportService"} <= class_names
    assert {"format_report_title", "normalize_email", "create_admin_report", "run"} <= function_names
    assert {"build_report", "save_report", "row_count", "for_current_dir", "default_title"} <= method_names
    assert "models.User" in imports
    assert "utils.normalize_email" in imports


def test_detects_inheritance_and_calls() -> None:
    analysis = analyze_path(EXAMPLE)
    inheritance = build_inheritance_graph(analysis)
    call_graph = build_call_graph(analysis, include_dunder=True)

    inheritance_edges = {(edge.source, edge.target, edge.relation) for edge in inheritance.edges}
    call_edges = {(edge.source, edge.target, edge.relation) for edge in call_graph.edges}

    assert ("models.AdminUser", "models.User", "inherits") in inheritance_edges
    assert ("services.ReportService.build_report", "utils.normalize_email", "calls") in call_edges
    assert ("services.ReportService.build_report", "models.format_report_title", "calls") in call_edges
    assert ("main.run", "services.create_admin_report", "calls") in call_edges


def test_builds_graphs_and_writes_csv_json(tmp_path: Path) -> None:
    analysis = analyze_path(EXAMPLE)
    graphs = [
        build_class_graph(analysis, include_dunder=True),
        build_import_graph(analysis, include_external=True),
        build_project_graph(analysis, include_dunder=True, include_external=True),
    ]

    for graph in graphs:
        assert graph.nodes
        assert graph.edges

    outputs = write_graph_outputs(graphs[-1], tmp_path)
    assert outputs["nodes_csv"].exists()
    assert outputs["edges_csv"].exists()
    assert outputs["graph_json"].exists()
    assert "services.ReportService" in outputs["nodes_csv"].read_text(encoding="utf-8")


def test_html_uses_mathmongo_control_contract(tmp_path: Path) -> None:
    analysis = analyze_path(EXAMPLE)
    graph = build_project_graph(analysis, include_dunder=True, include_external=True)
    output = render_graph_html(graph, tmp_path / "project_graph.html")
    html = output.read_text(encoding="utf-8")

    for text in [
        "▶ Activar física",
        "📌 Congelar posiciones",
        "♻ Resetear física",
        "📌 Fijar nodos seleccionados",
        "🔓 Liberar nodos seleccionados",
        "🧲 Separar por tipo",
        "🧭 Separar por fuente",
        "🧩 Separar componentes",
        "♻ Resetear posiciones",
        "↔ Enderezar enlaces",
        "🔁 Recalcular enlaces",
        "📐 Alinear etiquetas",
        "💾 Descargar grafo actual",
        "📋 Copiar estado JSON",
        "📥 Descargar estado JSON",
        "🎨 Ocultar leyenda",
        "⚙️ Ocultar controles",
    ]:
        assert text in html

    for element_id in [
        'id="physics-overlay"',
        'id="toggle-physics-overlay"',
        'id="left-graph-controls"',
        'id="toggle-left-controls"',
        'id="layout-status"',
        'id="edge-status"',
        'id="download-status"',
        'id="node-info"',
        'id="nodeIdSelector"',
        'id="nodeTypeSelector"',
    ]:
        assert element_id in html

    for function_name in [
        "selectedNodeIds",
        "currentPositionUpdates",
        "fixSelectedNodes",
        "releaseSelectedNodes",
        "freezePhysics",
        "enablePhysics",
        "resetPhysics",
        "applyCurrentPhysics",
    ]:
        assert f"function {function_name}" in html

    assert "multiselect: true" in html
    assert "selectConnectedEdges: false" in html
    assert "Tip: Ctrl/Shift + click selecciona varios nodos" in html
