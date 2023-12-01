# Maral Dadvar
#This code extracts further information from GND for the authors of Freimann collection who have an GND-ID assigned to them.
#15/01/2018
#Ver. 01

from SPARQLWrapper import SPARQLWrapper2, XML
from rdflib import Namespace, URIRef, Graph
from rdflib.namespace import RDF

sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")

foaf = Namespace("http://xmlns.com/foaf/0.1/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
jl = Namespace("http://data.judaicalink.org/ontology/")
owl = Namespace ("http://www.w3.org/2002/07/owl#")

graph = Graph()
#graph.parse('../output/interlinks-04.ttl', format="turtle")
#graph.parse('../output/interlinks-04-enriched-01.ttl', format="turtle")
#graph.parse('../output/interlinks-04-enriched-02.ttl', format="turtle")
#graph.parse('../output/interlinks-04-enriched-03.ttl', format="turtle")
#graph.parse('../output/interlinks-04-enriched-04.ttl', format="turtle")
#graph.parse('../output/interlinks-04-enriched-05.ttl', format="turtle")
graph.parse('../output/interlinks-04-enriched-06.ttl', format="turtle")




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

  GRAPH <https://data.judaicalink.org/data/interlinks> {

    ?x owl:sameAs ?same

   }

  #GRAPH <https://data.judaicalink.org/data/gnd_persons>  {
  #GRAPH <https://data.judaicalink.org/data/bhr>  {
  #GRAPH <https://data.judaicalink.org/data/dbpedia_persons>  {
  #GRAPH <https://data.judaicalink.org/data/rujen>  {
  GRAPH <https://data.judaicalink.org/data/freimann-gnd>  {
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




