#Maral Dadvar
#09/01/2018
#This script enriches the common CM and GND authors files with GND-id. This is for those with only one GND-ID.



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
graphno=Graph()

gndname=[]

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

graphno.bind('jl', jl)
graphno.bind('rdfs',RDFS)
graphno.bind('foaf',foaf)
graphno.bind('skos',skos)
graphno.bind('owl',OWL)
graphno.bind('gndo',gndo)
graphno.bind('dc',dc)
graphno.bind('edm',edm)



graph = Graph()
graph.parse('C:\Users\Maral\Desktop\cm-gnd-multi.rdf', format="turtle")



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

for item in result:
    gndname.append((item[1].value.encode('utf-8'),item[0]))

print gndname



g = Graph()
g.parse('C:\Users\Maral\Desktop\compact-extracted-02.rdf', format="turtle")

spar= """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX gndo: <http://d-nb.info/standards/elementset/gnd#>
        PREFIX pro: <http://purl.org/spar/pro/#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX edm: <http://www.europeana.eu/schemas/edm/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dblp: <http://dblp.org/rdf/schema-2015-01-26#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX dbpedia: <http://dbpedia.org/resource/>

        SELECT ?x ?id ?author ?name ?desc ?title

        where {


          ?x a edm:ProvidedCHO.
          ?x dc:identifier ?id.
          ?x dc:description ?desc.
          ?x dc:title ?title.
          ?x <http://purl.org/spar/pro/author> ?author.
          ?author skos:prefLabel ?name

           }

    """

results = g.query(spar)


for ubitem in results: #names from UB Freimann


   name = ubitem[3].encode('utf-8') #name of the author

   for i in range(0,len(gndname)):

       if name == gndname[i][0]:

               print  item[1].value , name

               graphout.add((URIRef(ubitem[0]), RDF.type , edm.ProvidedCHO ))
               graphout.add( (URIRef(ubitem[0]), dc.creator , Literal(name) ) )
               graphout.add( (URIRef(ubitem[0]), dc.identifier , Literal(ubitem[1]) ) )
               graphout.add( (URIRef(ubitem[0]), gndo.gndIdentifier , URIRef(gndname[i][1]) ) )
               graphout.add ((URIRef(ubitem[0]) , dc.description , Literal((ubitem[4]))))
               graphout.add ((URIRef(ubitem[0]) , dc.title , Literal((ubitem[5]))))




graphout.serialize(destination = 'cm-authors-context-GND-multi-02.rdf' , format="turtle")




