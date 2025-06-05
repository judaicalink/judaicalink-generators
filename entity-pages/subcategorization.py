# this script generates subcategorization triples for entity pages
# resources "natively" belonging to JL are further described by a jl:represents property
# entity_page_uri jl:represents local_judaicalink_resource_uri
import pprint, pickle, os, logging
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDF, OWL, RDFS
g = Graph()
jl = Namespace("http://data.judaicalink.org/ontology/")
g.bind('jl', jl)
# query entity pages
sparql = SPARQLWrapper("http://data.judaicalink.org/sparql/query")
sparql.setQuery("""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?ep ?resource
    WHERE {
        GRAPH <http://data.judaicalink.org/data/ep> {
            ?ep owl:sameAs ?resource
        }}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
internal_prefix = "http://data.judaicalink.org/"
for res in results['results']['bindings']:
    ep = res['ep']['value']
    resource = res['resource']['value']
    if resource.startswith(internal_prefix):
        resource_uri = URIRef(resource)
        ep_uri = URIRef(ep)
        g.add((ep_uri, jl.represents, resource_uri))
# double check
for (s,p,o) in g.triples((None,None,None)):
    assert s.startswith('http://data.judaicalink.org/data/ep/')
g.serialize(destination='subcategorization.ttl', format='ttl')
