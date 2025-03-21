# -*- coding: utf-8 -*-

"""
Generator for the Gidal Image Archive. http://www.steinheim-institut.de/wiki/index.php/Archive:Gidal-Bildarchiv
By Benjamin Schnabel, 2022.
schnabel@hdm-stuttgart.de
# Licence of the data: CC-BY-SA 4.0
# https://creativecommons.org/licenses/by-sa/4.0/
"""

import gzip
import shutil
from datetime import datetime
import pandas as pd
from rdflib import Graph, Namespace, RDF, Literal, URIRef

file_name = 'gba-final-01.ttl'
output_path = "/data/dumps/gba/current/"

graph = Graph()

# Namespaces
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
dcterms = Namespace("http://purl.org/dc/terms/")

graph.bind('skos', skos)
graph.bind('foaf', foaf)
graph.bind('gndo', gndo)
graph.bind('dcterms', dcterms)

csv_file = "./gidal.csv"


def compress_ttl(file_name):
    try:
        with open(file_name, 'rb') as f_in:
            with gzip.open(file_name + '.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    except Exception as e:
        print("Could not compress file. Error: ", e)


def move_ttl_file(file_name):
    try:
        shutil.move(file_name, output_path)
    except Exception as e:
        print("Could not move file. Error: ", e)


def clean_url_string(string):
    if pd.isna(string):
        return ''
    string = string.strip()
    for char in ["'", '"', ',', '<', '>', '|', ' ', '.', '[', ']', '(', ')', '{', '}']:
        string = string.replace(char, '_')
    return string


def generate_rdf(csv_file):
    df = pd.read_csv(csv_file, sep=',', encoding='utf-8', header=0)

    for _, row in df.iterrows():
        # Create URI
        url_name = clean_url_string(row['name'])
        uri = URIRef(f"http://data.judaicalink.org/data/gba/{url_name}")

        # GND ID (optional)
        if row.get('gnd') and not pd.isna(row['gnd']):
            graph.add((uri, gndo.gndIdentifier, Literal(row['gnd'])))

        # Type
        if row.get('type') == 'person':
            graph.add((uri, RDF.type, foaf.Person))
        elif row.get('type') == 'organisation':
            graph.add((uri, RDF.type, foaf.Organization))

        # Labels
        graph.add((uri, foaf.name, Literal(row['name'])))
        graph.add((uri, skos.prefLabel, Literal(row['name'])))

        # Birth and death
        if row.get('birthDate') and not pd.isna(row['birthDate']):
            graph.add((uri, gndo.birthDate, Literal(int(row['birthDate']))))

        if row.get('deathDate') and not pd.isna(row['deathDate']):
            graph.add((uri, gndo.deathDate, Literal(int(row['deathDate']))))

        # Multi-valued: occupation (split on ";")
        if row.get('occupation') and not pd.isna(row['occupation']):
            for occ in str(row['occupation']).split(';'):
                occ = occ.strip()
                if occ:
                    graph.add((uri, gndo.occupation, Literal(occ)))

        # Multi-valued: hasPublication (split on ";")
        if row.get('hasPublication') and not pd.isna(row['hasPublication']):
            for pub in str(row['hasPublication']).split(';'):
                pub = pub.strip()
                if pub:
                    graph.add((uri, gndo.hasPublication, Literal(pub)))

        # Relation
        if row.get('relation') and not pd.isna(row['relation']):
            graph.add((uri, gndo.relation, Literal(row['relation'].strip())))

        # Alternative name
        if row.get('alternativeName') and not pd.isna(row['alternativeName']):
            graph.add((uri, gndo.alternativeName, Literal(row['alternativeName'].strip())))

        # Abstract
        if row.get('hasAbstract') and not pd.isna(row['hasAbstract']):
            graph.add((uri, gndo.hasAbstract, Literal(row['hasAbstract'].strip())))

        # Metadata: creation timestamp
        graph.add((uri, dcterms.created, Literal(datetime.now())))

    graph.serialize(destination=file_name, format="turtle")


generate_rdf(csv_file)
compress_ttl(file_name)
move_ttl_file(file_name + '.gz')
