# Maral Dadvar
# This code integrates the two bhr generated files, the old one and the new one.
# the integration is done in several stages, first by checking the sameAs links which are similar, both for those with and without publications, and then for those with similar names.
# 30/04/2018
# Ver. 01

from rdflib import Namespace, URIRef, Graph, Literal
from rdflib.namespace import RDF

# sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")

foaf = Namespace("http://xmlns.com/foaf/0.1/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
jl = Namespace("http://data.judaicalink.org/ontology/")
owl = Namespace("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace("http://purl.org/dc/elements/1.1/")

graph = Graph()

graph.parse('../output/bhr-new-enrich.rdf', format="turtle")

spar = """
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


        SELECT ?x ?desc ?abs ?same ?name #?publication

        where {


          ?x a foaf:Person.
          ?x jl:describedAt ?desc.
          ?x jl:hasAbstract ?abs.
          ?x owl:sameAs ?same.
          ?x skos:prefLabel ?name.
          #?x  jl:hasPublication ?publication

           }

    """

results = graph.query(spar)

for item in results:
    same = item[3]
    # print same

graph2 = Graph()

# graph2.parse('../output/EncycBHR-ID-GND-JL.ttl', format="turtle")
graph2.parse('../output/bhr-final.ttl', format="turtle")

graph2.bind('foaf', foaf)
graph2.bind('skos', skos)
graph2.bind('owl', owl)
graph2.bind('jl', jl)

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

        SELECT ?x ?same

        where {

          ?x a foaf:Person.
          ?x owl:sameAs ?same.


           }

    """

results2 = graph2.query(spar2)

for item in results:
    # uri = item[0]
    desc = item[1].value
    print(desc)
    abs = item[2].value
    same = item[3]
    # pub = item[5].value
    name = item[4].value

    for item2 in results2:
        uri = item2[0]
        same2 = item2[1]

        if same == same2:
            graph2.add((URIRef(uri), RDF.type, foaf.Person))
            graph2.add((URIRef(uri), jl.describedAt, Literal(desc)))
            graph2.add((URIRef(uri), jl.hasAbstract, Literal(abs)))
            # graph2.add((URIRef(uri) , jl.hasPublication , Literal(pub)))
            graph2.add((URIRef(uri), owl.sameAs, URIRef(same)))

# graph2.serialize(destination='bhr-final.ttl', format="turtle")
graph2.serialize(destination='bhr-final-02.ttl', format="turtle")
