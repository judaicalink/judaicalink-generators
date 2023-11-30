"""
Generator for Hamburger Schlüsseldokumente zur deutsch-jüdischen Geschichte. https://schluesseldokumente.net/person
By Christian Deuschle, 2023.
cd060@hdm-stuttgart.de
# Licence of the data: CC-BY-SA 4.0
# https://creativecommons.org/licenses/by-sa/4.0/
"""

# IMPORTS

import requests
import json
import pprint
from bs4 import BeautifulSoup
import unicodedata
from rdflib.namespace import RDF
from datetime import datetime
from rdflib import Namespace, URIRef, Graph, Literal
from tqdm import tqdm

file_name = 'HHKeyDocs-final-01.ttl'

graph = Graph()

#get GND IDs from schluesseldokumente.net

ids = []

def get_ids(url):
    response1 = requests.get(url)
    soup = BeautifulSoup(response1.content, 'html.parser')
    soup = str(soup)
    soup = soup.split('\n')
    # ids = soup[4:]
    for id in soup:
        try:
            id = int(id)
            ids.append(id)
        except:
            pass
            
            
            
place_ids = []

def get_place_ids(url):
    html = requests.get(url)
    soup = BeautifulSoup(html.content, 'html.parser')
    list_items = soup.select('.list-unstyled li a')
    if list_items:
        for item in list_items:
            place_ids.append(item.get('href'))
    else:
        print("ERROR: no links found")

#get GND IDs of Organisations from schluesseldokumente.net

org_ids = []

def get_org_ids(url):
    response1 = requests.get(url)
    soup = BeautifulSoup(response1.content, 'html.parser')
    soup = str(soup)
    soup = soup.split('\n')
    # ids = soup[4:]
    for id in soup:
        try:
            id = int(id)
            org_ids.append(id)
        except:
            pass


def clean_url_string(string):
    """
    Clean the name of a person.
    returns: cleaned name.
    """

    string = string.strip()
    string = string.replace('\'', '')
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

    string =  unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')
    return string


# Create list of professions

professions = []

def get_professions_from_WD():
    sparql_query = """
    SELECT ?profession ?professionLabel
    WHERE {
      ?profession wdt:P31 wd:Q28640;
                 rdfs:label ?professionLabel.
    
      FILTER(LANG(?professionLabel) = "de")
    }
    ORDER BY ?professionLabel
    """
    
    url = "https://query.wikidata.org/sparql"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
        "Accept": "application/json",
    }
    params = {"query": sparql_query, "format": "json"}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    newitems = ['Talmud-Gelehrter', ]
    
    for item in data["results"]["bindings"]:
        professions.append(item["professionLabel"]["value"])
        professions.append(newitems)

def create_graph():
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
    
    
    place_uris = []
    for id in tqdm(place_ids):                                                      #get place-JSON
        place_url = f'https://schluesseldokumente.net{id}.jsonld'
        place_response = requests.get(place_url)
        if place_response.status_code == 200:
            if place_response.text:                                                           # test any if data is loaded
                try: 
                    data = json.loads(place_response.text)
                    name = clean_url_string(data['name'])
                    name = name.decode('utf-8')
                    name = str(name)
                    uri = URIRef(f"http://data.judaicalink.org/data/HHSdocs/{name}")
                    place_uris.append(uri)
                    graph.add((URIRef(uri), jl.describedAt, (Literal(f"https://schluesseldokumente.net/{id}"))))
                    graph.add((URIRef(uri), RDF.type, gndo.PlaceOrGeographicName))   #??? RICHTIG???
                    graph.add((URIRef(uri), foaf.name, (Literal(name))))
                    graph.add((URIRef(uri), skos.prefLabel, (Literal(name))))
                    try:
                        graph.add((URIRef(uri), jl.lat, (Literal(data['geo']['latitude']))))
                    except:
                    	pass
                    try:
                        graph.add((URIRef(uri), jl.lon, (Literal(data['geo']['longitude']))))
                    except:
                    	pass
                    graph.add((URIRef(uri), gndo.hierarchicalSuperiorOfPlaceOrGeographicName, (Literal(data['containedInPlace']['name']))))
                    
                    #TODO Skript for GND ID
    
                except json.JSONDecodeError as e:
                    print(f"Fehler beim Laden von JSON: {e}")
            graph.serialize(destination=file_name, format="turtle")
        else:
            print('ERROR' + response2.status_code)  
    
    
  
    for id in tqdm(ids):
        gndId = id
       
        url2 = f'https://schluesseldokumente.net/person/gnd/{gndId}.jsonld'              # get JSON-files by by GND-ID from schluesseldokumente.net
        response2 = requests.get(url2)
        if response2.status_code == 200:
            if response2.text:                                                           # test any if data is loaded
                try: 
                    data = json.loads(response2.text)
                    name = clean_url_string(data['name'])
                    name = name.decode('utf-8')
                    name = str(name)
                    uri = URIRef(f"http://data.judaicalink.org/data/HHSdocs/{name}")
                                                                                    
                    graph.add((URIRef(uri), RDF.type, foaf.Person))                       # add name + id
                    graph.add((URIRef(uri), jl.describedAt, (Literal(f"https://schluesseldokumente.net/person/gnd/{gndId}"))))
                    graph.add((URIRef(uri), foaf.name, (Literal(name))))
                    graph.add((URIRef(uri), skos.prefLabel, (Literal(name))))
                    graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(id))))
                    if 'birthDate' in data:
                        try:                                                              #clean and add birthdate
                            birth_date = data['birthDate']
                            if birth_date is not None:
                                birth_date = str(birth_date)
                                try:
                                    birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                                except:
                                    pass 
                                graph.add((URIRef(uri), jl.birthDate, (Literal(birth_date)))) 
                            else:
                                print(countterId, 'ERROR1 Birthdate der ID: ', id, name, 'ist vom Typ ', type(birth_date),birth_date)
                        except:
                            print(countterId, 'ERROR2 Birthdate der ID: ', id, name, 'ist vom Typ ', type(birth_date),birth_date)
                    if 'deathDate' in data:                                                 #clean and add deathdate
                        try:
                            death_date = data['deathDate']
                            if death_date is not None:
                                death_date = str(death_date)
                                try:
                                    death_date = datetime.strptime(death_date, '%Y-%m-%d').date()
                                except:
                                    pass
                                graph.add((URIRef(uri), jl.deathDate, (Literal(death_date))))
                            else:
                                print(countterId, 'ERROR1 Deathdate der ID: ', id, name, 'ist vom Typ ', type(death_date),death_date)
                        except:
                            print(countterId, 'ERROR2 Deathdate der ID: ', id, name, 'ist vom Typ ', type(death_date),death_date)
                    birth_place_name = data.get('birthPlace', {}).get('name')
                    if birth_place_name is not None:                                       #clean and add birthplace
                        graph.add((URIRef(uri), jl.birthLocation, (Literal(birth_place_name))))
                    death_place_name = data.get('deathPlace', {}).get('name')
                    #if data['deathPlace']['name']:
                    if death_place_name is not None:                                        #clean and add deathdate
                        graph.add((URIRef(uri), jl.deathLocation, (Literal(death_place_name))))     
                    graph.add((URIRef(uri), dcterms.created, (Literal(datetime.now()))))
                    if 'description' in data:                                               #find and add occupations
                        description = data['description']
                        graph.add((URIRef(uri), jl.hasAbstract, (Literal(description))))
                        description = description.replace('.', '')
                        description = description.replace(',', '')
                        description = description.split(' ')
                        for d in description:
                            if d in professions:
                                graph.add((URIRef(uri), jl.occupation, (Literal(d))))                 
                except json.JSONDecodeError as e:
                    print(f"Fehler beim Laden von JSON: {e}")

            graph.serialize(destination=file_name, format="turtle")
        else:
            print('ERROR' + response2.status_code)

    for id in tqdm(org_ids):
        orgID = id
       # countterId += 1
        org_url = f'https://schluesseldokumente.net/organisation/gnd/{orgID}.jsonld'             
        response3 = requests.get(org_url)
        if response3.status_code == 200:
            if response3.text:                                                          
                try: 
                    data = json.loads(response3.text)
                    name = clean_url_string(data['name'])
                    name = name.decode('utf-8')
                    name = str(name)
                    uri = URIRef(f"http://data.judaicalink.org/data/HHSdocs/{name}")
                    graph.add((URIRef(uri), jl.describedAt, (Literal(f"https://schluesseldokumente.net/organisation/gnd/{orgID}"))))
                    graph.add((URIRef(uri), RDF.type, foaf.Organisation))                #??? RICHTIG???
                    graph.add((URIRef(uri), foaf.name, (Literal(name))))
                    graph.add((URIRef(uri), skos.prefLabel, (Literal(name))))
                    graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(orgID))))
                    if 'description' in data:                                              
                        description = data['description']
                        graph.add((URIRef(uri), jl.hasAbstract, (Literal(description)))) 
                        
 # TODO What happens with foundingDate
                
                except json.JSONDecodeError as e:
                    print(f"Fehler beim Laden von JSON: {e}")
            graph.serialize(destination=file_name, format="turtle")
        else:
            print('ERROR' + response2.status_code)  

    print('graph created')
    
get_place_ids('https://schluesseldokumente.net/ort')
get_ids('https://schluesseldokumente.net/person/gnd/beacon')
get_org_ids('https://schluesseldokumente.net/organisation/gnd/beacon')
get_professions_from_WD()
create_graph()
