#Maral Dadvar
#09/01/2019
#This script filters the names with initialls.



import unicodedata
import os , glob
import rdflib
from rdflib import Namespace, URIRef, Graph , Literal , OWL, RDFS , RDF
from SPARQLWrapper import SPARQLWrapper2, XML  , JSON , TURTLE
import re
import pprint

os.chdir('C:\\Users\\Maral\\Desktop')

graphout = Graph()

foaf = Namespace("http://xmlns.com/foaf/0.1/")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
jl = Namespace("http://data.judaicalink.org/ontology/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
dc = Namespace ("http://purl.org/dc/elements/1.1/")
edm = Namespace("http://www.europeana.eu/schemas/edm/")

graphout.bind('jl', jl)
graphout.bind('rdfs',RDFS)
graphout.bind('foaf',foaf)
graphout.bind('skos',skos)
graphout.bind('owl',OWL)
graphout.bind('gndo',gndo)
graphout.bind('dc',dc)
graphout.bind('edm',edm)


graph = Graph()
graph.parse('C:\\Users\\Maral\\Desktop\\cm-authors-context-GND-uni-02.rdf', format="turtle")



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

        SELECT ?x ?label ?id ?desc ?title ?gnd

        where {

          ?x a edm:ProvidedCHO.
          ?x dc:creator ?label.
          ?x dc:identifier ?id.
          ?x dc:description ?desc.
          ?x dc:title ?title.
          ?x gndo:gndIdentifier ?gnd.

        }

    """

result = graph.query(spar1)

for item in result:

        labels = item[1].value
        print (labels)

        if re.search(r'\w{1}\.\s*\w{1}\.',labels):
            print ('not valid')
        elif re.search(r'\w{1}\.',labels):
            print ('not valid')
        else:

            graphout.add((URIRef(item[0]), RDF.type , edm.ProvidedCHO ))
            graphout.add( (URIRef(item[0]), dc.creator , Literal(item[1].value) ) )
            graphout.add( (URIRef(item[0]), dc.identifier , Literal(item[2].value) ) )
            graphout.add( (URIRef(item[0]), gndo.gndIdentifier , URIRef(item[5]) ) )
            graphout.add ((URIRef(item[0]) , dc.description , Literal((item[3].value))))
            graphout.add ((URIRef(item[0]) , dc.title , Literal((item[4]))))


graphout.serialize(destination = 'cm-uni-names-filtered.ttl' , format="turtle")





