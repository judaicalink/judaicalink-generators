# -*- coding: utf-8 -*-
"""
Build script for the dataset "nrwbibdjg"
(Bibliography of German-Jewish History in North Rhine-Westphalia).

Workflow:
1. Load data from the sources (Steinheim BEACON + GND).
2. Generate an RDF graph according to the ontologies.
3. Save as a .ttl file in the output/ directory and gzip it.
4. Generate metadata from nrwbibdjg.md (.meta.ttl + .gz).
5. Optional: Copy the files to the dumps directory.
6. Optional: Load the data graph and metadata into Fuseki.
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import requests
from bs4 import BeautifulSoup
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, DC, DCTERMS
from tqdm import tqdm

# Find the repository root and add to sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Generator infrastructure imports
from generator.base import RDFGeneratorBase  # type: ignore
from generator.metadata import build_metadata_graph  # type: ignore
from generator.loader import load_to_fuseki, upsert_metadata_graph  # type: ignore
from generator.util import ensure_dir, load_frontmatter_toml  # type: ignore
from generator.rdf import JL_DS  # type: ignore

# Namespaces
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
JL = Namespace("http://data.judaicalink.org/ontology/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
GNDO = Namespace("http://d-nb.info/standards/elementset/gnd#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
EDM = Namespace("http://www.europeana.eu/schemas/edm/")
DCNS = Namespace("http://purl.org/dc/elements/1.1/")
DCT = Namespace("http://purl.org/dc/terms/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")

VOID = Namespace("http://rdfs.org/ns/void#")

SLUG = "nrwbibdjg"
DATASET_URI = JL_DS[SLUG]

# ----------------------------------------------------------------------------------------------
# Logging setup (root logger, so that generator.base etc. are also written to the same log file)
# ----------------------------------------------------------------------------------------------

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


# ----------------------------------------------------------------------
# Helper functions for zipping and copying to dumps
# ----------------------------------------------------------------------
def compress_file(path: Path) -> Path:
    """
    Compresses the given file with gzip and returns the path to the .gz file.
    :param path: Path to the file to compress
    :return: Path to the compressed .gz file
    """
    gz_path = path.with_suffix(path.suffix + ".gz")
    with path.open("rb") as f_in, gzip.open(gz_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return gz_path


def copy_to_dumps(slug: str, files: list[Path]) -> list[Path]:
    """
    Copy generated dataset files into the dumps directory.

    Directory structure:
        <DUMPS_ROOT>/<slug>/current/     -> always contains the latest files
        <DUMPS_ROOT>/<slug>/archive/     -> contains all previous versions

    Before copying new files:
        - All existing files in <slug>/current/ are moved to <slug>/archive/
        - Files are renamed using:
              YYYY-mm-dd-hh-ss-<original_name>

    If a file cannot be copied, the error is logged and processing continues.
    :param slug: Dataset slug
    :param files: List of Paths to files to copy
    """

    dumps_root = Path(os.environ.get("JL_DUMPS_ROOT", "/data/dumps")).resolve()
    slug_dir = dumps_root / slug
    current_dir = slug_dir / "current"
    archive_dir = slug_dir / "archive"

    current_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    # 1) Archive existing files in current/
    for old_file in current_dir.iterdir():
        if not old_file.is_file():
            continue
        try:
            new_name = f"{timestamp}-{old_file.name}"
            archived_path = archive_dir / new_name
            old_file.rename(archived_path)
        except Exception as e:
            logger.error(f"[DUMPS] Failed to archive '{old_file}': {e}")
            # continue even if one file fails

    # 2) Copy new files to current/
    copied_files = []
    for f in files:
        try:
            destination = current_dir / f.name
            shutil.copy2(f, destination)
            copied_files.append(destination)
        except Exception as e:
            logger.error(f"[DUMPS] Failed to copy '{f}' to '{destination}': {e}")
            # continue with next file

    return copied_files


# -----------------------------
# Specific logic for nrwbibdjg
# -----------------------------
BEACON_URL = "http://www.steinheim-institut.de/ebib-djg-nrw/ebib-djg-nrw-beacon.txt"
QUERY_URL = "http://www.steinheim-institut.de/ebib-djg-nrw/query.html"


def get_gnd_ttl_data(gndid: str) -> list[list[str]]:
    """
    Enriches data with data from GND if GND ID is known.
    :param gndid: GND ID of the person
    :return: List of [predicate, object] pairs
    """
    pr_obj: list[list[str]] = []
    try:
        headers = {"Accept": "text/turtle"}
        gnd_url = f"http://d-nb.info/gnd/{gndid}/about/lds"
        response = requests.get(gnd_url, headers=headers, timeout=30)
        if response.status_code != 200:
            logger.warning("GND request for %s returned status %s", gndid, response.status_code)
            return pr_obj

        temp_graph = Graph()
        temp_graph.parse(data=response.text, format="turtle")
        for _s, p, o in temp_graph:
            p = str(p)
            o = str(o)
            if p.startswith("https://d-nb.info/standards/elementset/gnd#"):
                p = p.replace("https://d-nb.info/standards/elementset/gnd#", "gndo.")
                if o.startswith("https://d-nb.info/gnd/"):
                    oid = o.replace("https://d-nb.info/gnd/", "")
                    o = f"http://data.judaicalink.org/data/nrwbibdjg/{oid}"
                pr_obj.append([p, o])
            if p.startswith("http://www.w3.org/2002/07/owl#"):
                p = p.replace("http://www.w3.org/2002/07/owl#", "owl.")
                pr_obj.append([p, o])
    except Exception as e:
        logger.error("An error occurred while fetching GND data for %s: %s", gndid, e)
    return pr_obj


def get_ids_from_beacon(url: str) -> List[str]:
    """
    Creates a list of IDs from beacon URL.
    :param url: URL to the BEACON file
    :return: List of IDs
    """
    ids: List[str] = []
    logger.info("Fetching BEACON ids from %s", url)
    resp = requests.get(url, timeout=60)
    if resp.status_code != 200:
        logger.error("BEACON request failed with status %s", resp.status_code)
        return ids

    content = resp.content.decode("utf-8", errors="ignore")
    for line in content.splitlines():
        if not line or line.startswith("#"):
            continue
        ids.append(line.strip())
    logger.info("Found %d ids in BEACON file", len(ids))
    return ids


def clean_url_string(string: str) -> str:
    """
    Clean the name of a person or title to form a URI path segment.
    :param string: Original string
    :return: Cleaned string
    """
    import unicodedata

    s = string.strip()
    for ch_old, ch_new in [
        ("'", ""),
        ('"', ""),
        (",", "_"),
        ("<<", ""),
        (">>", ""),
        ("|", "_"),
        (" ", ""),
        ("<", "_"),
        (">", "_"),
        (".", ""),
        ("[", ""),
        ("]", ""),
        ("(", ""),
        (")", ""),
        ("{", ""),
        ("}", ""),
        ("#", ""),
        ("-", ""),
        ("?", ""),
    ]:
        s = s.replace(ch_old, ch_new)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore")
    return s.decode("utf-8")


def add_creation_date(graph: Graph, uri: URIRef) -> None:
    """
    Adds a dcterms:created triple if none exists yet.
    :param graph: RDF Graph
    :param uri: URIRef of the resource
    :return: None
    """
    if (uri, DCTERMS.created, None) not in graph:
        graph.add((uri, DCTERMS.created, Literal(datetime.now().isoformat())))


def build_nrwbibdjg_graph(g: Graph) -> None:
    """
    Builds the RDF graph for the nrwbibdjg dataset.
    :param g: RDF Graph to populate
    :return: None
    """

    # Prefixes binden
    g.bind("skos", SKOS)
    g.bind("foaf", FOAF)
    g.bind("jl", JL)
    g.bind("gndo", GNDO)
    g.bind("owl", OWL)
    g.bind("edm", EDM)
    g.bind("dc", DCNS)
    g.bind("dcterms", DCT)
    g.bind("rdfs", RDFS)
    g.bind("geo", GEO)

    headers1 = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    ids = get_ids_from_beacon(BEACON_URL)
    if not ids:
        logger.warning("No ids fetched from BEACON; graph will be empty.")
        return

    for gndID in tqdm(ids, desc="nrwbibdjg GND ids"):
        url = f"{QUERY_URL}?database=NRW-Bibliografie&text1={gndID}&kategorie1=gnd"
        try:
            response = requests.get(url, headers=headers1, timeout=60)
        except Exception as e:
            logger.error("Error requesting %s: %s", url, e)
            continue

        if response.status_code != 200:
            logger.warning("Query for %s returned status %s", gndID, response.status_code)
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        titles = soup.find_all("span", class_="lit_title")  # find titles

        # for each title found
        for title_span in titles:
            inbuch_div = title_span.find_next_sibling("div", class_="inbuch")
            title = title_span.text.replace('\u2009\u2009', "")
            title = title.replace("[Online-Ressource]", "")
            title = title.replace("\n", "")
            title = title.replace("\\", "")
            title = title.strip()
            title = " ".join(filter(None, title.split()))

            cleantitle = clean_url_string(title)
            work_uri = URIRef(f"http://data.judaicalink.org/data/nrwbibdjg/{cleantitle}")

            g.add((work_uri, RDF.type, URIRef(str(GNDO) + "Work")))
            g.add((work_uri, JL.describedAt, Literal(url)))
            g.add((work_uri, DC.title, Literal(title)))
            g.add(
                (
                    work_uri,
                    URIRef(str(GNDO) + "author"),
                    URIRef(f"http://data.judaicalink.org/data/nrwbibdjg/{gndID}"),
                )
            )

            if inbuch_div:
                inbuch = inbuch_div.text.strip()
                inbuch = inbuch.replace("\n", "")
                inbuch = inbuch.replace("→ Ressource in externer Webseite betrachten ...", "")
                inbuch = inbuch.strip()
                inbuch = " ".join(filter(None, inbuch.split()))
                g.add((work_uri, JL.hasAbstract, Literal(inbuch)))

            add_creation_date(g, work_uri)

        # Person-URI from GND-ID
        person_uri = URIRef(f"http://data.judaicalink.org/data/nrwbibdjg/{gndID}")
        g.add((person_uri, RDF.type, FOAF.Person))

        # GND enrichment
        for pred_obj in get_gnd_ttl_data(gndID):
            obj = pred_obj[1]
            prefix, predicate_name = pred_obj[0].split(".")
            if prefix == "gndo":
                predicate_uri = GNDO[predicate_name]
            elif prefix == "owl":
                predicate_uri = OWL[predicate_name]
            elif prefix == "foaf":
                predicate_uri = FOAF[predicate_name]
            elif prefix == "skos":
                predicate_uri = SKOS[predicate_name]
            elif prefix == "jl":
                predicate_uri = JL[predicate_name]
            elif prefix == "edm":
                predicate_uri = EDM[predicate_name]
            elif prefix == "dc":
                predicate_uri = DCNS[predicate_name]
            elif prefix == "dcterms":
                predicate_uri = DCT[predicate_name]
            elif prefix == "rdfs":
                predicate_uri = RDFS[predicate_name]
            elif prefix == "geo":
                predicate_uri = GEO[predicate_name]
            else:
                predicate_uri = URIRef(f"http://{prefix}/{predicate_name}")

            if obj.startswith("http"):
                obj_term = URIRef(obj)
            else:
                obj_term = Literal(obj)

            g.add((person_uri, predicate_uri, obj_term))

        add_creation_date(g, person_uri)

    logger.info("nrwbibdjg graph construction finished; triples: %d", len(g))


# ----------------------------------------------------------------------
# Generator Adapter (ABC)
# ----------------------------------------------------------------------
class Generator(RDFGeneratorBase):
    def build(self, g: Graph, ctx) -> None:
        build_nrwbibdjg_graph(g)


# ----------------------------------------------------------------------
# CLI / main()
# ----------------------------------------------------------------------
def parse_args(argv: list[str] | None = None):
    """
    Parse command line arguments.
    :param argv: List of command line arguments (or None for sys.argv)
    :return: Parsed arguments
    """
    p = argparse.ArgumentParser(description="Build RDF for nrwbibdjg and (optionally) load & publish.")
    p.add_argument("--load", action="store_true", help="Load into Fuseki after generation")
    p.add_argument("--append", action="store_true", help="Append instead of replacing in Fuseki")
    p.add_argument(
        "--only-newer",
        action="store_true",
        help="Only load if file has not changed (hash/mtime)",
    )
    p.add_argument("--no-dumps", action="store_true", help="Don't copy files to dumps directory")
    p.add_argument("--meta-only", action="store_true", help="Write only metadata, no data graph")
    p.add_argument(
        "--graph",
        default=None,
        help="Named graph URI; Standard from frontmatter: graph",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None):
    """
    Main function to build the nrwbibdjg dataset.
    :param argv: List of command line arguments (or None for sys.argv)
    :return: None
    """
    args = parse_args(argv)

    ds_root = Path(__file__).resolve().parents[1]  # …/nrwbibdjg/
    out_dir = ds_root / "output"
    ensure_dir(out_dir)

    logger.info("Starting nrwbibdjg build (meta_only=%s)", args.meta_only)

    # 1) Generate data graph (.ttl + .gz)
    res: dict = {"status": "success", "ttl": str(out_dir / f"{SLUG}.ttl"), "slug": SLUG}
    ttl_path: Path | None = None

    if not args.meta_only:
        gen = Generator(ds_root)
        res = gen.run()
        print(json.dumps(res, indent=2, ensure_ascii=False))

        if res.get("status") != "success":
            err = res.get("error")
            tb = res.get("traceback")
            if err:
                logger.error("nrwbibdjg generation failed with error: %s", err)
            if tb:
                logger.error("Traceback from result:\n%s", tb)
            logger.error("nrwbibdjg generation failed; aborting.")
            return

        ttl_path = Path(res["ttl"])

    gz_path: Path | None = None
    if ttl_path and ttl_path.exists() and not args.meta_only:
        gz_path = compress_file(ttl_path)
        logger.info("gzipped data: %s", gz_path)

    # 2) Metadata graph from TOML (nrwbibdjg/nrwbibdjg.md)
    meta_md = ds_root / f"{SLUG}.md"
    meta_front = load_frontmatter_toml(meta_md) if meta_md.exists() else {}

    metadata = {
        "slug": SLUG,
        "title": meta_front.get("title") or "Bibliografie deutsch-jüdische Geschichte Nordrhein-Westfalen",
        "license": meta_front.get("license") or {
            "uri": "https://creativecommons.org/licenses/by/4.0/",
            "name": "CC-BY 4.0",
        },
        "generator": {
            "gitweb": meta_front.get("generator", {}).get("gitweb")
            if isinstance(meta_front.get("generator"), dict)
            else "https://github.com/judaicalink/judaicalink-generators/tree/main/nrwbibdjg",
            "commit": os.environ.get("GIT_COMMIT", "local"),
            "script": "nrwbibdjg/scripts/build.py",
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
            b = URIRef(url) if url else subject
            meta_g.add((b, DCTERMS.description, Literal(desc)))

    meta_ttl = out_dir / f"{SLUG}.meta.ttl"
    meta_g.serialize(destination=str(meta_ttl), format="turtle")
    meta_gz = compress_file(meta_ttl)
    logger.info("metadata written: %s (+ .gz)", meta_ttl)

    # 3) Optional: load into Fuseki (data graph + meta graph)
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
        print(json.dumps(lr_data.__dict__, indent=2, ensure_ascii=False))

        lr_meta = upsert_metadata_graph(
            slug=f"{SLUG}-meta",
            ttl_path=str(meta_ttl),
            graph="http://data.judaicalink.org/datasets",
            subject=str(DATASET_URI),
            only_newer=True,
        )
        print(json.dumps(lr_meta.__dict__, indent=2, ensure_ascii=False))

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


if __name__ == "__main__":
    main()
