from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from uml_diagram_creator.analyzer.graph_utils import finalize_graph, make_edge, make_node
from uml_diagram_creator.analyzer.model import GraphData


BUILD_ARTIFACT_DIRS = {"build", "dist", "_skbuild"}
VENV_DIRS = {"venv", ".venv", "env", "parsel2-env", "site-packages"}
ALWAYS_EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
THIRD_PARTY_DIRS = {"pybind11", "praat"}

TRACKED_EXTENSIONS = (".py", ".cpp", ".h", ".c", ".cmake", ".so", ".praat")
TRACKED_FOLDERS = ("src", "praat", "pybind11", "tests", "docs", "_skbuild")


@dataclass(frozen=True)
class ScanOptions:
    include_build_artifacts: bool = False
    include_venv: bool = False
    include_third_party: bool = False


@dataclass
class RepoScanSummary:
    root: Path
    total_files: int = 0
    extension_counts: Counter[str] = field(default_factory=Counter)
    folder_counts: Counter[str] = field(default_factory=Counter)
    category_counts: Counter[str] = field(default_factory=Counter)
    warnings: list[str] = field(default_factory=list)
    detected_paths: dict[str, list[str]] = field(default_factory=dict)


def scan_repository(root: str | Path, options: ScanOptions | None = None) -> RepoScanSummary:
    root_path = Path(root).resolve()
    options = options or ScanOptions()
    summary = RepoScanSummary(root=root_path)

    detected_warning_dirs = detect_warning_directories(root_path)
    for path in detected_warning_dirs:
        summary.warnings.append(f"Detected generated or environment-like directory: {path}")

    for file_path in iter_project_files(root_path, options):
        summary.total_files += 1
        rel = relative_path(file_path, root_path)
        summary.extension_counts[extension_key(file_path)] += 1
        summary.folder_counts[folder_key(file_path, root_path)] += 1

        for category in categories_for_file(file_path, root_path):
            summary.category_counts[category] += 1
            summary.detected_paths.setdefault(category, [])
            if len(summary.detected_paths[category]) < 8:
                summary.detected_paths[category].append(rel)

    for folder in TRACKED_FOLDERS:
        summary.folder_counts.setdefault(folder + "/", 0)
    for ext in TRACKED_EXTENSIONS:
        summary.extension_counts.setdefault(ext, 0)
    summary.extension_counts.setdefault("CMakeLists.txt", 0)

    return summary


def build_repo_scan_graph(root: str | Path, options: ScanOptions | None = None) -> GraphData:
    summary = scan_repository(root, options)
    graph = GraphData(name=f"Repo scan: {summary.root.name}", graph_type="repo_scan")

    root_id = "repo:root"
    graph.nodes.append(
        make_node(
            node_id=root_id,
            label=summary.root.name,
            kind="repository",
            name=summary.root.name,
            file=str(summary.root),
            metadata={"total_files": summary.total_files},
        )
    )

    for category, count in sorted(summary.category_counts.items()):
        node_id = f"category:{category}"
        graph.nodes.append(
            make_node(
                node_id=node_id,
                label=category,
                kind=category_kind(category),
                name=category,
                metadata={
                    "files": count,
                    "examples": summary.detected_paths.get(category, []),
                },
            )
        )
        graph.edges.append(make_edge(root_id, node_id, "contains", label=str(count), files=count))

    for folder, count in sorted(summary.folder_counts.items()):
        if count <= 0:
            continue
        node_id = f"folder:{folder}"
        graph.nodes.append(
            make_node(
                node_id=node_id,
                label=folder,
                kind=folder_kind(folder),
                name=folder,
                metadata={"files": count},
            )
        )
        graph.edges.append(make_edge(root_id, node_id, "contains", label=str(count), files=count))

    return finalize_graph(graph)


def iter_project_files(root: Path, options: ScanOptions | None = None) -> Iterable[Path]:
    options = options or ScanOptions()
    root = Path(root)
    for current_raw, dirnames, filenames in os.walk(root):
        current = Path(current_raw)
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if not should_skip_dir(
                dirname,
                include_build_artifacts=options.include_build_artifacts,
                include_venv=options.include_venv,
                include_third_party=options.include_third_party,
            )
        ]
        for filename in filenames:
            yield current / filename


def should_skip_dir(dirname: str, *, include_build_artifacts: bool, include_venv: bool, include_third_party: bool) -> bool:
    if dirname in ALWAYS_EXCLUDE_DIRS:
        return True
    if not include_build_artifacts and dirname in BUILD_ARTIFACT_DIRS:
        return True
    if not include_venv and dirname in VENV_DIRS:
        return True
    if not include_third_party and dirname in THIRD_PARTY_DIRS:
        return True
    return False


def detect_warning_directories(root: Path) -> list[str]:
    warning_names = sorted(BUILD_ARTIFACT_DIRS | VENV_DIRS | {"build", "dist"})
    detected: list[str] = []
    for current_raw, dirnames, _filenames in os.walk(root):
        current = Path(current_raw)
        for dirname in dirnames:
            if dirname in warning_names:
                detected.append(relative_path(current / dirname, root))
        dirnames[:] = [dirname for dirname in dirnames if dirname not in ALWAYS_EXCLUDE_DIRS]
    return detected


def extension_key(file_path: Path) -> str:
    if file_path.name == "CMakeLists.txt":
        return "CMakeLists.txt"
    return file_path.suffix.lower() or "[no extension]"


def folder_key(file_path: Path, root: Path) -> str:
    try:
        relative = file_path.relative_to(root)
    except ValueError:
        return "[outside]/"
    if len(relative.parts) <= 1:
        return "[root]/"
    return relative.parts[0] + "/"


def categories_for_file(file_path: Path, root: Path) -> list[str]:
    categories: list[str] = []
    rel_parts = relative_parts(file_path, root)
    top = rel_parts[0] if rel_parts else ""
    suffix = file_path.suffix.lower()

    if suffix == ".py":
        categories.append("Python package")
    if suffix in {".cpp", ".cc", ".cxx"}:
        categories.append("C++ source")
    if suffix in {".h", ".hpp", ".hh", ".hxx"}:
        categories.append("C headers")
    if suffix == ".c":
        categories.append("C source")
    if file_path.name == "CMakeLists.txt" or suffix == ".cmake":
        categories.append("CMake build system")
    if top == "pybind11" or "pybind11" in rel_parts:
        categories.append("pybind11 subtree")
    if top == "praat" or "praat" in rel_parts:
        categories.append("Praat embedded source")
    if top == "tests" or file_path.name.startswith("test_"):
        categories.append("tests")
    if top == "docs":
        categories.append("docs")
    if top in BUILD_ARTIFACT_DIRS:
        categories.append("build artifacts")
    if any(part in VENV_DIRS for part in rel_parts):
        categories.append("virtual environment")
    if suffix == ".so":
        categories.append("compiled extension .so")
    if suffix == ".praat":
        categories.append("Praat script")

    return categories or ["other files"]


def category_kind(category: str) -> str:
    mapping = {
        "Python package": "python_package",
        "C++ source": "cpp_source",
        "C headers": "c_header",
        "C source": "c_source",
        "CMake build system": "cmake_build",
        "pybind11 subtree": "pybind11",
        "Praat embedded source": "praat_source",
        "tests": "tests",
        "docs": "docs",
        "build artifacts": "build_artifact",
        "virtual environment": "virtual_environment",
        "compiled extension .so": "compiled_extension",
        "Praat script": "praat_script",
    }
    return mapping.get(category, "repo_category")


def folder_kind(folder: str) -> str:
    stripped = folder.rstrip("/")
    mapping = {
        "src": "source_folder",
        "praat": "praat_source",
        "pybind11": "pybind11",
        "tests": "tests",
        "docs": "docs",
        "_skbuild": "build_artifact",
    }
    return mapping.get(stripped, "folder")


def relative_parts(path: Path, root: Path) -> tuple[str, ...]:
    try:
        return path.relative_to(root).parts
    except ValueError:
        return path.parts


def relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
