# this code creates triples from the csv file containing information extarcted from the encyclopedia this time containing the internal ids.
# 01/Sep/2017
# Maral Dadvar


import csv
from rdflib import Namespace, URIRef, Graph, Literal
from rdflib.namespace import RDF

graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")

graph.bind('skos', skos)
graph.bind('foaf', foaf)
graph.bind('jl', jl)
graph.bind('gndo', gndo)
graph.bind('owl', owl)

data = csv.reader(open('BHR-ID.csv'))
fields = data.next()
eventdic = {}

dic = {}

listuri = []

for row in data:
    i = 0

    items = zip(fields, row)
    item = {}
    for (name, value) in items:
        item[name] = value.strip()

    names = item['Name'].strip()

    if '(' in names:
        names = names.rsplit('(', 1)[0].strip()

    names = names.rsplit('-', (names.count('-') - 1))[0].strip()

    names = names.replace('.', '')
    names = names.replace('-', ',')
    names = names.decode('utf8').title()

    namesuri = names.replace(',', '_')

    namesuri = namesuri.replace(' ', '')  # the names used in person uri can not have space

    print(names)

    id = item['ID']
    gnd = item['GND']

    uri0 = 'http://data.judaicalink.org/data/bhr/' + namesuri

    sameas1 = 'http://steinheim-institut.de:50580/cgi-bin/bhr?id=' + id

    if uri0 not in listuri:
        listuri.append(uri0)
        uri = uri0
    else:
        i = i + 1
        uri = uri0 + '-' + str(i)
        if uri not in listuri:
            listuri.append(uri)

        else:
            i = i + 1
            uri = uri0 + '-' + str(i)
            if uri not in listuri:
                listuri.append(uri)

            else:
                i = i + 1
                uri = uri0 + '-' + str(i)
                listuri.append(uri)

    graph.add((URIRef(uri), RDF.type, foaf.Person))
    graph.add((URIRef(uri), owl.sameAs, (URIRef(sameas1))))

    if gnd != 'NA':
        graph.add((URIRef(uri), gndo.gndIdentifier, (URIRef(gnd))))
    else:
        graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(gnd))))

    graph.add((URIRef(uri), skos.prefLabel, (Literal(names))))

graph.serialize(destination='EncycBHR-ID.rdf', format="turtle")
