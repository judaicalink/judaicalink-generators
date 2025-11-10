"""
Generator for Hamburger Schlüsseldokumente zur deutsch-jüdischen Geschichte. https://schluesseldokumente.net/person
By Christian Deuschle, 2023.
cd060@hdm-stuttgart.de
# Licence of the data: CC-BY-SA 4.0
# https://creativecommons.org/licenses/by-sa/4.0/
"""

import requests
import json
import unicodedata
import shutil
import gzip
import re
from bs4 import BeautifulSoup
from rdflib.namespace import RDF, XSD
from datetime import datetime
from rdflib import Namespace, URIRef, Graph, Literal
from tqdm import tqdm

file_name = 'hhkeydocs-final-01.ttl'
output_path = "/data/dumps/hhkeydocs/current/"
graph = Graph()

# NAMESPACES
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
dc = Namespace("http://purl.org/dc/elements/1.1/")
dcterms = Namespace("http://purl.org/dc/terms/")
geo = Namespace("http://www.opengis.net/ont/geosparql#")

graph.bind('skos', skos)
graph.bind('foaf', foaf)
graph.bind('jl', jl)
graph.bind('gndo', gndo)
graph.bind('owl', owl)
graph.bind('dc', dc)
graph.bind('dcterms', dcterms)
graph.bind('geo', geo)

ids = []
org_ids = []
place_ids = []
professions = []

# UTILS
def sanitize_literal(text):
    if not text:
        return ""
    text = re.sub(r'["\n\r]', '', text)
    text = text.strip()
    return text

def clean_url_string(string):
    string = unicodedata.normalize('NFKD', string).encode('ascii', 'ignore').decode()
    return re.sub(r'[\'"<>|.,()\[\]{}?#-]', '', string).replace(' ', '_')

def move_ttl_file(file_path):
    try:
        shutil.move(file_path, output_path)
        print(f"File moved to {output_path}")
    except Exception as e:
        print("Could not move file. Error: ", e)

def compress_ttl(file_path):
    gz_file_path = file_path + ".gz"
    with open(file_path, 'rb') as f_in, gzip.open(gz_file_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    print(f"File {gz_file_path} compressed successfully.")
    return gz_file_path

def get_viaf_id(gnd_id: str) -> str:
    try:
        request = requests.get("https://lobid.org/gnd/" + gnd_id + ".json")
        request_json = request.json()
        for sameAs in request_json.get("sameAs", []):
            if sameAs["collection"]["abbr"] == "VIAF":
                return sameAs["id"]
    except:
        return None

# BEACON + SCRAPERS

def get_ids(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    soup = str(soup).split('\n')
    for id_line in soup:
        try:
            id_line = int(id_line)
            ids.append(id_line)
        except:
            pass

def get_org_ids(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    soup = str(soup).split('\n')
    for id_line in soup:
        try:
            id_line = int(id_line)
            org_ids.append(id_line)
        except:
            pass

def get_place_ids(url):
    html = requests.get(url)
    soup = BeautifulSoup(html.content, 'html.parser')
    list_items = soup.select('.list-unstyled li a')
    if list_items:
        for item in list_items:
            place_ids.append(item.get('href'))
    else:
        print("ERROR: no links found in place list")

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
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }
    params = {"query": sparql_query, "format": "json"}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    extra = ['Talmud-Gelehrter']
    for item in data["results"]["bindings"]:
        professions.append(item["professionLabel"]["value"])
    professions.extend(extra)

# FULL GRAPH GENERATOR
def create_graph():
    # --------- PLACES ---------
    for id in tqdm(place_ids):
        place_url = f'https://schluesseldokumente.net{id}.jsonld'
        place_response = requests.get(place_url)
        if place_response.status_code == 200:
            data = json.loads(place_response.text)
            clean_name = clean_url_string(data['name'])
            uri = URIRef(f"http://data.judaicalink.org/data/hhkeydocs/{clean_name}")
            graph.add((uri, RDF.type, gndo.PlaceOrGeographicName))
            graph.add((uri, foaf.name, Literal(data['name'])))
            graph.add((uri, skos.prefLabel, Literal(data['name'])))
            graph.add((uri, jl.describedAt, URIRef(place_url)))
            if data.get('geo'):
                lat = data['geo'].get('latitude')
                long = data['geo'].get('longitude')
                if lat and long:
                    graph.add((uri, geo.asWKT, Literal(f"Point ( +{long} +{lat})")))
            if 'containedInPlace' in data:
                graph.add((uri, gndo.hierarchicalSuperiorOfPlaceOrGeographicName, Literal(data['containedInPlace']['name'])))
            graph.serialize(destination=file_name, format="turtle")

    # --------- PERSONS ---------
    for id in tqdm(ids):
        gndId = str(id)
        url2 = f'https://schluesseldokumente.net/person/gnd/{gndId}.jsonld'
        response2 = requests.get(url2)
        if response2.status_code == 200:
            data = json.loads(response2.text)
            clean_name = clean_url_string(data['name'])
            uri = URIRef(f"http://data.judaicalink.org/data/hhkeydocs/{clean_name}")
            graph.add((uri, RDF.type, foaf.Person))
            graph.add((uri, jl.describedAt, URIRef(url2)))
            graph.add((uri, foaf.name, Literal(data['name'])))
            graph.add((uri, skos.prefLabel, Literal(data['name'])))
            graph.add((uri, gndo.gndIdentifier, Literal(gndId)))

            viaf = get_viaf_id(gndId)
            if viaf:
                graph.add((uri, owl.sameAs, URIRef(f'https://viaf.org/viaf/{viaf}/')))

            if 'birthDate' in data:
                graph.add((uri, jl.birthDate, Literal(data['birthDate'])))
            if 'deathDate' in data:
                graph.add((uri, jl.deathDate, Literal(data['deathDate'])))

            birth_place = data.get('birthPlace', {}).get('name')
            if birth_place:
                birth_clean = clean_url_string(birth_place)
                graph.add((uri, jl.birthLocation, URIRef(f"http://data.judaicalink.org/data/hhkeydocs/{birth_clean}")))

            death_place = data.get('deathPlace', {}).get('name')
            if death_place:
                death_clean = clean_url_string(death_place)
                graph.add((uri, jl.deathLocation, URIRef(f"http://data.judaicalink.org/data/hhkeydocs/{death_clean}")))

            graph.add((uri, dcterms.created, Literal(datetime.now())))

            if 'description' in data:
                description = sanitize_literal(data['description'])
                graph.add((uri, jl.hasAbstract, Literal(description)))
            graph.serialize(destination=file_name, format="turtle")

    # --------- ORGANISATIONS ---------
    for id in tqdm(org_ids):
        orgID = str(id)
        org_url = f'https://schluesseldokumente.net/organisation/gnd/{orgID}.jsonld'
        response3 = requests.get(org_url)
        if response3.status_code == 200:
            data = json.loads(response3.text)
            clean_name = clean_url_string(data['name'])
            uri = URIRef(f"http://data.judaicalink.org/data/hhkeydocs/{clean_name}")
            graph.add((uri, RDF.type, foaf.Organization))
            graph.add((uri, jl.describedAt, URIRef(org_url)))
            graph.add((uri, foaf.name, Literal(data['name'])))
            graph.add((uri, skos.prefLabel, Literal(data['name'])))
            graph.add((uri, gndo.gndIdentifier, Literal(orgID)))

            if 'foundingDate' in data:
                graph.add((uri, gndo.dateOfEstablishment, Literal(data['foundingDate'])))
            if 'dissolutionDate' in data:
                graph.add((uri, gndo.dateOfTermination, Literal(data['dissolutionDate'])))
            if 'description' in data:
                graph.add((uri, jl.hasAbstract, Literal(sanitize_literal(data['description']))))
            if 'url' in data:
                graph.add((uri, foaf.homepage, URIRef(data['url'])))
            graph.serialize(destination=file_name, format="turtle")

    print('Graph created successfully!')

# FINAL EXECUTION BLOCK:
get_place_ids('https://schluesseldokumente.net/ort')
get_ids('https://schluesseldokumente.net/person/gnd/beacon')
get_org_ids('https://schluesseldokumente.net/organisation/gnd/beacon')
get_professions_from_WD()

create_graph()
gz_file = compress_ttl(file_name)
move_ttl_file(gz_file)
