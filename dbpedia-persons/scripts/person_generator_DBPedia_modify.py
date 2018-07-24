#Maral Dadvar
#21/04/2017
#This scrips reads a list of occupation URIs extracted from DBPedia and extracts the Persons label and sameAs links from each URI.
#The occpuation ontology rdf file is used for the occupation URI's.

import unicodedata
import os , glob
import rdflib
from rdflib import Namespace, URIRef, Graph , Literal , OWL, RDFS , RDF
from SPARQLWrapper import SPARQLWrapper2, XML  , JSON , TURTLE
import re
import pprint

os.chdir('C:\Users\Maral\Desktop')

path = 'C:\Users\Maral\Desktop' #adapted to the list file path

graph = Graph()

foaf = Namespace("http://xmlns.com/foaf/0.1/")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
jl = Namespace("http://data.judaicalink.org/ontology/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
dct = Namespace("http://purl.org/dc/terms/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")

graph.bind('jl', jl)
graph.bind('owl',OWL)
graph.bind('rdfs',RDFS)
graph.bind('foaf',foaf)
graph.bind('dct',dct)
graph.bind('skos',skos)



g = Graph()
g.parse('C:\Users\Maral\Desktop\generated_person_dbpedia.ttl', format="turtle")


spar= """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX pro: <http://purl.org/hpi/patchr#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dbpedia: <http://dbpedia.org/resource/>

    SELECT ?y ?sub ?same ?name ?occ ?lan
    where {
      ?y a foaf:Person.
      ?y dct:subject ?sub.
      ?y owl:sameAs ?same.
      ?y skos:prefLabel ?name.
      bind(lang(?name) as ?lan).
      #BIND(str(?name) As ?strippedlabel).
      ?y jl:occupation ?occ

      }
"""


result = g.query(spar)

for item in result:

   print item

   URI = item[0]
   #print URI
   subject = item[1]
   same = item[2]
   name = item[3]
   vname = name.value
   occ = item[4]
   lan = item[5]

   graph.add( (URIRef(URI), RDF.type , foaf.Person ) )
   graph.add( (URIRef(URI), dct.subject , URIRef(subject) ) )
   graph.add( (URIRef(URI), jl.occupation , URIRef(occ) ) )
   graph.add( (URIRef(URI), OWL.sameAs , URIRef(same) ) )
   graph.add( (URIRef(URI), skos.altLabel, Literal(name) ) )

   print lan
   if lan.value == 'en' :
    if '(' in vname:
         vname= re.sub("[\(\[].*?[\)\]]", "", vname)

    if ' ' in vname:

        fname = vname.rsplit(' ',1)[1]
        lname = vname.rsplit(' ',1)[0]

        if fname == '':

            prefname = lname

        elif lname == '':

            prefname = fname
        else:

            prefname = fname + ', ' + lname
    else:
        prefname = vname


    graph.add( (URIRef(URI), skos.prefLabel, Literal(prefname)))



graph.serialize(destination= 'generated_person_dbpedia_modified.ttl' , format="turtle")