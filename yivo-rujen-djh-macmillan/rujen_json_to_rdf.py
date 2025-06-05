import json
from urllib.parse import unquote
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, SKOS, DCTERMS, FOAF

JL = Namespace("http://data.judaicalink.org/ontology/")

SCHEME_URI = URIRef("http://data.judaicalink.org/data/rujen")
SOURCE_URI = URIRef("http://www.rujen.ru/")

latin_substitution = [
    "a", "b", "v", "g", "d", "e", "zh", "z", "i", "y",
    "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
    "f", "kh", "ts", "ch", "sh", "shch", "j", "y", "j", "e",
    "yu", "ya", "e", "e",
]
UTF8_BEGIN = 1072


def transliterate(text: str) -> str:
    result = ""
    for ch in text.lower():
        code = ord(ch) - UTF8_BEGIN
        if 0 <= code < len(latin_substitution):
            result += latin_substitution[code]
        else:
            result += ch
    return result


def local(uri: str) -> URIRef:
    replaced = unquote(uri).replace(
        "http://rujen.ru/index.php/",
        "http://data.judaicalink.org/data/rujen/",
    )
    return URIRef(transliterate(replaced))


def create_graph(records: list) -> Graph:
    g = Graph()
    g.bind("skos", SKOS)
    g.bind("dcterms", DCTERMS)
    g.bind("foaf", FOAF)
    g.bind("rdfs", RDFS)
    g.bind("jl", JL)

    g.add((SCHEME_URI, RDF.type, SKOS.ConceptScheme))
    g.add((SCHEME_URI, RDFS.label, Literal("Russian Jewish Encyclopedia", lang="en")))
    g.add((SCHEME_URI, DCTERMS.source, SOURCE_URI))

    for record in records:
        uri = local(record["uri"])
        g.add((uri, RDF.type, SKOS.Concept))
        g.add((uri, SKOS.prefLabel, Literal(record.get("title"))))
        g.add((uri, JL.describedAt, URIRef(record["uri"])))
        g.add((uri, SKOS.inScheme, SCHEME_URI))
        g.add((uri, DCTERMS.identifier, Literal(unquote(record["uri"].split("index.php/")[-1]))))

        for l in record.get("links", []) or []:
            target = local(l["href"])
            g.add((uri, SKOS.related, target))
            if l.get("text"):
                g.add((target, SKOS.altLabel, Literal(l["text"])))

        for cat in record.get("categories", []) or []:
            if cat == "\u041f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u0438\u0438":
                g.add((uri, JL.hasCategory, URIRef("http://data.judaicalink.org/data/rujen/person")))
            elif cat == "\u0413\u0435\u043e\u0433\u0440\u0430\u0444\u0438\u044f":
                g.add((uri, JL.hasCategory, URIRef("http://data.judaicalink.org/data/rujen/geography")))

        if record.get("abstract"):
            g.add((uri, JL.hasAbstract, Literal(record["abstract"], lang="ru")))

        if record.get("empty"):
            g.add(
                (uri, SKOS.scopeNote, Literal(
                    "The article describing this concept does not (yet) exist in the encyclopedia.",
                    lang="en",
                ))
            )

    return g


def main(input_path: str = "rujen.json", output_path: str = "rujen.ttl") -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    graph = create_graph(records)
    graph.serialize(destination=output_path, format="turtle")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert RUJEN JSON to RDF")
    parser.add_argument("input", nargs="?", default="rujen.json", help="Input JSON file")
    parser.add_argument("output", nargs="?", default="rujen.ttl", help="Output Turtle file")
    args = parser.parse_args()
    main(args.input, args.output)
