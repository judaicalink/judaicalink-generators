"""
Generator for Hamburger Schlüsseldokumente zur deutsch-jüdischen Geschichte. https://schluesseldokumente.net/person
By Christian Deuschle, 2023.
cd060@hdm-stuttgart.de
# Licence of the data: CC-BY-SA 4.0
# https://creativecommons.org/licenses/by-sa/4.0/
"""

# IMPORTS

# from http.client import _DataType
import requests
import json
import pprint
from bs4 import BeautifulSoup
import unicodedata
from rdflib.namespace import RDF, XSD
from datetime import datetime
from rdflib import Namespace, URIRef, Graph, Literal
from tqdm import tqdm
import googletrans
from googletrans import *

file_name = 'hhkeydocs-final-01.ttl'

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
            
def get_viaf_id(gnd_id: str) -> str:
    """
    Get the VIAF ID for a given GND ID.
    Args: gnd_id (str): GND ID of the entity.
    Returns: str: VIAF ID of the entity.
    """
    
    try:
        request = requests.get(
            "https://lobid.org/gnd/" + gnd_id + ".json"
        )
        request_json = request.json()
        #print(json.dumps(request_json, indent=4))
        for sameAs in request_json["sameAs"]:
            if sameAs["collection"]["abbr"] == "VIAF":
                #print("VIAF ID found for " + gnd_id + ".")
                viaf_id = sameAs["id"]
                return viaf_id
            
        #print("No VIAF ID found for " + gnd_id + ".")
        return None
    
    except:
        #print("No VIAF ID found for " + gnd_id + ".")
        return None
         
            
def get_gnd_id(name: str, type: str) -> str:
    """Get the GND ID for a given name and type.
    Args:
        name (str): Name of the entity.
        type (str): Type of the entity.
    Returns:
        str: GND ID of the entity.
    """
    try:
        request = requests.get(
            "https://lobid.org/gnd/search?q=" + name + "&filter=type:" + type + "&format=json"
        )
        request_json = request.json()
        #print(json.dumps(request_json, indent=4))
        gnd_id = request_json["member"][0]["gndIdentifier"]
        
        return gnd_id
    except:
        return None                    
            
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

def occupation_to_en(text):
    translator = googletrans.Translator()
    translation = translator.translate(text, dest='en')
    return translation.text

def create_graph():
    skos = Namespace("http://www.w3.org/2004/02/skos/core#")
    jl = Namespace("http://data.judaicalink.org/ontology/")
    foaf = Namespace("http://xmlns.com/foaf/0.1/")
    gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
    owl = Namespace("http://www.w3.org/2002/07/owl#")
    edm = Namespace("http://www.europeana.eu/schemas/edm/")
    dc = Namespace("http://purl.org/dc/elements/1.1/")
    dcterms = Namespace("http://purl.org/dc/terms/")
    geo = Namespace("http://www.opengis.net/ont/geosparql#")


    graph.bind('skos', skos)
    graph.bind('foaf', foaf)
    graph.bind('jl', jl)
    graph.bind('gndo', gndo)
    graph.bind('owl', owl)
    graph.bind('edm', edm)
    graph.bind('dc', dc)
    graph.bind('dcterms', dcterms)
    graph.bind('geo', geo)
    
# Places  
    place_uris = []
    for id in tqdm(place_ids):                                                      #get place-JSON
        place_url = f'https://schluesseldokumente.net{id}.jsonld'
        place_response = requests.get(place_url)
        if place_response.status_code == 200:
            if place_response.text:                                                           # test any if data is loaded
                try: 
                    data = json.loads(place_response.text)
                    clean_name = clean_url_string(data['name'])
                    clean_name = clean_name.decode('utf-8')
                    clean_name = clean_name
                    name = str(data['name'])
                    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')
                    name = name.decode('utf-8')
                    gndID = get_gnd_id(name, "PlaceOrGeographicName")  
                    uri = URIRef(f"http://data.judaicalink.org/data/hhkeydocs/{clean_name}")
                    if gndID is not None:      
                        graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(gndID))))
                    graph.add((URIRef(uri), jl.describedAt, (Literal(f"https://schluesseldokumente.net{id}.jsonld", datatype = XSD.anyURI))))
                    graph.add((URIRef(uri), RDF.type, gndo.PlaceOrGeographicName))   
                    graph.add((URIRef(uri), foaf.name, (Literal(name, datatype = XSD.string))))
                    graph.add((URIRef(uri), skos.prefLabel, (Literal(name, datatype = XSD.string))))
                    
                    try:
                        lat = data['geo']['latitude']
                        long = data['geo']['longitude']
                        longlat = f'"Point ( +{long} +{lat})' 
                        graph.add((URIRef(uri), geo.asWKT, (Literal(longlat))))  #  "Point ( +006.083333 +050.776388 )"
                    except:
                        pass
                    
                    graph.add((URIRef(uri), gndo.hierarchicalSuperiorOfPlaceOrGeographicName, (Literal(data['containedInPlace']['name']))))
                     
                except json.JSONDecodeError as e:
                    print(f"Fehler beim Laden von JSON: {e}")
            graph.serialize(destination=file_name, format="turtle")
        else:
            print('ERROR' + response2.status_code)  
    
            
# Persons    
    for id in tqdm(ids):
        gndId = id
       
        url2 = f'https://schluesseldokumente.net/person/gnd/{gndId}.jsonld'              # get JSON-files by by GND-ID from schluesseldokumente.net
        response2 = requests.get(url2)
        if response2.status_code == 200:
            if response2.text:                                                           # test any if data is loaded
                try: 
                    data = json.loads(response2.text)
                    clean_name = clean_url_string(data['name'])
                    clean_name = clean_name.decode('utf-8')
                    clean_name = str(clean_name)
                    name = str(data['name'])
                    name =unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')
                    name = name.decode('utf-8')
                    uri = URIRef(f"http://data.judaicalink.org/data/hhkeydocs/{clean_name}")                                                        
                    graph.add((URIRef(uri), RDF.type, foaf.Person))                       # add name + id
                    graph.add((URIRef(uri), jl.describedAt, (URIRef(f"https://schluesseldokumente.net/person/gnd/{gndId}.jsonld"))))
                    graph.add((URIRef(uri), foaf.name, (Literal(name, datatype = XSD.string)))) 
                    graph.add((URIRef(uri), skos.prefLabel, (Literal(name, datatype = XSD.string))))
                    graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(id))))
                    viaf = get_viaf_id(gndId)
                    if viaf is not None:
                        graph.add((URIRef(uri), owl.sameAs, (Literal(viaf, datatype = XSD.decimal))))
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
                        graph.add((URIRef(uri), jl.birthLocation, (Literal(birth_place_name, datatype = XSD.string))))
                        birth_place_name = clean_url_string(str(birth_place_name))
                        birth_place_name = birth_place_name.decode('utf-8')
                        birth_place_uri = URIRef(f"http://data.judaicalink.org/data/hhkeydocs/{birth_place_name}")
                        graph.add((URIRef(uri), jl.birthLocation, birth_place_uri))    
                    death_place_name = data.get('deathPlace', {}).get('name')
                    if death_place_name is not None:                                        #clean and add deathdate
                        graph.add((URIRef(uri), jl.deathLocation, (Literal(death_place_name, datatype = XSD.string))))  
                        death_place_name = clean_url_string(str(death_place_name))
                        death_place_name = death_place_name.decode('utf-8')
                        death_place_uri = URIRef(f"http://data.judaicalink.org/data/hhkeydocs/{death_place_name}")
                        graph.add((URIRef(uri), jl.deathLocation, death_place_uri))     
                    graph.add((URIRef(uri), dcterms.created, (Literal(datetime.now()))))
                    if 'description' in data:                                               #find and add occupations
                        description = data['description']
                        graph.add((URIRef(uri), jl.hasAbstract, (Literal(description))))
                        description = description.replace('.', '')
                        description = description.replace(',', '')
                        description = description.split(' ')
                        for d in description:
                            if d in professions:
                                dtrans = occupation_to_en(d)
                                graph.add((URIRef(uri), jl.occupation, (Literal(d))))     
                                graph.add((URIRef(uri), jl.occupation, (Literal(dtrans))))              
                except json.JSONDecodeError as e:
                    print(f"Fehler beim Laden von JSON: {e}")

            graph.serialize(destination=file_name, format="turtle")
        else:
            print('ERROR' + response2.status_code)

# Organisations
    for id in tqdm(org_ids):
        orgID = id
        org_url = f'https://schluesseldokumente.net/organisation/gnd/{orgID}.jsonld'             
        response3 = requests.get(org_url)
        if response3.status_code == 200:
            if response3.text:                                                          
                try: 
                    data = json.loads(response3.text)
                    clean_name = clean_url_string(data['name'])
                    clean_name = clean_name.decode('utf-8')
                    clean_name = str(clean_name)
                    name = str(data['name'])
                    name =unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')
                    name = name.decode('utf-8')
                    uri = URIRef(f"http://data.judaicalink.org/data/HHSdocs/{clean_name}")
                    graph.add((URIRef(uri), jl.describedAt, (URIRef(f"https://schluesseldokumente.net/organisation/gnd/{orgID}.jsonld"))))
                    graph.add((URIRef(uri), RDF.type, foaf.Organisation))               
                    graph.add((URIRef(uri), foaf.name, (Literal(name, datatype = XSD.string))))
                    graph.add((URIRef(uri), skos.prefLabel, (Literal(name, datatype = XSD.string))))
                    graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(orgID)))) 
                    if 'foundingDate' in data:
                        est = data['foundingDate']
                        graph.add((URIRef(uri), gndo.dateOfEstablishment, (Literal(est))))
                    if 'description' in data:                                              
                        description = data['description']
                        graph.add((URIRef(uri), jl.hasAbstract, (Literal(description, datatype = XSD.string))))
                    if 'url' in data:                                              
                        hp = data['url']
                        graph.add((URIRef(uri), foaf.homepage, (Literal(hp))))
                    if 'dissolutionDate' in data:                                              
                        dis = data['dissolutionDate']
                        graph.add((URIRef(uri), gndo.dateOfTermination, (Literal(dis))))
                    
                   

                
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
