# generator/util.py
import os
import re
import shutil
from pathlib import Path

from rdflib import Graph

FRONT_TOML_RE = re.compile(r"(?s)^\s*\+\+\+\s*(.*?)\s*\+\+\+\s*")


def load_frontmatter_toml(md_path: Path) -> dict:
    """Liest TOML-Frontmatter aus einer Markdown-Datei. Fehlende Datei => {}."""
    if not md_path.exists():
        return {}
    try:
        text = md_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    m = FRONT_TOML_RE.search(text)
    if not m:
        return {}
    import toml
    try:
        return toml.loads(m.group(1))
    except Exception:
        return {}


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_graph(g: Graph, path: Path) -> None:
    g.serialize(destination=str(path), format="turtle")


def mirror_to_public(local_ttl: Path, slug: str) -> Path | None:
    root = os.environ.get("JL_OUTPUT_ROOT")
    if not root:
        return None
    dest_dir = Path(root) / slug
    ensure_dir(dest_dir)
    dest = dest_dir / local_ttl.name
    shutil.copy2(local_ttl, dest)
    return dest
