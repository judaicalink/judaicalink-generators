# -*- coding: utf-8 -*-
"""
Build script for the dataset "occupations" (derived from jl:occupation literals in the union graph).

Workflow (like other generators):
1. Query union graph for distinct jl:occupation literals.
2. Build SKOS concept URIs for each occupation.
3. Optional enrichment:
   - link to EP concept (skos:exactMatch) if EP contains matching prefLabel/altLabel
   - link to DBpedia (owl:sameAs) by exact label match
   - link to GND (skos:exactMatch) by exact label match
4. Save as occupations.ttl (+ .gz)
5. Generate metadata from occupations.md (.meta.ttl + .gz)
6. Optional: Copy to dumps
7. Optional: Load data + metadata into Fuseki
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import os
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from tqdm import tqdm

import requests
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, DCTERMS

# Find repo root and add to sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Generator infrastructure
from generator.base import RDFGeneratorBase  # type: ignore
from generator.metadata import build_metadata_graph  # type: ignore
from generator.loader import load_to_fuseki, upsert_metadata_graph  # type: ignore
from generator.util import ensure_dir, load_frontmatter_toml  # type: ignore
from generator.rdf import JL_DS  # type: ignore

# Namespaces
JL = Namespace("http://data.judaicalink.org/ontology/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

DATA_PREFIX = "http://data.judaicalink.org/data/"
OCCUPATION_BASE = URIRef(DATA_PREFIX + "occupation/")

# EP graph (already in Fuseki)
EP_GRAPH_URI = "http://data.judaicalink.org/data/ep"

SLUG = "occupations"
DATASET_URI = JL_DS[SLUG]

# External endpoints (can be overridden by env)
DBPEDIA_SPARQL = os.environ.get("JL_DBPEDIA_SPARQL", "https://dbpedia.org/sparql")
GND_SPARQL = os.environ.get("JL_GND_SPARQL", "https://sparql.dnb.de/api/gnd")  # public SPARQL (GND)

# Logging
LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"{SLUG}.log"

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
if not root_logger.handlers:
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

logger = logging.getLogger(f"{SLUG}-build")
logger.info("Logging initialized → %s", LOG_FILE)


# ------------------------------------------------------------------------------
# Helpers: gzip, dumps
# ------------------------------------------------------------------------------
def compress_file(path: Path) -> Path:
    gz_path = path.with_suffix(path.suffix + ".gz")
    with path.open("rb") as f_in, gzip.open(gz_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return gz_path


def copy_to_dumps(slug: str, files: list[Path]) -> list[Path]:
    dumps_root = Path(os.environ.get("LABS_DUMPS_LOCAL", "/data/dumps")).resolve()
    slug_dir = dumps_root / slug
    current_dir = slug_dir / "current"
    archive_dir = slug_dir / "archive"

    current_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    # Archive existing files
    for old_file in current_dir.iterdir():
        if not old_file.is_file():
            continue
        try:
            archived_path = archive_dir / f"{timestamp}-{old_file.name}"
            old_file.rename(archived_path)
        except Exception as e:
            logger.error("[DUMPS] Failed to archive '%s': %s", old_file, e)

    copied_files: list[Path] = []
    for f in files:
        destination = current_dir / f.name
        try:
            shutil.copy2(f, destination)
            copied_files.append(destination)
        except Exception as e:
            logger.error("[DUMPS] Failed to copy '%s' to '%s': %s", f, destination, e)

    return copied_files


# ------------------------------------------------------------------------------
# Helpers: SPARQL
# ------------------------------------------------------------------------------
def sparql_escape_literal(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')


def sparql_select(endpoint: str, query: str, timeout: int = 60) -> list[dict]:
    headers = {"Accept": "application/sparql-results+json"}
    r = requests.get(endpoint, params={"query": query}, headers=headers, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return data.get("results", {}).get("bindings", [])


# ------------------------------------------------------------------------------
# Helpers: URI building
# ------------------------------------------------------------------------------
def slugify(label: str) -> str:
    s = (label or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("ß", "ss")
    # keep letters/digits/space/hyphen
    out = []
    for ch in s:
        if ch.isalnum() or ch in [" ", "-"]:
            out.append(ch)
    s = "".join(out)
    s = "-".join(filter(None, s.replace("-", " ").split()))
    return s or "unknown"


def occupation_uri(label: str) -> URIRef:
    return URIRef(str(OCCUPATION_BASE) + slugify(label))


# ------------------------------------------------------------------------------
# Fetch + enrichment
# ------------------------------------------------------------------------------
def fetch_distinct_occupations(union_sparql: str) -> list[str]:
    q = """
PREFIX jl: <http://data.judaicalink.org/ontology/>

SELECT DISTINCT ?occ WHERE {
  ?person jl:occupation ?occ .
  FILTER(isLiteral(?occ))
  FILTER(STRLEN(STR(?occ)) > 0)
}
ORDER BY LCASE(STR(?occ))
"""
    rows = sparql_select(union_sparql, q, timeout=120)
    labels: list[str] = []
    for b in rows:
        v = b.get("occ", {}).get("value", "")
        v = (v or "").strip()
        if v:
            labels.append(v)
    return labels


def enrich_ep_concept(union_sparql: str, label: str) -> Optional[str]:
    """
    Try to find an EP concept with exact prefLabel/altLabel match.
    Returns the EP URI if found.
    """
    label_esc = sparql_escape_literal(label)
    q = f"""
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT DISTINCT ?occ WHERE {{
  GRAPH <{EP_GRAPH_URI}> {{
    ?occ ?p ?l .
    VALUES ?p {{ skos:prefLabel skos:altLabel }}
    FILTER(LCASE(STR(?l)) = LCASE("{label_esc}"))
  }}
}}
LIMIT 1
"""
    try:
        rows = sparql_select(union_sparql, q, timeout=60)
        if rows:
            return rows[0]["occ"]["value"]
    except Exception as e:
        logger.debug("EP enrichment failed for '%s': %s", label, e)
    return None


def enrich_dbpedia(label: str, cache: Dict[str, Optional[str]]) -> Optional[str]:
    """
    Exact label match in DBpedia (de/en/none).
    """
    logger.debug("Enriching DBpedia for occupation '%s'", label)

    if label in cache:
        return cache[label]


    label_esc = sparql_escape_literal(label)

    q = f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?uri WHERE {{
  ?uri rdfs:label ?l .
  FILTER(LCASE(STR(?l)) = LCASE("{label_esc}"))
  FILTER(LANG(?l) IN ("de","en",""))
}}
LIMIT 1
"""
    try:
        rows = sparql_select(DBPEDIA_SPARQL, q, timeout=60)
        cache[label] = rows[0]["uri"]["value"] if rows else None
        logger.debug("DBpedia match for '%s' → %s", label, cache[label])
        return cache[label]
    except Exception as e:
        logger.debug("DBpedia enrichment failed for '%s': %s", label, e)
        cache[label] = None
        return None


def enrich_gnd(label: str, cache: Dict[str, Optional[str]]) -> Optional[str]:
    """
    Exact label match in GND via SPARQL endpoint.
    Note: This can be noisy/slow; keep optional & cached.
    """
    logger.debug("Enriching GND for occupation '%s'", label)

    if label in cache:
        return cache[label]

    label_esc = sparql_escape_literal(label)
    q = f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?uri WHERE {{
  ?uri rdfs:label ?l .
  FILTER(LCASE(STR(?l)) = LCASE("{label_esc}"))
}}
LIMIT 1
"""
    try:
        rows = sparql_select(GND_SPARQL, q, timeout=60)
        cache[label] = rows[0]["uri"]["value"] if rows else None
        logger.debug("GND match for '%s' → %s", label, cache[label])
        return cache[label]
    except Exception as e:
        logger.debug("GND enrichment failed for '%s': %s", label, e)
        cache[label] = None
        return None


def build_occupations_graph(g: Graph, ctx, do_enrich: bool = True) -> None:
    """
    Build occupation concept dataset.
    Uses union graph endpoint (Fuseki) from ctx or env.
    """
    # Bind prefixes
    g.bind("jl", JL)
    g.bind("skos", SKOS)
    g.bind("owl", OWL)
    g.bind("rdfs", RDFS)
    g.bind("dcterms", DCTERMS)

    union_sparql = (
        getattr(ctx, "sparql_endpoint", None)
        or os.environ.get("ENDPOINT")
        or "http://localhost:3030/judaicalink/query"
    )
    if not union_sparql:
        raise RuntimeError("No SPARQL endpoint found. Set ENDPOINT (union graph).")

    logger.info("Fetching distinct jl:occupation literals from %s", union_sparql)
    labels = fetch_distinct_occupations(union_sparql)
    total = len(labels)
    logger.info("Found %d distinct occupations", total)

    # caches
    dbpedia_cache: Dict[str, Optional[str]] = {}
    gnd_cache: Dict[str, Optional[str]] = {}

    seen_uri: Set[str] = set()

    logger.info("Building occupation concepts (enrichment=%s)", do_enrich)

    for i, lab in enumerate(
            tqdm(labels, desc="Occupations", unit="occ"), start=1
    ):
        occ_u = occupation_uri(lab)
        if str(occ_u) in seen_uri:
            continue
        seen_uri.add(str(occ_u))

        g.add((occ_u, RDF.type, SKOS.Concept))
        g.add((occ_u, SKOS.prefLabel, Literal(lab)))
        g.add((occ_u, DCTERMS.source, DATASET_URI))

        if do_enrich:
            ep_uri = enrich_ep_concept(union_sparql, lab)
            if ep_uri:
                g.add((occ_u, SKOS.exactMatch, URIRef(ep_uri)))

            dbp = enrich_dbpedia(lab, dbpedia_cache)
            if dbp:
                g.add((occ_u, OWL.sameAs, URIRef(dbp)))

            gnd = enrich_gnd(lab, gnd_cache)
            if gnd:
                g.add((occ_u, SKOS.exactMatch, URIRef(gnd)))

        # alle 50 Items ein INFO-Log
        if i % 50 == 0:
            logger.info("Processed %d / %d occupations", i, total)

    logger.info("occupations graph built; triples: %d", len(g))


# ------------------------------------------------------------------------------
# Generator adapter (ABC)
# ------------------------------------------------------------------------------
class Generator(RDFGeneratorBase):
    def build(self, g: Graph, ctx) -> None:
        do_enrich = getattr(self, "do_enrich", True)
        build_occupations_graph(g, ctx, do_enrich=do_enrich)


# ------------------------------------------------------------------------------
# CLI / main
# ------------------------------------------------------------------------------
def parse_args(argv: list[str] | None = None):
    p = argparse.ArgumentParser(description="Build occupations dataset and (optionally) load & publish.")
    p.add_argument("--load", action="store_true", help="Load into Fuseki after generation")
    p.add_argument("--append", action="store_true", help="Append instead of replacing in Fuseki")
    p.add_argument("--only-newer", action="store_true", help="Only load if file has not changed (hash/mtime)")
    p.add_argument("--no-dumps", action="store_true", help="Don't copy files to dumps directory")
    p.add_argument("--meta-only", action="store_true", help="Write only metadata, no data graph")
    p.add_argument("--graph", default=None, help="Named graph URI; default from frontmatter: graph")
    p.add_argument("--no-enrich", action="store_true", help="Disable EP/DBpedia/GND enrichment")
    return p.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)

    ds_root = Path(__file__).resolve().parents[1]  # …/occupations/
    out_dir = ds_root / "output"
    ensure_dir(out_dir)

    logger.info("Starting occupations build (meta_only=%s)", args.meta_only)

    # 1) Data graph
    res: dict = {"status": "success", "ttl": str(out_dir / f"{SLUG}.ttl"), "slug": SLUG}
    ttl_path: Path | None = None

    if not args.meta_only:
        gen = Generator(ds_root)
        # pass flags into ctx (RDFGeneratorBase usually creates ctx; we attach here if supported)
        # if base doesn't allow, fallback to env var in build_occupations_graph.
        gen.do_enrich = (not args.no_enrich)  # <-- Generator-Attribut

        res = gen.run()
        logger.info(json.dumps(res, indent=2, ensure_ascii=False))

        if res.get("status") != "success":
            logger.error("occupations generation failed: %s", res.get("error"))
            if res.get("traceback"):
                logger.error("Traceback:\n%s", res.get("traceback"))
            return

        ttl_path = Path(res["ttl"])

    gz_path: Path | None = None
    if ttl_path and ttl_path.exists() and not args.meta_only:
        gz_path = compress_file(ttl_path)
        logger.info("gzipped data: %s", gz_path)

    # 2) Metadata graph from TOML frontmatter (occupations/occupations.md)
    meta_md = ds_root / f"{SLUG}.md"
    meta_front = load_frontmatter_toml(meta_md) if meta_md.exists() else {}

    metadata = {
        "slug": SLUG,
        "title": meta_front.get("title") or "Occupations (derived from jl:occupation)",
        "license": meta_front.get("license") or {
            "uri": "https://creativecommons.org/licenses/by/4.0/",
            "name": "CC-BY 4.0",
        },
        "generator": {
            "gitweb": meta_front.get("generator", {}).get("gitweb")
            if isinstance(meta_front.get("generator"), dict)
            else "https://github.com/judaicalink/judaicalink-generators/tree/master/occupations",
            "commit": os.environ.get("GIT_COMMIT", "local"),
            "script": "occupations/scripts/build.py",
        },
    }
    meta_g = build_metadata_graph(metadata, scriptinfo={"slug": SLUG})
    subject = DATASET_URI

    # additional metadata from frontmatter
    if (author := meta_front.get("author")):
        meta_g.add((subject, DCTERMS.creator, Literal(author)))
    if (authorlink := meta_front.get("authorlink")):
        meta_g.add((subject, DCTERMS.creator, URIRef(authorlink)))
    if (website := meta_front.get("website")):
        meta_g.add((subject, DCTERMS.source, URIRef(website)))
    if (date := meta_front.get("date")):
        meta_g.add((subject, DCTERMS.issued, Literal(date)))

    meta_ttl = out_dir / f"{SLUG}.meta.ttl"
    meta_g.serialize(destination=str(meta_ttl), format="turtle")
    meta_gz = compress_file(meta_ttl)
    logger.info("metadata written: %s (+ .gz)", meta_ttl)

    # 3) Optional: load into Fuseki
    if args.load and not args.meta_only and ttl_path:
        graph_uri = args.graph or meta_front.get("graph")

        lr_data = load_to_fuseki(
            slug=SLUG,
            ttl_path=str(ttl_path),
            graph=graph_uri,
            endpoint=None,
            replace=(not args.append),
            only_newer=args.only_newer,
        )
        logger.info(json.dumps(lr_data.__dict__, indent=2, ensure_ascii=False))

        lr_meta = upsert_metadata_graph(
            slug=f"{SLUG}-meta",
            ttl_path=str(meta_ttl),
            graph="http://data.judaicalink.org/datasets",
            subject=str(DATASET_URI),
            only_newer=True,
        )
        logger.info(json.dumps(lr_meta.__dict__, indent=2, ensure_ascii=False))

    # 4) Optional: copy to dumps
    if not args.no_dumps:
        files: list[Path] = [meta_ttl, meta_gz]
        if ttl_path and ttl_path.exists() and not args.meta_only:
            files.append(ttl_path)
            if gz_path:
                files.append(gz_path)
        copied = copy_to_dumps(SLUG, files)
        for c in copied:
            logger.info("copied → %s", c)

    logger.info("Occupations build finished.")
    logger.info("Task finished.")


if __name__ == "__main__":
    main()
