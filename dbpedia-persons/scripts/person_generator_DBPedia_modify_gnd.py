# Maral Dadvar
# 21/04/2017
# This scrips reads a list of occupation URIs extracted from DBPedia and extracts the Persons label and sameAs links from each URI.
# The occpuation ontology rdf file is used for the occupation URI's.

from rdflib import Namespace, URIRef, Graph, Literal, OWL, RDFS, RDF

path = './'  # adapted to the list file path

foaf = Namespace("http://xmlns.com/foaf/0.1/")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
jl = Namespace("http://data.judaicalink.org/ontology/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
dct = Namespace("http://purl.org/dc/terms/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
owl = Namespace("http://www.w3.org/2002/07/owl#")

g2 = Graph()
g2.parse('../output/person-gndid.ttl', format="turtle")

g = Graph()
g.parse('../output/generated_person_dbpedia_modified.ttl', format="turtle")

g.bind('jl', jl)
g.bind('owl', OWL)
g.bind('rdfs', RDFS)
g.bind('foaf', foaf)
g.bind('dct', dct)
g.bind('skos', skos)
g.bind('gndo', gndo)

spar2 = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX pro: <http://purl.org/hpi/patchr#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dbpedia: <http://dbpedia.org/resource/>

    SELECT ?x ?gnd
    where {
      ?x a foaf:Person.
      ?x gndo:gndIdentifier ?gnd.

      }
"""

result2 = g2.query(spar2)

for item2 in result2:
    print(item2)

    URI = item2[0]
    gnduri = item2[1]
    gnd = str(gnduri).rsplit('/', 1)[1]

    g.add((URIRef(URI), RDF.type, foaf.Person))
    g.add((URIRef(URI), gndo.gndIdentifier, Literal(gnd)))
    g.add((URIRef(URI), owl.sameAs, URIRef(gnduri)))

g.serialize(destination='generated_person_dbpedia_modified_gnd.ttl', format="turtle")
