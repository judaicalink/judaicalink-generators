import rdflib
import SPARQLWrapper as sw

prefixes = []
prefixes.append(('skos', 'http://www.w3.org/2004/02/skos/core#'))
prefixes.append(('gndo', 'http://d-nb.info/standards/elementset/gnd#'))

sparql = sw.SPARQLWrapper2("http://zbw.eu/beta/sparql/gnd/query")

def get_prefixes():
    return "\n".join(["PREFIX {}: <{}>".format(prefix, url) for prefix, url in prefixes])

def sparql_query(q):
    q = get_prefixes() + "\n\n" + q
    sparql.setQuery(q)
    return sparql.query()
res = sparql_query('''
SELECT DISTINCT ?forename ?forename2 WHERE {
        ?s a gndo:UndifferentiatedPerson .
        ?s gndo:preferredNameEntityForThePerson ?pne .
        ?pne gndo:forename ?forename .
            ?s gndo:variantNameEntityForThePerson ?vne .
            ?vne gndo:forename ?forename2 .
  FILTER regex(str(?forename), "^[^ ]+$")
  FILTER regex(str(?forename2), "^[^ ]+$")
  FILTER regex(str(?forename2), "^[^.]+$")
  FILTER regex(str(?forename), "^[^.]+$")
    } LIMIT 100

''')
len(res.bindings)
res.bindings

