import gzip
import json
import logging
import os
import re
import shutil
from datetime import datetime

import requests
import urllib3
from SPARQLWrapper import RDF
from rdflib import Namespace, URIRef, Graph, Literal
from rdflib.namespace import RDF

file_name = 'sosy-final-01.ttl'
working_path = "./"
output_path = "/data/judaicalink/dumps/sosy/current/"

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

linklist = []
personsDict = []


def compress_ttl(compress_file_name):
    """
    Compress the ttl file.
    returns: compressed ttl file.
    """
    # compress the ttl file
    try:
        with open(compress_file_name, 'rb') as f_in:
            with gzip.open(compress_file_name + '.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return compress_file_name + '.gz'
    except Exception as e:
        logging.error("Could not compress file. Error: %e", e)


def move_ttl_file(move_file_name):
    """
    Move the ttl file to the correct folder.
    returns: the path of the ttl file.
    """
    # move the ttl file to the correct folder
    try:
        # if the file exists, delete it
        if os.path.isfile(move_file_name):
            os.remove(move_file_name)
        # move the file
        shutil.move(move_file_name, output_path)
    except Exception as e:
        logging.error("Could not move file. Error: %s", e)


def get_urls():
    """
    Get the URL and return the response
    """
    url = "https://www.soundscape-synagoge.de/api/person/all/base"

    response = requests.get(url)
    json_values = response.json()
    for value in json_values:
        linklist.append(value['identifier'])


def get_person_data(identifier_list):
    list_url = 'https://www.soundscape-synagoge.de/api/person/list'

    body = json.dumps(identifier_list)
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json'}

    try:
        http = urllib3.PoolManager()
        response = http.request('POST', list_url, headers=headers, body=body)
        logging.debug("Response: %s", response.status)
        if response.status == 200:
            persons_result = json.loads(response.data.decode('utf-8'))
            # returns a list, because the search input is a list of identifiers.
            return persons_result
    except Exception as e:
        logging.error("Could not get data. Error: %s", e)


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


def generate_rdf(persons_list):
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

    for person in persons_list:
        logging.debug(type(person))
        logging.debug("Person: %s", person)
        # create url from name
        url_name = clean_url_string(person['person']['displayName'])
        logging.debug(url_name)
        uri = URIRef(f"http://data.judaicalink.org/data/sosy/{url_name}")

        # person
        graph.add((URIRef(uri), RDF.type, foaf.Person))

        # Name
        graph.add((URIRef(uri), foaf.name, (Literal(person['person']['displayName']))))

        # prefLabel
        graph.add((URIRef(uri), skos.prefLabel, (Literal(person['person']['displayName']))))

        # alternative names
        if person['person']['alternateNameList'] is not None:
            if len(person['person']['alternateNameList']) > 0:
                for name in person['person']['alternateNameList'].split(','):
                    graph.add((URIRef(uri), skos.altLabel, (Literal(name))))
        if person['person']['mainName'] is not None:
            graph.add((URIRef(uri), skos.altLabel, (Literal(person['person']['mainName']))))
        if person['person']['birthName'] is not None:
            graph.add((URIRef(uri), skos.altLabel, (Literal(person['person']['birthName']))))

        # related, saved for later, but did not match any content in the data
        # mother
        # father
        # siblingsList
        # cohabitantList
        # childList
        # relatedOtherList
        # siblings (list)

        # describedAt
        graph.add((URIRef(uri), jl.describedAt, (Literal(
            'https://www.soundscape-synagoge.de/person?tab=masterdata&identifier=' + person['person']['personBase'][
                'identifier']))))

        # birthDate
        if person['person']['birthDate'] is not None and person['person']['birthDate'] != '':
            graph.add((URIRef(uri), jl.birthDate, (Literal(person['person']['birthDate']))))

        # deathDate
        if person['person']['dateOfDeath'] is not None and person['person']['dateOfDeath'] != '':
            graph.add((URIRef(uri), jl.deathDate, (Literal(person['person']['dateOfDeath']))))

        # birthLocation
        if person['person']['birthPlace'] is not None and person['person']['birthPlace'] != '':
            graph.add((URIRef(uri), jl.birthLocation, (Literal(person['person']['birthPlace']))))

        # deathLocation
        if person['person']['placeOfDeath'] is not None and person['person']['placeOfDeath'] != '':
            graph.add((URIRef(uri), jl.deathLocation, (Literal(person['person']['placeOfDeath']))))

        # hasPublication
        if person['writings'] is not None:
            for key, writing in person['writings'].items():
                # contains a dict
                if writing is not None:
                    if len(writing) > 0:
                        for item in writing:
                            graph.add((URIRef(uri), jl.hasPublication, (Literal(item.strip()))))
        # occupation
        if person['biography'] is not None:
            if person['biography']['jobDescriptionList'] is not None:
                if len(person['biography']['jobDescriptionList']) > 0:
                    for jobDescription in person['biography']['jobDescriptionList']:
                        for job in re.split(r',\s*(?![^()]*\))', jobDescription):
                            graph.add((URIRef(uri), jl.occupation, (Literal(job.strip()))))

            if person['biography']['titleList'] is not None:
                if len(person['biography']['titleList']) > 0:
                    for title in person['biography']['titleList']:
                        graph.add((URIRef(uri), jl.hasAbstract, (Literal(title))))

        graph.add((URIRef(uri), dcterms.created, (Literal(datetime.now()))))

    graph.serialize(destination=file_name, format="turtle")


get_urls()

logging.basicConfig(level=logging.INFO, filename='log.txt', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')


logging.getLogger().addHandler(logging.StreamHandler())

logging.debug(linklist)

logging.info("Generator started at: %s", datetime.now())

personsList = get_person_data(linklist)

generate_rdf(personsList)

compress_ttl(file_name)

move_ttl_file(file_name + '.gz')

logging.info('%s entries found.', len(personsList))
logging.info("Done")
