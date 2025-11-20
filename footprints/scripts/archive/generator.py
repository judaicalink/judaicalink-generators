"""
Generator for Footprints traces the history and movement of Jewish books since the inception of print. https://footprints.ctl.columbia.edu/
By Christian Deuschle, 2023.
cd060@hdm-stuttgart.de
# Licence of the data: CC-BY-SA 4.0
# https://creativecommons.org/licenses/by-sa/4.0/
"""

import requests
import json
import unicodedata
from rdflib.namespace import RDF, XSD
from rdflib.term import URIRef
from datetime import datetime
from rdflib import Namespace, URIRef, Graph, Literal
import re
from tqdm import tqdm
import uuid
import hashlib
import gzip
import shutil
import os
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

file_name = 'footprints.ttl'
output_path = "/data/dumps/footprints/current/"
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

def move_ttl_file(file_name):
    try:
        shutil.move(file_name, output_path)
        print("File moved successfully.")
    except Exception as e:
        print("Could not move file. Error: ", e)

def compress_ttl(file_path):
    gz_file_path = file_path + ".gz"
    with open(file_path, 'rb') as f_in, gzip.open(gz_file_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    print(f"File {gz_file_path} compressed successfully.")
    return gz_file_path

def generate_hashUU(name):
    hashed_string = hashlib.sha256(name.encode()).hexdigest()
    uuid_from_hash = uuid.uuid5(uuid.NAMESPACE_OID, hashed_string)
    return uuid_from_hash

def createGraph():
    p_page = 1
    headers = {'User-Agent': 'Mozilla/5.0'}

    while True:
        url = f"https://footprints.ctl.columbia.edu/api/person/?format=json&page={p_page}"
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code != 200:
            break
        data = response.json()
        if 'results' not in data:
            break
        for person in data['results']:
            if person['name']:
                name = person['name'].strip()
                uu = generate_hashUU(name)
                uri = URIRef(f"http://data.judaicalink.org/data/footprints/{uu}")
                graph.add((uri, RDF.type, foaf.Person))
                graph.add((uri, foaf.name, Literal(name)))
                graph.add((uri, skos.prefLabel, Literal(name)))
        graph.serialize(destination=file_name, format="turtle")
        p_page += 1

    print("Graph created")

createGraph()
gz_file = compress_ttl(file_name)
move_ttl_file(gz_file)
