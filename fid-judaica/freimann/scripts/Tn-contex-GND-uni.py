#Maral Dadvar
#21/07/2017
#This script enriches the common UB and GND athors files with GND-id. This is for those with only one GND-ID.



import unicodedata
import os , glob
import rdflib
from rdflib import Namespace, URIRef, Graph , Literal , OWL, RDFS , RDF
from SPARQLWrapper import SPARQLWrapper2, XML  , JSON , TURTLE
import re
import pprint

os.chdir('C:\Users\Maral\Desktop')

path = 'C:\Users\Maral\Desktop' #adapted to the list file path

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
graph.parse('C:\Users\Maral\Desktop\Tn-gnd-uni.rdf', format="turtle")



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

        SELECT ?uri ?label

        where {

         ?uri a foaf:Person.
         ?uri skos:prefLabel ?label.


        }

    """

result = graph.query(spar1)




g = Graph()
g.parse('C:\Users\Maral\Desktop\Tn-authors.ttl', format="turtle")

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

        SELECT ?x ?name ?id

        where {

          ?x a edm:WebResource.
          ?x dc:creator ?name.
          ?x dc:Personidentifier ?id }

    """

results = g.query(spar)


for ubitem in results: #names from UB Freimann

   #print str(ubitem[0]) , str(ubitem[1]) , str(ubitem[2])


   name = ubitem[1].encode('utf-8') #name of the author
   print '.........',name
   graphout.add((URIRef(ubitem[0]), RDF.type , edm.WebResource ))
   graphout.add( (URIRef(ubitem[0]), dc.creator , Literal(name) ) )
   graphout.add( (URIRef(ubitem[0]), dc.Personidentifier , Literal(ubitem[2]) ) )


   for item in result: #names from GND generated persons

      #print item
      if item[1].encode('utf-8') == name:

           print  item[1] , name

           graphout.add((URIRef(ubitem[0]), RDF.type , edm.WebResource ))
           graphout.add( (URIRef(ubitem[0]), gndo.gndIdentifier , URIRef(item[0]) ) )


graphout.serialize(destination = 'Tn-authors-context-GND-uni.rdf' , format="turtle")






