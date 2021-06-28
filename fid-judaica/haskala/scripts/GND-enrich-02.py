# Maral Dadvar
#This code read the Hakala graph from Fuseki and generates an ttl file.
#19/06/2019
#Ver. 01

import rdflib
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON
from rdflib.namespace import RDF, FOAF , SKOS ,RDFS
import os

os.chdir('C:\\Users\\Maral\\Desktop')

sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")

graphuni = Graph()

foaf = Namespace("http://xmlns.com/foaf/0.1/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
jl = Namespace("http://data.judaicalink.org/ontology/")
owl = Namespace ("http://www.w3.org/2002/07/owl#")


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
    PREFIX jl: <http://data.judaicalink.org/ontology/>



Select ?x ?y ?z

where{

  GRAPH <http://maral.wisslab.org/graphs/haskala> {

    ?x ?y ?z

   }

}

""")

sparql.setReturnFormat(XML)

results = sparql.query().convert()

graphuni.bind('foaf',foaf)
graphuni.bind('skos',skos)
graphuni.bind('gndo',gndo)
graphuni.bind('jl',jl)
graphuni.bind('owl',owl)

for i in range(0,len(results.bindings)):


    print (results.bindings[i]['y'])
    URI = results.bindings[i]['x'].value

    graphuni.add((URIRef(URI), RDF.type, foaf.Person ))

    if results.bindings[i]['y'].value == 'http://data.judaicalink.org/ontology/deathLocation':
        graphuni.add( (URIRef(URI) , jl.deathLocation ,  Literal(results.bindings[i]['z'].value) ))

    if results.bindings[i]['y'].value == 'http://data.judaicalink.org/ontology/birthLocation':
        graphuni.add( (URIRef(URI) , jl.birthLocation ,  Literal(results.bindings[i]['z'].value) ))

    if results.bindings[i]['y'].value == 'http://data.judaicalink.org/ontology/deathDate':
        graphuni.add( (URIRef(URI) , jl.deathDate ,  Literal(results.bindings[i]['z'].value) ))

    if results.bindings[i]['y'].value == 'http://data.judaicalink.org/ontology/birthDate':
        graphuni.add( (URIRef(URI) , jl.birthDate ,  Literal(results.bindings[i]['z'].value) ))

    if results.bindings[i]['y'].value == 'http://data.judaicalink.org/ontology/hasPublication':
        graphuni.add( (URIRef(URI) , jl.hasPublication ,  URIRef(results.bindings[i]['z'].value) ))

    if results.bindings[i]['y'].value == 'http://www.w3.org/2004/02/skos/core#prefLabe':
        graphuni.add( (URIRef(URI) , skos.prefLabel ,  Literal(results.bindings[i]['z'].value) ))

    if results.bindings[i]['y'].value == 'http://www.w3.org/2004/02/skos/core#altLabel':
        graphuni.add( (URIRef(URI) , skos.altLabel ,  Literal(results.bindings[i]['z'].value) ))

    if results.bindings[i]['y'].value == 'http://www.w3.org/2004/02/skos/core#prefLabel':
        graphuni.add( (URIRef(URI) , skos.prefLabel ,  Literal(results.bindings[i]['z'].value) ))

    if results.bindings[i]['y'].value == 'http://www.w3.org/2002/07/owl#sameAs':
        graphuni.add( (URIRef(URI) , owl.sameAs ,  URIRef(results.bindings[i]['z'].value) ))

    if results.bindings[i]['y'].value == 'http://d-nb.info/standards/elementset/gnd#gndIdentifier':
        graphuni.add( (URIRef(URI) , gndo.gndIdentifier ,  Literal(results.bindings[i]['z'].value) ))

graphuni.serialize(destination='Haskala_enriched.ttl', format="turtle")
