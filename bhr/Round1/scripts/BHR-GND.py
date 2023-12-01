# Maral Dadvar
# 13/06/2017
# This script matches the BHR information of Encyc.rdf file with the Encyc ID information from another file to create one final version.

# -*- coding: utf-8 -*-

from rdflib import Namespace, URIRef, Graph, Literal

foaf = Namespace("http://xmlns.com/foaf/0.1/")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
jl = Namespace("http://data.judaicalink.org/ontology/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")

g = Graph()
g.parse('../output/Encyc.rdf', format="turtle")

g2 = Graph()
g2.parse('../output/EncycBHR-ID.rdf', format="turtle")

g.bind('gndo', gndo)
g.bind('foaf', foaf)
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

SELECT ?x

WHERE{

    ?x a foaf:Person

 }


    """

resultencyc = g.query(spar1)

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

SELECT ?x ?gnd ?sameas

WHERE{

    ?x a foaf:Person.
    ?x gndo:gndIdentifier ?gnd.
    ?x owl:sameAs ?sameas

 }


    """

resultID = g2.query(spar2)

for itemencyc in resultencyc:

    for itemid in resultID:

        if itemencyc[0].encode('utf-8') == itemid[0].encode('utf-8'):

            g.add((URIRef(itemencyc[0].encode('utf-8')), owl.sameAs, (URIRef(itemid[2]))))

            if 'NA' in itemid[1]:

                gnd = 'NA'
                g.add((URIRef(itemencyc[0].encode('utf-8')), gndo.gndIdentifier, (Literal(gnd))))

            elif itemid[1].rsplit('/', 1)[1] == '-':

                gnd = 'NA'
                g.add((URIRef(itemencyc[0].encode('utf-8')), gndo.gndIdentifier, (Literal(gnd))))

            else:

                gnd = itemid[1].rsplit('/', 1)[1]
                g.add((URIRef(itemencyc[0].encode('utf-8')), gndo.gndIdentifier, (Literal(gnd))))
                g.add((URIRef(itemencyc[0].encode('utf-8')), owl.sameAs, (URIRef(itemid[1]))))

            print(gnd)

g.serialize(destination='EncycBHR-ID-GND.rdf', format="turtle")
