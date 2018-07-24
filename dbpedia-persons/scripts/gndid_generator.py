#Maral Dadvar
#23/03/2017
#This script reads the rdf file generated for person from dbpedia and generates the GNDid URI from Wikidata for the persons.

import unicodedata
import os , glob
import rdflib
from rdflib import Namespace, URIRef, Graph , Literal , OWL, RDFS , RDF
from SPARQLWrapper import SPARQLWrapper2, XML  , JSON , TURTLE
import re
import pprint

os.chdir('C:\Users\Maral\Desktop\output')

sparql = SPARQLWrapper2("https://query.wikidata.org/sparql")

graph = Graph()


foaf = Namespace("http://xmlns.com/foaf/0.1/")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
jl = Namespace("http://data.judaicalink.org/ontology/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")

wikilist=[]

def generator_gndid (URI):

    "this function extracts the gndid of the person from Wikidata"

    spar1= """
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
        PREFIX p: <http://www.wikidata.org/prop/>
        PREFIX ps: <http://www.wikidata.org/prop/statement/>

        SELECT ?id

        where {{

        {0} p:P227 ?gnd.
         ?gnd ps:P227 ?id

        }}


        """.format(URI)

    sparql.setQuery(spar1)
    sparql.setReturnFormat(TURTLE)
    results = sparql.query().convert()


    if (u"id") in results:
        bindings = results[u"id"]
        for b in bindings:
           return b[u"id"].value



g = Graph()
g.parse('C:\Users\Maral\Desktop\generated_person\generated_person.rdf', format="turtle")

#this query will extract only the sameAs links to Wikidata

spar= """
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

      ?x owl:sameAs ?same.
      FILTER ( strstarts(str(?same), "http://www.wikidata.org/entity/")). }

"""

results = g.query(spar)

graph.bind('gndo',gndo)
graph.bind('foaf',foaf)

for item in results:


   URI = '<'+ str(item[1]) + '>' #turn it into query adaptable URI format

   wikilist.append(URI)

   gnd = generator_gndid(URI) #generate the GNDid


   if gnd != None: #if an id was found

        gndid = 'http://d-nb.info/gnd/' + gnd
        print gndid

        graph.add( (URIRef(item[0]), RDF.type , foaf.Person ) )
        graph.add( (URIRef(item[0]), gndo.gndIdentifier , URIRef(gndid) ) ) #add the GNDid to the graph



graph.serialize(destination = 'generated_gndid.rdf' , format="turtle")

