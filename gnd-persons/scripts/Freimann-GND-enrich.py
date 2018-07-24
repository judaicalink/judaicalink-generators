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

graphuni = Graph()
#graphuni.parse('C:\Users\Maral\Desktop\Freimann-GND-03.rdf', format="turtle") #first the original file is enriched only with those which have altlabels and occ in GND.
#graphuni.parse('C:\Users\Maral\Desktop\Freimann-GND-enriched-01.ttl', format="turtle") #then the generated file is parsed again to add further information like date and place of birth and death.
#graphuni.parse('C:\Users\Maral\Desktop\Freimann-GND-enriched-02.ttl', format="turtle") #to extarct only those which have date of birth and death with out the place
#graphuni.parse('C:\Users\Maral\Desktop\Freimann-GND-enriched-03.ttl', format="turtle") #to extarct only those which have no alt lable but date of birth and death
graphuni.parse('C:\Users\Maral\Desktop\Freimann-GND-enriched-04.ttl', format="turtle") #to extarct only those which have no alt lable and no occ and no date of death but date of birth.



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



Select distinct  ?x ?label ?id ?y   ?birth  #?placebn ?placedn ?alt ?occlabel ?death
{

  GRAPH <http://maral.wisslab.org/graphs/freimann-gnd> {

    ?x a foaf:Person.
    ?x skos:prefLabel ?label.
    ?x gndo:gndIdentifier ?id.
    ?x owl:sameAs ?y.

   }
  GRAPH <http://maral.wisslab.org/graphs/gnd>  {
    ?y a gndo:DifferentiatedPerson.
    #?y gndo:preferredNameForThePerson  ?label.
    #?y gndo:variantNameForThePerson ?alt.

    ?y gndo:dateOfBirth ?birth.
    #?y gndo:dateOfDeath ?death.
    #?y gndo:placeOfBirth ?placeb.
    #?placeb gndo:preferredNameForThePlaceOrGeographicName ?placebn.
    #?y gndo:placeOfDeath ?placed.
    #?placed gndo:preferredNameForThePlaceOrGeographicName ?placedn.

    #?y gndo:professionOrOccupation ?occ.
    #?occ gndo:preferredNameForTheSubjectHeading ?occlabel.

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



#if (u"x",u"label",u"id",u"y",u"alt",u"occlabel") in results: #first round
#if (u"x",u"label",u"id",u"y",u"alt",u"occlabel",u"birth",u"death",u"placebn",u"placedn") in results: #second round
#if (u"x",u"label",u"id",u"y",u"alt",u"occlabel",u"birth",u"death") in results: #third round
#if (u"x",u"label",u"id",u"y",u"occlabel",u"birth",u"death") in results: #fourth round
if (u"x",u"label",u"id",u"y",u"birth") in results: #fifth round

    #bindings = results[u"x",u"label",u"id",u"y",u"alt",u"occlabel"] #first round
    #bindings = results[u"x",u"label",u"id",u"y",u"alt",u"occlabel",u"birth",u"death",u"placebn",u"placedn"] #second round
    #bindings = results[u"x",u"label",u"id",u"y",u"alt",u"occlabel",u"birth",u"death"] #third round
   #bindings = results[u"x",u"label",u"id",u"y",u"occlabel",u"birth",u"death"] #fourth round
    bindings = results[u"x",u"label",u"id",u"y",u"birth"] #fifth round
    for b in bindings:

        uri = b['x'].value
        label = b['label'].value
        #alt = b['alt'].value
       # occ = b['occlabel'].value
        #occ = occ.replace(' ','_')
        #occuri = 'http://data.judaicalink.org/data/occupation/' + occ
        id = b['id'].value
        same = b['y'].value
        birth = b['birth'].value
        #death = b['death'].value
        #birthp = b['placebn'].value
        #deathp = b['placedn'].value

        graphuni.add( (URIRef(uri),  RDF.type , foaf.Person ) )
        graphuni.add( (URIRef(uri) , skos.prefLabel ,  Literal(label) ))
        #graphuni.add( (URIRef(uri) , skos.altLabel ,  Literal(alt) ))
        graphuni.add( (URIRef(uri) , gndo.gndIdentifier ,  Literal(id) ))
        graphuni.add( (URIRef(uri) , owl.sameAs ,  URIRef(same) ))
       #graphuni.add( (URIRef(uri) , jl.occupation ,  URIRef(occuri) ))
        graphuni.add( (URIRef(uri) , jl.birthDate ,  Literal(birth) ))
        #graphuni.add( (URIRef(uri) , jl.deathDate ,  Literal(death) ))
        #graphuni.add( (URIRef(uri) , jl.deathLocation ,  Literal(deathp) ))
        #graphuni.add( (URIRef(uri) , jl.birthLocation ,  Literal(birthp) ))



#graphuni.serialize(destination='Freimann-GND-enriched-01.ttl', format="turtle") #the first generated file
#graphuni.serialize(destination='Freimann-GND-enriched-02.ttl', format="turtle") #the second generated file
#graphuni.serialize(destination='Freimann-GND-enriched-03.ttl', format="turtle") #the third generated file
#graphuni.serialize(destination='Freimann-GND-enriched-04.ttl', format="turtle") #the fourth generated file
graphuni.serialize(destination='Freimann-GND-enriched-05.ttl', format="turtle") #the fourth generated file





