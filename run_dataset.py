from pathlib import Path
import sys, argparse, importlib.util

DATASETS = Path(__file__).resolve().parent


def available_slugs() -> list[str]:
    """
    Find all available dataset slugs under datasets/ that contain
    scripts/build.py (excluding 'legacy').
    """
    slugs: list[str] = []
    if not DATASETS.exists():
        return slugs

    for p in DATASETS.iterdir():
        if not p.is_dir():
            continue
        if p.name == "legacy":
            # exclude legacy datasets
            continue
        if (p / "scripts" / "build.py").exists():
            slugs.append(p.name)

    return sorted(slugs)


def run_slug(slug: str, argv: list[str]):
    """
    Loads datasets/<slug>/scripts/build.py dynamically and calls its main()
    (or alternatively Generator.run()) with the given arguments.
    """
    mod_path = DATASETS / slug / "scripts" / "build.py"
    if not mod_path.exists():
        raise SystemExit(f"build.py not found: {mod_path}")

    spec = importlib.util.spec_from_file_location(f"ds_{slug}_build", mod_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load spec for {mod_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]

    # Delegate to main() or Generator.run()
    if hasattr(mod, "main"):
        # set sys.argv for the module
        sys.argv = [str(mod_path), *argv]
        mod.main(argv)
    else:
        print(f"No main() in the build.py of '{slug}' – execute the Generator class directly.")
        mod.Generator(mod_path.parent.parent).run()


def main():
    p = argparse.ArgumentParser(
        description=(
            "Helper script to run dataset generators located in <slug>/scripts/build.py."
            "Supports single slug or --all."
        )
    )
    p.add_argument(
        "--all",
        action="store_true",
        help="Run all datasets under datasets/ with scripts/build.py (without 'legacy')."
    )
    p.add_argument(
        "--load",
        action="store_true",
        help="Add the --load argument to all called build.py scripts."
    )
    p.add_argument(
        "slug",
        nargs="?",
        help="Dataset slug (folder under datasets/). Ignored when --all is used.",
    )
    p.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help=(
            "Additional arguments for build.py (e.g., --only-newer)."
            "If necessary, separate from the run_dataset parser using '--'."
        ),
    )

    a = p.parse_args()

    # --all: run all datasets
    if a.all:
        slugs = available_slugs()
        if not slugs:
            raise SystemExit(f"No datasets found under {DATASETS}.")

        print(f"Found datasets (without 'legacy'): {', '.join(slugs)}")
        for slug in slugs:
            print("\n" + "=" * 80)
            print(f"Start dataset '{slug}'")
            print("=" * 80)

            ds_argv = list(a.args)
            # --load for each dataset passed
            if a.load and "--load" not in ds_argv:
                ds_argv.insert(0, "--load")

            run_slug(slug, ds_argv)
        return

    # Single slug mode
    if not a.slug:
        p.error("Please either specify a slug or use --all.")

    ds_argv = list(a.args)
    if a.load and "--load" not in ds_argv:
        ds_argv.insert(0, "--load")

    run_slug(a.slug, ds_argv)


if __name__ == "__main__":
    main()
