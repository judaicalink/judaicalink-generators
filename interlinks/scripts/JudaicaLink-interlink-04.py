# Maral Dadvar
#This code extracts further information from GND for the authors of Freimann collection who have an GND-ID assigned to them.
#15/01/2018
#Ver. 01

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
jl = Namespace("http://data.judaicalink.org/ontology/")
owl = Namespace ("http://www.w3.org/2002/07/owl#")

graph = Graph()
#graph.parse('C:\Users\Maral\Desktop\interlinks-04.ttl', format="turtle")
#graph.parse('C:\Users\Maral\Desktop\interlinks-04-enriched-01.ttl', format="turtle")
#graph.parse('C:\Users\Maral\Desktop\interlinks-04-enriched-02.ttl', format="turtle")
#graph.parse('C:\Users\Maral\Desktop\interlinks-04-enriched-03.ttl', format="turtle")
#graph.parse('C:\Users\Maral\Desktop\interlinks-04-enriched-04.ttl', format="turtle")
#graph.parse('C:\Users\Maral\Desktop\interlinks-04-enriched-05.ttl', format="turtle")
graph.parse('C:\Users\Maral\Desktop\interlinks-04-enriched-06.ttl', format="turtle")




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



Select  ?x ?same ?same2
{

  GRAPH <http://maral.wisslab.org/graphs/interlinks> {

    ?x owl:sameAs ?same

   }

  #GRAPH <http://maral.wisslab.org/graphs/gnd_persons>  {
  #GRAPH <http://maral.wisslab.org/graphs/bhr>  {
  #GRAPH <http://maral.wisslab.org/graphs/dbpedia_persons>  {
  #GRAPH <http://maral.wisslab.org/graphs/rujen>  {
  GRAPH <http://maral.wisslab.org/graphs/freimann-gnd>  {
    ?same a foaf:Person.
    ?same owl:sameAs ?same2
   }

}

""")

sparql.setReturnFormat(XML)

results = sparql.query().convert()

graph.bind('foaf',foaf)
graph.bind('skos',skos)
graph.bind('gndo',gndo)
graph.bind('jl',jl)
graph.bind('owl',owl)


if (u"x",u"same2") in results:



    bindings = results[u"x",u"same2"]

    for b in bindings:

        uri = b['x'].value
        same = b['same2'].value

        if uri != same:
            graph.add( (URIRef(uri),  RDF.type , foaf.Person ) )
            graph.add( (URIRef(uri) , owl.sameAs ,  URIRef(same2) ))


#graph.serialize(destination='interlinks-04-enriched-01.ttl', format="turtle")
#graph.serialize(destination='interlinks-04-enriched-02.ttl', format="turtle")
#graph.serialize(destination='interlinks-04-enriched-03.ttl', format="turtle")
#graph.serialize(destination='interlinks-04-enriched-04.ttl', format="turtle")
#graph.serialize(destination='interlinks-04-enriched-05.ttl', format="turtle")
#graph.serialize(destination='interlinks-04-enriched-06.ttl', format="turtle")
graph.serialize(destination='interlinks-04-enriched-07.ttl', format="turtle")




