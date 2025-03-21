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
from rdflib.term import URIRef
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

def sanitize_literal(text):
    if not text:
        return ""
    text = re.sub(r'["\n\r]', '', text)
    text = text.strip()
    return text

def sanitize_uri(uri):
    return uri.strip().replace(' ', '%20')

def zip_file(file_path):
    if not os.path.exists(file_path):
        print(f'file "{file_path}" does not exist.')
        return
    gz_file_path = file_path + ".gz"
    with open(file_path, 'rb') as f_in, gzip.open(gz_file_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    print(f"Zipping {gz_file_path} succeeded.")

def generate_hashUU(name):
    hashed_string = hashlib.sha256(name.encode()).hexdigest()
    uuid_from_hash = uuid.uuid5(uuid.NAMESPACE_OID, hashed_string)
    return uuid_from_hash

file_name = 'footprints.ttl'
output_path = "/data/dumps/footprints/current/"

graph = Graph()

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

def move_ttl_file(file_name):
    try:
        shutil.move(file_name, output_path)
    except Exception as e:
        print("Could not move file. Error: ", e)

def add_creation_date(graph, uri):
    if (URIRef(uri), dcterms.created, None) not in graph:
        graph.add((URIRef(uri), dcterms.created, Literal(datetime.now())))

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
                            if s.startswith('http://d-nb.info/gnd'):
                                return s
    return None

def createGraph():
    headers = {'User-Agent': 'Mozilla/5.0'}
    p_page = 1
    while True:
        url = f"https://footprints.ctl.columbia.edu/api/person/?format=json&page={p_page}"
        response = requests.get(url, headers=headers)
        if response.text:
            data = json.loads(response.text)
            if 'results' in data:
                for date in data['results']:
                    if date['name']:
                        name = sanitize_literal(date['name'])
                        uu = generate_hashUU(name)
                        uri = f"http://data.judaicalink.org/data/footprints/{uu}"
                        graph.add((URIRef(uri), RDF.type, foaf.Person))
                        graph.add((URIRef(uri), foaf.name, Literal(name)))
                        graph.add((URIRef(uri), skos.prefLabel, Literal(name)))

                        if 'standardized_identifier' in date and date['standardized_identifier']:
                            sid = date['standardized_identifier']
                            if sid['authority'] == "VIAF Identifier":
                                viaf_id = sid['identifier']
                                graph.add((URIRef(uri), owl.sameAs, URIRef(f"https://viaf.org/viaf/{viaf_id}/")))
                                gnd_uri = get_gnd_from_viaf(viaf_id)
                                if gnd_uri:
                                    graph.add((URIRef(uri), owl.sameAs, URIRef(gnd_uri)))

                        if 'birth_date' in date and date['birth_date']:
                            graph.add((URIRef(uri), jl.birthDate, Literal(date['birth_date']['edtf_format'])))
                        if 'death_date' in date and date['death_date']:
                            graph.add((URIRef(uri), jl.deathDate, Literal(date['death_date']['edtf_format'])))

                        add_creation_date(graph, uri)
                        graph.serialize(destination=file_name, format="turtle")
            p_page += 1
        if "detail" in data and data["detail"] == "Invalid page.":
            print(f"last page loaded: page {p_page - 1}")
            break

    # Similar changes can now be applied to "book" and "place" sections...

createGraph()
zip_file(file_name)
move_ttl_file(file_name + '.gz')
