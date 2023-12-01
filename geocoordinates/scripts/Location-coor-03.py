# Maral Dadvar
# This code selects a unique geo-coordinate for each city
# 17/07/2018
# Ver. 02

from SPARQLWrapper import SPARQLWrapper2
from decimal import Decimal
from rdflib import Namespace, URIRef, Graph, Literal
from rdflib.namespace import RDF

sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")

foaf = Namespace("http://xmlns.com/foaf/0.1/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
jl = Namespace("http://data.judaicalink.org/ontology/")
owl = Namespace("http://www.w3.org/2002/07/owl#")
geo = Namespace("http://www.opengis.net/ont/geosparql#")

graph = Graph()
graph.parse('./city-geocoor-04-all.ttl', format="turtle")

graph1 = Graph()
graph2 = Graph()
graph3 = Graph()

graph1.bind('skos', skos)
graph1.bind('jl', jl)
graph1.bind('gndo', gndo)
graph1.bind('owl', owl)
graph1.bind('geo', geo)

graph2.bind('skos', skos)
graph2.bind('jl', jl)
graph2.bind('gndo', gndo)
graph2.bind('owl', owl)
graph2.bind('geo', geo)

graph3.bind('skos', skos)
graph3.bind('jl', jl)
graph3.bind('gndo', gndo)
graph3.bind('owl', owl)
graph3.bind('geo', geo)

spar = """
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
    PREFIX geo:<http://www.opengis.net/ont/geosparql#>

Select  ?x ?name ?same ?coo ?gnd (group_concat(?lat; SEPARATOR=",") as ?lat2) (group_concat(?lon; SEPARATOR=",") as ?lon2)
where
{

 ?x skos:prefLabel ?name.
 ?x owl:sameAs ?same.
 ?x jl:lat ?lat.
 ?x jl:lon ?lon.
 ?x geo:asWKT ?coo.
 ?x gndo:gndIdentifier ?gnd.

} group by ?x ?name ?same ?coo ?gnd

"""

results = graph.query(spar)

for i in range(0, len(results.bindings)):

    uri = results.bindings[i]['x']
    if '(' in uri:
        uri = uri.rsplit('(', 1)[0]

    name = results.bindings[i]['name'].value

    count = results.bindings[i]['lat2'].value.count(',')

    if count == 3:

        lat1 = results.bindings[i]['lat2'].value.rsplit(',', 3)[1]
        lat2 = results.bindings[i]['lat2'].value.rsplit(',', 1)[1]
        lat1 = lat1.replace('+', '')
        lat2 = lat2.replace('+', '')
        print(lat1, lat2)
        lon1 = results.bindings[i]['lon2'].value.rsplit(',', 1)[1]
        lon2 = results.bindings[i]['lon2'].value.rsplit(',', 3)[1]
        print('lon', lon1, lon2)

        if (abs(Decimal(lat1) - Decimal(lat2)) < 0.01):
            coor = 'Point (' + lat1 + ' ' + lon1 + ' )'
            graph2.add((URIRef(uri), RDF.type, skos.Concept))
            graph2.add((URIRef(uri), geo.asWKT, (Literal(coor))))
            graph2.add((URIRef(uri), gndo.gndIdentifier, (URIRef(results.bindings[i]['gnd']))))
            graph2.add((URIRef(uri), jl.lat, (Literal(lat1))))
            graph2.add((URIRef(uri), jl.lon, (Literal(lon1))))
            graph2.add((URIRef(uri), owl.sameAs, (URIRef(results.bindings[i]['same']))))
            graph2.add((URIRef(uri), skos.prefLabel, (Literal(name))))

            graph1.add((URIRef(uri), RDF.type, skos.Concept))
            graph1.add((URIRef(uri), geo.asWKT, (Literal(results.bindings[i]['coo'].value))))
            graph1.add((URIRef(uri), gndo.gndIdentifier, (URIRef(results.bindings[i]['gnd']))))
            graph1.add((URIRef(uri), jl.lat, (Literal(lat1))))
            graph1.add((URIRef(uri), jl.lon, (Literal(lon1))))
            graph1.add((URIRef(uri), owl.sameAs, (URIRef(results.bindings[i]['same']))))
            graph1.add((URIRef(uri), skos.prefLabel, (Literal(name))))



    elif count == 0:

        graph1.add((URIRef(uri), RDF.type, skos.Concept))
        graph1.add((URIRef(uri), geo.asWKT, (Literal(results.bindings[i]['coo'].value))))
        graph1.add((URIRef(uri), gndo.gndIdentifier, (URIRef(results.bindings[i]['gnd']))))
        graph1.add((URIRef(uri), owl.sameAs, (URIRef(results.bindings[i]['same']))))
        graph1.add((URIRef(uri), skos.prefLabel, (Literal(name))))


    else:

        graph3.add((URIRef(uri), RDF.type, skos.Concept))
        graph3.add((URIRef(uri), geo.asWKT, (Literal(results.bindings[i]['coo'].value))))
        graph3.add((URIRef(uri), gndo.gndIdentifier, (URIRef(results.bindings[i]['gnd']))))
        graph3.add((URIRef(uri), owl.sameAs, (URIRef(results.bindings[i]['same']))))
        graph3.add((URIRef(uri), skos.prefLabel, (Literal(name))))

graph1.serialize(destination='city-geocoor-05.ttl', format="turtle")
graph2.serialize(destination='city-geocoor-06.ttl', format="turtle")
graph3.serialize(destination='city-geocoor-07.ttl', format="turtle")
