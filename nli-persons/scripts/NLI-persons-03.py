#thos code extracts the authors from NLI dataset and creats an RDF file.
#04/01/2019

import urllib.request as urllib2
from bs4 import BeautifulSoup
import rdflib
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON , TURTLE
from rdflib.namespace import RDF, FOAF , OWL
import json
import os



graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace ("http://purl.org/dc/elements/1.1/")

graph.bind('skos', skos)
graph.bind ('foaf' , foaf)
graph.bind ('jl' , jl)
graph.bind('gndo',gndo)
graph.bind ('owl' , owl)
graph.bind('edm',edm)
graph.bind('dc',dc)

namelist=[]
namedic={}


with open('auth.json', encoding='utf8') as filehandle:
      for line in filehandle:
            record = json.loads(line)
            altlabel = []
            titlelist=[]
            namecount = 0

            if '100' in record.keys():

                #print (record['100'])
                for i in range (0, len(record['100'])):

                    if len(record['100']) > 1:
                        if record['100'][i]['9'][0] == 'lat':
                            preflabel = record['100'][i]['a'][0]
                            pref = preflabel.replace('.','')
                            pref = pref.replace('_','')

                    else:
                        preflabel = record['100'][i]['a'][0]
                        pref = preflabel.replace('.','')
                        pref = pref.replace('_','')

                    #print (preflabel)
                    uriname = preflabel.replace('\'','')
                    uriname = uriname.replace('"','')
                    uriname = uriname.replace(',','_')
                    uriname = uriname.replace('<<','')
                    uriname = uriname.replace('>>','')
                    uriname = uriname.replace('|','_')
                    uriname = uriname.replace(' ','')
                    uriname = uriname.replace('<','_')
                    uriname = uriname.replace('>','_')
                    uriname = uriname.replace('.','')


                    if 't' in record['100'][i].keys():
                       title = record['100'][i]['t'][0]
                       titlelist.append(title)

                    else: title = 'NA'


                    if 'd' in record['100'][i].keys():
                       date = record['100'][i]['d'][0]
                       if '-' in date:
                           bd = date.rsplit('-',1)[0]
                           dd = date.rsplit('-',1)[1]

                    else: date = 'NA'




                if uriname not in namedic.keys():
                    uri = 'http://data.judaicalink.org/data/nli/' + uriname
                    namedic[uriname] = date
                    #print (namedic)

                else:

                    if uriname in namedic.keys():

                            if date == namedic[uriname]:
                                uri = 'http://data.judaicalink.org/data/nli/' + uriname

                            elif date != namedic[uriname]:

                                namecount = namecount + 1
                                uriname = uriname + str(namecount)

                                if uriname in namedic.keys():

                                    if date == namedic[uriname]:
                                        uri = 'http://data.judaicalink.org/data/nli/' + uriname
                                    elif date != namedic[uriname]:

                                        namecount = namecount + 1
                                        uriname = uriname + str(namecount)
                                        uri = 'http://data.judaicalink.org/data/nli/' + uriname
                                        namedic[uriname] = date
                                        #print (namedic)

                                else:
                                    uri = 'http://data.judaicalink.org/data/nli/' + uriname
                                    namedic[uriname] = date
                                    #print (namedic)


                graph.add((URIRef(uri), RDF.type, foaf.Person ))

                if date != 'NA':

                    graph.add((URIRef(uri), jl.birthDate, (Literal(bd) )))
                    graph.add((URIRef(uri), jl.deathDate, (Literal(dd) )))

                for z in range (0,len(titlelist)):

                     graph.add((URIRef(uri), jl.hasTitle, (Literal(titlelist[z]) )))

                altlabel.append(record['100'][i]['a'][0])


                graph.add((URIRef(uri), skos.prefLabel, (Literal(pref) )))

                for j in range (0,len(altlabel)):
                    graph.add((URIRef(uri), skos.altLabel, (Literal(altlabel[j])) ))


graph.serialize(destination='nli-persons-03.ttl', format="turtle")
