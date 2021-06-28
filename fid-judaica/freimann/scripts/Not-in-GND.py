# Maral Dadvar
#This code looks for authors who are in Freimann dataset but has no GND-ID in GND.
#06.02.2018

import rdflib
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON
from rdflib.namespace import RDF, FOAF , SKOS ,RDFS
import os

os.chdir('C:\Users\Maral\Desktop')

sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")

foaf = Namespace("http://xmlns.com/foaf/0.1/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace ("http://purl.org/dc/elements/1.1/")

graphout = Graph()

gndauthor = []
ubauthor=[]

sparql.setQuery("""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX gndo: <http://d-nb.info/standards/elementset/gnd#>
    PREFIX pro: <http://purl.org/spar/pro/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX edm: <http://www.europeana.eu/schemas/edm/>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dblp: <http://dblp.org/rdf/schema-2015-01-26#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX bibtex: <http://data.bibbase.org/ontology/#>


SELECT distinct ?Author
WHERE {

     GRAPH <http://maral.wisslab.org/graphs/gnd>
     {
       ?z a gndo:DifferentiatedPerson.
    ?z gndo:preferredNameForThePerson  ?Author.
  }
}

""")

sparql.setReturnFormat(XML)

results = sparql.query().convert()


if (u"Author") in results:


    bindings = results[u"Author"]

    for b in bindings:
       #print b
       gndauthor.append(b['Author'].value)


sparql.setQuery("""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX gndo: <http://d-nb.info/standards/elementset/gnd#>
    PREFIX pro: <http://purl.org/spar/pro/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX edm: <http://www.europeana.eu/schemas/edm/>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dblp: <http://dblp.org/rdf/schema-2015-01-26#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX bibtex: <http://data.bibbase.org/ontology/#>


SELECT distinct  ?RecordLink ?Author ?PersonLink
WHERE {
 GRAPH <http://maral.wisslab.org/graphs/ub>
 {

      ?y a edm:ProvidedCHO.
      ?y pro:author ?PersonLink.
      ?y dc:identifier ?RecordLink.
      ?PersonLink a foaf:Person.
      ?PersonLink skos:prefLabel ?Author.

 }
}

""")

sparql.setReturnFormat(XML)

results = sparql.query().convert()


graphout.bind('foaf',foaf)
graphout.bind('skos',skos)
graphout.bind('dc',dc)
graphout.bind('edm',edm)


if (u"RecordLink",u"Author",u"PersonLink") in results:


    bindings = results[u"RecordLink",u"Author",u"PersonLink"]

    for b in bindings:
       #print b
       rl = b['RecordLink'].value
       au = b['Author'].value
       pl = b['PersonLink'].value
       ubauthor.append((rl,au,pl))

for i in range (0,len(ubauthor)):

    if ubauthor[i][1] not in gndauthor:
        print ubauthor[i]
        graphout.add((URIRef(ubauthor[i][0]) , RDF.type , edm.WebResource))
        graphout.add((URIRef(ubauthor[i][0]) , skos.prefLabel , Literal(ubauthor[i][1])))
        graphout.add((URIRef(ubauthor[i][0]) , dc.Personidentifier , Literal(ubauthor[i][2])))



graphout.serialize(destination = 'Not-in-GND.ttl' , format="turtle")






