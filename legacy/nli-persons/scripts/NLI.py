import urllib.request as urllib2
from bs4 import BeautifulSoup
import rdflib
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON , TURTLE
from rdflib.namespace import RDF, FOAF , OWL
import json
import os
os.chdir('../input')
graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace ("http://purl.org/dc/elements/1.1/")
graph.bind('skos', skos)
graph.bind ('foaf' , foaf)
graph.bind ('jl' , jl)
graph.bind('gndo',gndo)
graph.bind ('owl' , owl)
graph.bind('edm',edm)
graph.bind('dc',dc)

print(graph)

