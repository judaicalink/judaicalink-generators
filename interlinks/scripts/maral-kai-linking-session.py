import rdflib
import SPARQLWrapper as sw

prefixes = []
prefixes.append(('skos', 'http://www.w3.org/2004/02/skos/core#'))

sparql = sw.SPARQLWrapper2("http://data.judaicalink.org/sparql/query")

def get_prefixes():
    return "\n".join(["PREFIX {}: <{}>".format(prefix, url) for prefix, url in prefixes])

def sparql_query(q):
    q = get_prefixes() + "\n\n" + q
    sparql.setQuery(q)
    return sparql.query()

def get_named_graphs():
    result = sparql_query('SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }')
    return [ b['g'].value for b in result.bindings]


def get_all_resources(dataset):
    query = "SELECT DISTINCT ?s WHERE {{ GRAPH <{0}> {{?s ?p ?o}} }}".format(dataset)
    result = sparql_query(query)
    return [ b['s'].value for b in result.bindings]

def get_labels(uri):
    query = """
    SELECT DISTINCT ?l WHERE {{
    
        {{ <{}> skos:prefLabel ?l  }}
        UNION
        {{ <{}> skos:altLabel ?l  }}
    
    }}
    """.format(uri, uri)
    result = sparql_query(query)
    return [ b['l'].value for b in result.bindings]

def get_resource_by_label(ds, labels):
    query = """
        select DISTINCT ?s WHERE {{
            GRAPH <{}> {{
                {{
                
                {}
                
                }}
            
            }}
        }} 
    """.format(ds, "\n} UNION {\n".join(['{{ ?s skos:prefLabel "{}" }} UNION {{ ?s skos:altLabel "{}" }}'.format(l, l) for l in labels]))
    # print(query)
    result = sparql_query(query)
    return [ b['s'].value for b in result.bindings]





print ("\n".join(get_named_graphs()))

ds1 = 'http://data.judaicalink.org/data/yivo'
ds2 = 'http://data.judaicalink.org/data/dbpedia-persons'
ds3 = 'http://data.judaicalink.org/data/gnd-persons'

yivo_resources = get_all_resources(ds1)
len(yivo_resources)
labels = get_labels('http://data.judaicalink.org/data/yivo/Abeles_Shimon')
get_resource_by_label(ds2, labels)
labels
labels
labels[0]

shimon = yivo_resources[0]
labels = get_labels(shimon)

get_resource_by_label(ds2, labels)
testlabels = ['ʾLPNDʾRY, ʾHRN BN MŠH', 'another name']
get_resource_by_label(ds2, testlabels)
linked_resources = []
count = 0
for res in yivo_resources:
    count += 1
    print('.', end='')
    if count % 100 == 0:
        print(' {}'.format(count))
    labels = get_labels(res)
    try:
        result = get_resource_by_label(ds2, labels)
        if len(result) > 0:
            linked_resources.extend(result)
    except Exception as e:
        print('Error on {} with these labels: {}'.format(res, labels))

len(linked_resources)
get_resource_by_label(ds3,['Abeles, Shim‘on'])

