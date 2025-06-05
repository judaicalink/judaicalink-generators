import json
from pathlib import Path
from urllib.parse import unquote
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, SKOS, DCTERMS, FOAF

JL = Namespace("http://data.judaicalink.org/ontology/")

SCHEME_URI = URIRef("http://data.judaicalink.org/data/yivo")
SOURCE_URI = URIRef("http://www.yivoencyclopedia.org/")


def local(uri: str) -> URIRef:
    return URIRef(uri.replace(
        "http://www.yivoencyclopedia.org/article.aspx/",
        "http://data.judaicalink.org/data/yivo/",
    ))


def create_graph(records: list) -> Graph:
    g = Graph()
    g.bind("skos", SKOS)
    g.bind("dcterms", DCTERMS)
    g.bind("foaf", FOAF)
    g.bind("rdfs", RDFS)
    g.bind("jl", JL)

    g.add((SCHEME_URI, RDF.type, SKOS.ConceptScheme))
    g.add((SCHEME_URI, RDFS.label, Literal("YIVO Encyclopedia", lang="en")))
    g.add((SCHEME_URI, DCTERMS.source, SOURCE_URI))

    for record in records:
        uri = local(record["uri"])
        g.add((uri, RDF.type, SKOS.Concept))
        g.add((uri, SKOS.prefLabel, Literal(record.get("title"))))
        g.add((uri, JL.describedAt, URIRef(record["uri"])))
        g.add((uri, SKOS.inScheme, SCHEME_URI))

        for l in record.get("links", []):
            target = local(l["href"])
            g.add((uri, SKOS.related, target))
            if l.get("text"):
                g.add((target, SKOS.altLabel, Literal(l["text"])))

        if record.get("abstract"):
            g.add((uri, JL.hasAbstract, Literal(record["abstract"], lang="en")))

        for sc in record.get("subconcepts", []):
            sub_uri = URIRef(f"{uri}/{sc.replace(' ', '_')}")
            g.add((sub_uri, RDF.type, SKOS.Concept))
            g.add((sub_uri, SKOS.prefLabel, Literal(sc)))
            g.add((sub_uri, SKOS.broader, uri))
            g.add((sub_uri, SKOS.inScheme, SCHEME_URI))
            g.add((uri, SKOS.narrower, sub_uri))

        for sr in record.get("subrecords", []):
            g.add((uri, SKOS.narrower, local(sr["href"])))

        if record.get("broader"):
            g.add((uri, SKOS.broader, local(record["broader"])))

    return g


def main(input_path: str = "output.json", output_path: str = "output.ttl") -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    graph = create_graph(records)
    graph.serialize(destination=output_path, format="turtle")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert YIVO JSON to RDF")
    parser.add_argument("input", nargs="?", default="output.json", help="Input JSON file")
    parser.add_argument("output", nargs="?", default="output.ttl", help="Output Turtle file")
    args = parser.parse_args()
    main(args.input, args.output)
