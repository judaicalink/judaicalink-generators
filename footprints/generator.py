"""
Generator for Footprints traces the history and movement of Jewish books since the inception of print. https://footprints.ctl.columbia.edu/
By Christian Deuschle, 2023.
cd060@hdm-stuttgart.de
# Licence of the data: CC-BY-SA 4.0
# https://creativecommons.org/licenses/by-sa/4.0/
"""

import requests
import json
# import unicodedata
from rdflib.namespace import RDF, XSD
from datetime import datetime
from rdflib import Namespace, URIRef, Graph, Literal
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

'''
def track_time():
    global counted_time
    while True:
        time.sleep(60)
        counted_time += 1
        print(f"Zeit seit Beginn: {counted_time} Minuten")
'''



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


file_name = 'footprints.ttl'

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
    p_page = 1
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}    # simulate a browser request
#get person from persons
    while True:
        url = f"https://footprints.ctl.columbia.edu/api/person/?format=json&page={p_page}"  # call the pages of 'person': 'https://footprints.ctl.columbia.edu/api/person/'
        if p_page % 10 == 0:
            print('Persons Page: ',p_page)  # print an indication of which 10 pages are currently being processed
        response = requests.get(url, headers=headers)
        if response.text:
            data = json.loads(response.text)    # load data
            if 'results' in data:
                for date in data['results']:    # process every record of the page
                    if date['name'] and date['name'] is not None:   # get persons name and id
                        name = date['name']
                        fID = date['id']
                        if contains_non_digits(name) == True:   # skip especially one record, that has its own id as a name TODO get name from VIAF
                            name = name.strip()
                            uu= generate_hashUU(name)

                            uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}") # create uri with UUid 
                            graph.add((URIRef(uri), jl.describedAt, (Literal(f'https://footprints.ctl.columbia.edu/api/person/{fID}'))))
                            graph.add((URIRef(uri), RDF.type, foaf.Person))  # add name + id
                            if hebrew_name_recogition(name) == True:
                                name = clean_hebrew_name(name)
                            graph.add((URIRef(uri), foaf.name, (Literal(name))))
                            graph.add((URIRef(uri), skos.prefLabel, (Literal(name))))
                            if 'birth_date' in date:
                                try:  # clean and add birthdate
                                    birth_date = date['birth_date']
                                    if birth_date is not None:
                                        birth_date = birth_date['edtf_format']
                                        try:
                                            graph.add((URIRef(uri), jl.birthDate, (Literal(birth_date))))
                                        except Exception as e:
                                            print(e, ' in birthdate of ', name, ' on Persons page', p_page)
                                except:
                                    print('ERROR2 Birthdate der ID: ', date['id'], name, 'ist vom Typ ',
                                          type(birth_date), birth_date)
                            if 'death_date' in date:
                                try:  # clean and add birthdate
                                    death_date = date['death_date']
                                    if death_date is not None:
                                        death_date = death_date['edtf_format']
                                        try:
                                            graph.add((URIRef(uri), jl.deathDate, (Literal(death_date))))
                                        except Exception as e:
                                            print(e, ' in deathdate of ', name, ' on Persons page', p_page)
                                except:
                                    print('ERROR2 Birthdate der ID: ', date['id'], name, 'ist vom Typ ',
                                          type(death_date), death_date)
                            if 'standardized_identifier' in date:
                                try:
                                    idf = date['standardized_identifier']
                                    if idf is not None:
                                        if idf['authority'].strip() == "VIAF Identifier": # add sameAs identifiers for GND, LOC and VIAF
                                            idf = idf['identifier']
                                            idgnd =  get_gnd_from_viaf(idf)
                                            idf = f'https://viaf.org/viaf/{idf}/'  
                                            graph.add((URIRef(uri), owl.sameAs, (Literal(idf)))) #VIAF
                                            graph.add((URIRef(uri), owl.sameAs, (Literal(idgnd)))) # GND

                                        elif idf['authority'].strip() == "Library of Congress": # LOC
                                            idf = idf['identifier']
                                            idf = idf.replace('LOC ', '')
                                            idf =      f'https://id.loc.gov/authorities/names/n{idf}'
                                            graph.add((URIRef(uri), owl.sameAs, (Literal(idf))))


                                        else:
                                            print('Seite:', idf, ', ', name, ', identifier = ', idf['authority'])
                                except Exception as e:
                                    print(e, 'auf Seite: ', p_page)

                              #  finally: 
                              #      add_creation_date(graph, uri)         
                              #      graph.serialize(destination=file_name, format="turtle")

                                    
                            add_creation_date(graph, uri)         
                    graph.serialize(destination=file_name, format="turtle")
            p_page += 1 # process next site
        if "detail" in data and data["detail"] == "Invalid page.": # stop if data corpus is processed
            print(f"last page loaded: page {p_page - 1}")
            break

    b_page = 1
    '''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    '''
    while True:
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
                            
# get books from books
                        wtitle = date['imprint']['work']['title']
                        wtitle = wtitle.strip()
                        uu= generate_hashUU(wtitle)
                        uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}")
                        graph.add((URIRef(uri), RDF.type, gndo.Work))
                        graph.add((URIRef(uri), dc.title, (Literal(wtitle))))
                        graph.add((URIRef(uri), skos.prefLabel, (Literal(wtitle))))
                        for actor in date['imprint']['work']['actor']:
                            act = actor['person']['name']
                            act = act.strip()
                            uu= generate_hashUU(act) 
                            a = f'http://data.judaicalink.org/data/footprints/{uu}'
                            arole = actor['role']['name']
                            if arole == 'Author':
                                graph.add((URIRef(uri), gndo.author, (Literal(a))))
                        wnotes =  date['imprint']['work']['notes']
                        if wnotes is not None:
                            wnotes = wnotes.replace('"', '')
                            wnotes = wnotes.replace('"', '')
                            wnotes = wnotes.replace('"', '')
                            wnotes = wnotes.replace('\n', ' ')
                            graph.add((URIRef(uri), jl.hasAbstract, (Literal(wnotes))))
                        for lang in date['imprint']['language']:
                            language = lang['name']
                            graph.add((URIRef(uri), gndo.language, (Literal(language))))

                        if 'imprint' in date and date['imprint'].get('place') is not None and date['imprint']['place'] is not None:
                            place = date['imprint']['place']
                            if 'display_title' in place and place['display_title'] is not None:
                                wholeplace = date['imprint']['place']['display_title']
                                place = wholeplace.split(',')
                                wplace = place[0]
                                transl_place = text_to_en(wplace, b_page)
                                graph.add((URIRef(uri), gndo.associatedPlace, (Literal(wplace))))
                                graph.add((URIRef(uri), gndo.associatedPlace, (Literal(transl_place))))
                        if 'imprint' in date and date['imprint'].get('publication_date') is not None and date['imprint']['publication_date'] is not None:
                            pdate = date['imprint']['publication_date']
                            if 'display' in pdate and pdate['display'] is not None:
                                wpubdate = date['imprint']['publication_date']['display']
                                graph.add((URIRef(uri), gndo.dateOfPublication, (Literal(wpubdate))))
                        for actor in date['imprint']['actor']:
                            name = actor['person']['name']
                            name = name.strip()
                            uu= generate_hashUU(name)
                            a = f'http://data.judaicalink.org/data/footprints/{uu}'
                            arole = actor['role']['name']
                            if arole == 'Publisher':
                                graph.add((URIRef(uri), dc.publisher, (Literal(a))))
                            elif arole == 'Author':
                                graph.add((URIRef(uri), gndo.author, (Literal(a))))
                            elif arole == 'Editor':
                                graph.add((URIRef(uri), gndo.ditor, (Literal(a))))
                            elif arole == 'Expurgator':
                                graph.add((URIRef(uri), gndo.editor, (Literal(a))))
                            elif arole == 'Printer':
                                graph.add((URIRef(uri), gndo.printer, (Literal(a))))
                            elif arole == 'Approbator':
                                graph.add((URIRef(uri), dc.contributor, (Literal(a))))
                            elif arole == 'Compiler':
                                graph.add((URIRef(uri), gndo.compiler, (Literal(a))))
                            elif arole == 'Translator':
                                graph.add((URIRef(uri), gndo.translator, (Literal(a))))
                            elif arole == 'Patron':
                                graph.add((URIRef(uri), gndo.sponsorOrPatron, (Literal(a))))
                            elif arole == 'Dedicatee':
                                graph.add((URIRef(uri), gndo.dedicatee, (Literal(a))))  
                            else:
                                print(act, ': ', arole)
                        notes = date['imprint']['notes']
                        if notes is not None:
                            notes = notes.replace('"', '')
                            notes = notes.replace('"', '')
                            notes = notes.replace('"', '')
                            notes = notes.replace('\n', ' ')
                            notes = notes.strip()
                            graph.add((URIRef(uri), jl.hasAbstract, (Literal(notes))))
                        for idf in date['imprint']['standardized_identifier']:
                            i = idf['identifier']
                            a = idf['authority']
                            d = {a: i}
                            if a == 'Incunabula Short Title Catalog':
                                identifier = f'https://data.cerl.org/istc/{i}'
                                graph.add((URIRef(uri), jl.describedAt, (Literal(identifier))))
                            elif a == 'WorldCat (OCLC)':
                                identifier = f'https://search.worldcat.org/de/title/{i}'
                                graph.add((URIRef(uri), jl.describedAt, (Literal(identifier))))
                            elif  a == 'NLI Yiddish Monographs Union List':
                                identifier = f'https://merhav.nli.org.il/primo-explore/search?query=any,contains,{i}&tab=default_tab&search_scope=ULY&vid=ULY&lang=en_US&offset=0&fromRedirectFilter=true'
                                graph.add((URIRef(uri), jl.describedAt, (Literal(identifier))))
                            elif a == 'Bibliography of the Hebrew Book':
                                identifier = f'https://merhav.nli.org.il/primo-explore/search?query=any,contains,{i}&tab=default_tab&search_scope=Local&vid=NLI&lang=en_US&offset=0'
                                graph.add((URIRef(uri), jl.describedAt, (Literal(identifier))))
                            elif a == 'Universal Short Title Catalog':
                                identifier = f'https://www.ustc.ac.uk/editions/{i}'
                                graph.add((URIRef(uri), jl.describedAt, (Literal(identifier))))
                            elif a == 'NLI Catalog (Merhav)':
                                identifier = f'https://merhav.nli.org.il/primo-explore/search?query=any,contains,{i}&tab=default_tab&search_scope=Local&vid=NLI&lang=en_US&offset=0'
                                graph.add((URIRef(uri), jl.describedAt, (Literal(identifier))))
                            elif a == 'Thesaurus (Vinograd)':
                                pass
                            else: print(a, ': ', i) 
                        rnotes = date['notes']
                        if rnotes is not None:
                            rnotes = rnotes.replace('"', '')
                            rnotes = rnotes.replace('"', '')
                            rnotes = rnotes.replace('"', '')
                            rnotes = rnotes.replace('\n', ' ')
                            graph.add((URIRef(uri), jl.hasAbstract, (Literal(rnotes))))
                        
                        for cowner in date['current_owners']:
                            c = cowner['person']['name']
                            graph.add((URIRef(uri), gndo.owner, (Literal(c))))

                        for fowner in date['owners']:
                            c = fowner['person']['name']
                            graph.add((URIRef(uri), gndo.formerOwner, (Literal(c))))
                        ridenifier = date['identifier']
                        add_creation_date(graph, uri)     
                        graph.serialize(destination=file_name, format="turtle")           
        b_page += 1
        if "detail" in data and data["detail"] == "Invalid page.": # stop if data corpus is processed
            print(f"last page loaded: page {b_page - 1}")
            break
# Places
    ppage = 1
    higher_geo_names =[] # List of higher geo units
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    while True:
        url = f"https://footprints.ctl.columbia.edu/api/place/?page={ppage}"
        response = requests.get(url, headers=headers)
        if response.text:
            data = json.loads(response.text)
            if 'results' in data:
                for date in data['results']:
                    if date['canonical_name'] and date['canonical_name'] is not None:
                        canonical_name  = date['canonical_name']
                        canonical_name = canonical_name.split(',')
                        place = canonical_name[0]
                        place = place.strip()
                        
                        uu= generate_hashUU(place)
                        uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}")
                        gndID = get_gnd_id(place, "PlaceOrGeographicName")  
                        if gndID is not None:      
                            graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(gndID))))
                        graph.add((URIRef(uri), jl.describedAt, (Literal('https://footprints.ctl.columbia.edu/'))))
                        graph.add((URIRef(uri), RDF.type, gndo.PlaceOrGeographicName))
                        graph.add((URIRef(uri), rdfs.label, (Literal(place))))
                        graph.add((URIRef(uri), skos.prefLabel, (Literal(place, datatype = XSD.string))))
                        long = date['longitude']
                        lat = date['latitude']
                        longlat = f'Point ( +{long} +{lat})' 
                        graph.add((URIRef(uri), geo.asWKT, (Literal(longlat))))
                        if len(canonical_name) > 1:
                            higher_geo_unit_1 = canonical_name[1]
                            higher_geo_unit_1 = higher_geo_unit_1.lstrip()
                            graph.add((URIRef(uri), gndo.hierarchicalSuperiorOfPlaceOrGeographicName, (Literal(higher_geo_unit_1))))
                        add_creation_date(graph, uri)



                    graph.serialize(destination=file_name, format="turtle") 
                    if len(canonical_name) > 1:
                            higher_geo_unit_1 = canonical_name[1].lstrip()
                            if higher_geo_unit_1 not in higher_geo_names:
                                hgu1_name = higher_geo_unit_1.strip()
                                uu= generate_hashUU(hgu1_name)
                                uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}")
                                gndID = get_gnd_id(higher_geo_unit_1, "PlaceOrGeographicName") 
                                if gndID is not None:      
                                    graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(gndID))))
                                graph.add((URIRef(uri), jl.describedAt, (Literal('https://footprints.ctl.columbia.edu/'))))
                                graph.add((URIRef(uri), RDF.type, gndo.PlaceOrGeographicName))
                                graph.add((URIRef(uri), foaf.name, (Literal(higher_geo_unit_1, datatype = XSD.string))))
                                graph.add((URIRef(uri), skos.prefLabel, (Literal(higher_geo_unit_1, datatype = XSD.string))))
                                if len(canonical_name) > 2:
                                    graph.add((URIRef(uri), gndo.hierarchicalSuperiorOfPlaceOrGeographicName, (Literal(higher_geo_unit_1))))
                                graph.serialize(destination=file_name, format="turtle")  
                            higher_geo_names.append(higher_geo_unit_1)
                            add_creation_date(graph, uri)
                            graph.serialize(destination=file_name, format="turtle")
                    if len(canonical_name) > 2:
                            higher_geo_unit_2 = canonical_name[2].lstrip()
                            if higher_geo_unit_2 not in higher_geo_names:
                                hgu2_name = higher_geo_unit_2.strip()
                                uu= generate_hashUU(hgu2_name)
                                uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}")
                                gndID = get_gnd_id(higher_geo_unit_2, "PlaceOrGeographicName") 
                                if gndID is not None:      
                                    graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(gndID))))
                                graph.add((URIRef(uri), jl.describedAt, (Literal('https://footprints.ctl.columbia.edu/'))))
                                graph.add((URIRef(uri), RDF.type, gndo.PlaceOrGeographicName))
                                graph.add((URIRef(uri), foaf.name, (Literal(higher_geo_unit_2, datatype = XSD.string))))
                                graph.add((URIRef(uri), skos.prefLabel, (Literal(higher_geo_unit_2, datatype = XSD.string))))
                                graph.serialize(destination=file_name, format="turtle")  
                            higher_geo_names.append(higher_geo_unit_2)
                            add_creation_date(graph, uri)
                            graph.serialize(destination=file_name, format="turtle")
            ppage += 1
        if "detail" in data and data["detail"] == "Invalid page.": # stop if data corpus is processed
            print(f"last page loaded: page {ppage - 1}")
            break


    
    print('graph created')


createGraph()

zip_file(file_name)