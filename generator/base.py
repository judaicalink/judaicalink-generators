# generator/base.py
from __future__ import annotations

import datetime as dt
import traceback
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph, Literal, URIRef

from .rdf import JL_DS, DCTERMS
from .util import load_frontmatter_toml, ensure_dir, write_graph, mirror_to_public

logger = logging.getLogger(__name__)

@dataclass
class GeneratorContext:
    slug: str
    root: Path  # datasets/<slug>/
    source_dir: Path  # datasets/<slug>/source
    output_dir: Path  # datasets/<slug>/output
    tmp_dir: Path  # datasets/<slug>/tmp
    meta: dict  # TOML aus <slug>.md (Frontmatter)
    now: dt.datetime


class RDFGeneratorBase(ABC):
    """
    Wiederverwendbare ABC für alle Datensatz-Generatoren.
    Implementiere nur `build(self, g: Graph, ctx: GeneratorContext) -> None`.
    """

    def __init__(self, dataset_root: Path):
        self.dataset_root = dataset_root
        self.slug = dataset_root.name

    def run(self) -> dict:
        ctx = self._context()
        ensure_dir(ctx.output_dir)
        g = Graph()
        try:
            self._add_dataset_metadata(g, ctx)
            self.build(g, ctx)
            out_ttl = ctx.output_dir / f"{ctx.slug}.ttl"
            write_graph(g, out_ttl)
            public_path = mirror_to_public(out_ttl, ctx.slug)
            return {
                "slug": ctx.slug,
                "status": "success",
                "ttl": str(out_ttl),
                "public_ttl": str(public_path) if public_path else None,
                "triples": len(g),
                "generated_at": ctx.now.isoformat(),
            }
        except Exception as e:
            tb = traceback.format_exc()

            logger.exception("Generator '%s' failed", ctx.slug)

            return {
                "slug": ctx.slug,
                "status": "error",
                "error": str(e),
                "traceback": tb,
                "generated_at": ctx.now.isoformat(),
            }

    @abstractmethod
    def build(self, g: Graph, ctx: GeneratorContext) -> None:
        """Füge alle Tripel in `g` hinzu."""
        raise NotImplementedError

    # --- intern ---
    def _context(self) -> GeneratorContext:
        md = self.dataset_root / f"{self.slug}.md"
        meta = load_frontmatter_toml(md)
        return GeneratorContext(
            slug=self.slug,
            root=self.dataset_root,
            source_dir=self.dataset_root / "source",
            output_dir=self.dataset_root / "output",
            tmp_dir=self.dataset_root / "tmp",
            meta=meta,
            now=dt.datetime.utcnow(),
        )

    def _add_dataset_metadata(self, g: Graph, ctx: GeneratorContext):
        ds = JL_DS[ctx.slug]  # URIRef für den Dataset-Knoten

        # Identifier als Literal (früher: plain string -> AssertionError)
        g.add((ds, DCTERMS.identifier, Literal(ctx.slug)))

        # optionale Felder aus TOML-Frontmatter
        title = ctx.meta.get("title")
        if title:
            g.add((ds, DCTERMS.title, Literal(str(title))))

        desc = ctx.meta.get("description")
        if desc:
            g.add((ds, DCTERMS.description, Literal(str(desc))))

        lic = ctx.meta.get("license")
        if lic:
            # license kann dict oder string sein
            if isinstance(lic, dict) and lic.get("uri"):
                g.add((ds, DCTERMS.license, URIRef(str(lic["uri"]))))
            else:
                g.add((ds, DCTERMS.license, Literal(str(lic))))

        creator = ctx.meta.get("creator")
        if creator:
            g.add((ds, DCTERMS.creator, Literal(str(creator))))

        source = ctx.meta.get("source")
        if source:
            # wenn es wie eine URL aussieht → URIRef, sonst Literal
            s = str(source)
            term = URIRef(s) if s.startswith("http://") or s.startswith("https://") else Literal(s)
            g.add((ds, DCTERMS.source, term))
