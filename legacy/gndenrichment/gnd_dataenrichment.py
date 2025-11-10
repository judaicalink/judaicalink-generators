#IMPORTS
import requests
import json
# import unicodedata
from rdflib.namespace import RDF, XSD
from datetime import datetime
from rdflib import Namespace, URIRef, Graph, Literal
from rdflib.term import Node
import re
from edtf import parse_edtf
from tqdm import tqdm
# import urllib.parse
import langid
import googletrans
from googletrans import *
import uuid
import hashlib
# import threading
# import time
import gzip
import shutil
import os


from bs4 import BeautifulSoup
import requests


def get_name_from_gndid(gndid):
    """
    Get a name or naming for an entity from a given GND-ID via lobid.org
        Params: 
            gndid str or int: Id for the given entity
        Returns:
            str: name or naming for the entity
    """
    
    headers = {'Accept': 'html'} 

# url = f'https://lobid.org/gnd/{gndid}'
    url = f'https://d-nb.info/gnd/{gndid}'

    response = requests.get(url, headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        yellow_cells = soup.find_all('td', class_='yellow')
        
        if len(yellow_cells) >= 2:
            second_yellow_cell = yellow_cells[1]
            entitynameing = second_yellow_cell.text.strip()
            return entitynameing
        else:
            print("Element not found")

    else:
        print('ERROR: ', response.status_code)
def get_gnd_ttl_data(gndid, uri, graph):
    """ 
    enriches data with data from gnd if gnd id is known
    Params: 
        gndid (str or int): ID for GND (Gemeinsame Normdatei)
        uri (str): the uri of the entity to wich the gndid belongs
        graph (class): graph in wich creation the function  is called

    Return: 
        dictionary for dataenrichment from gnd ({predicate : object})
        
        to add information to graph use: 
        
        ``` 
        for pair in get_gnd_ttl_data(idgndraw, uri, graph):
            prefix, predicate_name = pair[0].split(".")
            predicate_uri = URIRef(f"{prefix}.{predicate_name}")
            graph.add((URIRef(uri), predicate_uri, Literal(pair[1])))
        ```
        

    """
    pr_obj = []
    print('get_gnd_ttl_data aufgerufen')
    headers = {'Accept': 'text/turtle'} 
    gnd_url = f'http://d-nb.info/gnd/{gndid}/about/lds'
    response = requests.get(gnd_url, headers=headers)    
    if response.status_code == 200:
        # Parse the Turtle data
        g = Graph()
        g.parse(data=response.text, format='turtle')

    # Iterate over triples and add them to the graph
    for s, p, o in g:
       # s = str(s)
        #print('s: ', s)
       # print('---------------------')
        p = str(p)
        o = str(o)
        if p.startswith('https://d-nb.info/standards/elementset/gnd#'):
            p = p.replace('https://d-nb.info/standards/elementset/gnd#', 'gndo.')
            if o.startswith('https://d-nb.info/gnd/'):
                oid = o.replace('https://d-nb.info/gnd/', '')
                o = get_name_from_gndid(oid)
            pr_obj.append([p,o])        
        if p.startswith('http://www.w3.org/2002/07/owl#'):
            p = p.replace('http://www.w3.org/2002/07/owl#', 'owl.')
            pr_obj.append([p,o])
    return pr_obj
def zip_file(file_path):
    """
    Zips file
    :param str file_path: path to file to be zipped
    :return: zipped file 
    :rtype: .gz file

    """
    if not os.path.exists(file_path):
        print(f'file "{file_path}" does not exist.')
        return
    gz_file_path = file_path + ".gz"
    with open(file_path, 'rb') as f_in, gzip.open(gz_file_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    
    print(f"Zipping {gz_file_path} succeeded.")
def generate_hashUU(name):
    """
    Generate a uuID out of the hash-value of a name or prefered label
    :param str name: name or prefered label of the entity from which the ID should be generated
    :return: the uuID
    :rtype: str
    """
# Hash the string using a hashing algorithm (e.g., SHA-256)
    hashed_string = hashlib.sha256(name.encode()).hexdigest()
    # Generate a UUID based on the hashed string
    uuid_from_hash = uuid.uuid5(uuid.NAMESPACE_OID, hashed_string)
    return uuid_from_hash
file_name = 'test_gnd_enriched.ttl'

graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace("http://purl.org/dc/elements/1.1/")
dcterms = Namespace("http://purl.org/dc/terms/")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
geo = Namespace("http://www.opengis.net/ont/geosparql#")

graph.bind('skos', skos)
graph.bind('foaf', foaf)
graph.bind('jl', jl)
graph.bind('gndo', gndo)
graph.bind('owl', owl)
graph.bind('edm', edm)
graph.bind('dc', dc)
graph.bind('dcterms', dcterms)
graph.bind('rdfs', rdfs)
graph.bind('geo', geo)
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
        gnd_id = request_json["member"][0]["gndIdentifier"]  
        return gnd_id
    except:
        return None  
def hebrew_name_recogition(h_string):
    """
    recognices if a string is written in hebrew letters
    :param str h_string: string to be analyzed
    :return: True if h_string is in hebrew
    :rtype: bool
    """
    lang, confidence = langid.classify(h_string)
    return lang == 'he'

'''
def he_to_en(text):  # does not work propper with familynames yet
    """
    translates hebrew text to english
    :param str text: text to be translated
    :return: translated text
    :rtype: text
    
    """
    translator = googletrans.Translator()
    translation = translator.translate(text, dest='en')
    return translation.text
'''
def text_to_en(text, page):
    """
    translates given text to english
    :param str text: text to be translated
    :param int page: processed page for error messages
    :return: translated text
    :rtype: str
    
    """
    translator = googletrans.Translator()
    try:
        translation = translator.translate(text, dest='en')
        return translation.text
    except Exception as e:
        print(e, 'bei: ', text, ' -- auf Seite: ', page)
def clean_hebrew_name(name):
    """
    Removes leading and suffixed whitespaces and dots from a string
    :param str name: name to be cleaned
    :return: cleaned string
    :rtype: str
    """
    name = name.strip()
    name = name.replace('.', '')
    return name
def contains_non_digits(s):
    """
    Checks if a string contains non-digit characters
    :param str s: string to be analyzed
    :return: True if s contains characters, that are not digits
    :rtype: bool
    """
    return bool(re.search(r'\D', s))
def get_gnd_from_viaf(viafid):
    """"
    Takes a VIAF id and returns GND id embedded in an uri
    :param str or int viafid: String or Integer thet represents a VIAF id
    :return: uri for the GND id that represents the smae entity
    :rtype: str
    """
    url = f'https://www.viaf.org/viaf/{viafid}/viaf.jsonld'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "@graph" in data:
            for entry in data["@graph"]:
                if "@type" in entry and entry["@type"] == "schema:Person":
                    if "sameAs" in entry:
                        for s in entry["sameAs"]:
                            if s.startswith('http://d-nb.info/gnd') == True:
                                gnd=s
    try:
        return gnd
    except Exception as e:
        print(e, 'for VIAF id: ', viafid)
    
 
   

def add_creation_date(graph, uri):
    """"
    Checks if a creation date for an uri already exists and if not creates one
    :param str graph: graph that is processed
    :param str uri: uri that is processed
    :return: adds dcterms.created - datetime.now to graph
    :rtype: str
    """
    if (URIRef(uri), dcterms.created, None) not in graph:
        graph.add((URIRef(uri), dcterms.created, Literal(datetime.now())))  # onnly add creatioon date if it doesnt exist yet


'''
# Initialisiere die Zeitmessung
counted_time = 0

# Starte den Thread für die Zeitmessung
time_thread = threading.Thread(target=track_time)
time_thread.start()
'''
def createGraph():
    """
    Creates Graph from scraped information from the footprints-api for 'person': 'https://footprints.ctl.columbia.edu/api/person/', 'book': 'https://footprints.ctl.columbia.edu/api/book/' and 'place': 'https://footprints.ctl.columbia.edu/api/place/'
    :return: creates .ttl-file
    :rtype: ttl
    
    """
    b_page = 31
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}    # simulate a browser request
#get person from persons
    
    url = f"https://footprints.ctl.columbia.edu/api/book/?page={b_page}" # "book": "https://footprints.ctl.columbia.edu/api/book/"
    response = requests.get(url, headers=headers)
    if b_page % 10 == 0:
        print('books: page ', b_page)   # print an indication of which 10 pages are currently being processed
    if response.text:
        data = json.loads(response.text)    # load data
        if 'results' in data:
            for date in data['results']: # process every record of the page
                # get person (actor) from books            
                if date['imprint']['work']['title']:
                    for actor in date['imprint']['work']['actor']:
                        name = actor['person']['name']
                        name = name.strip()
                        uu= generate_hashUU(name)
                        uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}")
                        graph.add((URIRef(uri), RDF.type, foaf.Person))
                        if hebrew_name_recogition(name) == True:
                            name = clean_hebrew_name(name)
                        graph.add((URIRef(uri), foaf.name, (Literal(name))))
                        graph.add((URIRef(uri), skos.prefLabel, (Literal(name))))
                        if actor['person']['birth_date'] is not None:
                            actor_bd = actor['person']['birth_date']
                            try:
                                graph.add((URIRef(uri), jl.deathDate, (Literal(actor_bd))))
                            except Exception as e:
                                print(e, ' in birthdate of ', name, ' on Persons page', b_page)
                        if actor['person']['death_date'] is not None:
                            actor_dd = actor['person']['death_date']
                            try:
                                graph.add((URIRef(uri), jl.deathDate, (Literal(actor_dd))))
                            except Exception as e:
                                print(e, ' in deathdate of ', name, ' on Persons page', b_page)
                        if 'standardized_identifier' in actor['person'] and actor['person']['standardized_identifier'] is not None:
                            if 'identifier' in actor['person']['standardized_identifier'] and actor['person']['standardized_identifier']['identifier'] is not None:
                                sID = actor['person']['standardized_identifier']['identifier']
                                if 'authority' in actor['person']['standardized_identifier'] and actor['person']['standardized_identifier']['authority'].strip() == 'VIAF Identifier':
                                    idgnd =  get_gnd_from_viaf(sID)
                                    if idgnd and idgnd is not None:
                                        idgndraw = idgnd.replace('http://d-nb.info/gnd/', '')
                                        print(idgnd)
                                        for pair in get_gnd_ttl_data(idgndraw, uri, graph):
                                            print(f'pair: {pair} uri:{uri}')
                                            # Beispiel für das Prädikat im String-Format
                                            # Extrahiere den Präfix und den Prädikatsnamen
                                            obj = pair[1]
                                            prefix, predicate_name = pair[0].split(".")
                                            # Erstelle eine URIRef mit dem vollen Prädikats-URI
                                            #predicate_uri = URIRef(f"{prefix}.{predicate_name}")
                                            predicate_uri = f"{prefix}.{predicate_name}"
                                            if obj.startswith('http'):
                                                obj = URIRef(obj)
                                                graph.add(((URIRef(uri), (prefix, predicate_name) , obj)))
                                            else:
                                                graph.add(((uri), (prefix, predicate_name) , Literal(obj)))
                                    idurl = f'https://viaf.org/viaf/{sID}/'
                                    graph.add((URIRef(uri), jl.describedAt, (Literal(idurl))))
                                    graph.add((URIRef(uri), jl.describedAt, (Literal(idgnd))))
                                elif 'authority' in actor['person']['standardized_identifier'] and actor['person']['standardized_identifier']['authority'].strip() == "Library of Congress":
                                    sID = sID.replace('LOC ', '')
                                    sID =      f'https://id.loc.gov/authorities/names/{sID}'
                                    graph.add((URIRef(uri), owl.sameAs, (Literal(sID))))
                                else:
                                    print(name, 'on Page: ', b_page, 'has: ', actor['person']['standardized_identifier']['authority'], 'as identifier.')
                        role =  actor['role']['name']
                        graph.add((URIRef(uri), jl.occupation, (Literal(role)))) # add role in context with book as occupation
                        add_creation_date(graph, uri)
                        graph.serialize(destination=file_name, format="turtle")
            

   


    
    print('graph created')
createGraph()

zip_file(file_name)
file_name = 'test_NOT_gnd_enriched.ttl'

graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace("http://purl.org/dc/elements/1.1/")
dcterms = Namespace("http://purl.org/dc/terms/")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
geo = Namespace("http://www.opengis.net/ont/geosparql#")

graph.bind('skos', skos)
graph.bind('foaf', foaf)
graph.bind('jl', jl)
graph.bind('gndo', gndo)
graph.bind('owl', owl)
graph.bind('edm', edm)
graph.bind('dc', dc)
graph.bind('dcterms', dcterms)
graph.bind('rdfs', rdfs)
graph.bind('geo', geo)
def createGraphII():
    """
    Creates Graph from scraped information from the footprints-api for 'person': 'https://footprints.ctl.columbia.edu/api/person/', 'book': 'https://footprints.ctl.columbia.edu/api/book/' and 'place': 'https://footprints.ctl.columbia.edu/api/place/'
    :return: creates .ttl-file
    :rtype: ttl
    
    """
    b_page = 31
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}    # simulate a browser request
#get person from persons
    
    url = f"https://footprints.ctl.columbia.edu/api/book/?page={b_page}" # "book": "https://footprints.ctl.columbia.edu/api/book/"
    response = requests.get(url, headers=headers)
    if b_page % 10 == 0:
        print('books: page ', b_page)   # print an indication of which 10 pages are currently being processed
    if response.text:
        data = json.loads(response.text)    # load data
        if 'results' in data:
            for date in data['results']: # process every record of the page
                # get person (actor) from books            
                if date['imprint']['work']['title']:
                    for actor in date['imprint']['work']['actor']:
                        name = actor['person']['name']
                        name = name.strip()
                        uu= generate_hashUU(name)
                        uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}")
                        graph.add((URIRef(uri), RDF.type, foaf.Person))
                        if hebrew_name_recogition(name) == True:
                            name = clean_hebrew_name(name)
                        graph.add((URIRef(uri), foaf.name, (Literal(name))))
                        graph.add((URIRef(uri), skos.prefLabel, (Literal(name))))
                        if actor['person']['birth_date'] is not None:
                            actor_bd = actor['person']['birth_date']
                            try:
                                graph.add((URIRef(uri), jl.deathDate, (Literal(actor_bd))))
                            except Exception as e:
                                print(e, ' in birthdate of ', name, ' on Persons page', b_page)
                        if actor['person']['death_date'] is not None:
                            actor_dd = actor['person']['death_date']
                            try:
                                graph.add((URIRef(uri), jl.deathDate, (Literal(actor_dd))))
                            except Exception as e:
                                print(e, ' in deathdate of ', name, ' on Persons page', b_page)
                        if 'standardized_identifier' in actor['person'] and actor['person']['standardized_identifier'] is not None:
                            if 'identifier' in actor['person']['standardized_identifier'] and actor['person']['standardized_identifier']['identifier'] is not None:
                                sID = actor['person']['standardized_identifier']['identifier']
                                if 'authority' in actor['person']['standardized_identifier'] and actor['person']['standardized_identifier']['authority'].strip() == 'VIAF Identifier':
                                    idgnd =  get_gnd_from_viaf(sID)
                                    if idgnd and idgnd is not None:
                                        idgndraw = idgnd.replace('http://d-nb.info/gnd/', '')
                                        print(idgnd)
                                    idurl = f'https://viaf.org/viaf/{sID}/'
                                    graph.add((URIRef(uri), jl.describedAt, (Literal(idurl))))
                                    graph.add((URIRef(uri), jl.describedAt, (Literal(idgnd))))
                                elif 'authority' in actor['person']['standardized_identifier'] and actor['person']['standardized_identifier']['authority'].strip() == "Library of Congress":
                                    sID = sID.replace('LOC ', '')
                                    sID =      f'https://id.loc.gov/authorities/names/{sID}'
                                    graph.add((URIRef(uri), owl.sameAs, (Literal(sID))))
                                else:
                                    print(name, 'on Page: ', b_page, 'has: ', actor['person']['standardized_identifier']['authority'], 'as identifier.')
                        role =  actor['role']['name']
                        graph.add((URIRef(uri), jl.occupation, (Literal(role)))) # add role in context with book as occupation
                        add_creation_date(graph, uri)
                        graph.serialize(destination=file_name, format="turtle")
            

   


    
    print('graph created')


createGraphII()

zip_file(file_name)



