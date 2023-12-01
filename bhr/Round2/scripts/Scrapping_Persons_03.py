# this code creates URL for BHR Encyc. perons based on their internal ids. Then scrapes each page to extract the GNDID and Name of the persons.

import urllib2
from bs4 import BeautifulSoup, NavigableString, Tag
from rdflib import Namespace, URIRef, Graph, Literal
from rdflib.namespace import RDF

foaf = Namespace("http://xmlns.com/foaf/0.1/")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
jl = Namespace("http://data.judaicalink.org/ontology/")
owl = Namespace("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace("http://purl.org/dc/elements/1.1/")

graph = Graph()

graph.bind('foaf', foaf)
graph.bind('skos', skos)
graph.bind('jl', jl)
graph.bind('gndo', gndo)
graph.bind('owl', owl)

names = []

for i in range(1, 2704):

    n = 0

    url = 'http://www.steinheim-institut.de:50580/cgi-bin/bhr?id=' + str(i)

    # print url

    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page)

    h3 = soup.find_all('h3')
    name = h3[0].string
    # print name
    if name != None:

        pname = name.encode('utf-8')
        if '(' in pname:
            pname = pname.rsplit('(', 1)[0].strip()
        if '[' in pname:
            pname = pname.rsplit('[', 1)[0].strip()
        if pname.count(',') == 2:
            pname = pname.rsplit(',', 1)[0].strip()
        if pname.count(',') == 3:
            pname = pname.rsplit(',', 2)[0].strip()
        if pname.count(',') == 4:
            pname = pname.rsplit(',', 3)[0].strip()
        if pname.count(',') == 5:
            pname = pname.rsplit(',', 4)[0].strip()
        pname = pname.replace('.', '')
        uriname = pname.replace(',', '_')
        # uriname = uriname.replace('-','_')

        uriname = uriname.replace(' ', '')  # the fn and ln used in person uri can not have space
        uriname = uriname.title()
        uri0 = 'http://data.judaicalink.org/data/bhr/' + uriname

        if uri0 not in names:
            names.append(uri0)
            uri = uri0

        else:
            n = n + 1
            uri = uri0 + '-' + str(n)
            if uri not in names:
                names.append(uri)
            else:
                n = n + 1
                uri = uri0 + '-' + str(n)
                if uri not in names:
                    names.append(uri)
                else:
                    n = n + 1
                    uri = uri0 + '-' + str(n)
                    names.append(uri)

        graph.add((URIRef(uri), RDF.type, foaf.Person))
        graph.add((URIRef(uri), skos.prefLabel, Literal(pname.title())))

        citation = soup.find_all('nav')
        cit = str(citation[1]).rsplit('<br', 1)[0]
        cit = cit.replace('<nav>', '')
        idbhr = str(i)
        finalcitation = cit + ', id:' + idbhr
        sameurl = 'http://steinheim-institut.de:50580/cgi-bin/bhr?id=' + idbhr

        graph.add((URIRef(uri), owl.sameAs, URIRef(sameurl)))
        graph.add((URIRef(uri), jl.describedAt, Literal(finalcitation)))

        # print name , finalcitation

    for link in soup.find_all('a'):
        if 'gnd' in link.get('href'):
            gnd = link.get('href')
            graph.add((URIRef(uri), owl.sameAs, URIRef(gnd)))
            # print gnd
        if 'viaf' in link.get('href'):
            viaf = link.get('href')
            graph.add((URIRef(uri), owl.sameAs, URIRef(viaf)))
            # print viaf
        if 'entityfacts' in link.get('href'):
            entityfacts = link.get('href')
            graph.add((URIRef(uri), owl.sameAs, URIRef(entityfacts)))

        if 'wikidata' in link.get('href'):
            wikidata = link.get('href')
            graph.add((URIRef(uri), owl.sameAs, URIRef(wikidata)))
            # print wikidata
        if 'steinheim-institut.de/see-also/' in link.get('href'):
            steinheim = link.get('href')
            graph.add((URIRef(uri), owl.sameAs, URIRef(steinheim)))
            # print wikidata
        if 'wikipedia' in link.get('href'):
            wikipedia = link.get('href')
            graph.add((URIRef(uri), owl.sameAs, URIRef(wikipedia)))
            # print wikidata

    for header in soup.find_all('h3'):

        if header.text == 'Publikationen':

            nextNode = header

            while True:
                nextNode = nextNode.nextSibling
                if nextNode is None:
                    break
                if isinstance(nextNode, NavigableString):
                    print(nextNode.strip())
                if isinstance(nextNode, Tag):
                    if nextNode.name == "h3":
                        break
                    print(nextNode.get_text(strip=True).strip())
                    publication = (nextNode.get_text(strip=True).strip())
                    graph.add((URIRef(uri), jl.hasPublication, Literal(publication)))


        # elif header.text == 'Literatur': #to add the text in the literature section

        # nextNode = header

        # while True:
        #   nextNode = nextNode.nextSibling
        #  if nextNode is None:
        #     break
        # if isinstance(nextNode, NavigableString):
        #   print (nextNode.strip())
        # if isinstance(nextNode, Tag):
        #   if nextNode.name == "h3":
        #      break
        # print (nextNode.get_text(strip=True).strip())
        # literature = (nextNode.get_text(strip=True).strip())
        # graph.add((URIRef(uri) , jl.hasPublication , Literal(literature)))

        elif header.text == name:

            nextNode = header

            while True:
                nextNode = nextNode.nextSibling
                if nextNode is None:
                    break
                if isinstance(nextNode, NavigableString):
                    print(nextNode.strip())
                if isinstance(nextNode, Tag):
                    if nextNode.name == "h3":
                        break
                    print(nextNode.get_text(strip=True).strip())
                    abstract = (nextNode.get_text(strip=True).strip())
                    if cit not in abstract:
                        graph.add((URIRef(uri), jl.hasAbstract, Literal(abstract)))

graph.serialize(destination='bhr-new-enrich.rdf', format="turtle")
