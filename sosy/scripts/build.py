# -*- coding: utf-8 -*-
"""
Generator für Soundscape Synagogue (Sosy),
refactored nach dem Workflow von hhkeydocs/build.py:

1. Daten aus API laden
2. RDF-Graph generieren (Ontologien: SKOS, FOAF, JL, GND, EDM, DC/DCTERMS, OWL)
3. TTL in datasets/sosy/output/sosy.ttl schreiben und gzippen
4. Metadaten aus sosy/sosy.md erzeugen (sosy.meta.ttl + .gz)
5. Optional: Dateien nach $JL_DUMPS_ROOT/sosy/current/ kopieren
6. Optional: Datengraph + Metadaten in Fuseki laden
"""

from __future__ import annotations

import argparse
import gzip
import json
import locale
import logging
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import requests
import urllib3
from dateutil.parser import parse
from rdflib import Graph, Literal, Namespace, URIRef, BNode
from rdflib.namespace import RDF, DCTERMS, XSD, OWL

# ---------- Repo-Root für Standalone-Import ----------
REPO_ROOT = Path(__file__).resolve().parents[2]  # .../judaicalink-generators
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Core-Utilities / ABC / Metadata / Loader
from generator.util import ensure_dir, load_frontmatter_toml  # type: ignore
from generator.base import RDFGeneratorBase  # type: ignore
from generator.metadata import build_metadata_graph  # type: ignore
from generator.loader import load_to_fuseki, upsert_metadata_graph  # type: ignore

# ---------- Namespaces ----------
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
JL = Namespace("http://data.judaicalink.org/ontology/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
GNDO = Namespace("http://d-nb.info/standards/elementset/gnd#")
EDM = Namespace("http://www.europeana.eu/schemas/edm/")
DC = Namespace("http://purl.org/dc/elements/1.1/")
JL_DATA = Namespace("http://data.judaicalink.org/data/")
JL_DS = Namespace("http://data.judaicalink.org/datasets/")
VOID = Namespace("http://rdfs.org/ns/void#")

SLUG = "sosy"
DATASET_URI = URIRef(f"{JL_DS}{SLUG}")

# ---------- Logging Setup ----------
LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"{SLUG}.log"

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# configure root logger, all modules inherit from this
root = logging.getLogger()
root.setLevel(logging.DEBUG)
root.handlers.clear()
root.addHandler(console_handler)
root.addHandler(file_handler)

# optional: own logger for this module
logger = logging.getLogger("sosy-build")

logger.info(f"Logging initialized → {LOG_FILE}")

# ---------- Locale / Logging ----------
try:
    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
except Exception:
    # Fallback, if de_DE locale not installed
    pass

logger = logging.getLogger("sosy-build")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


# ---------- Helper: copy files & gzip ----------
def compress_file(path: Path) -> Path:
    """
    Compress a file with gzip and return the new path.
    :param path: Path to the file to compress
    :return: Path to the compressed .gz file
    """
    gz_path = path.with_suffix(path.suffix + ".gz")
    with path.open("rb") as f_in, gzip.open(gz_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return gz_path


def copy_to_dumps(slug: str, files: list[Path]) -> list[Path]:
    """
    Copies files to the dumps directory for the given slug.
    JL_DUMPS_ROOT/<slug>/current/   (Default: /data/dumps)
    :param slug: Dataset slug (e.g., "sosy")
    :param files: List of file paths to copy
    :return: List of copied file paths in the dumps directory
    """
    dumps_root = Path(os.environ.get("JL_DUMPS_ROOT", "/data/dumps")).resolve()
    dest_dir = dumps_root / slug / "current"
    ensure_dir(dest_dir)
    copied: list[Path] = []
    for f in files:
        dest = dest_dir / f.name
        shutil.copy2(str(f), str(dest))
        copied.append(dest)
    return copied


# ---------- sosy specific helper functions ----------

def get_occupation(occupation: str) -> tuple[str, str]:
    """
    Checks if a JL Occupations URI already exists for a job title.
    :param occupation: Job title string
    :return: Tuple of ("url", URL) or ("literal", occupation)
    """
    url = "https://data.judaicalink.org/data/html/occupation/" + occupation
    try:
        response = requests.get(url, timeout=20)
    except Exception:
        return "literal", occupation
    if response.status_code == 200:
        return "url", url
    return "literal", occupation


def fetch_identifiers() -> List[str]:
    """
    Fetches all person identifiers from the Sosy API.
    :return: List of person identifiers
    """
    url = "https://www.soundscape-synagoge.de/api/person/all/base"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    json_values = resp.json()
    ids: List[str] = []
    for value in json_values:
        ids.append(value["identifier"])
    logger.info("Fetched %d identifiers from Sosy API", len(ids))
    return ids


def convert_date(date: str) -> Optional[datetime.date]:
    """
    Attempts to interpret various German date formats.
    (Logic from old generator.py, slightly cleaned up.)
    :param date: Date string from Sosy API
    :return: datetime.date object or None if parsing failed
    """
    if not date:
        return None

    date = date.replace("?", "")
    date = date.replace("dem", "")
    date = date.replace("nach", "")
    date = date.replace("verschollen", "")
    date = date.replace("Anfang", "")
    date = date.replace("beigesetzt am", "")
    date = date.replace("im", "")
    date = date.replace("ca.", "")
    date = date.replace("geb. am", "")
    date = date.split(",")[0]
    date = date.split("(")[0]
    date = date.split("[")[0]
    date = date.strip()

    # try to parse with known formats
    for fmt in [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d. %b. %Y",
        "%d. %B %Y",
        "%B %Y",
        "%b. %Y",
        "%Y",
    ]:
        try:
            return datetime.strptime(date, fmt).date()
        except Exception:
            pass

    # Fallback with dateutil.parse for more complex cases
    try:
        # Examples: "12. Januar 1942", "Jan. 1942" etc.
        if re.search(r"[A-Za-z]", date):
            return parse(date, fuzzy=True).date()
    except Exception:
        pass

    logger.error("Could not convert date: %s", date)
    return None


def get_person_data(identifier_list: list[str]) -> list[dict]:
    """
    POST request to Sosy API to load person data.
    Corresponds to get_person_data() from old script.
    :param identifier_list: List of person identifiers
    :return: List of person data dictionaries
    """
    list_url = "https://www.soundscape-synagoge.de/api/person/list"
    body = json.dumps(identifier_list)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    http = urllib3.PoolManager()
    try:
        response = http.request("POST", list_url, headers=headers, body=body)
        logger.info("Sosy list response: %s", response.status)
        if response.status == 200:
            persons_result = json.loads(response.data.decode("utf-8"))
            return persons_result  # list from person dict
    except Exception as e:
        logger.error("Could not get Sosy data. Error: %s", e)

    return []


def clean_url_string(string: str) -> str:
    """
    Cleans a person's name for use in a URI.
    :param string: Input string (person's name)
    :return: Cleaned string
    """
    s = string.strip()
    s = s.replace("'", "")
    s = s.replace('"', "")
    s = s.replace(",", "_")
    s = s.replace("<<", "")
    s = s.replace(">>", "")
    s = s.replace("|", "_")
    s = s.replace(" ", "")
    s = s.replace("<", "_")
    s = s.replace(">", "_")
    s = s.replace(".", "")
    s = s.replace("[", "")
    s = s.replace("]", "")
    s = s.replace("(", "")
    s = s.replace(")", "")
    s = s.replace("{", "")
    s = s.replace("}", "")
    return s


def build_sosy_graph(g: Graph) -> None:
    """
    Builds the Sosy RDF graph in the provided rdflib Graph 'g'.
    :param g: rdflib Graph to populate
    :return: None
    """

    # Prefixes
    g.bind("skos", SKOS)
    g.bind("foaf", FOAF)
    g.bind("jl", JL)
    g.bind("gndo", GNDO)
    g.bind("owl", OWL)
    g.bind("edm", EDM)
    g.bind("dc", DC)
    g.bind("dcterms", DCTERMS)

    # 1)Fetch all identifiers
    identifiers = fetch_identifiers()
    if not identifiers:
        logger.warning("No identifiers fetched from Sosy API; graph will be empty.")
        return

    # 2) Fetch person data
    persons_list = get_person_data(identifiers)
    logger.info("Fetched %d persons from Sosy API", len(persons_list))

    # 3) Generate RDF triples
    for person in persons_list:
        try:
            pdata = person["person"]
        except Exception:
            logger.error("Unexpected person structure: %r", person)
            continue

        display_name = pdata.get("displayName") or ""
        if not display_name:
            continue

        url_name = clean_url_string(display_name)
        uri = URIRef(f"{JL_DATA}{SLUG}/{url_name}")

        # Person type
        g.add((uri, RDF.type, FOAF.Person))

        # Name
        g.add((uri, FOAF.name, Literal(display_name)))
        g.add((uri, SKOS.prefLabel, Literal(display_name)))

        # alternative names
        alt_list = pdata.get("alternateNameList")
        if alt_list:
            for name in alt_list.split(","):
                name = name.strip()
                if name:
                    g.add((uri, SKOS.altLabel, Literal(name)))
        if pdata.get("mainName"):
            g.add((uri, SKOS.altLabel, Literal(pdata["mainName"])))
        if pdata.get("birthName"):
            g.add((uri, SKOS.altLabel, Literal(pdata["birthName"])))

        # describedAt
        base_id = pdata.get("personBase", {}).get("identifier")
        if base_id:
            g.add(
                (
                    uri,
                    JL.describedAt,
                    URIRef(
                        f"https://www.soundscape-synagoge.de/person?"
                        f"tab=masterdata&identifier={base_id}"
                    ),
                )
            )

        # birthDate
        bd = pdata.get("birthDate")
        if bd:
            bd_parsed = convert_date(bd)
            if bd_parsed:
                g.add((uri, JL.birthDate, Literal(bd_parsed)))

        # deathDate
        dd = pdata.get("dateOfDeath")
        if dd:
            dd_parsed = convert_date(dd)
            if dd_parsed:
                g.add((uri, JL.deathDate, Literal(dd_parsed)))

        # birthLocation
        bp = pdata.get("birthPlace")
        if bp:
            g.add((uri, JL.birthLocation, Literal(bp)))

        # deathLocation
        dp = pdata.get("placeOfDeath")
        if dp:
            g.add((uri, JL.deathLocation, Literal(dp)))

        # hasPublication
        writings = person.get("writings")
        if writings:
            for _key, writing_list in writings.items():
                if not writing_list:
                    continue
                for item in writing_list:
                    txt = (item or "").strip()
                    if txt:
                        g.add((uri, JL.hasPublication, Literal(txt)))

        # occupation & titles
        bio = person.get("biography") or {}
        job_list = bio.get("jobDescriptionList") or []
        for job_desc in job_list:
            # Split an Kommata, aber Klammern respektieren
            for job in re.split(r",\s*(?![^()]*\))", job_desc):
                job = job.strip()
                if not job:
                    continue
                occ_type, occ_val = get_occupation(job)
                if occ_type == "url":
                    g.add((uri, JL.occupation, URIRef(occ_val)))
                else:
                    g.add((uri, JL.occupation, Literal(occ_val)))

        title_list = bio.get("titleList") or []
        for title in title_list:
            if title:
                g.add((uri, JL.hasAbstract, Literal(title)))

        # created timestamp
        g.add(
            (
                uri,
                DCTERMS.created,
                Literal(datetime.utcnow().isoformat(), datatype=XSD.dateTime),
            )
        )


# ---------- ABC adapter ----------
class Generator(RDFGeneratorBase):
    def build(self, g: Graph, ctx) -> None:
        build_sosy_graph(g)


# ---------- CLI ----------
def parse_args(argv: list[str] | None = None):
    p = argparse.ArgumentParser(description="Build RDF for Sosy and (optionally) load & publish.")
    p.add_argument("--load", action="store_true", help="Load into Fuseki after generation")
    p.add_argument("--append", action="store_true", help="Attach to existing graph instead of replacing")
    p.add_argument(
        "--only-newer",
        action="store_true",
        help="Load only when file is unchanged  (hash/mtime)",
    )
    p.add_argument("--no-dumps", action="store_true", help="Don't copy into the dumps folder")
    p.add_argument("--meta-only", action="store_true", help="Write only metadata (no data graph)")
    p.add_argument(
        "--graph",
        default=None,
        help="Named graph URI; Standard from TOML: graph",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None):
    """
    Main function for building the Sosy dataset.
    1) Generates the RDF data graph and writes it to output/sosy.ttl
    2) Generates the metadata graph from sosy/sosy.md
    3) Optionally loads both graphs into Fuseki
    4) Optionally copies the files to the dumps directory
    5) Supports a --meta-only mode to only generate metadata
    6) Command-line arguments for controlling behavior
    :param argv: List of command-line arguments (for testing); defaults to sys.argv
    """
    args = parse_args(argv)

    ds_root = Path(__file__).resolve().parents[1]
    out_dir = ds_root / "output"
    ensure_dir(out_dir)

    logger.info("Starting Sosy build (meta_only=%s)", args.meta_only)

    # 1) Data graph
    res: dict = {"status": "success", "ttl": str(out_dir / f"{SLUG}.ttl"), "slug": SLUG}
    if not args.meta_only:
        gen = Generator(ds_root)
        res = gen.run()  # write to output/sosy.ttl
        print(json.dumps(res, indent=2, ensure_ascii=False))
        if res.get("status") != "success":
            logger.error("Sosy generation failed; aborting.")
            return

    ttl_path = Path(res["ttl"])
    gz_path: Optional[Path] = None
    if ttl_path.exists() and not args.meta_only:
        gz_path = compress_file(ttl_path)
        logger.info("gzipped data: %s", gz_path)

    # 2) metadata graph from TOML (sosy/sosy.md)
    meta_md = ds_root / f"{SLUG}.md"
    meta_front = load_frontmatter_toml(meta_md) if meta_md.exists() else {}

    metadata = {
        "slug": SLUG,
        "title": meta_front.get("title") or "Soundscape Synagogue",
        "license": meta_front.get("license") or {
            "uri": "https://creativecommons.org/licenses/by/4.0/",
            "name": "CC-BY 4.0",
        },
        "generator": {
            "gitweb": meta_front.get("generator", {}).get("gitweb")
                      or "https://github.com/judaicalink/judaicalink-generators/tree/main/sosy",
            "commit": os.environ.get("GIT_COMMIT", "local"),
            "script": "sosy/scripts/build.py",
        },
    }
    meta_g = build_metadata_graph(metadata)

    # additional fields from frontmatter
    subject = DATASET_URI
    if (author := meta_front.get("author")):
        meta_g.add((subject, DCTERMS.creator, Literal(author)))
    if (authorlink := meta_front.get("authorlink")):
        meta_g.add((subject, DCTERMS.creator, URIRef(authorlink)))
    if (website := meta_front.get("website")):
        meta_g.add((subject, DCTERMS.source, URIRef(website)))
    if (date := meta_front.get("date")):
        meta_g.add((subject, DCTERMS.issued, Literal(date)))
    # Files from [[files]]
    for f in meta_front.get("files", []):
        if (url := f.get("url")):
            meta_g.add((subject, VOID.dataDump, URIRef(url)))
        if (desc := f.get("description")):
            node = BNode()
            meta_g.add((node, DCTERMS.description, Literal(desc)))

    meta_ttl = out_dir / f"{SLUG}.meta.ttl"
    meta_g.serialize(destination=str(meta_ttl), format="turtle")
    meta_gz = compress_file(meta_ttl)
    logger.info("metadata written: %s (+ .gz)", meta_ttl)

    # 3) Optional: load into Fuseki (data graph + meta graph)
    if args.load and not args.meta_only:
        graph_uri = args.graph or meta_front.get("graph")  # z.B. http://data.judaicalink.org/data/sosy

        # Data graph
        lr_data = load_to_fuseki(
            slug=SLUG,
            ttl_path=str(ttl_path),
            graph=graph_uri,
            endpoint=None,
            replace=(not args.append),
            only_newer=args.only_newer,
        )
        print(json.dumps(lr_data.__dict__, indent=2, ensure_ascii=False))

        # Metad data: specific upsert function in common metadata graph
        lr_meta = upsert_metadata_graph(
            slug=f"{SLUG}-meta",
            ttl_path=str(meta_ttl),
            graph="http://data.judaicalink.org/datasets",
            subject=str(DATASET_URI),
            only_newer=True,
        )
        print(json.dumps(lr_meta.__dict__, indent=2, ensure_ascii=False))

    if not args.meta_only:
        gen = Generator(ds_root)
        res = gen.run()
        print(json.dumps(res, indent=2, ensure_ascii=False))

        if res.get("status") != "success":
            err = res.get("error")
            tb = res.get("traceback")
            if err:
                logger.error("Sosy generation failed with error: %s", err)
            if tb:
                logger.error("Traceback from result:\n%s", tb)
            logger.error("Sosy generation failed; aborting.")
            return

    # 4) Optional: Copy to dumps
    if not args.no_dumps:
        files: list[Path] = []
        if ttl_path.exists() and not args.meta_only:
            files.append(ttl_path)
            if gz_path:
                files.append(gz_path)
        files.extend([meta_ttl, meta_gz])
        copied = copy_to_dumps(SLUG, files)
        for c in copied:
            logger.info("copied → %s", c)


if __name__ == "__main__":
    main()
