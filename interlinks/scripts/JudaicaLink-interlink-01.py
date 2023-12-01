# Maral Dadvar
# 02/10/2017
# This scripts look sfor sameAs lines between bhr and JudaicaLink

from SPARQLWrapper import SPARQLWrapper2, TURTLE
from rdflib import Namespace, URIRef, Graph

sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")

foaf = Namespace("http://xmlns.com/foaf/0.1/")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
jl = Namespace("http://data.judaicalink.org/ontology/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
owl = Namespace("http://www.w3.org/2002/07/owl#")

g = Graph()

g.bind('foaf', foaf)
g.bind('jl', jl)
g.bind('skos', skos)
g.bind('owl', owl)

spar1 = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX gndo: <http://d-nb.info/standards/elementset/gnd#>
    PREFIX pro: <http://purl.org/hpi/patchr#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX edm: <http://www.europeana.eu/schemas/edm/>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dblp: <http://dblp.org/rdf/schema-2015-01-26#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dbpedia: <http://dbpedia.org/resource/>
    PREFIX jl: <http://data.judaicalink.org/ontology/>
    PREFIX gnd: <http://d-nb.info/gnd/>


Select ?x ?sameas
From <https://data.judaicalink.org/data/yivo>
From <https://data.judaicalink.org/data/bhr>
From <https://data.judaicalink.org/data/rujen>
From <https://data.judaicalink.org/data/djh>
From <https://data.judaicalink.org/data/gnd_persons>


where{

    ?x a foaf:Person.
    ?x owl:sameAs ?sameas.

        }



    """

sparql.setQuery(spar1)
sparql.setReturnFormat(TURTLE)
results = sparql.query().convert()

if (u"x", u"sameas") in results:
    bindings = results[u"x", u"sameas"]
    for b in bindings:
        print(b)
        if 'http://data.judaicalink.org/data/bhr' in b[u"sameas"].value:
            g.add((URIRef(b[u"x"].value), owl.sameAs, URIRef(b[u"sameas"].value)))

        if 'http://data.judaicalink.org/data/yivo' in b[u"sameas"].value:
            g.add((URIRef(b[u"x"].value), owl.sameAs, URIRef(b[u"sameas"].value)))

        if 'http://data.judaicalink.org/data/djh' in b[u"sameas"].value:
            g.add((URIRef(b[u"x"].value), owl.sameAs, URIRef(b[u"sameas"].value)))

        if 'http://data.judaicalink.org/data/rujen' in b[u"sameas"].value:
            g.add((URIRef(b[u"x"].value), owl.sameAs, URIRef(b[u"sameas"].value)))

        if 'http://data.judaicalink.org/data/gnd' in b[u"sameas"].value:
            g.add((URIRef(b[u"x"].value), owl.sameAs, URIRef(b[u"sameas"].value)))

        if 'http://data.judaicalink.org/data/dbpedia' in b[u"sameas"].value:
            g.add((URIRef(b[u"x"].value), owl.sameAs, URIRef(b[u"sameas"].value)))

spar2 = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX gndo: <http://d-nb.info/standards/elementset/gnd#>
    PREFIX pro: <http://purl.org/hpi/patchr#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX edm: <http://www.europeana.eu/schemas/edm/>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dblp: <http://dblp.org/rdf/schema-2015-01-26#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dbpedia: <http://dbpedia.org/resource/>
    PREFIX jl: <http://data.judaicalink.org/ontology/>
    PREFIX gnd: <http://d-nb.info/gnd/>


Select ?x ?sameas
where{

graph <https://data.judaicalink.org/data/dbpedia_persons> {
    ?x a foaf:Person.
    ?x owl:sameAs ?sameas.

        }}



    """

sparql.setQuery(spar2)
sparql.setReturnFormat(TURTLE)
results = sparql.query().convert()

if (u"x", u"sameas") in results:
    bindings = results[u"x", u"sameas"]
    for b in bindings:
        print(b)
        if 'http://data.judaicalink.org/data/bhr' in b[u"sameas"].value:
            g.add((URIRef(b[u"x"].value), owl.sameAs, URIRef(b[u"sameas"].value)))

        if 'http://data.judaicalink.org/data/yivo' in b[u"sameas"].value:
            g.add((URIRef(b[u"x"].value), owl.sameAs, URIRef(b[u"sameas"].value)))

        if 'http://data.judaicalink.org/data/djh' in b[u"sameas"].value:
            g.add((URIRef(b[u"x"].value), owl.sameAs, URIRef(b[u"sameas"].value)))

        if 'http://data.judaicalink.org/data/rujen' in b[u"sameas"].value:
            g.add((URIRef(b[u"x"].value), owl.sameAs, URIRef(b[u"sameas"].value)))

        if 'http://data.judaicalink.org/data/gnd' in b[u"sameas"].value:
            g.add((URIRef(b[u"x"].value), owl.sameAs, URIRef(b[u"sameas"].value)))

g.serialize(destination='interlinks-02.ttl', format="turtle")
