# This script selects a preferred label and all alternative labels
# for entity pages.
import os
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Namespace, Literal
from rdflib.namespace import SKOS
# query preferred labels
sparql = SPARQLWrapper("http://data.judaicalink.org/sparql/query")
sparql.setQuery("""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?ep ?o ?pl (lang(?pl) as ?lang)
    WHERE {
        GRAPH <http://data.judaicalink.org/data/ep> {
            ?ep owl:sameAs ?o 
        }
        ?o skos:prefLabel ?pl
        }
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
# process preferred labels
pref_labels = {}
ep_to_labels = {}
for res in results['results']['bindings']:
    ep = res['ep']['value']
    uri = res['o']['value']
    pl = res['pl']['value']

    if '/gnd/' in uri: # take gnd pref label if available
        pref_labels[ep] = pl
    else: # count the number of times a given pref label is associated to an ep
        if ep not in ep_to_labels:
            ep_to_labels[ep] = {pl: 1}
        else:
            if pl not in ep_to_labels[ep]:
                ep_to_labels[ep][pl] = 0
            ep_to_labels[ep][pl] += 1

for ep, labs in ep_to_labels.items():
    if ep not in pref_labels: # if the label has not been found yet
        labs_set = set(labs.values())
        if len(labs_set) == 1: # all labels have the same frequency: take the first in lexicographic order
            sorted_labs = sorted([(k,v) for k,v in labs.items()], key=lambda x:x[0])
            pref_labels[ep] = sorted_labs[0][0]
        else: # take the most frequent label
            pref_labels[ep] = max(labs, key=labs.get)
# query alternative labels
sparql = SPARQLWrapper("http://data.judaicalink.org/sparql/query")
sparql.setQuery("""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX xml: <http://www.w3.org/XML/1998/namespace/>
    SELECT ?ep ?o ?al (lang(?al) as ?lang)
    WHERE {
        GRAPH <http://data.judaicalink.org/data/ep> {
            ?ep owl:sameAs ?o 
        }
        ?o skos:altLabel ?al .
        }
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
# process alternative labels
alt_labels = {}
for res in results['results']['bindings']:
    ep = res['ep']['value']
    al = res['al']['value'].strip('@') # see https://data.judaicalink.org/data/html/gnd/1073923363
    al = ' '.join(al.split('@')) # see http://data.judaicalink.org/data/ep/1024745 
    lang = res['lang']['value']
    
    if lang != '':
        al = al+'@'+lang
    
    if ep not in alt_labels:
        alt_labels[ep] = set([])
    alt_labels[ep].add(al)
# serialize
g = Graph()
g.bind('skos', SKOS)
for ep, pref_label in pref_labels.items():
    s = URIRef(ep)
    o = Literal(pref_label)
    g.add((s, SKOS.prefLabel, o))
for ep, alt_labs in alt_labels.items():
    for alt_lab in alt_labs:
        s = URIRef(ep)
        if '@' in alt_lab:
            label, label_lang = alt_lab.split('@')
            o = Literal(label, lang=label_lang)
        else:
            o = Literal(alt_lab)
        
        g.add((s, SKOS.altLabel, o))
g.serialize('ep_labels.ttl', format='ttl')
