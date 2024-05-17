import requests
from bs4 import BeautifulSoup
from rdflib.namespace import RDF, XSD, DC
from rdflib import Namespace, URIRef, Graph, Literal, BNode
from tqdm import tqdm
import unicodedata
from datetime import datetime
import gzip
import shutil
import os

file_name = 'nrwbibdjg.ttl'

working_path = "./"
output_path = "/data/dumps/nrwbibdjg/current/"

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

def get_gnd_ttl_data(gndid, uri, graph):
    """ 
    enriches data with data from gnd if gnd id is known
    Params: 
        gndid (str or int): ID for GND (Gemeinsame Normdatei)
        uri (str): the uri of the entity to wich the gndid belongs
        graph (class): graph in wich creation the function  is called

    Return: 
        dictionary for dataenrichment from gnd ({predicate : object})
        
    """
    pr_obj = []
    try:
        headers = {'Accept': 'text/turtle'} 
        gnd_url = f'http://d-nb.info/gnd/{gndid}/about/lds'
        response = requests.get(gnd_url, headers=headers)    
        if response.status_code == 200:
            # Parse the Turtle data
            graph.parse(data=response.text, format='turtle')
        # Iterate over triples and add them to the graph
        for s, p, o in graph:
            p = str(p)
            o = str(o)
            if p.startswith('https://d-nb.info/standards/elementset/gnd#'):
                p = p.replace('https://d-nb.info/standards/elementset/gnd#', 'gndo.')
                if o.startswith('https://d-nb.info/gnd/'):
                    oid = o.replace('https://d-nb.info/gnd/', '')

                    #o = get_name_from_gndid(oid)

                    o = f'http://data.judaicalink.org/data/nrwbibdjg/{oid}'
                pr_obj.append([p,o])        
            if p.startswith('http://www.w3.org/2002/07/owl#'):
                p = p.replace('http://www.w3.org/2002/07/owl#', 'owl.')
                pr_obj.append([p,o])
        return pr_obj
    except:
        print(f'an error occured with ID: {gndid}')

def get_ids_from_beacon(url):

    """
    Creates a List  of IDs from beacon url
    Args:
        str: url = url of the beacon
    """
    ids = []
    response1 = requests.get(url)
    soup = BeautifulSoup(response1.content, 'html.parser')
    soup = str(soup)
    soup = soup.split('\n')
    for id in soup:
        if not id.startswith('#'): # to cut of the header
            ids.append(id)         
    return ids


def clean_url_string(string):
    """
    Clean the name of a person.
    Args: 
        str: string raw name
    Returns: 
        str:cleaned name.
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


def createGraph():
    """
    Creates Graph 
    :return: creates .ttl-file
    :rtype: ttl
    
    """
    headers1 = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}    # simulate a browser request

    for gndID in tqdm(get_ids_from_beacon('http://www.steinheim-institut.de/ebib-djg-nrw/ebib-djg-nrw-beacon.txt')):
        url = f'http://www.steinheim-institut.de/ebib-djg-nrw/query.html?database=NRW-Bibliografie&text1={gndID}&kategorie1=gnd'
        response = requests.get(url, headers=headers1)
        soup = BeautifulSoup(response.text, 'html.parser')
        titlesss = soup.find_all('span', class_='lit_title') # find titles
        for title in titlesss:
            inbuch = title.find_next_sibling('div', class_='inbuch') # find additional information
            title = title.text.replace('\u2009\u2009', '') # clean title for human readable string
            title = title.replace('[Online-Ressource]', '')
            title = title.replace('\n', '')
            title = title.replace('\\', '')
            title = title.strip()
            title = ' '.join(filter(None, title.split()))
            cleantitle = clean_url_string(title)
            cleantitle = cleantitle.decode('utf-8')
            cleantitle = str(cleantitle) # clean title for urigeneration
            uri = URIRef(f'http://data.judaicalink.org/data/nrwbibdjg/{cleantitle}') # generate uri for Work
            graph.add((URIRef(uri), RDF.type, URIRef(gndo + "Work"))) 
            graph.add((URIRef(uri), jl.describedAt, Literal(url)))
            graph.add((URIRef(uri), dc.title, Literal(title)))
            graph.add((URIRef(uri), URIRef(gndo + "author"), URIRef(f'http://data.judaicalink.org/data/nrwbibdjg/{gndID}')))
            
            if inbuch:
                inbuch = inbuch.text.strip()
                inbuch = inbuch.replace('\n', '') 
                inbuch = inbuch.replace('→ Ressource in externer Webseite betrachten ...', '')
                inbuch = inbuch.strip()
                inbuch = ' '.join(filter(None, inbuch.split()))
                graph.add((URIRef(uri), jl.hasAbstract, Literal(inbuch)))
            add_creation_date(graph, uri)
            graph.serialize(destination=file_name, format="turtle")
            
        uri = URIRef(f'http://data.judaicalink.org/data/nrwbibdjg/{gndID}') # generate uri for Person from GND-ID
        graph.add((URIRef(uri), RDF.type, foaf.Person)) 
        for pair in get_gnd_ttl_data(gndID, uri, graph):   # enrich data with information from gnd
            
            obj = pair[1]
            prefix, predicate_name = pair[0].split(".")
                                                             # Explicitly use the bound namespace to create the predicate URI
            if prefix == 'gndo':
                predicate_uri = gndo[predicate_name]
            elif prefix == 'owl':
                predicate_uri = owl[predicate_name]
            elif prefix == 'foaf':
                predicate_uri = foaf[predicate_name]
            elif prefix == 'skos':
                predicate_uri = skos[predicate_name]
            elif prefix == 'jl':
                predicate_uri = jl[predicate_name]
            elif prefix == 'edm':
                predicate_uri = edm[predicate_name]
            elif prefix == 'dc':
                predicate_uri = dc[predicate_name]
            elif prefix == 'dcterms':
                predicate_uri = dcterms[predicate_name]
            elif prefix == 'rdfs':
                predicate_uri = rdfs[predicate_name]
            elif prefix == 'geo':
                predicate_uri = geo[predicate_name]
            else:
                predicate_uri = URIRef(f"http://{prefix}/{predicate_name}")  # fallback for unknown rrefixes

            if obj.startswith('http'):
                obj = URIRef(obj)
                graph.add((uri, predicate_uri, obj))
            else:
                graph.add((uri, predicate_uri, Literal(obj)))
            add_creation_date(graph, uri)
            graph.serialize(destination=file_name, format="turtle")

    print('graph created')

# Usage example
createGraph()


zip_file(file_name)

move_ttl_file(file_name + '.gz')