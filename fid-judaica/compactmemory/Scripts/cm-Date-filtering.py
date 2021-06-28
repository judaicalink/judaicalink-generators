# Maral Dadvar
# This code checks the publication date of compact memory and filters accordingly. It will also filter based on the occupation of the authors from GND. This is to deal with authors with multi GND-ids.
#28.08.2018


import rdflib
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON , TURTLE
from rdflib.namespace import RDF, FOAF , SKOS ,RDFS
import os

os.chdir('C:\Users\Maral\Desktop')


#output = open('date.csv','w')

#output.writelines([str('GNDID'),',',str('Name'),'\n'])



sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")


foaf = Namespace("http://xmlns.com/foaf/0.1/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
dc = Namespace("http://purl.org/dc/elements/1.1/")
edm = Namespace("http://www.europeana.eu/schemas/edm/")

g = Graph()

g.bind('gndo',gndo)
g.bind('dc',dc)
g.bind('edm',edm)



sparql.setQuery("""
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
    PREFIX bibtex: <http://data.bibbase.org/ontology/#>
    PREFIX pro: <http://purl.org/spar/pro/>




Select   distinct ?x ?label ?gnd ?date ?db ?title ?id
{
    GRAPH <http://maral.wisslab.org/graphs/ubcompact-multi> {

    ?x a edm:ProvidedCHO.
    ?x gndo:gndIdentifier ?gnd.
    ?x dc:creator ?label.
    ?x dc:description ?date.
    ?x dc:title ?title.
    ?x dc:identifier ?id.
   }

 GRAPH <http://maral.wisslab.org/graphs/gnd> {
    ?gnd a gndo:DifferentiatedPerson.
    ?gnd gndo:preferredNameForThePerson ?label.
  	?gnd gndo:dateOfBirth ?db.
    ?gnd gndo:professionOrOccupation ?occ.

    Filter(?occ = <http://d-nb.info/gnd/4176751-2> || ?occ =  <http://d-nb.info/gnd/4059756-8> || ?occ =  <http://d-nb.info/gnd/4415844-0> || ?occ =  <http://d-nb.info/gnd/4525103-4> || ?occ =  <http://d-nb.info/gnd/4053309-8>	|| ?occ =  <http://d-nb.info/gnd/4025098-2> || ?occ = 	<http://d-nb.info/gnd/4061414-1>)
    #Rabbiner, Theologe, Orientalist, Hebraist, Schriftsteller, Historiker, translator

  }
}


""")

sparql.setReturnFormat(XML)

results = sparql.query().convert()

if (u"x",u"label",u"date",u"gnd",u"db",u"title",u"id") in results:
    bindings = results[u"x",u"label",u"date",u"gnd",u"db",u"title",u"id"]
    for b in bindings:
         print b
         label = b[u"label"].value
         if len(b[u"db"].value) > 4:
            db = (b[u"db"].value).rsplit('-',2)[0]
         else:
            db = b[u"db"].value

         #if (b[u"date"].value).isdigit() :
          #   if b[u"date"].value > db :

           #         print b[u"date"].value , db

         g.add((URIRef(b[u"x"].value), RDF.type , edm.ProvidedCHO ))
         g.add( (URIRef(b[u"x"].value), dc.creator , Literal(label) ) )
         g.add( (URIRef(b[u"x"].value), gndo.gndIdentifier , URIRef(b[u"gnd"].value) ) )
         g.add( (URIRef(b[u"x"].value), dc.description , Literal(b[u"date"].value) ) )
         g.add( (URIRef(b[u"x"].value), dc.identifier , Literal(b[u"id"].value) ) )
         g.add( (URIRef(b[u"x"].value), dc.title , Literal(b[u"title"].value) ) )




g.serialize(destination = 'cm-authors-context-GND-multi-02-filtered.ttl' , format="turtle")
