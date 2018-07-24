#Maral Dadvar
#02/10/2017
#This scripts look sfor sameAs lines between bhr and JudaicaLink

import unicodedata
import os , glob
import rdflib
from rdflib import Namespace, URIRef, Graph , Literal , OWL, RDFS , RDF
from SPARQLWrapper import SPARQLWrapper2, XML  , JSON , TURTLE
import re
import pprint

os.chdir('C:\Users\Maral\Desktop')

sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")


foaf = Namespace("http://xmlns.com/foaf/0.1/")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
jl = Namespace("http://data.judaicalink.org/ontology/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
owl = Namespace("http://www.w3.org/2002/07/owl#")

g = Graph()
g.parse('C:\Users\Maral\Desktop\interlinks-03.ttl', format="turtle")


g.bind('foaf',foaf)
g.bind('jl',jl)
g.bind('skos',skos)
g.bind('owl',owl)

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
    PREFIX jl: <http://data.judaicalink.org/ontology/>
    PREFIX gnd: <http://d-nb.info/gnd/>


Select ?x ?sameas

where{

    ?x owl:sameAs ?sameas.

        }



    """
results = g.query(spar1)

for item in results:


    g.add( (URIRef(item[1]), owl.sameAs , URIRef(item[0]) ) )


g.serialize(destination = 'interlinks-04.ttl' , format="turtle")




