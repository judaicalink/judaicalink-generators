# -*- coding: utf-8 -*-
"""
Generator for Hamburger Schlüsseldokumente zur deutsch-jüdischen Geschichte.
Quelle: https://schluesseldokumente.net/
Refactor nach dem Muster des Gidal-Builders.
"""

from __future__ import annotations

import argparse
import gzip
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

import json
import requests
from bs4 import BeautifulSoup
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, DCTERMS, XSD, OWL
from tqdm import tqdm

# ---------- Repo-Root für Standalone-Import ----------
REPO_ROOT = Path(__file__).resolve().parents[2]  # .../judaicalink-generators
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Core-Utilities / ABC / Metadata
from generator.util import ensure_dir, load_frontmatter_toml  # type: ignore
from generator.base import RDFGeneratorBase  # type: ignore
from generator.metadata import build_metadata_graph  # type: ignore

# ---------- Namespaces ----------
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
JL   = Namespace("http://data.judaicalink.org/ontology/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
GNDO = Namespace("http://d-nb.info/standards/elementset/gnd#")
DC   = Namespace("http://purl.org/dc/elements/1.1/")
GEO  = Namespace("http://www.opengis.net/ont/geosparql#")
JL_DATA = Namespace("http://data.judaicalink.org/data/")
JL_DS   = Namespace("http://data.judaicalink.org/datasets/")

SLUG = "hhkeydocs"
DATASET_URI = URIRef(f"{JL_DS}{SLUG}")

# ---------- Helpers ----------
def sanitize_literal(text: Optional[str]) -> str:
    if not text:
        return ""
    text = re.sub(r'["\n\r]', "", str(text))
    return text.strip()

def clean_url_string(string: str) -> str:
    s = unicodedata.normalize("NFKD", str(string)).encode("ascii", "ignore").decode()
    s = re.sub(r'[\'"<>|.,()\[\]{}?#-]', "", s)
    return s.strip().replace(" ", "_")

def compress_file(path: Path) -> Path:
    gz_path = path.with_suffix(path.suffix + ".gz")
    with path.open("rb") as f_in, gzip.open(gz_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return gz_path

def copy_to_dumps(slug: str, files: list[Path]) -> list[Path]:
    """
    Kopiert Dateien in den Dumps-Ordner:
    $JL_DUMPS_ROOT/<slug>/current/   (Default: /data/dumps)
    """
    dumps_root = Path(os.environ.get("JL_DUMPS_ROOT", "/data/dumps")).resolve()
    dest_dir = dumps_root / slug / "current"
    ensure_dir(dest_dir)
    copied = []
    for f in files:
        dest = dest_dir / f.name
        shutil.copy2(str(f), str(dest))
        copied.append(dest)
    return copied

# ---------- VIAF über lobid ----------
def get_viaf_id(gnd_id: str) -> Optional[str]:
    try:
        r = requests.get(f"https://lobid.org/gnd/{gnd_id}.json", timeout=20)
        r.raise_for_status()
        data = r.json()
        for sameAs in data.get("sameAs", []):
            if sameAs.get("collection", {}).get("abbr") == "VIAF":
                return sameAs.get("id")
    except Exception:
        return None
    return None

# ---------- Beacon/Listen ziehn ----------
def fetch_person_ids(beacon_url: str) -> list[int]:
    ids: list[int] = []
    res = requests.get(beacon_url, timeout=30)
    soup = BeautifulSoup(res.content, "html.parser")
    for line in str(soup).splitlines():
        try:
            ids.append(int(line))
        except Exception:
            pass
    return ids

def fetch_org_ids(beacon_url: str) -> list[int]:
    ids: list[int] = []
    res = requests.get(beacon_url, timeout=30)
    soup = BeautifulSoup(res.content, "html.parser")
    for line in str(soup).splitlines():
        try:
            ids.append(int(line))
        except Exception:
            pass
    return ids

def fetch_place_ids(index_url: str) -> list[str]:
    links: list[str] = []
    res = requests.get(index_url, timeout=30)
    soup = BeautifulSoup(res.content, "html.parser")
    for a in soup.select(".list-unstyled li a"):
        href = a.get("href")
        if href:
            links.append(href)
    return links

# ---------- Graph-Erzeugung (Daten) ----------
def build_hhkeydocs_graph(g: Graph) -> None:
    """
    Holt Place-, Personen- und Organisationsdaten von schluesseldokumente.net
    und füllt den übergebenen Graphen (keine Serialisierung hier).
    """
    # Prefixes
    g.bind("skos", SKOS)
    g.bind("foaf", FOAF)
    g.bind("jl",   JL)
    g.bind("gndo", GNDO)
    g.bind("dc",   DC)
    g.bind("dcterms", DCTERMS)
    g.bind("geo",  GEO)
    g.bind("owl",  OWL)

    # --- Places ---
    place_ids = fetch_place_ids("https://schluesseldokumente.net/ort")
    for pid in tqdm(place_ids, desc="Places"):
        place_url = f"https://schluesseldokumente.net{pid}.jsonld"
        try:
            r = requests.get(place_url, timeout=30)
            if r.status_code != 200:
                continue
            data = json.loads(r.text)
            clean_name = clean_url_string(data.get("name", ""))
            if not clean_name:
                continue
            uri = URIRef(f"{JL_DATA}{SLUG}/{clean_name}")
            g.add((uri, RDF.type, GNDO.PlaceOrGeographicName))
            if nm := data.get("name"):
                g.add((uri, FOAF.name, Literal(nm)))
                g.add((uri, SKOS.prefLabel, Literal(nm)))
            g.add((uri, JL.describedAt, URIRef(place_url)))
            if geo := data.get("geo"):
                lat = geo.get("latitude"); lon = geo.get("longitude")
                if lat and lon:
                    g.add((uri, GEO.asWKT, Literal(f"Point (+{lon} +{lat})")))
            if data.get("containedInPlace", {}).get("name"):
                g.add((uri, GNDO.hierarchicalSuperiorOfPlaceOrGeographicName,
                       Literal(data["containedInPlace"]["name"])))
        except Exception:
            continue

    # --- Persons ---
    person_ids = fetch_person_ids("https://schluesseldokumente.net/person/gnd/beacon")
    for gid in tqdm(person_ids, desc="Persons"):
        url = f"https://schluesseldokumente.net/person/gnd/{gid}.jsonld"
        try:
            r = requests.get(url, timeout=30)
            if r.status_code != 200:
                continue
            data = json.loads(r.text)
            clean_name = clean_url_string(data.get("name", ""))
            if not clean_name:
                continue
            uri = URIRef(f"{JL_DATA}{SLUG}/{clean_name}")
            g.add((uri, RDF.type, FOAF.Person))
            g.add((uri, JL.describedAt, URIRef(url)))
            if nm := data.get("name"):
                g.add((uri, FOAF.name, Literal(nm)))
                g.add((uri, SKOS.prefLabel, Literal(nm)))
            g.add((uri, GNDO.gndIdentifier, Literal(str(gid))))
            viaf = get_viaf_id(str(gid))
            if viaf:
                g.add((uri, OWL.sameAs, URIRef(f"https://viaf.org/viaf/{viaf}/")))
            if bd := data.get("birthDate"):
                g.add((uri, JL.birthDate, Literal(bd)))
            if dd := data.get("deathDate"):
                g.add((uri, JL.deathDate, Literal(dd)))
            if bp := data.get("birthPlace", {}).get("name"):
                g.add((uri, JL.birthLocation, URIRef(f"{JL_DATA}{SLUG}/{clean_url_string(bp)}")))
            if dp := data.get("deathPlace", {}).get("name"):
                g.add((uri, JL.deathLocation, URIRef(f"{JL_DATA}{SLUG}/{clean_url_string(dp)}")))
            g.add((uri, DCTERMS.created, Literal(datetime.utcnow().isoformat(), datatype=XSD.dateTime)))
            if desc := data.get("description"):
                g.add((uri, JL.hasAbstract, Literal(sanitize_literal(desc))))
        except Exception:
            continue

    # --- Organisations ---
    org_ids = fetch_org_ids("https://schluesseldokumente.net/organisation/gnd/beacon")
    for oid in tqdm(org_ids, desc="Organisations"):
        url = f"https://schluesseldokumente.net/organisation/gnd/{oid}.jsonld"
        try:
            r = requests.get(url, timeout=30)
            if r.status_code != 200:
                continue
            data = json.loads(r.text)
            clean_name = clean_url_string(data.get("name", ""))
            if not clean_name:
                continue
            uri = URIRef(f"{JL_DATA}{SLUG}/{clean_name}")
            g.add((uri, RDF.type, FOAF.Organization))
            g.add((uri, JL.describedAt, URIRef(url)))
            if nm := data.get("name"):
                g.add((uri, FOAF.name, Literal(nm)))
                g.add((uri, SKOS.prefLabel, Literal(nm)))
            g.add((uri, GNDO.gndIdentifier, Literal(str(oid))))
            if fd := data.get("foundingDate"):
                g.add((uri, GNDO.dateOfEstablishment, Literal(fd)))
            if td := data.get("dissolutionDate"):
                g.add((uri, GNDO.dateOfTermination, Literal(td)))
            if desc := data.get("description"):
                g.add((uri, JL.hasAbstract, Literal(sanitize_literal(desc))))
            if hp := data.get("url"):
                g.add((uri, FOAF.homepage, URIRef(hp)))
        except Exception:
            continue


# ---------- ABC-Adapter ----------
class Generator(RDFGeneratorBase):
    def build(self, g: Graph, ctx) -> None:
        build_hhkeydocs_graph(g)


# ---------- CLI ----------
def parse_args(argv: list[str] | None = None):
    p = argparse.ArgumentParser(description="Build RDF for HHKeyDocs and (optionally) load & publish.")
    p.add_argument("--load", action="store_true", help="Nach Generierung in Fuseki laden")
    p.add_argument("--append", action="store_true", help="An Graph anhängen statt ersetzen")
    p.add_argument("--only-newer", action="store_true", help="Nur laden wenn Datei unverändert ist (hash/mtime -> skip)")
    p.add_argument("--no-dumps", action="store_true", help="Nicht in den Dumps-Ordner kopieren")
    p.add_argument("--meta-only", action="store_true", help="Nur Metadaten schreiben (kein Datengraph)")
    # Named-Graph aus TOML („graph“) kann überschrieben werden:
    p.add_argument("--graph", default=None, help="Named graph URI; Standard aus TOML: graph")
    return p.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)

    ds_root = Path(__file__).resolve().parents[1]  # .../hhkeydocs/
    out_dir = ds_root / "output"
    ensure_dir(out_dir)

    # 1) Datengraph
    res = {"status": "success", "ttl": str(out_dir / f"{SLUG}.ttl"), "slug": SLUG}
    if not args.meta_only:
        gen = Generator(ds_root)
        res = gen.run()  # schreibt output/hhkeydocs.ttl
        print(res)
        if res.get("status") != "success":
            return  # kein gzip/dumps/meta bei Fehler

    ttl_path = Path(res["ttl"])
    gz_path = None
    if ttl_path.exists() and not args.meta_only:
        gz_path = compress_file(ttl_path)
        print(f"gzipped: {gz_path}")

    # 2) Metadaten-Graph aus TOML (hhkeydocs/hhkeydocs.md)
    meta_md = ds_root / f"{SLUG}.md"
    meta_front = load_frontmatter_toml(meta_md) if meta_md.exists() else {}
    # Map in unser Metadata-Format:
    metadata = {
        "slug": SLUG,
        "title": meta_front.get("title") or "Hamburger Schlüsseldokumente",
        "license": meta_front.get("license") or {
            "uri": "https://creativecommons.org/licenses/by-sa/4.0/",
            "name": "CC-BY-SA 4.0",
        },
        "generator": {
            "gitweb": meta_front.get("generator", {}).get("gitweb") or
                      "https://github.com/judaicalink/judaicalink-generators/tree/main/hhkeydocs",
            "commit": os.environ.get("GIT_COMMIT", "local"),
            "script": "hhkeydocs/scripts/build.py",
        },
    }
    meta_g = build_metadata_graph(metadata)
    # optionale Extrafelder aus TOML
    subject = DATASET_URI
    if (author := meta_front.get("author")):
        meta_g.add((subject, DCTERMS.creator, Literal(author)))
    if (authorlink := meta_front.get("authorlink")):
        meta_g.add((subject, DCTERMS.creator, URIRef(authorlink)))
    if (website := meta_front.get("website")):
        meta_g.add((subject, DCTERMS.source, URIRef(website)))
    if (date := meta_front.get("date")):
        meta_g.add((subject, DCTERMS.issued, Literal(date)))
    # Dateien aus [[files]]
    for f in meta_front.get("files", []):
        if url := f.get("url"):
            meta_g.add((subject, Namespace("http://rdfs.org/ns/void#").dataDump, URIRef(url)))
        if desc := f.get("description"):
            node = BNode()
            meta_g.add((node, DCTERMS.description, Literal(desc)))

    meta_ttl = out_dir / f"{SLUG}.meta.ttl"
    meta_g.serialize(destination=str(meta_ttl), format="turtle")
    meta_gz = compress_file(meta_ttl)
    print(f"metadata written: {meta_ttl} (+ .gz)")

    # 3) Optional: in Fuseki laden (Datengraph + Metagraph)
    if args.load and not args.meta_only:
        from generator.loader import load_to_fuseki  # type: ignore
        graph_uri = args.graph or meta_front.get("graph")  # z.B. http://data.judaicalink.org/data/gba (hier: hhkeydocs)
        lr_data = load_to_fuseki(
            slug=SLUG,
            ttl_path=str(ttl_path),
            graph=graph_uri,
            endpoint=None,
            replace=(not args.append),
            only_newer=args.only_newer,
        )
        print(lr_data)
        lr_meta = load_to_fuseki(
            slug=f"{SLUG}-meta",
            ttl_path=str(meta_ttl),
            graph="http://data.judaicalink.org/datasets",
            endpoint=None,
            replace=True,
            only_newer=True,
        )
        print(lr_meta)

    # 4) Optional: Kopie nach dumps
    if not args.no_dumps:
        files = []
        if ttl_path.exists() and not args.meta_only:
            files.append(ttl_path)
            if gz_path:
                files.append(gz_path)
        files.extend([meta_ttl, meta_gz])
        copied = copy_to_dumps(SLUG, files)
        for c in copied:
            print(f"copied → {c}")


if __name__ == "__main__":
    main()
