from pathlib import Path

from uml_diagram_creator.analyzer.cmake_graph import build_cmake_graph, parse_cmake_file
from uml_diagram_creator.analyzer.pybind11_graph import analyze_pybind11_file, build_pybind11_graph
from uml_diagram_creator.analyzer.repo_scan import ScanOptions, scan_repository
from uml_diagram_creator.export.writers import write_graph_outputs
from uml_diagram_creator.render.html_renderer import render_graph_html


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "native_extension_project"


def test_repo_scan_counts_native_extension_files() -> None:
    summary = scan_repository(FIXTURE, ScanOptions(include_third_party=True))

    assert summary.extension_counts[".py"] == 2
    assert summary.extension_counts[".cpp"] == 2
    assert summary.extension_counts[".h"] == 1
    assert summary.extension_counts["CMakeLists.txt"] == 2
    assert summary.folder_counts["src/"] == 4
    assert summary.folder_counts["tests/"] == 1
    assert summary.category_counts["Python package"] == 2
    assert summary.category_counts["C++ source"] == 2
    assert summary.category_counts["CMake build system"] == 2


def test_cmake_graph_detects_projects_targets_sources_and_links() -> None:
    commands = parse_cmake_file(FIXTURE / "CMakeLists.txt")
    command_names = {command.command for command in commands}

    assert {"project", "add_subdirectory", "pybind11_add_module", "target_link_libraries"} <= command_names

    graph = build_cmake_graph(FIXTURE)
    node_ids = {node.id for node in graph.nodes}
    edges = {(edge.source, edge.target, edge.relation) for edge in graph.edges}

    assert "cmake_project:NativeExtensionFixture" in node_ids
    assert "cmake_target:native_fixture" in node_ids
    assert "source:src/bindings.cpp" in node_ids
    assert "library:praatlib" in node_ids
    assert ("cmake_target:native_fixture", "library:praatlib", "links") in edges


def test_pybind11_graph_detects_module_class_enum_macro_and_methods() -> None:
    analysis = analyze_pybind11_file(FIXTURE / "src" / "bindings.cpp")

    assert {module.python_name for module in analysis.modules} == {"native_fixture"}
    assert {"Sound", "SoundKind", "PraatSound"} <= {binding.python_name for binding in analysis.bindings}
    assert {"duration", "name"} <= {method.name for method in analysis.methods}

    graph = build_pybind11_graph(FIXTURE)
    node_ids = {node.id for node in graph.nodes}
    labels = {node.label for node in graph.nodes}

    assert "pybind_module:native_fixture" in node_ids
    assert "Sound" in labels
    assert "PraatSound" in labels
    assert "duration" in labels


def test_native_graphs_write_outputs_without_compilation(tmp_path: Path) -> None:
    for graph in [build_cmake_graph(FIXTURE), build_pybind11_graph(FIXTURE)]:
        output_dir = tmp_path / graph.graph_type
        outputs = write_graph_outputs(graph, output_dir)
        html = render_graph_html(graph, output_dir / f"{graph.graph_type}.html")

        assert outputs["nodes_csv"].exists()
        assert outputs["edges_csv"].exists()
        assert outputs["graph_json"].exists()
        assert html.exists()
