# this code creates rdf file from csv file
# 08/04/2019
# Maral Dadvar

from urllib import parse

import csv
import urllib.request as urllib2
from SPARQLWrapper import RDF
from bs4 import BeautifulSoup
from rdflib import Namespace, URIRef, Graph, Literal
from rdflib.namespace import RDF

graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace("http://purl.org/dc/elements/1.1/")

graph.bind('skos', skos)
graph.bind('foaf', foaf)
graph.bind('jl', jl)
graph.bind('gndo', gndo)
graph.bind('owl', owl)
graph.bind('edm', edm)
graph.bind('dc', dc)


def generator_persons(newuri):
    preflabel = ''
    altlabel = ''
    viaf = ''
    uriname = ''
    same = ''
    pb = ''
    pd = ''
    dd = ''
    db = ''

    personpage = urllib2.urlopen(newuri)

    soup = BeautifulSoup(personpage)

    personnode = soup.findAll('div', attrs={"class": "node node-person"})
    print(personnode)

    if personnode == []:
        return ('error')

    name = str(personnode[0].find('h1').string)

    if '-' in name:

        gernamefield = name.rsplit('-', 1)[0].strip()
        preflabel = gernamefield

        altlabel = name.rsplit('-', 1)[1].strip()

    else:

        preflabel = name.strip()

    uriname = preflabel.replace(' ', '_')
    uriname = uriname.replace(',', '')
    uriname = uriname.replace('"', '')
    uriname = uriname.replace('\'', '')

    print(uriname)

    jluri = 'http://data.judaicalink.org/data/haskala/' + uriname
    graph.add((URIRef(jluri), RDF.type, foaf.Person))
    graph.add((URIRef(jluri), skos.prefLabel, (Literal(preflabel))))
    if altlabel != '':
        graph.add((URIRef(jluri), skos.altLabel, (Literal(altlabel))))

    book = soup.findAll('div', attrs={"class": "book-title"})
    print(book)
    if book != []:
        for i in range(0, len(book)):
            bookuri = 'https://www.haskala-library.net/' + book[i].find('a').get('href')
            bookuri = parse.unquote(bookuri)
            print(bookuri)
            graph.add((URIRef(jluri), jl.hasPublication, (URIRef(bookuri))))
    else:
        bookuri = ''

    return (jluri)


data = csv.reader(open('../input/Assignments responsible persons_Maral.csv'))

for row in data:

    uri = row[0]

    print(uri)

    jlu = generator_persons(uri)
    print(jlu)

    if jlu != 'error':

        if row[3].strip() != 'None':
            graph.add((URIRef(jlu), owl.sameAs, (URIRef(row[3]))))

        if row[4].strip() != 'None':
            gnd = row[4].rsplit('/', 1)[1]
            graph.add((URIRef(jlu), owl.sameAs, (URIRef(row[4]))))
            graph.add((URIRef(jlu), gndo.gndIdentifier, (Literal(gnd))))

        urisame = parse.unquote(uri)
        graph.add((URIRef(jlu), owl.sameAs, (URIRef(urisame))))

graph.serialize(destination='Haskala.ttl', format="turtle")
