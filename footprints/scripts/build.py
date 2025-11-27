# -*- coding: utf-8 -*-
"""
Generator for Footprints – tracing the history and movement of Jewish books.

Generator by Christian Deuschle, 2023.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import os
import shutil
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
import urllib3
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

# ---------- Repo-Root ----------
REPO_ROOT = Path(__file__).resolve().parents[2]  # .../judaicalink-generators
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Core infrastructure
from generator.base import RDFGeneratorBase  # type: ignore
from generator.loader import load_to_fuseki, upsert_metadata_graph  # type: ignore
from generator.metadata import build_metadata_graph  # type: ignore
from generator.rdf import JL_DATA, JL_DS, DCTERMS, SKOS, FOAF  # type: ignore
from generator.util import ensure_dir, load_frontmatter_toml  # type: ignore

# Suppress SSL warnings for requests to Footprints (self-signed cert)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Namespaces
JL_ONTO = Namespace("http://data.judaicalink.org/ontology/")
GNDO = Namespace("http://d-nb.info/standards/elementset/gnd#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
EDM = Namespace("http://www.europeana.eu/schemas/edm/")
DCNS = Namespace("http://purl.org/dc/elements/1.1/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
VOID = Namespace("http://rdfs.org/ns/void#")

SLUG = "footprints"
DATASET_URI = JL_DS[SLUG]

API_BASE = "https://footprints.ctl.columbia.edu/api/person/?format=json&page={page}"

log = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; JudaicaLinkFootprintsBot/1.0)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
})

BASE_URL = "https://footprints.ctl.columbia.edu"

# ---------- Logging ----------
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

logger = logging.getLogger("footprints-build")
logger.info("Logging initialized → %s", LOG_FILE)


# ---------- Helpers ----------
def compress_file(path: Path) -> Path:
    """
    Gzips the given file and returns the path to the .gz file.
    ️:param path: Path to the file to compress
    ️:return: Path to the compressed .gz file
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
    :param slug: Dataset slug (e.g., 'footprints')
    :param files: List of Path objects to copy
    :return: List of Path objects that were successfully copied
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


def generate_hash_uuid(name: str) -> uuid.UUID:
    """
    Deterministic UUID based on SHA-256 hash of the name.
    ️:param name: Name string
    ️:return: UUID5 based on SHA-256 hash of the name
    """
    hashed_string = hashlib.sha256(name.encode("utf-8")).hexdigest()
    return uuid.uuid5(uuid.NAMESPACE_OID, hashed_string)


def fetch_person_page(page: int, max_polls: int = 10, poll_wait: float = 2.0) -> dict | None:
    """
    Calls one page of the Footprints person list.
    Treats 202 Accepted by polling a job/redirect URL if necessary.
    :param page: Page number to fetch
    :param max_polls: Maximum number of polls for 202 responses
    :param poll_wait: Seconds to wait between polls
    :return: Parsed JSON dict or None on error
    """
    url = f"{BASE_URL}/api/person/?format=json&page={page}"
    log.info("Requesting Footprints page %s -> %s", page, url)

    resp = SESSION.get(url, timeout=30)
    log.debug("Initial response: %s, headers=%r", resp.status_code, resp.headers)

    # Usual case: 200 OK
    if resp.status_code == 200:
        try:
            return resp.json()
        except ValueError:
            log.error("Footprints page %s: 200 OK but no valid JSON", page)
            return None

    # Asynchronous case: 202 Accepted
    if resp.status_code == 202:
        job_url = (
                resp.headers.get("Location")
                or resp.headers.get("Content-Location")
                or url  # Fallback on same URL
        )
        log.info("Footprints returned 202 for page %s, polling %s", page, job_url)

        for i in range(max_polls):
            time.sleep(poll_wait)
            r2 = SESSION.get(job_url, timeout=30)
            log.debug(
                "Poll %d for page %s -> %s, headers=%r",
                i + 1, page, r2.status_code, r2.headers
            )

            if r2.status_code == 200:
                try:
                    return r2.json()
                except ValueError:
                    log.error(
                        "Footprints poll for page %s returned 200 but no valid JSON",
                        page,
                    )
                    return None

            if r2.status_code not in (200, 202):
                log.error(
                    "Footprints poll for page %s failed: %s %s",
                    page, r2.status_code, r2.text[:500],
                )
                return None

        log.error(
            "Footprints page %s stayed in 202 Accepted after %d polls – giving up",
            page, max_polls,
        )
        return None

    # Error case
    log.error(
        "Footprints page %s failed: %s %s",
        page, resp.status_code, resp.text[:500],
    )
    return None


# ---------- Footprints logic ----------
def build_footprints_graph(g: Graph) -> None:
    """
    Retrieves people from the Footprints API and adds them to the graph `g`.
    - Based on the original script (generate_hashUU + person URIs)
    - Handles 202 (Accepted) errors with polling
    - Automatically follows redirects
    - Aborts with a log in case of obvious bot blocking (403/429).
    """

    # bind prefixes but only for this graph
    g.bind("skos", SKOS)
    g.bind("foaf", FOAF)
    g.bind("jl", JL_ONTO)
    g.bind("gndo", GNDO)
    g.bind("owl", OWL)
    g.bind("edm", EDM)
    g.bind("dc", DCNS)
    g.bind("dcterms", DCTERMS)
    g.bind("rdfs", RDFS)
    g.bind("geo", GEO)

    session = requests.Session()

    # Header for browser
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
        "Referer": "https://footprints.ctl.columbia.edu/",
        "X-Requested-With": "XMLHttpRequest",
    })

    REQUEST_TIMEOUT = (10, 60)  # (connect, read) – long, but not infinite
    MAX_202_POLLS = 2  # retry count for 202 Accepted
    POLL_SLEEP = 3  # seconds between polls

    page = 1
    total_persons = 0

    logger.info("Starting Footprints harvesting")

    while True:
        url = f"https://footprints.ctl.columbia.edu/api/person/?format=json&page={page}"
        logger.info("Requesting Footprints page %s: %s", page, url)

        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT, verify=False, allow_redirects=True)
        except requests.exceptions.RequestException as e:
            logger.error("Request to %s failed: %s", url, e)
            break

        status = resp.status_code
        logger.info("Initial response for page %s: HTTP %s", page, status)

        # possible bot protection / auth errors
        if status in (401, 403, 429):
            logger.error(
                "Got HTTP %s for %s – this may be authentication or bot protection. "
                "Body (first 300 chars): %r",
                status, url, resp.text[:300],
            )
            break

        # 202 = Accepted -> backend still processing
        polls = 0
        while status == 202 and polls < MAX_202_POLLS:
            polls += 1
            logger.warning(
                "Page %s: HTTP 202 Accepted (poll %d/%d). Waiting %d seconds before retry.",
                page, polls, MAX_202_POLLS, POLL_SLEEP,
            )
            time.sleep(POLL_SLEEP)
            try:
                resp = session.get(url, timeout=REQUEST_TIMEOUT, verify=False, allow_redirects=True)
            except requests.exceptions.RequestException as e:
                logger.error("Request to %s failed on poll %d: %s", url, polls, e)
                break
            status = resp.status_code
            logger.info("Poll %d for page %s: HTTP %s", polls, page, status)

            if status in (401, 403, 429):
                logger.error(
                    "Got HTTP %s on poll for %s – this may be authentication or bot protection. "
                    "Body (first 300 chars): %r",
                    status, url, resp.text[:300],
                )
                break

        if status != 200:
            logger.error(
                "Stopping at page %s: HTTP %s, body (first 300 chars): %r",
                page, status, resp.text[:300],
            )
            break

        # parse JSON
        try:
            data = resp.json()
        except ValueError:
            logger.error(
                "Could not parse JSON for page %s; body (first 300 chars): %r",
                page, resp.text[:300],
            )
            break

        results = data.get("results") or []
        if not results:
            logger.info("No more results at page %s – results empty. Stopping.", page)
            break

        logger.info("Page %s: %d persons", page, len(results))

        for person in results:
            name = (person.get("name") or "").strip()
            if not name:
                continue

            # URI scheme
            uu = generate_hash_uuid(name)
            uri = URIRef(f"https://footprints.ctl.columbia.edu/api/person/{uu}/?format=json")

            g.add((uri, RDF.type, FOAF.Person))
            g.add((uri, FOAF.name, Literal(name)))
            g.add((uri, SKOS.prefLabel, Literal(name)))
            g.add(
                (
                    uri,
                    DCTERMS.created,
                    Literal(datetime.now().isoformat(), datatype=XSD.dateTime),
                )
            )
            total_persons += 1

        # Pagination: next link
        next_url = data.get("next")
        if not next_url:
            logger.info("No 'next' link after page %s – assuming last page.", page)
            break

        page += 1

    logger.info(
        "Footprints person graph finished; persons: %d, triples in g: %d",
        total_persons,
        len(g),
    )


# ---------- ABC adapter ----------
class Generator(RDFGeneratorBase):
    """
    RDF Generator for Footprints.
    """

    def build(self, g: Graph, ctx) -> None:
        """
        Build the Footprints RDF graph.
        ️:param g: rdflib Graph to populate
        ️:param ctx: Context dictionary (not used)
        ️:return: None
        """
        build_footprints_graph(g)


# ---------- CLI ----------
def parse_args(argv: list[str] | None = None):
    p = argparse.ArgumentParser(description="Build RDF for Footprints and (optionally) load & publish.")
    p.add_argument("--load", action="store_true", help="Load into Fuseki after generation")
    p.add_argument("--append", action="store_true", help="Append to graph, instead of replacing")
    p.add_argument(
        "--only-newer",
        action="store_true",
        help="Only load if the file is unchanged (hash/mtime)",
    )
    p.add_argument("--no-dumps", action="store_true", help="Do not copy files to dumps")
    p.add_argument("--meta-only", action="store_true", help="Write only metadata (no data graph)")
    p.add_argument(
        "--graph",
        default=None,
        help="Named graph URI; Standard from footprints.md: graph or default",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)

    ds_root = Path(__file__).resolve().parents[1]  # .../footprints/
    out_dir = ds_root / "output"
    ensure_dir(out_dir)

    logger.info("Starting Footprints build (meta_only=%s)", args.meta_only)

    # 1) data graph
    res: dict = {"status": "success", "ttl": str(out_dir / f"{SLUG}.ttl"), "slug": SLUG}
    if not args.meta_only:
        gen = Generator(ds_root)
        res = gen.run()  # writes to output/footprints.ttl
        print(json.dumps(res, indent=2, ensure_ascii=False))
        if res.get("status") != "success":
            logger.error("Footprints generation failed: %s", res.get("error"))
            tb = res.get("traceback")
            if tb:
                logger.error("Traceback:\n%s", tb)
            return

    ttl_path = Path(res["ttl"])
    gz_path: Optional[Path] = None
    if ttl_path.exists() and not args.meta_only:
        gz_path = compress_file(ttl_path)
        logger.info("gzipped data: %s", gz_path)

    # 2) from footprints.md
    meta_md = ds_root / f"{SLUG}.md"
    meta_front = load_frontmatter_toml(meta_md) if meta_md.exists() else {}

    metadata = {
        "slug": SLUG,
        "title": meta_front.get("title") or "Footprints - Jewish Books through Time and Place",
        "license": meta_front.get("license") or {
            "uri": "https://creativecommons.org/licenses/by-sa/4.0/",
            "name": "CC-BY-SA 4.0",
        },
        "generator": {
            "gitweb": meta_front.get("generator", {}).get("gitweb")
            if isinstance(meta_front.get("generator"), dict)
            else "https://github.com/judaicalink/judaicalink-generators/tree/main/footprints",
            "commit": os.environ.get("GIT_COMMIT", "local"),
            "script": "footprints/scripts/build.py",
        },
    }

    meta_g = build_metadata_graph(metadata, scriptinfo={"slug": SLUG})
    subject = DATASET_URI

    # extra metadata from frontmatter
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

    # 3) Optional: Fuseki load
    if args.load and not args.meta_only:
        graph_uri = args.graph or meta_front.get("graph") or "http://data.judaicalink.org/data/footprints"

        lr_data = load_to_fuseki(
            slug=SLUG,
            ttl_path=str(ttl_path),
            graph=graph_uri,
            endpoint=None,  # JL_FUSEKI_URL from ENV
            replace=(not args.append),
            only_newer=args.only_newer,
        )
        print(json.dumps(lr_data.__dict__, indent=2, ensure_ascii=False))

        # Metadata graph: http://data.judaicalink.org/datasets
        lr_meta = upsert_metadata_graph(
            slug=f"{SLUG}-meta",
            ttl_path=str(meta_ttl),
            graph="http://data.judaicalink.org/datasets",
            subject=str(DATASET_URI),
            only_newer=True,
        )
        print(json.dumps(lr_meta.__dict__, indent=2, ensure_ascii=False))

    # 4) Optional: Dumps
    if not args.no_dumps:
        files: list[Path] = [meta_ttl, meta_gz]
        if ttl_path.exists() and not args.meta_only:
            files.append(ttl_path)
            if gz_path:
                files.append(gz_path)
        copied = copy_to_dumps(SLUG, files)
        for c in copied:
            logger.info("copied → %s", c)


if __name__ == "__main__":
    main()
