from pathlib import Path
import subprocess
import sys


SCRIPT = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT.parents[2]
OUTPUT = PROJECT_ROOT / "results" / "pyreverse" / "simple_project"
TARGET = PROJECT_ROOT / "examples" / "simple_project"


def main() -> None:
    print("Generando UML con Pyreverse para examples/simple_project...", flush=True)
    print("Carpeta de salida:", OUTPUT, flush=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "uml_diagram_creator",
        "pyreverse",
        str(TARGET),
        "--project-name",
        "simple_project",
        "--output",
        str(OUTPUT),
        "--formats",
        "dot,png,svg",
    ]

    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


if __name__ == "__main__":
    main()

