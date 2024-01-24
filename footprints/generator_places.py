"""
Generator for Footprints traces the history and movement of Jewish books since the inception of print. https://footprints.ctl.columbia.edu/ :Locations
By Christian Deuschle, 2023.
cd060@hdm-stuttgart.de
# Licence of the data: CC-BY-SA 4.0
# https://creativecommons.org/licenses/by-sa/4.0/
"""

import requests
import json
from bs4 import BeautifulSoup
import unicodedata
from rdflib.namespace import RDF, XSD
from datetime import datetime
from rdflib import Namespace, URIRef, Graph, Literal
import re
from edtf import parse_edtf
from tqdm import tqdm
import urllib.parse

file_name = 'footprintsplaces-final-01.ttl'

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

def createGraph():
    page = 1
    higher_geo_names =[]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    while True:
        url = f"https://footprints.ctl.columbia.edu/api/place/?page={page}"
        response = requests.get(url, headers=headers)
        if response.text:
            data = json.loads(response.text)
            if 'results' in data:
                for date in data['results']:
                    if date['canonical_name'] and date['canonical_name'] is not None:
                        canonical_name  = date['canonical_name']
                        canonical_name = canonical_name.split(',')
                        place = canonical_name[0]
                        name = clean_url_string(str(place))
                        name = name.decode('utf-8')
                        uri = URIRef(f"http://data.judaicalink.org/data/footprints/{name}")
                        gndID = get_gnd_id(place, "PlaceOrGeographicName")  #TODO only if not none
                        if gndID is not None:      
                            graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(gndID))))
                        graph.add((URIRef(uri), jl.describedAt, (Literal('https://footprints.ctl.columbia.edu/'))))
                        graph.add((URIRef(uri), RDF.type, gndo.PlaceOrGeographicName))
                        graph.add((URIRef(uri), foaf.name, (Literal(place, datatype = XSD.string))))
                        graph.add((URIRef(uri), skos.prefLabel, (Literal(place, datatype = XSD.string))))
                        graph.add((URIRef(uri), jl.lat, (Literal(date['latitude']))))
                        graph.add((URIRef(uri), jl.lon, (Literal(date['longitude']))))
                        if len(canonical_name) > 1:
                            higher_geo_unit_1 = canonical_name[1]
                            higher_geo_unit_1 = higher_geo_unit_1.lstrip()
                            graph.add((URIRef(uri), gndo.hierarchicalSuperiorOfPlaceOrGeographicName, (Literal(higher_geo_unit_1))))       
                    graph.serialize(destination=file_name, format="turtle") 
                    if len(canonical_name) > 2:
                            higher_geo_unit_2 = canonical_name[2].lstrip()
                            if higher_geo_unit_1 not in higher_geo_names:
                                hgu1_name = higher_geo_unit_1
                                hgu1_name = clean_url_string(str(hgu1_name))
                                hgu1_name = hgu1_name.decode('utf-8')
                                uri = URIRef(f"http://data.judaicalink.org/data/footprints/{hgu1_name}")
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
            page += 1
        if "detail" in data and data["detail"] == "Invalid page.":
            print(f"last page loaded: page {page - 1}")
            break
    print('graph created')
    

    
createGraph()
