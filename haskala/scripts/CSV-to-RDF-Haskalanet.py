#this code creates rdf file from csv file
# 01/07/2019
# Maral Dadvar

import urllib.request as urllib2
from bs4 import BeautifulSoup
import rdflib
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON , TURTLE
from rdflib.namespace import RDF, FOAF , OWL
import os , glob
import csv
import re

os.chdir('C:\\Users\\Maral\\Desktop')

graph = Graph()
graphex = Graph()

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

graphex.bind('skos', skos)
graphex.bind ('foaf' , foaf)
graphex.bind ('jl' , jl)
graphex.bind('gndo',gndo)
graphex.bind ('owl' , owl)
graphex.bind('edm',edm)
graphex.bind('dc',dc)

data = csv.reader(open('C:\\Users\\Maral\\Desktop\\haskalanet_01.csv'))

for row in data:

    gnduri = row[0]
    gndid = gnduri.rsplit('/',1)[1]
    name = row[1]
    fname = row[2]
    if ' ' in fname:
        fname = fname.replace(' ','')
    lname = row[3]
    same = row[4]
    occ = row[6]
    db = row[7]
    dd = row[8]
    pb = row[9]
    pd = row[10]


    uri = 'http://data.judaicalink.org/data/haskala/' + fname + '_' + lname
    graph.add((URIRef(uri), RDF.type, foaf.Person ))
    graph.add((URIRef(uri), skos.prefLabel,(Literal(name)) ))
    graph.add((URIRef(uri), gndo.gndIdentifier,(Literal(gndid)) ))
    graph.add((URIRef(uri), owl.sameAs ,(URIRef(gnduri)) ))
    graph.add((URIRef(uri), owl.sameAs ,(URIRef(same)) ))
    graph.add((URIRef(uri), jl.birthDate,(Literal(db)) ))
    graph.add((URIRef(uri), jl.birthLocation,(Literal(pb)) ))
    graph.add((URIRef(uri), jl.deathDate,(Literal(dd)) ))
    graph.add((URIRef(uri), jl.deathLocation,(Literal(pd)) ))
    graph.add((URIRef(uri), jl.Occupation,(Literal(occ)) ))


graph.serialize(destination='Haskala_net.ttl', format="turtle")


