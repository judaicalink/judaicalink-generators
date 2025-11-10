import os, pickle, urllib.parse
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import OWL, RDFS
from SPARQLWrapper import SPARQLWrapper, JSON, XML
to_enrich = {}
# Format 1 (city-geocoor and geo_interlinks)
# data.judaicalink.org/data/Aachen owl:sameAs sws.geonames.org/3247449
# data.judaicalink.org/data/geonames/10363016 owl:sameAs sws.geonames.org/10363016
g = Graph()
g.parse('city-geocoor-05.ttl', format='ttl')
g.parse('geo_interlinks.ttl', format='ttl')
for s,p,o in g.triples((None, OWL.sameAs, None)):
    if o.startswith("http://sws.geonames.org/"):
        if str(o) not in to_enrich:
            to_enrich[str(o)] = set([])
        to_enrich[str(o)].add(str(s))
# Format 2
# resource jl:deathLocationURI data.judaicalink.org/data/geonames/239845
jl = Namespace("http://data.judaicalink.org/ontology/")

datasets = ["bhr-final-05.ttl", "djh.ttl", "generated_persons_GND_enriched.ttl", "Haskala_enriched.ttl", "HirschFamily.ttl", "ubffm-authors.ttl"]
for dataset in datasets:
    graph = Graph()
    graph.bind('jl', jl)
    graph.parse(dataset, format='ttl')
    for s,p,o in graph.triples((None, jl.birthLocationURI, None)):
        if o.startswith('http://data.judaicalink.org/data/geonames/'):
            loc_id = o.lstrip('http://data.judaicalink.org/data/geonames/')
            geonames_url = 'http://sws.geonames.org/'+loc_id
            if geonames_url not in to_enrich:
                to_enrich[geonames_url] = set([])
            to_enrich[geonames_url].add(str(o))
    for s,p,o in graph.triples((None, jl.deathLocationURI, None)):
        if o.startswith('http://data.judaicalink.org/data/geonames/'):
            loc_id = o.lstrip('http://data.judaicalink.org/data/geonames/')
            geonames_url = 'http://sws.geonames.org/'+loc_id
            if geonames_url not in to_enrich:
                to_enrich[geonames_url] = set([])
            to_enrich[geonames_url].add(str(o))
sparql = SPARQLWrapper("http://www.lotico.com:3030/lotico/sparql")
sparql.setQuery("""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX gn:<http://www.geonames.org/ontology#>
    SELECT ?s ?dbp ?wiki
    WHERE {
        ?s rdfs:seeAlso ?dbp .
        ?s gn:wikipediaArticle ?wiki
        }
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
enriched = []
count = 0
for r in results['results']['bindings']:
    geonames_uri = r['s']['value'].rstrip('/')
    if geonames_uri in to_enrich:
        dbp_uri = urllib.parse.unquote(r['dbp']['value'])
        wiki_uri = urllib.parse.unquote(r['wiki']['value'])
        jl_resources = to_enrich[geonames_uri]
        for jl_resource in jl_resources:
            enriched.append([jl_resource, dbp_uri, wiki_uri])
geo_linking = Graph()
geo_linking.bind('owl', OWL)
for (jl_res, dbp_res, wiki_res) in enriched:
    geo_linking.add((URIRef(jl_res), OWL.sameAs, URIRef(dbp_res)))
    geo_linking.add((URIRef(jl_res), OWL.sameAs, URIRef(wiki_res)))
geo_linking.serialize('dbp_wiki_geo_linking.ttl', format='ttl')
