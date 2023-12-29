"""
Generator for Footprints traces the history and movement of Jewish books since the inception of print. https://footprints.ctl.columbia.edu/
By Christian Deuschle, 2023.
cd060@hdm-stuttgart.de
# Licence of the data: CC-BY-SA 4.0
# https://creativecommons.org/licenses/by-sa/4.0/
"""

import requests
import json
import pprint
from bs4 import BeautifulSoup
import unicodedata
from rdflib.namespace import RDF
from datetime import datetime
from rdflib import Namespace, URIRef, Graph, Literal
import re
from edtf import parse_edtf
from tqdm import tqdm
import urllib.parse

file_name = 'footPrints-final-01.ttl'

graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace("http://purl.org/dc/elements/1.1/")
dcterms = Namespace("http://purl.org/dc/terms/")

graph.bind('skos', skos)
graph.bind('foaf', foaf)
graph.bind('jl', jl)
graph.bind('gndo', gndo)
graph.bind('owl', owl)
graph.bind('edm', edm)
graph.bind('dc', dc)


def clean_url_string(string):
    """
    Clean the name of a person.
    returns: cleaned name.
    """

    # remove all unwanted characters
    string = string.strip() # strip trailing whitespaces
    string = string.replace('\'', '')
    string = string.replace(' ', '')
    string = string.replace('`', '')
    string = string.replace('"', '')
    string = string.replace(',', '_')
    string = string.replace('<<', '')
    string = string.replace('>>', '')
    string = string.replace('|', '_')
    string = string.replace(' ', '')
    string = string.replace('<', '_')
    string = string.replace('>', '_')
    string = string.replace('.', '')
    string = string.replace('[', '')
    string = string.replace(']', '')
    string = string.replace('(', '')
    string = string.replace(')', '')
    string = string.replace('{', '')
    string = string.replace('}', '')
    string = string.replace('#', '')
    string = string.replace('-', '')
    string = string.replace('?', '')
    string = string.replace("'", "")
    string = string.replace("&", "_")

    # remove trailing _
    string = string.rstrip('_')

    # remove all diacritics
    string = unicodedata.normalize('NFKD', string)
    # convert to normalized url string
    string = urllib.parse.quote_plus(string, encoding='utf-8', errors='replace')
    print(string)
    return string


def contains_non_digits(s):
    return bool(re.search(r'\D', s))


def createGraph():
    page = 330
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    # url = f"https://footprints.ctl.columbia.edu/api/person/?format=json&page={page}"
    # while True:
    # for i in tqdm(range(#604)):
    while True:
        url = f"https://footprints.ctl.columbia.edu/api/person/?format=json&page={page}"
        if page % 10 == 0:
            print(page)
        response = requests.get(url, headers=headers)
        if response.text:
            #  print(response.text)
            data = json.loads(response.text)
            if 'results' in data:
                for date in data['results']:
                    # if date['id']:
                    if date['name'] and date['name'] is not None:
                        name = clean_url_string(str(date['name']))
                        # name = name.decode('utf-8')
                        if contains_non_digits(name) == True:
                            uri = URIRef(f"http://data.judaicalink.org/data/footprints/{name}")
                            graph.add((URIRef(uri), jl.describedAt, (Literal('https://footprints.ctl.columbia.edu/'))))
                            graph.add((URIRef(uri), RDF.type, foaf.Person))  # add name + id
                            graph.add((URIRef(uri), foaf.name, (Literal(name))))
                            graph.add((URIRef(uri), skos.prefLabel, (Literal(name))))
                            if 'birth_date' in date:
                                try:  # clean and add birthdate
                                    birth_date = date['birth_date']
                                    if birth_date is not None:
                                        # birth_date = dict(birth_date)
                                        # birth_date = parse_edtf(edtf_date_str)
                                        birth_date = birth_date['edtf_format']
                                        try:
                                            graph.add((URIRef(uri), jl.birthDate, (Literal(birth_date))))
                                        except:
                                            pass
                                except:
                                    print('ERROR2 Birthdate der ID: ', date['id'], name, 'ist vom Typ ',
                                          type(birth_date), birth_date)
                            if 'death_date' in date:
                                try:  # clean and add birthdate
                                    death_date = date['death_date']
                                    if death_date is not None:
                                        # birth_date = dict(birth_date)
                                        # birth_date = parse_edtf(edtf_date_str)
                                        death_date = death_date['edtf_format']
                                        try:
                                            graph.add((URIRef(uri), jl.deathDate, (Literal(death_date))))
                                        except:
                                            pass
                                except:
                                    print('ERROR2 Birthdate der ID: ', date['id'], name, 'ist vom Typ ',
                                          type(death_date), death_date)
                            if 'standardized_identifier' in date:
                                try:
                                    idf = date['standardized_identifier']
                                    if idf is not None:
                                        if idf['authority'] == "VIAF Identifier":
                                            idf = idf['identifier']
                                            idf = f'https://viaf.org/viaf/{idf}/'
                                            try:
                                                graph.add((URIRef(uri), owl.sameAs, (Literal(idf))))
                                            except:
                                                pass
                                        else:
                                            print('Seite:', idf, ', ', name, ', identifier = ', idf['authority'])
                                except:
                                    pass
                    graph.serialize(destination=file_name, format="turtle")
            # TODO get gndID from Viaf
            # TODO fix ivrit alphabet
            page += 1
        if "detail" in data and data["detail"] == "Invalid page.":
            print(f"last page loaded: page {page - 1}")
            break
    print('graph created')


createGraph()
