from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from uml_diagram_creator.analyzer.graph_utils import finalize_graph, make_edge, make_node
from uml_diagram_creator.analyzer.model import GraphData
from uml_diagram_creator.analyzer.repo_scan import ScanOptions, iter_project_files, relative_path


CMAKE_COMMANDS = {
    "project",
    "add_subdirectory",
    "pybind11_add_module",
    "add_library",
    "add_executable",
    "target_sources",
    "target_link_libraries",
    "target_include_directories",
}

COMMAND_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)\s*$")


@dataclass(frozen=True)
class CMakeCommand:
    command: str
    args: tuple[str, ...]
    file: Path
    lineno: int


def build_cmake_graph(root: str | Path, options: ScanOptions | None = None) -> GraphData:
    root_path = Path(root).resolve()
    graph = GraphData(name=f"CMake graph: {root_path.name}", graph_type="cmake")
    files = find_cmake_files(root_path, options)

    for cmake_file in files:
        rel_file = relative_path(cmake_file, root_path)
        file_id = f"cmake_file:{rel_file}"
        graph.nodes.append(
            make_node(
                node_id=file_id,
                label=cmake_file.name if cmake_file.name != "CMakeLists.txt" else rel_file,
                kind="cmake_file",
                name=cmake_file.name,
                file=rel_file,
                metadata={"path": rel_file},
            )
        )

        for command in parse_cmake_file(cmake_file):
            add_cmake_command_to_graph(graph, command, file_id, root_path)

    return finalize_graph(graph)


def find_cmake_files(root: Path, options: ScanOptions | None = None) -> list[Path]:
    options = options or ScanOptions()
    files = [
        path
        for path in iter_project_files(root, options)
        if path.name == "CMakeLists.txt" or path.suffix.lower() == ".cmake"
    ]
    return sorted(files)


def parse_cmake_file(path: Path) -> list[CMakeCommand]:
    commands: list[CMakeCommand] = []
    buffer = ""
    start_lineno = 0
    balance = 0
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        cleaned = strip_cmake_comment(line).strip()
        if not cleaned:
            continue

        if not buffer and not re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*\(", cleaned):
            continue
        if not buffer:
            start_lineno = lineno
            buffer = cleaned
            balance = paren_delta(cleaned)
        else:
            buffer += " " + cleaned
            balance += paren_delta(cleaned)

        if balance > 0:
            continue

        match = COMMAND_RE.match(buffer)
        buffer = ""
        balance = 0
        if not match:
            continue
        command = match.group(1).lower()
        if command not in CMAKE_COMMANDS:
            continue
        commands.append(CMakeCommand(command=command, args=tokenize_cmake_args(match.group(2)), file=path, lineno=start_lineno))
    return commands


def add_cmake_command_to_graph(graph: GraphData, command: CMakeCommand, file_id: str, root: Path) -> None:
    if not command.args:
        return

    first = command.args[0]
    rel_file = relative_path(command.file, root)
    metadata = {"command": command.command, "file": rel_file, "lineno": command.lineno, "args": list(command.args)}

    if command.command == "project":
        project_id = f"cmake_project:{first}"
        graph.nodes.append(make_node(node_id=project_id, label=first, kind="cmake_project", name=first, file=rel_file, lineno=command.lineno, metadata=metadata))
        graph.edges.append(make_edge(file_id, project_id, "defines", label="project"))
        return

    if command.command == "add_subdirectory":
        subdir_id = f"cmake_subdirectory:{first}"
        graph.nodes.append(make_node(node_id=subdir_id, label=first, kind="cmake_subdirectory", name=first, file=rel_file, lineno=command.lineno, metadata=metadata))
        graph.edges.append(make_edge(file_id, subdir_id, "contains", label="subdir"))
        return

    if command.command in {"pybind11_add_module", "add_library", "add_executable"}:
        target_kind = "pybind11_module" if command.command == "pybind11_add_module" else "cmake_target"
        target_id = f"cmake_target:{first}"
        graph.nodes.append(make_node(node_id=target_id, label=first, kind=target_kind, name=first, file=rel_file, lineno=command.lineno, metadata=metadata))
        graph.edges.append(make_edge(file_id, target_id, "defines", label=command.command))
        for source in source_like_args(command.args[1:]):
            source_id = f"source:{source}"
            graph.nodes.append(make_node(node_id=source_id, label=source, kind="source_file", name=source, file=source, metadata={"declared_in": rel_file}))
            graph.edges.append(make_edge(target_id, source_id, "uses", label="source"))
        return

    target_id = f"cmake_target:{first}"
    graph.nodes.append(make_node(node_id=target_id, label=first, kind="cmake_target", name=first, file=rel_file, lineno=command.lineno, metadata={"seen_in": rel_file}))
    graph.edges.append(make_edge(file_id, target_id, "uses", label=command.command))

    if command.command == "target_sources":
        for source in source_like_args(command.args[1:]):
            source_id = f"source:{source}"
            graph.nodes.append(make_node(node_id=source_id, label=source, kind="source_file", name=source, file=source, metadata={"declared_in": rel_file}))
            graph.edges.append(make_edge(target_id, source_id, "uses", label="source"))
    elif command.command == "target_link_libraries":
        for library in filtered_target_args(command.args[1:]):
            library_id = f"library:{library}"
            graph.nodes.append(make_node(node_id=library_id, label=library, kind="linked_library", name=library, metadata={"declared_in": rel_file}))
            graph.edges.append(make_edge(target_id, library_id, "links", label="links"))
    elif command.command == "target_include_directories":
        for include_dir in filtered_target_args(command.args[1:]):
            include_id = f"include:{include_dir}"
            graph.nodes.append(make_node(node_id=include_id, label=include_dir, kind="include_dir", name=include_dir, metadata={"declared_in": rel_file}))
            graph.edges.append(make_edge(target_id, include_id, "includes", label="include"))


def tokenize_cmake_args(args: str) -> tuple[str, ...]:
    tokens = re.findall(r'"([^"]+)"|([^\s\)]+)', args)
    return tuple((quoted or bare).strip() for quoted, bare in tokens if (quoted or bare).strip())


def strip_cmake_comment(line: str) -> str:
    in_quote = False
    for index, char in enumerate(line):
        if char == '"':
            in_quote = not in_quote
        if char == "#" and not in_quote:
            return line[:index]
    return line


def paren_delta(text: str) -> int:
    in_quote = False
    delta = 0
    for char in text:
        if char == '"':
            in_quote = not in_quote
        elif not in_quote and char == "(":
            delta += 1
        elif not in_quote and char == ")":
            delta -= 1
    return delta


def source_like_args(args: tuple[str, ...]) -> list[str]:
    return [arg for arg in filtered_target_args(args) if Path(arg).suffix.lower() in {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hh", ".hxx"}]


def filtered_target_args(args: tuple[str, ...]) -> list[str]:
    keywords = {
        "PUBLIC",
        "PRIVATE",
        "INTERFACE",
        "SYSTEM",
        "BEFORE",
        "AFTER",
        "OBJECT",
        "STATIC",
        "SHARED",
        "MODULE",
        "EXCLUDE_FROM_ALL",
    }
    return [arg for arg in args if arg.upper() not in keywords and not arg.startswith("$<")]
