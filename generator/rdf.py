# generator/rdf.py
from rdflib import Namespace
from rdflib.namespace import RDF, RDFS, XSD, DC, DCTERMS, SKOS, FOAF

JL_DATA = Namespace("https://data.judaicalink.org/data/")
JL_DS = Namespace("https://data.judaicalink.org/datasets/")
JL_ONTO = Namespace("https://data.judaicalink.org/ontology/")

__all__ = ["JL_DATA", "JL_DS", "JL_ONTO", "RDF", "RDFS", "XSD", "DC", "DCTERMS", "SKOS", "FOAF"]
