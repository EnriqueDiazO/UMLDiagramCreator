from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


SUPPORTED_FORMATS = ("dot", "png", "svg")
PYREVERSE_OUTPUT_KINDS = ("classes", "packages")


class PyreverseError(RuntimeError):
    """Raised when the optional Pyreverse/Graphviz flow cannot complete."""


@dataclass(frozen=True)
class PyreverseResult:
    project_name: str
    output_dir: Path
    generated_files: tuple[Path, ...]
    pyreverse_command: tuple[str, ...]


def is_pyreverse_available() -> bool:
    """Return True when pylint's pyreverse module can be imported."""
    try:
        return importlib.util.find_spec("pylint.pyreverse.main") is not None
    except ModuleNotFoundError:
        return False


def find_graphviz_dot() -> str | None:
    """Return the Graphviz dot executable path, if available."""
    return shutil.which("dot")


def parse_formats(formats: str | Iterable[str]) -> tuple[str, ...]:
    """Parse a comma-separated output format list."""
    if isinstance(formats, str):
        raw_items = formats.split(",")
    else:
        raw_items = list(formats)

    parsed: list[str] = []
    for item in raw_items:
        fmt = str(item).strip().lower()
        if not fmt:
            continue
        if fmt not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Formato no soportado: {fmt}. Usa una combinacion de: {', '.join(SUPPORTED_FORMATS)}."
            )
        if fmt not in parsed:
            parsed.append(fmt)

    if not parsed:
        raise ValueError("Debes pedir al menos un formato: dot, png o svg.")
    return tuple(parsed)


def default_project_name(target: str | Path) -> str:
    """Infer a stable project name from a file or directory target."""
    path = Path(target)
    return path.stem if path.suffix == ".py" else path.name


def default_output_dir(project_name: str) -> Path:
    return Path("results") / "pyreverse" / project_name


def expected_dot_paths(output_dir: str | Path, project_name: str) -> tuple[Path, Path]:
    output = Path(output_dir)
    return tuple(output / f"{kind}_{project_name}.dot" for kind in PYREVERSE_OUTPUT_KINDS)  # type: ignore[return-value]


def expected_paths(output_dir: str | Path, project_name: str, formats: Sequence[str]) -> tuple[Path, ...]:
    output = Path(output_dir)
    return tuple(output / f"{kind}_{project_name}.{fmt}" for fmt in formats for kind in PYREVERSE_OUTPUT_KINDS)


def normalize_targets(targets: str | Path | Sequence[str | Path]) -> tuple[Path, ...]:
    if isinstance(targets, (str, Path)):
        items = (targets,)
    else:
        items = tuple(targets)
    return tuple(Path(item) for item in items)


def build_pyreverse_command(targets: Sequence[Path], project_name: str, output_dir: Path) -> tuple[str, ...]:
    return (
        sys.executable,
        "-m",
        "pylint.pyreverse.main",
        "-o",
        "dot",
        "-p",
        project_name,
        "-d",
        str(output_dir),
        *(str(target) for target in targets),
    )


def run_pyreverse_to_dot(targets: Sequence[Path], project_name: str, output_dir: Path) -> subprocess.CompletedProcess[str]:
    if not is_pyreverse_available():
        raise PyreverseError(
            "No se encontro Pyreverse. Instala el extra opcional con:\n"
            '  python -m pip install -e ".[pyreverse]"\n'
            "Tambien puedes probar:\n"
            "  python -m pylint.pyreverse.main --help"
        )

    missing_targets = [str(target) for target in targets if not target.exists()]
    if missing_targets:
        raise PyreverseError("No existen los targets para Pyreverse: " + ", ".join(missing_targets))

    output_dir.mkdir(parents=True, exist_ok=True)
    command = build_pyreverse_command(targets, project_name, output_dir)
    completed = subprocess.run(command, cwd=Path.cwd(), text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        details = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
        raise PyreverseError(
            "No se pudo generar el diagrama. Revisa que pylint y Graphviz esten instalados. "
            "Tambien puedes probar: dot -V y python -m pylint.pyreverse.main --help."
            + (f"\n\nSalida de Pyreverse:\n{details}" if details else "")
        )
    return completed


def find_generated_dot_files(output_dir: Path, project_name: str) -> tuple[Path, ...]:
    expected = [path for path in expected_dot_paths(output_dir, project_name) if path.exists()]
    if expected:
        return tuple(expected)
    return tuple(sorted(output_dir.glob("*.dot")))


def convert_dot_file(dot_file: Path, output_format: str, dot_executable: str) -> Path:
    output_file = dot_file.with_suffix(f".{output_format}")
    command = (dot_executable, f"-T{output_format}", str(dot_file), "-o", str(output_file))
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        details = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
        raise PyreverseError(
            f"No se pudo convertir {dot_file.name} a {output_format} con Graphviz."
            + (f"\n\nSalida de dot:\n{details}" if details else "")
        )
    return output_file


def run_pyreverse(
    targets: str | Path | Sequence[str | Path],
    *,
    project_name: str | None = None,
    output_dir: str | Path | None = None,
    formats: str | Iterable[str] = ("dot", "png", "svg"),
) -> PyreverseResult:
    parsed_formats = parse_formats(formats)
    normalized_targets = normalize_targets(targets)
    if not normalized_targets:
        raise PyreverseError("Debes indicar al menos un archivo, paquete o carpeta Python.")

    resolved_project_name = project_name or default_project_name(normalized_targets[0])
    resolved_output_dir = Path(output_dir) if output_dir else default_output_dir(resolved_project_name)

    completed = run_pyreverse_to_dot(normalized_targets, resolved_project_name, resolved_output_dir)
    dot_files = find_generated_dot_files(resolved_output_dir, resolved_project_name)
    if not dot_files:
        raise PyreverseError(
            f"Pyreverse termino sin errores, pero no se encontraron archivos .dot en {resolved_output_dir}."
        )

    generated: list[Path] = list(dot_files)
    image_formats = [fmt for fmt in parsed_formats if fmt != "dot"]
    if image_formats:
        dot_executable = find_graphviz_dot()
        if dot_executable is None:
            raise PyreverseError(
                "No se encontro Graphviz. Instala el ejecutable 'dot' y verifica con:\n"
                "  dot -V\n"
                "En Ubuntu: sudo apt install graphviz\n"
                "En Windows: winget install Graphviz.Graphviz"
            )
        for fmt in image_formats:
            for dot_file in dot_files:
                generated.append(convert_dot_file(dot_file, fmt, dot_executable))

    requested = set(parsed_formats)
    visible_generated = [path for path in generated if path.suffix.lstrip(".") in requested or path.suffix == ".dot"]
    return PyreverseResult(
        project_name=resolved_project_name,
        output_dir=resolved_output_dir,
        generated_files=tuple(dict.fromkeys(visible_generated)),
        pyreverse_command=tuple(completed.args) if isinstance(completed.args, list) else tuple(completed.args),
    )
