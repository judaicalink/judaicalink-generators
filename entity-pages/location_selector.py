# The script generates a triple that qualifies an entity page as a location
# the dbpedia dbo.Place Class is used
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDF
sparql = SPARQLWrapper("http://data.judaicalink.org/sparql/query")
sparql.setQuery("""
    PREFIX jl: <http://data.judaicalink.org/ontology/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX wgs84: <http://www.w3.org/2003/01/geo/wgs84_pos#>
    SELECT DISTINCT ?ep ?b_place ?d_place
    WHERE {
        GRAPH <http://data.judaicalink.org/data/ep> {
            ?ep owl:sameAs ?place
        }
        {?s jl:deathLocationURI ?place} UNION {?s jl:birthLocationURI ?place} UNION
        {?place geo:asWKT ?coords} UNION {?place wgs84:lat ?lat} UNION {?place wgs84:long ?long}
        }
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
locations = set([])
for res in results['results']['bindings']:
    ep = res['ep']['value']
    locations.add(ep)
locs = Graph()
dbo = Namespace('http://dbpedia.org/ontology/')
locs.bind('dbo', dbo)
locs.bind('rdf', RDF)
for l in locations:
    locs.add((URIRef(l), RDF.type, dbo.Place))
locs.serialize('ep_locations.ttl', format='ttl')
