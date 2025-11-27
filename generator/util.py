# generator/util.py
import os
import re
import shutil
from pathlib import Path

from rdflib import Graph

FRONT_TOML_RE = re.compile(r"(?s)^\s*\+\+\+\s*(.*?)\s*\+\+\+\s*")


def load_frontmatter_toml(md_path: Path) -> dict:
    """
    Reads TOML frontmatter from the Markdown file. Missing file => {}.
    :param md_path: Path to the Markdown file.
    :return: Dictionary with the parsed TOML frontmatter.
    """
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
    """
    Ensures that the directory exists.
    :param p: Path to the directory.
    :return: None
    """
    p.mkdir(parents=True, exist_ok=True)


def write_graph(g: Graph, path: Path) -> None:
    """
    Writes the RDF graph to a Turtle file.
    :param g: RDF Graph.
    :param path: Path to the output Turtle file.
    """
    g.serialize(destination=str(path), format="turtle")


def mirror_to_public(local_ttl: Path, slug: str) -> Path | None:
    """
    If the JL_OUTPUT_ROOT environment variable is set,
    copies the local_ttl file to JL_OUTPUT_ROOT/slug/ and returns the new path.
    :param local_ttl:  to the local Turtle file.
    :param slug: Dataset slug.
    :return: Path to the mirrored Turtle file, or None if JL_OUTPUT_ROOT is not set.
    """
    root = os.environ.get("JL_OUTPUT_ROOT")
    if not root:
        return None
    dest_dir = Path(root) / slug
    ensure_dir(dest_dir)
    dest = dest_dir / local_ttl.name
    shutil.copy2(local_ttl, dest)
    return dest
