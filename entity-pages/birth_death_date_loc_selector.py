import pprint, os
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Namespace, Literal
sparql = SPARQLWrapper("http://localhost:3030/judaicalink/sparql")
sparql.setQuery("""
    PREFIX jl: <http://data.judaicalink.org/ontology/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?ep ?same ?bd ?dd ?bl ?dl
    WHERE {
        GRAPH <http://data.judaicalink.org/data/ep> {
            ?ep owl:sameAs ?same 
        }
        {?same jl:birthDate ?bd} UNION {?same jl:deathDate ?dd} UNION
        {?same jl:birthLocation ?bl} UNION {?same jl:deathLocation ?dl}
        }
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
# gather birth/death date and birth/death location for each entity corresponding to the entity page
metadata = {}
for res in results['results']['bindings']:
    ep = res['ep']['value']
    
    if ep not in metadata:
        metadata[ep] = {'bd': {}, 'dd': {}, 'bl': {}, 'dl': {}}
    
    if 'bd' in res.keys() and res['bd'] != '':
        bd = res['bd']['value']
        if bd not in metadata[ep]['bd']:
            metadata[ep]['bd'][bd] = 0
        metadata[ep]['bd'][bd] += 1
        
    if 'dd' in res.keys() and res['dd'] != '':
        dd = res['dd']['value']
        if dd not in metadata[ep]['dd']:
            metadata[ep]['dd'][dd] = 0
        metadata[ep]['dd'][dd] += 1
        
    if 'bl' in res.keys() and res['bl'] != '':
        bl = res['bl']['value']
        if bl not in metadata[ep]['bl']:
            metadata[ep]['bl'][bl] = 0
        metadata[ep]['bl'][bl] += 1
        
    if 'dl' in res.keys() and res['dl'] != '':
        dl = res['dl']['value']
        if dl not in metadata[ep]['dl']:
            metadata[ep]['dl'][dl] = 0
        metadata[ep]['dl'][dl] += 1
def same_count_value(count_dict):
    # checks if items counts in an 'item': count dict have the same value
    vals = set(list(count_dict.values()))
    if len(vals) == 1:
        return True
    else:
        return False
# pick the date and the place
output = {k: {'bd': None, 'dd': None, 'bl': None, 'dl': None} for k in metadata.keys()}
for ep, data in metadata.items():
    # birth/death dates
    for prop in ('bd', 'dd'):
    
        if len(data[prop]) == 1:
            output[ep][prop] = list(data[prop].keys())[0]
        elif len(data[prop]) > 1:
            if same_count_value(data[prop]) is True:
                # take the shortest key, which usually corresponds to the year, ex. '1838'
                shortest = sorted([k for k in data[prop] if k != ''], key=len)
                output[ep][prop] = shortest[0]
            else:
                # take the key with the highest count
                output[ep][prop] = max(data[prop], key=data[prop].get)
    
    # birth/death locations
    for prop in ('bl', 'dl'):
        if len(data[prop]) == 1:
            output[ep][prop] = list(data[prop].keys())[0]
        elif len(data[prop]) > 1:
            if same_count_value(data[prop]) is True:
                # TO DO: heuristic for choosing between places
                pass
            else:
                # take the key with the highest count
                output[ep][prop] = max(data[prop], key=data[prop].get)
# generate rdf
g = Graph()
jl = Namespace('http://data.judaicalink.org/ontology/')
g.bind('jl', jl)
for ep, data in output.items():
    s = URIRef(ep)
    for prop, value in data.items():
        if value != None and value != "":
            o = Literal(value)
            if prop == 'bd':            
                g.add((s, jl.birthDate, o))
            elif prop == 'dd':
                g.add((s, jl.deathDate, o))
            elif prop == 'bl':
                g.add((s, jl.birthLocation, o))
            elif prop == 'dl':
                g.add((s, jl.deathLocation, o))
g.serialize('ep_birth_death_date_loc.ttl', format='ttl')
