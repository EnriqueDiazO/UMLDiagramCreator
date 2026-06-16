from pathlib import Path
import subprocess

import pytest

from uml_diagram_creator.integrations import pyreverse_runner as runner


def test_parse_formats_normalizes_and_deduplicates() -> None:
    assert runner.parse_formats("dot,png,svg") == ("dot", "png", "svg")
    assert runner.parse_formats(" PNG, dot ,png ") == ("png", "dot")
    assert runner.parse_formats(["svg", "dot"]) == ("svg", "dot")


def test_parse_formats_rejects_unknown_or_empty_values() -> None:
    with pytest.raises(ValueError, match="Formato no soportado"):
        runner.parse_formats("dot,pdf")
    with pytest.raises(ValueError, match="al menos un formato"):
        runner.parse_formats(" , ")


def test_expected_output_names() -> None:
    output = Path("results") / "pyreverse" / "demo"
    assert runner.default_project_name(Path("src/demo_project")) == "demo_project"
    assert runner.default_project_name(Path("src/demo_file.py")) == "demo_file"
    assert runner.default_output_dir("demo") == Path("results") / "pyreverse" / "demo"
    assert runner.expected_dot_paths(output, "demo") == (
        output / "classes_demo.dot",
        output / "packages_demo.dot",
    )
    assert runner.expected_paths(output, "demo", ("dot", "png")) == (
        output / "classes_demo.dot",
        output / "packages_demo.dot",
        output / "classes_demo.png",
        output / "packages_demo.png",
    )


def test_run_pyreverse_to_dot_uses_subprocess_without_graphviz(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "pkg"
    target.mkdir()
    output = tmp_path / "out"
    calls = []

    def fake_run(command, cwd=None, text=None, capture_output=None, check=None):
        calls.append(command)
        output.mkdir(exist_ok=True)
        (output / "classes_demo.dot").write_text("digraph classes {}", encoding="utf-8")
        (output / "packages_demo.dot").write_text("digraph packages {}", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(runner, "is_pyreverse_available", lambda: True)
    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    completed = runner.run_pyreverse_to_dot((target,), "demo", output)

    assert completed.returncode == 0
    assert calls
    assert calls[0][0:5] == (runner.sys.executable, "-m", "pylint.pyreverse.main", "-o", "dot")
    assert (output / "classes_demo.dot").exists()


def test_run_pyreverse_fails_cleanly_when_graphviz_is_missing(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "pkg"
    target.mkdir()
    output = tmp_path / "out"

    def fake_run_to_dot(targets, project_name, output_dir):
        output_dir.mkdir()
        (output_dir / "classes_demo.dot").write_text("digraph classes {}", encoding="utf-8")
        return subprocess.CompletedProcess(["pyreverse"], 0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_pyreverse_to_dot", fake_run_to_dot)
    monkeypatch.setattr(runner, "find_graphviz_dot", lambda: None)

    with pytest.raises(runner.PyreverseError, match="No se encontro Graphviz"):
        runner.run_pyreverse(target, project_name="demo", output_dir=output, formats="dot,png")


def test_run_pyreverse_converts_dot_files_with_monkeypatched_dot(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "pkg"
    target.mkdir()
    output = tmp_path / "out"

    def fake_run_to_dot(targets, project_name, output_dir):
        output_dir.mkdir()
        (output_dir / "classes_demo.dot").write_text("digraph classes {}", encoding="utf-8")
        (output_dir / "packages_demo.dot").write_text("digraph packages {}", encoding="utf-8")
        return subprocess.CompletedProcess(["pyreverse"], 0, stdout="", stderr="")

    def fake_convert(dot_file, output_format, dot_executable):
        path = dot_file.with_suffix(f".{output_format}")
        path.write_text("image", encoding="utf-8")
        return path

    monkeypatch.setattr(runner, "run_pyreverse_to_dot", fake_run_to_dot)
    monkeypatch.setattr(runner, "find_graphviz_dot", lambda: "/usr/bin/dot")
    monkeypatch.setattr(runner, "convert_dot_file", fake_convert)

    result = runner.run_pyreverse(target, project_name="demo", output_dir=output, formats="dot,png,svg")

    names = {path.name for path in result.generated_files}
    assert {
        "classes_demo.dot",
        "packages_demo.dot",
        "classes_demo.png",
        "packages_demo.png",
        "classes_demo.svg",
        "packages_demo.svg",
    } <= names
