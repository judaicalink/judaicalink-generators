# -*- coding: utf-8 -*-
"""
Generator for the Gidal Image Archive (GBA).
http://www.steinheim-institut.de/wiki/index.php/Archive:Gidal-Bildarchiv

Workflow:
1. RDF-Daten aus gidal.csv generieren (Personen/Organisationen etc.).
2. output/gba.ttl schreiben und gzippen.
3. Metadaten aus gba.md erzeugen (gba.meta.ttl + .gz).
4. Optional: Dateien nach $JL_DUMPS_ROOT/gba/current/ kopieren.
5. Optional: Daten-Graph nach Fuseki laden (Named Graph gba).
6. Optional: Metadaten-Graph nach Fuseki upserten (Datasets-Graph).
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, DCTERMS

# --- Repo-Root für Standalone-Import setzen ---
REPO_ROOT = Path(__file__).resolve().parents[2]  # .../judaicalink-generators
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Core-Utilities / ABC / Loader / Metadata
from generator.util import ensure_dir, load_frontmatter_toml  # type: ignore
from generator.base import RDFGeneratorBase  # type: ignore
from generator.metadata import build_metadata_graph  # type: ignore
from generator.loader import load_to_fuseki, upsert_metadata_graph  # type: ignore

# Namespaces
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
GNDO = Namespace("http://d-nb.info/standards/elementset/gnd#")
JL_DATA = Namespace("http://data.judaicalink.org/data/")  # Daten-Basis
JL_DS = Namespace("http://data.judaicalink.org/datasets/")  # Datasets-Basis
VOID = Namespace("http://rdfs.org/ns/void#")

SLUG = "gba"
DATASET_URI = URIRef(f"{JL_DS}{SLUG}")  # http://data.judaicalink.org/datasets/gba

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


# ------------- Helpers ------------- #
def clean_url_string(string: Optional[str]) -> str:
    """
    Cleans a string to be URL/URI friendly by replacing problematic characters with underscores.
    1. Trims whitespace.
    2. Replaces characters: ' " , < > | . [ ] ( ) { } and spaces with underscores.
    3. Returns empty string for None or NaN inputs.
    4. Returns the cleaned string
    :param string: The input string to clean.
    :return: A cleaned string suitable for URLs/URIs.
    """
    if string is None or (isinstance(string, float) and pd.isna(string)):
        return ""
    s = str(string).strip()
    for ch in ["'", '"', ",", "<", ">", "|", " ", ".", "[", "]", "(", ")", "{", "}"]:
        s = s.replace(ch, "_")
    return s


def compress_file(path: Path) -> Path:
    """
    Compress a file using gzip and return the path to the compressed file.
    :param path: Path to the file to compress.
    :return: Path to the compressed .gz file.
    """
    gz_path = path.with_suffix(path.suffix + ".gz")
    with path.open("rb") as f_in, gzip.open(gz_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return gz_path


def copy_to_dumps(slug: str, files: list[Path]) -> list[Path]:
    """
    Copies given files to the dumps directory for the specified slug.
    JL_DUMPS_ROOT/<slug>/current/
    :param slug: The dataset slug (e.g., 'gba').
    :param files: List of file paths to copy.
    :return: List of paths to the copied files in the dumps directory.
    """
    dumps_root = Path(os.environ.get("JL_DUMPS_ROOT", "/mnt/data/dumps")).resolve()
    dest_dir = dumps_root / slug / "current"
    ensure_dir(dest_dir)
    copied = []
    for f in files:
        dest = dest_dir / f.name
        shutil.copy2(str(f), str(dest))
        copied.append(dest)
    return copied


# ------------- Data mapping ------------- #
def generate_rdf_from_csv(g: Graph, csv_path: Path) -> None:
    """
    Mapping from gidal.csv to RDF triples in the provided graph.
    Expected columns: name, gnd, type, birthDate, deathDate, occupation,
                      hasPublication, relation, alternativeName, hasAbstract
    :param g: RDFLib Graph to populate.
    :param csv_path: Path to the gidal.csv file.
    :return: None
    """
    df = pd.read_csv(csv_path, sep=",", encoding="utf-8", header=0)

    # Prefix bBindings (for readable TTL)
    g.bind("skos", SKOS)
    g.bind("foaf", FOAF)
    g.bind("gndo", GNDO)
    g.bind("dcterms", DCTERMS)

    for _, row in df.iterrows():
        # URI
        url_name = clean_url_string(row.get("name"))
        if not url_name:
            continue
        uri = URIRef(f"{JL_DATA}gba/{url_name}")

        # Type
        rtype = str(row.get("type") or "").strip().lower()
        if rtype == "person":
            g.add((uri, RDF.type, FOAF.Person))
        elif rtype in ("organisation", "organization", "org"):
            g.add((uri, RDF.type, FOAF.Organization))

        # Labels / Name
        name = row.get("name")
        if pd.notna(name):
            name_str = str(name)
            g.add((uri, FOAF.name, Literal(name_str)))
            g.add((uri, SKOS.prefLabel, Literal(name_str)))

        # GND
        gnd = row.get("gnd")
        if pd.notna(gnd):
            g.add((uri, GNDO.gndIdentifier, Literal(str(gnd))))

        # Birth/Death
        birth = row.get("birthDate")
        if pd.notna(birth):
            try:
                g.add((uri, GNDO.birthDate, Literal(int(birth))))
            except Exception:
                g.add((uri, GNDO.birthDate, Literal(str(birth))))

        death = row.get("deathDate")
        if pd.notna(death):
            try:
                g.add((uri, GNDO.deathDate, Literal(int(death))))
            except Exception:
                g.add((uri, GNDO.deathDate, Literal(str(death))))

        # occupation separated by ;
        occs = row.get("occupation")
        if pd.notna(occs):
            for occ in str(occs).split(";"):
                occ = occ.strip()
                if occ:
                    g.add((uri, GNDO.occupation, Literal(occ)))

        # hasPublication separated by ;
        pubs = row.get("hasPublication")
        if pd.notna(pubs):
            for pub in str(pubs).split(";"):
                pub = pub.strip()
                if pub:
                    g.add((uri, GNDO.hasPublication, Literal(pub)))

        # relation
        rel = row.get("relation")
        if pd.notna(rel):
            g.add((uri, GNDO.relation, Literal(str(rel).strip())))

        # alternativeName
        alt = row.get("alternativeName")
        if pd.notna(alt):
            g.add((uri, GNDO.alternativeName, Literal(str(alt).strip())))

        # abstract
        ab = row.get("hasAbstract")
        if pd.notna(ab):
            g.add((uri, GNDO.hasAbstract, Literal(str(ab).strip())))


# ------------- ABC integration ------------- #
class Generator(RDFGeneratorBase):
    """
    Uses the common ABC (RDFGeneratorBase).
    - build() fills the graphen g (data graph)
    :param g: RDFLib Graph to populate.
    :param ctx: Build context with source_dir etc.
    :return: None
    """

    def build(self, g: Graph, ctx) -> None:
        src = ctx.source_dir / "gidal.csv"
        if not src.exists():
            logger.warning("Source missing: %s", src)
            return

        logger.info("Generating RDF from %s", src)
        generate_rdf_from_csv(g, src)
        logger.info("GBA RDF generation finished; triples: %d", len(g))


# ------------- CLI ------------- #
def parse_args(argv: list[str] | None = None):
    """
    Parse command-line arguments.
    :param argv: List of command-line arguments (default: sys.argv).
    :return: Parsed arguments.
    """
    p = argparse.ArgumentParser(description="Build RDF for gba and (optionally) load & publish.")
    p.add_argument("--load", action="store_true", help="Load into Fuseki after generation")
    p.add_argument("--graph", default=None, help="Named graph URI; overwrites value from gba.md")
    p.add_argument("--append", action="store_true", help="Append to graph, instead of replacing")
    p.add_argument("--only-newer", action="store_true",
                   help="Only load if the file is unchanged (hash/mtime -> skip)")
    p.add_argument("--no-dumps", action="store_true", help="Do not copy files to dumps")
    p.add_argument("--meta-only", action="store_true", help="Write only metadata (no data graph)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None):
    """
    Main build workflow for GBA.
    1) Build data graph (unless --meta-only).
    2) Gzip data graph.
    3) Build metadata graph.
    4) Optional: Load data graph to Fuseki.
    5) Optional: Copy files to dumps.
    :param argv: Command-line arguments (default: sys.argv).
    :return: None
    """
    args = parse_args(argv)

    ds_root = Path(__file__).resolve().parents[1]  # gba/
    out_dir = ds_root / "output"
    ensure_dir(out_dir)

    logger.info("Starting GBA build (meta_only=%s)", args.meta_only)

    # 1) build data graph bauen
    res = {"status": "success", "ttl": str(out_dir / f"{SLUG}.ttl"), "slug": SLUG}
    if not args.meta_only:
        gen = Generator(ds_root)
        res = gen.run()  # writes to output/gba.ttl
        print(json.dumps(res, indent=2, ensure_ascii=False))

        if res.get("status") != "success":
            logger.error("GBA generation failed: %s", res.get("error"))
            tb = res.get("traceback")
            if tb:
                logger.error("Traceback:\n%s", tb)
            return

    ttl_path = Path(res["ttl"])
    gz_path: Optional[Path] = None

    # 2) gzip (onlxy if data graph was generated)
    if ttl_path.exists() and not args.meta_only:
        gz_path = compress_file(ttl_path)
        logger.info("gzipped: %s", gz_path)

    # 3) metadata graph build
    meta_md = ds_root / f"{SLUG}.md"
    if meta_md.exists():
        meta_front = load_frontmatter_toml(meta_md)
    else:
        meta_front = {}

    metadata = {
        "slug": SLUG,
        "title": meta_front.get("title") or "Gidal Image Archive",
        "license": meta_front.get("license") or {
            "uri": "https://creativecommons.org/licenses/by-sa/4.0/",
            "name": "CC-BY-SA 4.0",
        },
        "generator": {
            "gitweb": meta_front.get("generator", {}).get("gitweb")
            if isinstance(meta_front.get("generator"), dict)
            else "https://github.com/judaicalink/judaicalink-generators/tree/main/gba",
            "commit": os.environ.get("GIT_COMMIT", "local"),
            "script": "gba/scripts/build.py",
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

    for f in meta_front.get("files", []):
        url = f.get("url")
        if url:
            meta_g.add((subject, VOID.dataDump, URIRef(url)))
        desc = f.get("description")
        if desc:
            meta_g.add((subject, DCTERMS.description, Literal(desc)))

    meta_ttl = out_dir / f"{SLUG}.meta.ttl"
    meta_g.serialize(destination=str(meta_ttl), format="turtle")
    meta_gz = compress_file(meta_ttl)
    logger.info("metadata written: %s (+ .gz)", meta_ttl)

    # 4) Optional: Loader (Fuseki)
    if args.load and not args.meta_only and res.get("status") == "success":
        # Graph-URI: CLI-Argument > gba.md:graph > Default
        graph_uri = args.graph or meta_front.get("graph") or "http://data.judaicalink.org/data/gba"

        # load data graph
        lr = load_to_fuseki(
            slug=SLUG,
            ttl_path=str(ttl_path),
            endpoint=None,
            graph=graph_uri,
            replace=(not args.append),
            only_newer=args.only_newer,
        )
        print(json.dumps(lr.__dict__, indent=2, ensure_ascii=False))

        # upsert metadata graph
        lr_meta = upsert_metadata_graph(
            slug=f"{SLUG}-meta",
            ttl_path=str(meta_ttl),
            graph="http://data.judaicalink.org/datasets",
            subject=str(DATASET_URI),
            only_newer=True,
        )
        print(json.dumps(lr_meta.__dict__, indent=2, ensure_ascii=False))

    # 5) Optional: copy to dumps
    if not args.no_dumps:
        files = [meta_ttl, meta_gz]
        if ttl_path.exists() and not args.meta_only:
            files.append(ttl_path)
            if gz_path:
                files.append(gz_path)
        copied = copy_to_dumps(SLUG, files)
        for m in copied:
            logger.info("copied → %s", m)


if __name__ == "__main__":
    main()
