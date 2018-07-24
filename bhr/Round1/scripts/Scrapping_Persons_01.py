#this code creates URL for BHR Encyc. perons based on their internal ids. Then scrapes each page to extract the GNDID and Name of the persons.

import urllib2
from bs4 import BeautifulSoup
import rdflib
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON
from rdflib.namespace import RDF, FOAF , OWL
import os , glob
import csv
import re

os.chdir('C:\Users\Maral\Desktop')

output = open('BHR-ID.csv','w')

output.writelines([str('Name'),',',str('ID'),',',str('GND'),'\n'])



for i in range (1 , 2704):

    url = 'http://www.steinheim-institut.de:50580/cgi-bin/bhr?id=' + str(i)

    print url

    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page)

    h1 = soup.find_all('h1')
    name = h1[1].string
    if name!= None:
        name = name.replace(',',' -')
        name = name.encode('utf-8')


    print h1[1]

    for link in soup.find_all('a'):
        if 'gnd' in link.get('href'):
            gnd = link.get('href')
            print gnd
        else:
            gnd = 'NA'

    output.writelines([str(name),',',str(i),',',str(gnd),'\n'])


output.close()




