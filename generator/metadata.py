# -*- coding: utf-8 -*-
"""
Utilities to generate RDF metadata graphs for JudaicaLink datasets.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from urllib.parse import urlencode
from rdflib import Graph, Namespace, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, DCTERMS

# Namespaces
VOID = Namespace("http://rdfs.org/ns/void#")
PROV = Namespace("http://www.w3.org/ns/prov#")
CC = Namespace("http://creativecommons.org/ns#")
JLO = Namespace("http://data.judaicalink.org/ontology/")
JL_DS = Namespace("http://data.judaicalink.org/datasets/")


def build_metadata_graph(metadata: dict, scriptinfo: Optional[dict] = None) -> Graph:
    """
    Builds a RDF graph with the metadata of a JudaicaLink dataset.

    Expects:
    metadata = {
        "slug": "gidal",
        "title": "Gidal Image Archive",
        "license": {
            "uri": "https://creativecommons.org/licenses/by-sa/4.0/",
            "name": "CC-BY-SA 4.0"
        },
        "generator": {
            "gitweb": "https://github.com/judaicalink/judaicalink-generators/tree/main/datasets/gidal",
            "commit": "abc1234",
            "script": "datasets/gidal/scripts/build.py"
        }
    }
    :param metadata: Metadata dictionary.
    :param scriptinfo: Optional script information dictionary.
    :return: RDF Graph with the metadata.
    """

    g = Graph()
    g.bind("void", VOID)
    g.bind("dcterms", DCTERMS)
    g.bind("prov", PROV)
    g.bind("cc", CC)
    g.bind("rdfs", RDFS)
    g.bind("jlo", JLO)

    slug = metadata.get("slug")
    if not slug:
        raise ValueError("metadata['slug'] is required")

    subject = URIRef(f"{JL_DS}{slug}")
    creation_date = datetime.utcnow().isoformat()

    # primary structure
    g.add((subject, RDF.type, VOID.Dataset))
    g.add((subject, DCTERMS.date, Literal(creation_date)))
    g.add((subject, DCTERMS.subject, Literal(slug)))

    title = metadata.get("title")
    if title:
        g.add((subject, DCTERMS.title, Literal(title)))

    # Licence (URI + Name)
    license_info = urlencode(metadata.get("license")) or {}
    if isinstance(license_info, dict):
        if "uri" in license_info:
            g.add((subject, CC.license, URIRef(license_info["uri"])))
        if "name" in license_info:
            g.add((subject, DCTERMS.rights, Literal(license_info["name"])))

    # Provenance (Generator, Commit, Script)
    gen_info = metadata.get("generator") or {}
    if gen_info or scriptinfo:
        g.add((subject, RDF.type, PROV.Entity))
        activity = BNode()
        script = BNode()
        g.add((subject, PROV.wasGeneratedBy, activity))
        g.add((activity, PROV.used, script))

        # Priority: metadata["generator"] > scriptinfo
        src = {**(scriptinfo or {}), **gen_info}
        if "gitweb" in src:
            g.add((script, JLO.gitWeb, URIRef(src["gitweb"])))
        if "commit" in src:
            g.add((script, JLO.gitCommit, Literal(src["commit"])))
        if "script" in src:
            g.add((script, RDFS.label, Literal(src["script"])))

    return g


def write_metadata_graph(metadata: dict, out_path: Path, scriptinfo: Optional[dict] = None) -> Path:
    """
    Writes the metadata  graph to a .ttl file.
    Returns the path.
    :param metadata: Metadata dictionary.
    :param out_path: Output file path.
    :param scriptinfo: Optional script information dictionary.
    """
    g = build_metadata_graph(metadata, scriptinfo=scriptinfo)
    out_path.write_text(g.serialize(format="turtle"), encoding="utf-8")
    return out_path
