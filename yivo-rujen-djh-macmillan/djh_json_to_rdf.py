import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, SKOS, DCTERMS, FOAF

JL = Namespace("http://data.judaicalink.org/ontology/")

SCHEME_URI = URIRef("http://data.judaicalink.org/data/djh")
SOURCE_URI = URIRef("http://dasjuedischehamburg.de/")


def local(uri: str) -> URIRef:
    return URIRef(uri.replace(
        "http://dasjuedischehamburg.de/inhalt/",
        "http://data.judaicalink.org/data/djh/",
    ))


def create_graph(records: list) -> Graph:
    g = Graph()
    g.bind("skos", SKOS)
    g.bind("dcterms", DCTERMS)
    g.bind("foaf", FOAF)
    g.bind("rdfs", RDFS)
    g.bind("jl", JL)

    g.add((SCHEME_URI, RDF.type, SKOS.ConceptScheme))
    g.add((SCHEME_URI, RDFS.label, Literal("Das J\u00fcdische Hamburg", lang="de")))
    g.add((SCHEME_URI, DCTERMS.source, SOURCE_URI))

    for record in records:
        uri = local(record["uri"])
        g.add((uri, RDF.type, SKOS.Concept))
        if record.get("isPerson"):
            g.add((uri, RDF.type, FOAF.Person))
            if record.get("occupation"):
                g.add((uri, JL.occupation, Literal(record["occupation"], lang="de")))
            if record.get("birthDate"):
                g.add((uri, JL.birthDate, Literal(record["birthDate"], lang="de")))
            if record.get("birthLocation"):
                g.add((uri, JL.birthLocation, Literal(record["birthLocation"], lang="de")))
            if record.get("deathDate"):
                g.add((uri, JL.deathDate, Literal(record["deathDate"], lang="de")))
            if record.get("deathLocation"):
                g.add((uri, JL.deathLocation, Literal(record["deathLocation"], lang="de")))
        g.add((uri, JL.describedAt, URIRef(record["uri"])))
        g.add((uri, SKOS.prefLabel, Literal(record.get("title"))))
        g.add((uri, SKOS.inScheme, SCHEME_URI))

        for l in record.get("links", []):
            target = local(l["href"])
            g.add((uri, SKOS.related, target))
            if l.get("text"):
                g.add((target, SKOS.altLabel, Literal(l["text"])))

        if record.get("abstract"):
            g.add((uri, JL.hasAbstract, Literal(record["abstract"], lang="de")))

    return g


def main(input_path: str = "djh.json", output_path: str = "djh.ttl") -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    graph = create_graph(records)
    graph.serialize(destination=output_path, format="turtle")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert DJH JSON to RDF")
    parser.add_argument("input", nargs="?", default="djh.json", help="Input JSON file")
    parser.add_argument("output", nargs="?", default="djh.ttl", help="Output Turtle file")
    args = parser.parse_args()
    main(args.input, args.output)
