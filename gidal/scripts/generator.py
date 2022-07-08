# -*- coding: utf-8 -*-

"""
Generator for the Gidal Image Archive. http://www.steinheim-institut.de/wiki/index.php/Archive:Gidal-Bildarchiv
By Benjamin Schnabel, 2022.
schnabel@hdm-stuttgart.de
# Licence of the data: CC-BY-SA 4.0
# https://creativecommons.org/licenses/by-sa/4.0/
"""
import gzip
import math
import shutil
from datetime import datetime

import pandas as pd
from rdflib import Graph, Namespace, RDF, Literal, URIRef

file_name = 'gba-final-01.ttl'
working_path = "./"
output_path = "/data/judaicalink/dumps/epi/current/"

graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace("http://purl.org/dc/elements/1.1/")

graph.bind('skos', skos)
graph.bind('foaf', foaf)
graph.bind('jl', jl)
graph.bind('gndo', gndo)
graph.bind('owl', owl)
graph.bind('edm', edm)
graph.bind('dc', dc)


csv_file = "./gidal.csv"




def compress_ttl(file_name):
    """
    Compress the ttl file.
    returns: compressed ttl file.
    """
    # compress the ttl file
    try:
        with open(file_name, 'rb') as f_in:
            with gzip.open(file_name + '.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    except Exception as e:
        print("Could not compress file. Error: ", e)


def move_ttl_file(file_name):
    """
    Move the ttl file to the correct folder.
    returns: the path of the ttl file.
    """
    # move the ttl file to the correct folder
    try:
        shutil.move(file_name, output_path)
    except Exception as e:
        print("Could not move file. Error: ", e)


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
    return string




def generate_rdf(csv_file):
    """
    Generate RDF from the personsDict.
    returns: nothing
    """

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

    # create pandas dataframe from csv file
    df = pd.read_csv(csv_file, sep=',', encoding='utf-8', header=0)

    # iterate over the rows in the dataframe
    for index, row in df.iterrows():

        url_name = clean_url_string(row['name'])
        uri = URIRef(f"http://data.judaicalink.org/data/gba/{url_name}")

        if row['gnd'] != '' and not pd.isna(row['gnd']):
            base_url = "http://www.steinheim-institut.de/gidal-bildarchiv/query.html?text1={ID}&kategorie1=GND"
            url_name = base_url.format(ID=row['gnd'])
            graph.add((URIRef(uri), gndo.gndIdentifier, Literal(row['gnd'])))
        else:
            base_url = "http://www.steinheim-institut.de/gidal-bildarchiv/query.html?text1={name}"
            url_name = base_url.format(name=clean_url_string(row['name']))

        if row['type'] == 'person':
            graph.add((URIRef(uri), RDF.type, foaf.Person))
        elif row['type'] == 'organisation':
            graph.add((URIRef(uri), RDF.type, foaf.Organization))

        graph.add((URIRef(uri), foaf.name, Literal(row['name'])))
        graph.add((URIRef(uri), skos.prefLabel, Literal(row['name'])))

        if row['birthDate'] != '' and not pd.isna(row['birthDate']):
            graph.add((URIRef(uri), gndo.birthDate, Literal(int(row['birthDate']))))
        if row['deathDate'] != '' and not pd.isna(row['deathDate']):
            graph.add((URIRef(uri), gndo.deathDate, Literal(int(row['deathDate']))))
        if row['occupation'] != '' and not pd.isna(row['occupation']):
            for occupation in str(row['occupation']).split(';'):
                graph.add((URIRef(uri), gndo.occupation, Literal(occupation.strip())))
        if row['hasPublication'] != '' and not pd.isna(row['hasPublication']):
            for publication in str(row['hasPublication']).split(';'):
                graph.add((URIRef(uri), gndo.hasPublication, Literal(publication.strip())))
        if row['alternativeName'] != '' and not pd.isna(row['alternativeName']):
            graph.add((URIRef(uri), gndo.alternativeName, Literal(row['alternativeName'])))
        if row['hasAbstract'] != '' and not pd.isna(row['hasAbstract']):
            graph.add((URIRef(uri), gndo.hasAbstract, Literal(row['hasAbstract'].strip())))
        if row['relation'] != '' and not pd.isna(row['relation']):
            graph.add((URIRef(uri), gndo.relation, Literal(row['relation'])))

        graph.add((URIRef(uri), dcterms.created, (Literal(datetime.now()))))


    graph.serialize(destination=file_name, format="turtle")


generate_rdf(csv_file)
compress_ttl(file_name)
move_ttl_file(file_name + '.gz')
