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

os.chdir('C:\Users\Maral\Desktop\generated_persons')

sparql = SPARQLWrapper2("http://dbpedia.org/sparql")

path = 'C:\Users\Maral\Desktop' #adapted to the list file path

graph = Graph()

foaf = Namespace("http://xmlns.com/foaf/0.1/")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
jl = Namespace("http://data.judaicalink.org/ontology/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
dct = Namespace("http://purl.org/dc/terms/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")

def generator_person (URI ,OccURI):

    "This function generates a rdf file of the person based on their occupation."

    print URI
    print OccURI
    newURI = '<'+URI+'>'
    print newURI

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
    PREFIX dct: <http://purl.org/dc/terms/>
    PREFIX dbpedia: <http://dbpedia.org/resource/>

    SELECT  ?x ?name ?lan ?same

    where {{

      ?x dct:subject {0}.
      ?x rdfs:label ?name.
      bind(lang(?name) as ?lan).
      ?x owl:sameAs ?same.

    }}


    """.format(newURI)

    sparql.setQuery(spar)
    sparql.setReturnFormat(TURTLE)
    results = sparql.query().convert()

    graph.bind('jl', jl)
    graph.bind('owl',OWL)
    graph.bind('rdfs',RDFS)
    graph.bind('foaf',foaf)
    graph.bind('dct',dct)
    graph.bind('skos',skos)


    if (u"x",u"name",u"lan",u"same") in results:

        bindings = results[u"x",u"name",u"lan","same"]

        for b in bindings:

            print b

            jlURI = b[u"x"].value.lower()


            if 'list' not in jlURI: #to eliminate irrelevant lists extracted from dbpedia

                jlend = b[u"x"].value.rsplit('/',1)[1]
                jlid = 'http://data.judaicalink.org/data/dbpedia/' + jlend #change to Judaicalink URI


                graph.add( (URIRef(jlid), RDF.type , foaf.Person ) )
                graph.add( (URIRef(jlid), OWL.sameAs , URIRef(b[u"x"].value) ) )
                graph.add( (URIRef(jlid), jl.occupation , URIRef(OccURI) ) )
                graph.add( (URIRef(jlid), skos.prefLabel, Literal(b[u"name"].value, lang = b[u"lan"].value) ) )
                graph.add( (URIRef(jlid), OWL.sameAs , URIRef(b[u"same"].value) ) )
                graph.add( (URIRef(jlid), dct.subject , URIRef(URI) ) )

    return

g = Graph()
g.parse('C:\Users\Maral\Desktop\generated_persons\occ_ontology.rdf', format="turtle")


spar= """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX pro: <http://purl.org/hpi/patchr#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dbpedia: <http://dbpedia.org/resource/>


    SELECT ?y ?subject ?oc

    where {

      ?y a jl:Occupation.
      ?y jl:hasLabel ?oc.
      ?y jl:relatedSubject ?subject

      }

"""

result = g.query(spar)

for item in result:

   print item

   URI = str(item[1])
   print URI
   OccURI = str(item[0])
   print OccURI

   generator_person(URI , OccURI)


graph.serialize(destination= 'generated_person_dbpedia.ttl' , format="turtle")

