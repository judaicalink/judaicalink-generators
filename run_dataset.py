# run_dataset.py
from pathlib import Path
import sys, argparse, importlib.util

REPO_ROOT = Path(__file__).resolve().parent
DATASETS = REPO_ROOT / "datasets"

def run_slug(slug: str, argv):
    mod_path = DATASETS / slug / "scripts" / "build.py"
    if not mod_path.exists():
        raise SystemExit(f"build.py nicht gefunden: {mod_path}")
    spec = importlib.util.spec_from_file_location(f"ds_{slug}_build", mod_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore
    # delegiere an main() des build-Skripts
    if hasattr(mod, "main"):
        sys.argv = [str(mod_path), *argv]
        mod.main()
    else:
        print("Kein main() im build.py – führe Klasse Generator direkt aus.")
        mod.Generator(mod_path.parent.parent).run()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("slug", help="Dataset-Slug (Ordner unter datasets/)")
    p.add_argument("args", nargs=argparse.REMAINDER, help="Argumente für build.py (z. B. --load)")
    a = p.parse_args()
    run_slug(a.slug, a.args)

if __name__ == "__main__":
    main()
