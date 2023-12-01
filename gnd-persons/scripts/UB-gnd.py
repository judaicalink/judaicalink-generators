# this code uses the GND links of UB and extracts all their info from GND to creat a new dataset for JL.
# 17/07/2018
# Maral Dadvar


import csv
import re
from SPARQLWrapper import SPARQLWrapper2, RDF, TURTLE
from rdflib import Namespace, URIRef, Graph, Literal
from rdflib.namespace import RDF

sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")

graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")


def generator_gnd(gndURI):
    newURI = '<' + gndURI + '>'

    spar2 = """
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

        select ?name ?alt ?gnd ?same ?pb ?pd ?db ?dd

        WHERE{{
          graph <https://data.judaicalink.org/data/gnd> {{

            	{0} gndo:preferredNameForThePerson ?name.
                optional {{{0} gndo:variantNameForThePerson ?alt.}}
                optional {{{0} gndo:gndIdentifier ?gnd}}
                optional {{{0} owl:sameAs ?same}}
                optional {{{0} gndo:placeOfBirth ?pb1.
                ?pb1 gndo:preferredNameForThePlaceOrGeographicName ?pb}}
                optional {{{0} gndo:placeOfDeath ?pd1.
                ?pd1 gndo:preferredNameForThePlaceOrGeographicName ?pd}}
                optional {{{0} gndo:dateOfBirth ?db}}
                optional {{{0} gndo:dateOfDeath ?dd}}

          }}
          }}


        """.format(newURI)

    sparql.setQuery(spar2)
    sparql.setReturnFormat(TURTLE)
    results = sparql.query().convert()

    graph.bind('skos', skos)
    graph.bind('foaf', foaf)
    graph.bind('jl', jl)
    graph.bind('gndo', gndo)
    graph.bind('owl', owl)

    for i in range(0, len(results.bindings)):

        URI = 'http://data.judaicalink.org/data/gnd/' + results.bindings[i]['gnd'].value

        graph.add((URIRef(URI), RDF.type, foaf.Person))

        name = results.bindings[i]['name'].value
        graph.add((URIRef(URI), skos.prefLabel, (Literal(name))))

        graph.add((URIRef(URI), owl.sameAs, (URIRef(gndURI))))

        if 'alt' in results.bindings[i].keys():
            alt = results.bindings[i]['alt'].value
            graph.add((URIRef(URI), skos.altLabel, (Literal(alt))))
        else:
            alt = "NA"

        if 'gnd' in results.bindings[i].keys():
            gnd = results.bindings[i]['gnd'].value
            graph.add((URIRef(URI), gndo.gndIdentifier, (Literal(gnd))))
        else:
            gnd = "NA"

        if 'same' in results.bindings[i].keys():
            same = results.bindings[i]['same'].value
            graph.add((URIRef(URI), owl.sameAs, (URIRef(same))))
        else:
            same = "NA"

        if 'pb' in results.bindings[i].keys():
            pbirth = results.bindings[i]['pb'].value
            graph.add((URIRef(URI), jl.birthLocation, (Literal(pbirth))))
        else:
            pbirth = "NA"

        if 'pd' in results.bindings[i].keys():
            pdeath = results.bindings[i]['pd'].value
            graph.add((URIRef(URI), jl.deathLocation, (Literal(pdeath))))
        else:
            pdeath = "NA"

        if 'db' in results.bindings[i].keys():
            dbirth = results.bindings[i]['db'].value
            bdate = re.findall(r'\d{4}', dbirth)
            if bdate != []:
                graph.add((URIRef(URI), jl.birthDate, (Literal(bdate[0]))))
        else:
            dbirth = "NA"

        if 'dd' in results.bindings[i].keys():
            ddeath = results.bindings[i]['dd'].value
            ddate = re.findall(r'\d{4}', ddeath)
            if ddate != []:
                graph.add((URIRef(URI), jl.deathDate, (Literal(ddate[0]))))
        else:
            ddeath = "NA"

    return


data = csv.reader(open('../sources/tp-records_gnd-ids.csv'))
fields = data.next()
eventdic = {}

dic = {}

for row in data:

    items = zip(fields, row)
    item = {}
    for (name, value) in items:
        item[name] = value.strip()

    gnduri = item['GND_ID'].strip()
    print(gnduri)
    generator_gnd(gnduri)

graph.serialize(destination='UB-gnd-enrich.ttl', format="turtle")
