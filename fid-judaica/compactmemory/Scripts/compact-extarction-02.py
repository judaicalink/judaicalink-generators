# Maral Dadvar
#This code extracts the names of the authors from the ub CM dataset.
#13.03.2017
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
edm = Namespace("http://www.europeana.eu/schemas/edm/")
pro = Namespace ("http://purl.org/spar/pro/")
dc = Namespace ("http://purl.org/dc/elements/1.1/")

graph = Graph()


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



Select ?x ?name ?z ?ubid ?desc ?title

WHERE {
  GRAPH <http://maral.wisslab.org/graphs/ubcompact> {
    ?x a foaf:Person.
    ?x skos:prefLabel ?name.


  ?z a edm:ProvidedCHO.

  ?z pro:author ?x.
  ?z dc:identifier ?ubid .
  ?z dc:description ?desc.
  ?z dc:title ?title.



}
}

""")

sparql.setReturnFormat(XML)

results = sparql.query().convert()

graph.bind('foaf',foaf)
graph.bind('skos',skos)
graph.bind('edm',edm)
graph.bind('pro',pro)
graph.bind('dc',dc)

if (u"x",u"name",u"z",u"ubid",u"desc",u"title") in results:
    bindings = results[u"x",u"name",u"z",u"ubid",u"desc",u"title"]
    for b in bindings:
        #print b
        print b[u"name"].value

        ln = (b[u"name"].value).rsplit(',',1)[0].strip()
        #print ln

        if ',' in b[u"name"].value:

            fn = (b[u"name"].value).rsplit(',',1)[1].strip()
            name = fn+ ' ' + ln
            print name
        else:
            name = ln

            print name

        chouri = b[u"z"].value.rsplit('graphs/ubcompact#',1)[1]
        personuri = b[u"x"].value.rsplit('graphs/ubcompact#',1)[1]

        graph.add( (URIRef(personuri),  RDF.type , foaf.Person ) )

        graph.add( (URIRef(personuri) , skos.prefLabel ,  Literal(b[u"name"].value) ))
        graph.add( (URIRef(personuri) , skos.altLabel ,  Literal(name) ))
        graph.add ((URIRef( chouri) , RDF.type , edm.ProvidedCHO  ))
        graph.add ((URIRef( chouri) , pro.author , (URIRef(personuri)  )))
        graph.add ((URIRef( chouri) , dc.identifier , Literal((b[u"ubid"].value))))
        graph.add ((URIRef( chouri) , dc.description , Literal((b[u"desc"].value))))
        graph.add ((URIRef( chouri) , dc.title , Literal((b[u"title"].value))))

graph.serialize(destination='compact-extracted-02.rdf', format="turtle")




