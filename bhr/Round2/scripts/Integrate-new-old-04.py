# Maral Dadvar
#This code integrates the two bhr generated files, the old one and the new one.
#the sameAs links are integrated into the new file
#30/04/2018
#Ver. 01

import rdflib
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON
from rdflib.namespace import RDF, FOAF , SKOS ,RDFS
import os

os.chdir('C:\Users\Maral\Desktop')

#sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")

foaf = Namespace("http://xmlns.com/foaf/0.1/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
jl = Namespace("http://data.judaicalink.org/ontology/")
owl = Namespace ("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace ("http://purl.org/dc/elements/1.1/")

graph= Graph()

graph.parse('C:\\Users\\Maral\\Desktop\\bhr-new-enrich.rdf', format="turtle")


dicsame = {}


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


        SELECT ?x ?desc ?same

        where {


          ?x a foaf:Person.
          ?x jl:describedAt ?desc.
          ?x owl:sameAs ?same.


           }

    """

results = graph.query(spar)

graph2= Graph()

graph2.parse('C:\\Users\\Maral\\Desktop\\bhr-final-04.ttl', format="turtle")


graph2.bind('foaf',foaf)
graph2.bind('skos',skos)
graph2.bind('owl',owl)
graph2.bind('jl',jl)


spar2= """
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

        SELECT ?x ?desc

        where {

          ?x a foaf:Person.
          ?x jl:describedAt ?desc

           }

    """

results2 = graph2.query(spar2)


for item2 in results2:
        #print item2
        uri = item2[0]
        desc2 = item2[1].value

        for item in results:

            desc = item[1].value
            same = item[2]
            #print item
            if desc == desc2:

                graph2.add((URIRef(uri) , owl.sameAs , URIRef(same)))

graph2.serialize(destination='bhr-final-05.ttl', format="turtle")



