# Maral Dadvar
#This code looks for authors in CM dataset which have no gndid in the gnd dataset.
#10.01.2018
#Ver. 01

import rdflib
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON
from rdflib.namespace import RDF, FOAF , SKOS ,RDFS, OWL
import os

os.chdir('C:\Users\Maral\Desktop')

sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")


foaf = Namespace("http://xmlns.com/foaf/0.1/")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
jl = Namespace("http://data.judaicalink.org/ontology/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
dc = Namespace ("http://purl.org/dc/elements/1.1/")
edm = Namespace("http://www.europeana.eu/schemas/edm/")


graphout = Graph()

graphout.bind('jl', jl)
graphout.bind('rdfs',RDFS)
graphout.bind('foaf',foaf)
graphout.bind('skos',skos)
graphout.bind('owl',OWL)
graphout.bind('gndo',gndo)
graphout.bind('dc',dc)
graphout.bind('edm',edm)

graph1 = Graph()
graph1.parse('C:\Users\Maral\Desktop\cm-gnd-uni.rdf', format="turtle")

unilist=[]

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

result = graph1.query(spar1)

for item in result:
    unilist.append(item[1].value.encode('utf-8'))

graph2= Graph()
graph2.parse('C:\Users\Maral\Desktop\cm-gnd-multi.rdf', format="turtle")

multilist=[]

spar2= """
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

result = graph2.query(spar2)

for item in result:
    multilist.append(item[1].value.encode('utf-8'))



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



Select distinct  ?x ?title ?id ?desc ?name
{

  GRAPH <http://maral.wisslab.org/graphs/ubcompact> {

    #?x a foaf:Person.
    #?x skos:prefLabel ?label.
      ?x a edm:ProvidedCHO.
      ?x dc:identifier ?id.
      ?x dc:description ?desc.
      ?x dc:title ?title.
      ?x <http://purl.org/spar/pro/author> ?author.
      ?author skos:prefLabel ?name

   }}

""")

sparql.setReturnFormat(XML)

results = sparql.query().convert()



if (u"x",u"title",u"id",u"desc",u"name") in results:
    bindings = results[u"x",u"title",u"id",u"desc",u"name"]
    for b in bindings:

        name = b['name'].value.encode('utf-8')
        if name not in unilist and name not in multilist:


           graphout.add((URIRef(b['x'].value), RDF.type , edm.ProvidedCHO ))
           graphout.add( (URIRef(b['x'].value), dc.creator , Literal(name) ) )
           graphout.add( (URIRef(b['x'].value), dc.identifier , Literal(b['id'].value) ) )
           graphout.add ((URIRef(b['x'].value) , dc.description , Literal((b['desc'].value))))
           graphout.add ((URIRef(b['x'].value) , dc.title , Literal((b['title'].value))))


graphout.serialize(destination='cm-no-gnd.rdf', format="turtle")




