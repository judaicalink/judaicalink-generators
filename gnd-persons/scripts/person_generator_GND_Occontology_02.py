# Maral Dadvar
# 27/04/2017
# This script generates persons from GND, based on the land set to Israel. The occupation of the persons are also extracted and maaped to Occ_ontology

from SPARQLWrapper import SPARQLWrapper2, TURTLE
from rdflib import Namespace, URIRef, Graph, Literal, RDF

sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")

graph = Graph()

foaf = Namespace("http://xmlns.com/foaf/0.1/")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
jl = Namespace("http://data.judaicalink.org/ontology/")
jlo = Namespace("http://data.judaicalink.org/occupation/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")

g = Graph()

g.bind('gndo', gndo)
g.bind('foaf', foaf)
g.bind('jl', jl)
g.bind('jlo', jlo)
g.bind('skos', skos)

# extracts differentiated persons from GND who live in Israel(occupation and label and gndid).
spar1 = """
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
    PREFIX gnd: <http://d-nb.info/gnd/>

select ?person ?occ ?name ?occname ?occont ?label

		WHERE{

  GRAPH <https://data.judaicalink.org/data/gnd> {
    ?person a gndo:DifferentiatedPerson .
    ?person gndo:geographicAreaCode <http://d-nb.info/standards/vocab/gnd/geographic-area-code#XY>.
   ?person gndo:professionOrOccupation ?occ.
    ?person gndo:preferredNameForThePerson ?name.
    ?person gndo:variantNameForThePerson ?label.
    ?occ gndo:preferredNameForTheSubjectHeading ?occname

 GRAPH <https://data.judaicalink.org/data/occ_ontology> {
    	?occont a jl:Occupation.
        ?occont owl:sameAs ?occ

  }


  }     }


    """

sparql.setQuery(spar1)
sparql.setReturnFormat(TURTLE)
results = sparql.query().convert()

if (u"person", u"occ", u"name", u"occname", u"occont", u"label") in results:
    bindings = results[u"person", u"occ", u"name", u"occname", u"occont", u"label"]
    for b in bindings:
        print(b)

        name = b[u"name"].value.encode('utf-8')
        label = b[u"label"].value.encode('utf-8')
        name = name.replace('<', '')
        name = name.replace('>', '')
        name = name.replace('-', '')
        name = name.replace('_', '')
        name = name.replace('/', '')
        name = name.replace('\\', '')

        URIending = b[u"person"].value.rsplit('/', 1)[1]

        if ',' and ' ' not in b[u"name"].value:  # check if the name has only one part

            jlURI = 'http://data.judaicalink.org/data/gnd/' + URIending
            print(jlURI)

        elif b[u"name"].value.count(',') == 2:  # check if the name has more that 3 parts

            altname = name.rsplit(',', 2)[1].strip() + ' ' + name.rsplit(',', 2)[1].strip() + ' ' + name.rsplit(',', 2)[
                2].strip()
            jlURI = 'http://data.judaicalink.org/data/gnd/' + URIending
            print(jlURI)

        elif b[u"name"].value.count(',') == 1:  # check if the name has 2 parts

            altname = name.rsplit(',', 1)[1].strip() + ' ' + name.rsplit(',', 1)[0]
            jlURI = 'http://data.judaicalink.org/data/gnd/' + URIending
            print(jlURI)

        elif ',' not in b[u"name"].value:  # check if name parts are separated with space insetad of ','

            altname = name.rsplit(' ', 1)[1].strip() + ' ' + name.rsplit(' ', 1)[0]
            jlURI = 'http://data.judaicalink.org/data/gnd/' + URIending
            print(jlURI)

        g.add((URIRef(jlURI), RDF.type, foaf.Person))
        g.add((URIRef(jlURI), skos.altLabel, Literal(label)))
        g.add((URIRef(jlURI), skos.prefLabel, Literal(b[u"name"].value)))
        g.add((URIRef(jlURI), skos.altLabel, Literal(altname)))
        g.add((URIRef(jlURI), gndo.gndIdentifier, URIRef(b[u"person"].value)))
        g.add((URIRef(jlURI), jl.occupation, URIRef(b[u"occont"].value)))

g.serialize(destination='generated_person_GND_Occontology.ttl', format="turtle")
