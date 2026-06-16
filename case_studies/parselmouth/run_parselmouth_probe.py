from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPT = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT.parents[2]
SRC = PROJECT_ROOT / "src"
CONFIG = SCRIPT.with_name("parselmouth_probe_config.json")

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uml_diagram_creator.analyzer.repo_scan import ScanOptions, scan_repository
from uml_diagram_creator.integrations.pyreverse_runner import is_pyreverse_available


@dataclass
class ProbeResult:
    name: str
    command: list[str]
    output_dir: Path
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the UMLDiagramCreator Parselmouth case study probe.")
    parser.add_argument("parselmouth_path", help="Path to a Parselmouth checkout.")
    parser.add_argument(
        "--output-root",
        default=None,
        help="Output directory. Default: results/case_studies/parselmouth.",
    )
    args = parser.parse_args()

    target = Path(args.parselmouth_path).expanduser().resolve()
    if not target.exists():
        print(f"Parselmouth path does not exist: {target}")
        return 2
    if not target.is_dir():
        print(f"Parselmouth path must be a directory: {target}")
        return 2

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    output_root = Path(args.output_root) if args.output_root else PROJECT_ROOT / config["output_root"]
    output_root.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    results: list[ProbeResult] = []
    for spec in config["python_graphs"]:
        command = [
            sys.executable,
            "-m",
            "uml_diagram_creator",
            spec["command"],
            str(target),
            "--output",
            str(output_root / spec["name"]),
            "--max-nodes",
            str(spec.get("max_nodes", 300)),
        ]
        if spec.get("exclude_tests"):
            command.append("--exclude-tests")
        results.append(run_probe_command(spec["name"], command, output_root / spec["name"], env))

    for spec in config["native_graphs"]:
        command = [
            sys.executable,
            "-m",
            "uml_diagram_creator",
            spec["command"],
            str(target),
            "--output",
            str(output_root / spec["name"]),
            "--max-nodes",
            str(spec.get("max_nodes", 300)),
        ]
        if spec.get("include_third_party"):
            command.append("--include-third-party")
        results.append(run_probe_command(spec["name"], command, output_root / spec["name"], env))

    if is_pyreverse_available():
        pyreverse_output = output_root / "pyreverse"
        command = [
            sys.executable,
            "-m",
            "uml_diagram_creator",
            "pyreverse",
            str(target),
            "--project-name",
            "parselmouth",
            "--output",
            str(pyreverse_output),
            "--formats",
            "dot,png,svg",
        ]
        results.append(run_probe_command("pyreverse", command, pyreverse_output, env))
    else:
        results.append(
            ProbeResult(
                name="pyreverse",
                command=["umlgraph", "pyreverse", str(target)],
                output_dir=output_root / "pyreverse",
                returncode=127,
                stdout="",
                stderr="Skipped: optional pyreverse extra is not installed.",
            )
        )

    summary = scan_repository(
        target,
        ScanOptions(
            include_build_artifacts=False,
            include_venv=False,
            include_third_party=True,
        ),
    )
    report_path = output_root / "REPORT.md"
    report_path.write_text(build_report(target, output_root, summary, results), encoding="utf-8")
    print(f"Report written to: {report_path}")
    return 0


def run_probe_command(name: str, command: list[str], output_dir: Path, env: dict[str, str]) -> ProbeResult:
    print(f"Running {name}...")
    completed = subprocess.run(command, cwd=PROJECT_ROOT, env=env, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        print(f"  failed with exit code {completed.returncode}")
    else:
        print(f"  ok: {output_dir}")
    return ProbeResult(
        name=name,
        command=command,
        output_dir=output_dir,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def build_report(target: Path, output_root: Path, summary, results: list[ProbeResult]) -> str:
    lines: list[str] = [
        "# Parselmouth Case Study Report",
        "",
        f"Repository: `{target}`",
        f"Output root: `{output_root}`",
        "",
        "This report is generated by `case_studies/parselmouth/run_parselmouth_probe.py`.",
        "",
        "The repository scan includes embedded third-party trees for architecture counts, but excludes build artifacts and virtual environments from file traversal by default.",
        "",
        "## Repository Scan",
        "",
        f"Total scanned files: **{summary.total_files}**",
        "",
        "### Counts by Extension",
        "",
    ]

    for key in [".py", ".cpp", ".h", ".c", ".cmake", "CMakeLists.txt", ".so", ".praat"]:
        lines.append(f"- `{key}`: {summary.extension_counts.get(key, 0)}")

    lines.extend(["", "### Counts by Main Folder", ""])
    for key in ["src/", "praat/", "pybind11/", "tests/", "docs/", "_skbuild/"]:
        lines.append(f"- `{key}`: {summary.folder_counts.get(key, 0)}")

    extra_folders = [
        (folder, count)
        for folder, count in summary.folder_counts.most_common()
        if folder not in {"src/", "praat/", "pybind11/", "tests/", "docs/", "_skbuild/"}
    ][:12]
    if extra_folders:
        lines.extend(["", "Other frequent top-level folders:", ""])
        for folder, count in extra_folders:
            lines.append(f"- `{folder}`: {count}")

    lines.extend(["", "### Warnings", ""])
    if summary.warnings:
        for warning in summary.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- No build or virtual-environment directories were detected by the warning scan.")

    lines.extend(["", "## Generated Outputs", ""])
    for result in results:
        status = "ok" if result.ok else f"failed/skipped ({result.returncode})"
        lines.append(f"### {result.name}")
        lines.append("")
        lines.append(f"- Status: {status}")
        lines.append(f"- Output directory: `{result.output_dir}`")
        for artifact in sorted(result.output_dir.glob("*")) if result.output_dir.exists() else []:
            if artifact.suffix in {".html", ".json", ".csv", ".dot", ".png", ".svg"}:
                lines.append(f"- `{artifact}`")
        if not result.ok:
            detail = (result.stderr or result.stdout).strip()
            if detail:
                lines.append("")
                lines.append("```text")
                lines.append(detail[:2000])
                lines.append("```")
        lines.append("")

    py_count = summary.extension_counts.get(".py", 0)
    cpp_count = summary.extension_counts.get(".cpp", 0)
    h_count = summary.extension_counts.get(".h", 0)
    cmake_count = summary.extension_counts.get("CMakeLists.txt", 0) + summary.extension_counts.get(".cmake", 0)

    lines.extend(
        [
            "## Technical conclusion",
            "",
            (
                "UMLDiagramCreator can currently visualize the Python surface of Parselmouth: "
                "tests, documentation helpers, packaging scripts, and Python utility files. "
                f"In this scan it found {py_count} `.py` files."
            ),
            "",
            (
                "However, the core architecture of Parselmouth is not represented by the current Python AST analyzer "
                "because the project is mainly a native extension built with C++, CMake, pybind11, and an embedded Praat source tree. "
                f"This scan found {cpp_count} `.cpp` files, {h_count} `.h` files, and {cmake_count} CMake-related files."
            ),
            "",
            "Pyreverse has the same limitation because it is also Python-oriented.",
            "",
            "To properly visualize Parselmouth, UMLDiagramCreator needs additional analyzers for:",
            "",
            "- CMake target graphs;",
            "- C/C++ include graphs;",
            "- pybind11 binding graphs;",
            "- native-extension build graphs;",
            "- repository-level architecture graphs.",
            "",
            "This case study adds first experimental versions of `repo-scan`, `cmake-graph`, and `pybind11-graph`. "
            "They are useful as architectural probes, but they are not full parsers for CMake or C++.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
