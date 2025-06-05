# The script generates a triple that qualifies an entity page as a person
# the dbpedia FOAF.Person Class is used
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, FOAF
sparql = SPARQLWrapper("http://data.judaicalink.org/sparql/query")
sparql.setQuery("""
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX jl: <http://data.judaicalink.org/ontology/>
    SELECT ?ep
    WHERE {
        GRAPH <http://data.judaicalink.org/data/ep> {
            ?ep owl:sameAs ?s 
        }
        {?s rdf:type foaf:Person} UNION {?s jl:birthDate ?bd} UNION {?s jl:deathDate ?dd}
        }
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
persons = set([])
for res in results['results']['bindings']:
    ep = res['ep']['value']
    persons.add(ep)
pers = Graph()
pers.bind('rdf', RDF)
pers.bind('foaf', FOAF)
for p in persons:
    pers.add((URIRef(p), RDF.type, FOAF.Person))
pers.serialize('ep_persons.ttl', format='ttl')
