# Maral Dadvar
#This code looks for common authors in Tn authors at UB dataset and the authors extracted from GND with unique occurance and based on the specified occupations.
#10.07.2017
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

graphuni = Graph()
graphmulti = Graph()


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



Select distinct  ?y ?label
{

  GRAPH <http://maral.wisslab.org/graphs/ub_tn> {

    ?x a foaf:Person.
    ?x skos:prefLabel ?label.

   }
  GRAPH <http://maral.wisslab.org/graphs/gnd>  {
   ?y a gndo:DifferentiatedPerson.
    ?y gndo:preferredNameForThePerson  ?label.

    ?y gndo:professionOrOccupation ?occ
    Filter(?occ = <http://d-nb.info/gnd/4176751-2> || ?occ =  <http://d-nb.info/gnd/4059756-8> || ?occ =  <http://d-nb.info/gnd/4415844-0> || ?occ =  <http://d-nb.info/gnd/4525103-4>	)
    #?occ gndo:preferredNameForTheSubjectHeading ?occlabel

   }

}

""")

sparql.setReturnFormat(XML)

results = sparql.query().convert()

graphuni.bind('foaf',foaf)
graphuni.bind('skos',skos)
graphuni.bind('gndo',gndo)

graphmulti.bind('foaf',foaf)
graphmulti.bind('skos',skos)
graphmulti.bind('gndo',gndo)

names={}

if (u"y",u"label") in results:
    bindings = results[u"y",u"label"]
    for b in bindings:
        names[b[u"y"]] = b[u"label"].value

        #print b


reverse_names = {}  #create a dic to all GNDid and labels.
for key, value in names.items():
    try:reverse_names[value].append(key)
    except:reverse_names[value] = [key]


for key, value in reverse_names.items():
   if len(reverse_names[key]) > 1:  #reverse the dic to check for labels which have multi entries in GND
        print key , reverse_names[key]

        for i in range (0, len(reverse_names[key])):

            graphmulti.add( (URIRef(reverse_names[key][i].value),  RDF.type , foaf.Person ) )
            graphmulti.add( (URIRef(reverse_names[key][i].value) , skos.prefLabel ,  Literal(key) ))

   else:
            graphuni.add( (URIRef(reverse_names[key][0].value),  RDF.type , foaf.Person ) )
            graphuni.add( (URIRef(reverse_names[key][0].value) , skos.prefLabel ,  Literal(key) ))



graphmulti.serialize(destination='Tn-gnd-multi.rdf', format="turtle")
graphuni.serialize(destination='Tn-gnd-uni.rdf', format="turtle")




