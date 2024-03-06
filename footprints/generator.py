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
from rdflib.namespace import RDF, XSD
from datetime import datetime
from rdflib import Namespace, URIRef, Graph, Literal
import re
from edtf import parse_edtf
from tqdm import tqdm
import urllib.parse
import langid
import googletrans
from googletrans import *
import uuid
import hashlib




def geerate_hashUU(name):
# Hash the string using a hashing algorithm (e.g., SHA-256)
    hashed_string = hashlib.sha256(name.encode()).hexdigest()
    # Generate a UUID based on the hashed string
    uuid_from_hash = uuid.uuid5(uuid.NAMESPACE_OID, hashed_string)
    return uuid_from_hash


file_name = 'footprints-final-01.ttl'

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

graph.bind('skos', skos)
graph.bind('foaf', foaf)
graph.bind('jl', jl)
graph.bind('gndo', gndo)
graph.bind('owl', owl)
graph.bind('edm', edm)
graph.bind('dc', dc)
graph.bind('dcterms', dcterms)
graph.bind('rdfs', rdfs)

'''
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
    # print(string)
    return string
'''

######################### Test 22-01-2024
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

#############################

def hebrew_name_recogition(name):
    '''recognices if a string is written in hebrew letters'''
    lang, confidence = langid.classify(name)
    return lang == 'he'
'''
def he_to_en(text):  # does not work propper with familynames
    translator = googletrans.Translator()
    translation = translator.translate(text, dest='en')
    return translation.text
'''

def text_to_en(text):
    translator = googletrans.Translator()
    translation = translator.translate(text, dest='en')
    return translation.text


def clean_hebrew_name(name):
    name = name.strip()
    name = name.replace('.', '')
    return name


def contains_non_digits(s):
    return bool(re.search(r'\D', s))

def get_gnd_from_viaf(viafid):
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
                               # print(s)
    try:
        return gnd
    except:
        pass
    

def add_creation_date(graph, uri):
    if (URIRef(uri), dcterms.created, None) not in graph:
        graph.add((URIRef(uri), dcterms.created, Literal(datetime.now())))  # onnly add creatioon darte if it doesnt exist yet


def createGraph():
    p_page = 1
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
#get person from persons
    while True:
        url = f"https://footprints.ctl.columbia.edu/api/person/?format=json&page={p_page}"
        if p_page % 10 == 0:
            print('Persons Page: ',p_page)
        response = requests.get(url, headers=headers)
        if response.text:
            data = json.loads(response.text)
            if 'results' in data:
                for date in data['results']:
                    if date['name'] and date['name'] is not None:
                        name = date['name']
                        fID = date['id']
                        if contains_non_digits(name) == True:
                            name = name.strip()
                            uu= geerate_hashUU(name)

                            uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}")
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
                                        except:
                                            pass
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
                                            idgnd =  get_gnd_from_viaf(idf)
                                            idf = f'https://viaf.org/viaf/{idf}/'
                                           # try:
                                            graph.add((URIRef(uri), owl.sameAs, (Literal(idf)))) #VIAF
                                            graph.add((URIRef(uri), owl.sameAs, (Literal(idgnd)))) # GND
                                            #except:
                                            #    pass
                                        if idf['authority'] == "Library of Congress":
                                            idf = idf['identifier']
                                            idf = idf.replace('LOC ', '')
                                            idf =      f'https://id.loc.gov/authorities/names/n{idf}'
                                            #try:
                                            graph.add((URIRef(uri), owl.sameAs, (Literal(idf))))
                                           # except:
                                           #     pass

                                        else:
                                            print('Seite:', idf, ', ', name, ', identifier = ', idf['authority'])
                                except:
                                    pass
                    add_creation_date(graph, uri)         
                    graph.serialize(destination=file_name, format="turtle")
    
            # TODO fix ivrit alphabet
            p_page += 1
        if "detail" in data and data["detail"] == "Invalid page.":
            print(f"last page loaded: page {p_page - 1}")
            break

    b_page = 1
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    while True:
   # while b_page < 10:
        url = f"https://footprints.ctl.columbia.edu/api/book/?page={b_page}"
        response = requests.get(url, headers=headers)
        if b_page % 10 == 0:
            print('books: page ',b_page)
        if response.text:
            data = json.loads(response.text)
            if 'results' in data:
                for date in data['results']:
# get person (actor) from books            
                    if date['imprint']['work']['title']:
                        for actor in date['imprint']['work']['actor']:
                            name = actor['person']['name']
                            name = name.strip()
                            uu= geerate_hashUU(name)
                            uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}")
                            graph.add((URIRef(uri), RDF.type, foaf.Person))
                            if hebrew_name_recogition(name) == True:
                                name = clean_hebrew_name(name)
                            graph.add((URIRef(uri), foaf.name, (Literal(name))))
                            graph.add((URIRef(uri), skos.prefLabel, (Literal(name))))
                            if actor['person']['birth_date'] is not None:
                                actor_bd = actor['person']['birth_date']
                                graph.add((URIRef(uri), jl.birthDate, (Literal(actor_bd))))
                            if actor['person']['death_date'] is not None:
                                actor_dd = actor['person']['death_date']
                                graph.add((URIRef(uri), jl.birthDate, (Literal(actor_dd))))
                            if 'standardized_identifier' in actor['person'] and actor['person']['standardized_identifier'] is not None:
                                if 'identifier' in actor['person']['standardized_identifier'] and actor['person']['standardized_identifier']['identifier'] is not None:
                                    sID = actor['person']['standardized_identifier']['identifier']
                                    if 'authority' in actor['person']['standardized_identifier'] and actor['person']['standardized_identifier']['authority'] == 'VIAF Identifier':
                                        if actor['person']['standardized_identifier']['authority'] == 'VIAF Identifier': 
                                            idgnd =  get_gnd_from_viaf(sID)
                                            idurl = f'https://viaf.org/viaf/{sID}/'
                                            graph.add((URIRef(uri), jl.describedAt, (Literal(idurl))))
                                            graph.add((URIRef(uri), jl.describedAt, (Literal(idgnd))))
                                        else:
                                            print(actor['person']['standardized_identifier']['authority'])
                            role =  actor['role']['name']
                            graph.add((URIRef(uri), jl.occupation, (Literal(role))))
                            add_creation_date(graph, uri)
                            graph.serialize(destination=file_name, format="turtle")
                            
# get books from books
                        wtitle = date['imprint']['work']['title']
                        wtitle = wtitle.strip()
                        uu= geerate_hashUU(wtitle)
                        uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}")
                        graph.add((URIRef(uri), RDF.type, gndo.Work))
                        graph.add((URIRef(uri), dc.title, (Literal(wtitle))))
                        graph.add((URIRef(uri), skos.prefLabel, (Literal(wtitle))))
                        for actor in date['imprint']['work']['actor']:
                            act = actor['person']['name']
                            act = act.strip()
                            uu= geerate_hashUU(act) 
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
                                transl_place = text_to_en(wplace)
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
                            uu= geerate_hashUU(name)
                            a = f'http://data.judaicalink.org/data/footprints/{uu}'
                            arole = actor['role']['name']
                            if arole == 'Publisher':
                                graph.add((URIRef(uri), dc.publisher, (Literal(a))))
                            elif arole == 'Editor':
                                graph.add((URIRef(uri), gndo.editor, (Literal(a))))
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
                            #print('r: ',rnotes)
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
        if "detail" in data and data["detail"] == "Invalid page.":
            print(f"last page loaded: page {b_page - 1}")
            break
# Places
    ppage = 1
    higher_geo_names =[]
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
                        
                        uu= geerate_hashUU(place)
                        uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}")
                        gndID = get_gnd_id(place, "PlaceOrGeographicName")  #TODO only if not none
                        if gndID is not None:      
                            graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(gndID))))
                        graph.add((URIRef(uri), jl.describedAt, (Literal('https://footprints.ctl.columbia.edu/'))))
                        graph.add((URIRef(uri), RDF.type, gndo.PlaceOrGeographicName))
                        graph.add((URIRef(uri), rdfs.label, (Literal(place))))
                        graph.add((URIRef(uri), skos.prefLabel, (Literal(place, datatype = XSD.string))))
                        graph.add((URIRef(uri), jl.lat, (Literal(date['latitude']))))
                        graph.add((URIRef(uri), jl.lon, (Literal(date['longitude']))))
                        if len(canonical_name) > 1:
                            higher_geo_unit_1 = canonical_name[1]
                            higher_geo_unit_1 = higher_geo_unit_1.lstrip()
                            graph.add((URIRef(uri), gndo.hierarchicalSuperiorOfPlaceOrGeographicName, (Literal(higher_geo_unit_1))))
                        add_creation_date(graph, uri)    
                    graph.serialize(destination=file_name, format="turtle") 
                    if len(canonical_name) > 2:
                            higher_geo_unit_2 = canonical_name[2].lstrip()
                            if higher_geo_unit_1 not in higher_geo_names:
                                hgu1_name = higher_geo_unit_1.strip()
                                uu= geerate_hashUU(hgu1_name)
                                uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}")
                                gndID = get_gnd_id(higher_geo_unit_1, "PlaceOrGeographicName")  #TODO only if not none
                                if gndID is not None:      
                                    graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(gndID))))
                                graph.add((URIRef(uri), jl.describedAt, (Literal('https://footprints.ctl.columbia.edu/'))))
                                graph.add((URIRef(uri), RDF.type, gndo.PlaceOrGeographicName))
                                graph.add((URIRef(uri), foaf.name, (Literal(higher_geo_unit_1, datatype = XSD.string))))
                                graph.add((URIRef(uri), skos.prefLabel, (Literal(higher_geo_unit_1, datatype = XSD.string))))
                                graph.add((URIRef(uri), gndo.hierarchicalSuperiorOfPlaceOrGeographicName, (Literal(higher_geo_unit_2))))
                                graph.serialize(destination=file_name, format="turtle")  
                            higher_geo_names.append(higher_geo_unit_1)
            ppage += 1
        if "detail" in data and data["detail"] == "Invalid page.":
            print(f"last page loaded: page {ppage - 1}")
            break

    
    print('graph created')


createGraph()
