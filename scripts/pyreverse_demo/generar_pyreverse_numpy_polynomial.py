from pathlib import Path

from uml_diagram_creator.integrations.pyreverse_runner import PyreverseError, run_pyreverse


SCRIPT = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT.parents[2]
OUTPUT = PROJECT_ROOT / "results" / "pyreverse" / "numpy_polynomial"


def main() -> None:
    try:
        import numpy
    except ImportError:
        print("No se pudo importar NumPy. Instala NumPy o ejecuta solo el ejemplo simple_project.", flush=True)
        return

    numpy_root = Path(numpy.__file__).resolve().parent
    targets = [
        numpy_root / "polynomial" / "_polybase.py",
        numpy_root / "polynomial" / "polynomial.py",
    ]
    missing = [str(target) for target in targets if not target.exists()]
    if missing:
        print("No se encontraron los archivos esperados de NumPy:", flush=True)
        for path in missing:
            print("-", path, flush=True)
        return

    print("Generando UML con Pyreverse para numpy.polynomial...", flush=True)
    print("Carpeta de salida:", OUTPUT, flush=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    try:
        result = run_pyreverse(targets, project_name="numpy_polynomial", output_dir=OUTPUT, formats="dot,png,svg")
    except PyreverseError as exc:
        print(str(exc), flush=True)
        return

    print("Archivos generados:", flush=True)
    for path in result.generated_files:
        print("-", path, flush=True)


if __name__ == "__main__":
    main()
