# Maral Dadvar
#This code extracts further information from GND for the authors extarcted from DBPedia who have an GND-ID assigned to them.
#21/03/2018
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

#graphuni.parse('C:\Users\Maral\Desktop\generated_person_dbpedia_modified_gnd.ttl', format="turtle")
#graphuni.parse('C:\Users\Maral\Desktop\generated_persons_DBPedia-enriched-01.ttl', format="turtle")
graphuni.parse('C:\Users\Maral\Desktop\generated_persons_DBPedia-enriched-02.ttl', format="turtle")





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


CONSTRUCT{


    #?x skos:altLabel ?label.
    #?x skos:altLabel ?alt.
    #?x gndo:dateOfBirth ?birth.
    #?x gndo:dateOfDeath ?death.
    #?x gndo:preferredNameForThePlaceOrGeographicName ?placebn.
    #?x gndo:preferredNameForThePlaceOrGeographicName ?placedn.
    ?x gndo:preferredNameForTheSubjectHeading ?occlabel.
}
where
{

    GRAPH <http://maral.wisslab.org/graphs/dbpedia_persons> {

    ?x a foaf:Person.
    ?x owl:sameAs ?id

   }

  GRAPH <http://maral.wisslab.org/graphs/gnd>  {

    ?id a gndo:DifferentiatedPerson.

    ?id gndo:preferredNameForThePerson  ?label.
   # ?id gndo:variantNameForThePerson ?alt.

   # ?id gndo:dateOfBirth ?birthd.
    #BIND(str(?birthd) As ?birth)

   #?id gndo:dateOfDeath ?deathd.
   #BIND(str(?deathd) As ?death)

   #?id gndo:placeOfBirth ?placeb.
   #?placeb gndo:preferredNameForThePlaceOrGeographicName ?placebn.

   # ?id gndo:placeOfDeath ?placed.
    #?placed gndo:preferredNameForThePlaceOrGeographicName ?placedn.

    ?id gndo:professionOrOccupation ?occ.
    ?occ gndo:preferredNameForTheSubjectHeading ?occlabel.
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




for item in results:

    uri = item[0]
    #alt = item[2]
    #birth = item[2].value
    #death=item[2].value
    #placeb=item[2].value
    #placed=item[2].value
    occ=item[2].value.encode('utf-8')
    occ = occ.replace(' ','_')
    occ = occ.replace(' ','<')
    occ = occ.replace(' ','>')
    occuri = 'http://data.judaicalink.org/data/occupation/' + occ

    #graphuni.add( (URIRef(uri) , skos.altLabel ,  Literal(alt) ))
    #graphuni.add( (URIRef(uri) , jl.birthDate ,  Literal(birth) ))
    #graphuni.add( (URIRef(uri) , jl.deathDate ,  Literal(death) ))
    #graphuni.add( (URIRef(uri) , jl.birthLocation ,  Literal(placeb) ))
    #graphuni.add( (URIRef(uri) , jl.deathLocation ,  Literal(placed) ))
    graphuni.add( (URIRef(uri) , jl.occupation ,  Literal(occuri) ))




#graphuni.serialize(destination='generated_persons_DBPedia-enriched-01.ttl', format="turtle") #the first generated file, both gnd lable and altlabel are added as altlabel
graphuni.serialize(destination='generated_persons_DBPedia-enriched-02.ttl', format="turtle") #the second generated file all the other infomration were added






