# this code extarctes the sameAs links from the entityfacts pages.


# import urllib2
import urllib.request as urllib2
from bs4 import BeautifulSoup
import rdflib
from rdflib import Namespace, URIRef, Graph, Literal
from SPARQLWrapper import SPARQLWrapper2, XML, RDF, JSON, TURTLE
from rdflib.namespace import RDF, FOAF, OWL
import os, glob
import csv
import re
import time

sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")

graph = Graph()

foaf = Namespace("http://xmlns.com/foaf/0.1/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
jl = Namespace("http://data.judaicalink.org/ontology/")
owl = Namespace("http://www.w3.org/2002/07/owl#")

graph.bind('skos', skos)
graph.bind('foaf', foaf)
graph.bind('jl', jl)
graph.bind('gndo', gndo)
graph.bind('owl', owl)

sparql.setQuery("""
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
    PREFIX bibtex: <http://data.bibbase.org/ontology/#>
    PREFIX jl: <http://data.judaicalink.org/ontology/>

select ?o ?gnd

#from <https://data.judaicalink.org/data/freimann-gnd>
from <https://data.judaicalink.org/data/ub-gnd>
#from <https://data.judaicalink.org/data/gnd-persons>
#from <https://data.judaicalink.org/data/bhr>


where
{
    ?o a foaf:Person.
    ?o gndo:gndIdentifier ?gnd

}

""")

sparql.setReturnFormat(XML)

results = sparql.query().convert()

for i in range(0, len(results.bindings)):

    gnd = results.bindings[i]['gnd'].value
    URI = results.bindings[i]['o'].value

    sameURI = 'http://hub.culturegraph.org/entityfacts/' + str(gnd)
    print(sameURI)
    try:
        page = urllib2.urlopen(sameURI)
        soup = BeautifulSoup(page)

        lines = []

        for line in soup.contents[0].splitlines():
            print(line)
            lines.append(line)

        print(lines)

        for i in range(0, len(lines)):
            if 'sameAs' in lines[i]:
                for j in range(i + 1, len(lines)):
                    if '@id' in lines[j]:
                        same = lines[j].rsplit('"', 2)[1]
                        graph.add((URIRef(URI), RDF.type, foaf.Person))
                        graph.add((URIRef(URI), owl.sameAs, (URIRef(same))))
                        graph.add((URIRef(URI), owl.sameAs, (URIRef(sameURI))))
                        print(same)
                break;
    except:
        continue;

# graph.serialize(destination='Entityfacts-freimann-sameas.ttl', format="turtle")
# graph.serialize(destination='Entityfacts-gnd-sameas.ttl', format="turtle")
graph.serialize(destination='Entityfacts-ubgnd-sameas.ttl', format="turtle")
# graph.serialize(destination='Entityfacts-bhr-sameas.ttl', format="turtle")
