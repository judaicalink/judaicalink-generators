# this code creates triples from the csv file containing information extarcted from the encyclopedia
# 25/July/2017
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

data = csv.reader(open('./Encycoutput.csv'))
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

    fn = item['fn'].strip()
    fn = fn.replace('.', '')

    if '(' in fn:
        fn = fn.rsplit('(', 1)[0].strip()

    fnuri = fn.replace(' ', '')  # the fn and ln used in person uri can not have space

    ln = item['ln'].strip()
    ln = ln.replace('.', '')

    if '(' in ln:
        ln = ln.rsplit('(', 1)[0].strip()

    lnuri = ln.replace(' ', '')

    if ln != '':
        name = fn + ', ' + ln
        nameuri = fnuri + '_' + lnuri


    else:

        name = fn
        nameuri = fnuri

    geb = item['geb']
    gest = item['gest']
    bhr = item['BHR']

    uri0 = 'http://data.judaicalink.org/data/bhr/' + nameuri

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
    graph.add((URIRef(uri), jl.birthDate, (Literal(geb))))
    graph.add((URIRef(uri), jl.deathDate, (Literal(gest))))
    # graph.add((URIRef(uri), jl.describedAt ,(Literal(bhr)) ))
    graph.add((URIRef(uri), skos.prefLabel, (Literal(name))))
    graph.add((URIRef(uri), jl.occpation, (URIRef('http://data.judaicalink.org/data/occupation/Rabbi'))))

graph.serialize(destination='Encyc.rdf', format="turtle")
