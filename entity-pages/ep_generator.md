---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.2'
      jupytext_version: 1.7.1
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

```python
import pprint, pickle, os, logging
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, OWL, RDFS
import ep_manager as epm
```

```python
blacklist = ['http://www.dnb.de/DE/Service/DigitaleDienste/EntityFacts/entityfacts_node.html']

cwd = os.getcwd()
if not os.path.exists(cwd+'/runs'):
    os.mkdir(cwd+'/runs')
if not os.path.exists(cwd+'/logs'):
    os.mkdir(cwd+'/logs')

ep_old_index, ep_old_inv_index, splitted_eps, merged_eps = {}, {}, {}, {}

try:
    os.rmdir(cwd+'/runs/.ipynb_checkpoints')
except OSError:
    pass

latest = -1
current = -1
if len(os.listdir(cwd+'/runs')) != 0:
    
    for folder in os.listdir(cwd+'/runs'):
        run = int(folder.split('_')[1])
        if run > latest:
            latest = run
    ep_old_index = pickle.load(open(cwd+'/runs/run_'+str(latest)+'/ep_index.pickle', 'rb'))
    ep_old_index = {k:v for k,v in ep_old_index.items() if len(v) > 0}
    ep_old_inv_index = pickle.load(open(cwd+'/runs/run_'+str(latest)+'/ep_inv_index.pickle', 'rb'))
    current = latest + 1
    os.mkdir(cwd+'/runs/run_'+str(current))
    
else:
    os.mkdir(cwd+'/runs/run_0')
    current = 0

ep_new_index = {ep: {} for ep in ep_old_index.keys()}
ep_new_inv_index = {}

logging.basicConfig(
    filename = cwd+'/logs/run_{}.log'.format(current),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logging.info("Just set current RUN folders and loaded data structures...! Executing RUN {}.".format(current))
```

```python
logging.info("Performing queries...")
sparql = SPARQLWrapper("http://data.judaicalink.org/sparql/query")
sparql.setQuery("""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?s ?same
    WHERE { GRAPH ?g {
        ?s owl:sameAs ?same
        FILTER(!strstarts(str(?s), "http://data.judaicalink.org/data/ep/" ))
        FILTER(!strstarts(str(?same), "http://data.judaicalink.org/data/ep/" ))
        }}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
logging.info("Query 1: returned {} triples.".format(len(results['results']['bindings'])))
```

```python
sparql = SPARQLWrapper("http://data.judaicalink.org/sparql/query")
sparql.setQuery("""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?s ?p ?o
    WHERE { GRAPH ?g {
        ?s ?p ?o .
        MINUS {
            ?s owl:sameAs ?o .
        }
        }}
""")
sparql.setReturnFormat(JSON)
singleton_ents = sparql.query().convert()
logging.info("Query 2: returned {} triples.".format(len(singleton_ents['results']['bindings'])))
```

```python
singleton_resources = set()
for res in singleton_ents['results']['bindings']:
    singleton_resources.add(res['s']['value'])

    if res['o']['type'] != 'literal':
        singleton_resources.add(res['o']['value'])
```

```python
# generate temporary pools
logging.info("Generating temporary pools of entities...")

t_index = {}
t_inv_index = {}
next_t_i = epm.get_next_index(t_index)

for res in results['results']['bindings']:
    s = res['s']['value']
    same = res['same']['value']

    if s not in blacklist and same not in blacklist:
        if s in t_inv_index and same not in t_inv_index: # update existing pool
            pool_i = t_inv_index[s]
            t_index, t_inv_index = epm.update_pool(t_index, t_inv_index, pool_i, same)

        elif same in t_inv_index and s not in t_inv_index: # update existing pool
            pool_i = t_inv_index[same]
            t_index, t_inv_index = epm.update_pool(t_index, t_inv_index, pool_i, s)

        elif s not in t_inv_index and same not in t_inv_index: # standard case, create new pool
            t_index, t_inv_index = epm.create_new_pool(t_index, t_inv_index, s, same, next_t_i)
            next_t_i += 1
            
        else: # both uris are already in the index
            s_pool = t_inv_index[s]
            same_pool = t_inv_index[same]
            
            if s_pool != same_pool: # the two correponding pools are in fact the same --> MERGE
                t_index, t_inv_index = epm.merge_pools(s_pool, same_pool, t_index, t_inv_index, next_t_i)
                next_t_i += 1

# create singleton pools
for res in singleton_resources:
    if res not in t_inv_index:
        t_index, t_inv_index = epm.create_new_singleton_pool(t_index, t_inv_index, res, next_t_i)
        next_t_i += 1
    
logging.info("Done! Created {} pools for {} URIs.".format(len(t_index), len(t_inv_index)))    
```

```python
# Create entity pages from computed entity pools
logging.info("Creating entity pages from computed entity pools...")

# track activated case history
case_tracker = {
    'CREATE NEW': 0,
    'COPY': 0,
    'MERGE': 0,
    'SPLIT': 0,
    'UPDATE': 0
}

next_ep_id = epm.get_next_ep_index(ep_new_index)

for t_cluster in t_index.values():
    
    # create mapping between current cluster and previous (old) EP index
    mapping = {}
    diff = set([])
    for resource in t_cluster:
        try:
            old_ep = ep_old_inv_index[resource]
            if old_ep not in mapping:
                mapping[old_ep] = set([])
            mapping[old_ep].add(resource)
        except KeyError:
            diff.add(resource)
  

    if len(mapping) == 0:
        # create new entity page
        new_ep_URI = "http://data.judaicalink.org/data/ep/"+str(next_ep_id)
        next_ep_id += 1
        ep_new_index[new_ep_URI] = t_cluster
        for resource in t_cluster:
            ep_new_inv_index[resource] = new_ep_URI
        
        case_tracker['CREATE NEW'] += 1
    
    elif len(mapping) == 1: # current cluster maps to exactly one old entity page
        for ep_uri, ep_pool in mapping.items():
            old_ep_pool = ep_old_index[ep_uri]
            
            if old_ep_pool == ep_pool:
                # Copy the old ep in new index or update if t_cluster contains new (never seen) resources
                ep_new_index[ep_uri] = t_cluster
                for resource in t_cluster:
                    ep_new_inv_index[resource] = ep_uri
                
                if len(diff) == 0:
                    case_tracker['COPY'] += 1
                else:
                    case_tracker['UPDATE'] += 1
                    
            elif ep_pool.issubset(old_ep_pool):
                # Split old ep
                new_ep_URI = "http://data.judaicalink.org/data/ep/"+str(next_ep_id)
                next_ep_id += 1

                if ep_uri not in splitted_eps:
                    splitted_eps[ep_uri] = set()
                splitted_eps[ep_uri].add(new_ep_URI)

                ep_new_index[new_ep_URI] = t_cluster
                for resource in t_cluster:
                    ep_new_inv_index[resource] = new_ep_URI
                case_tracker['SPLIT'] += 1
                case_tracker['CREATE NEW'] += 1
    
    elif len(mapping) > 1: # current cluster maps to more than one old entity pages
        
        new_ep_URI = "http://data.judaicalink.org/data/ep/"+str(next_ep_id)
        next_ep_id += 1
        
        for ep_uri, ep_pool in mapping.items():
            old_ep_pool = ep_old_index[ep_uri]
            
            if ep_pool == old_ep_pool:
                # merge old ep into new
                merged_eps[ep_uri] = new_ep_URI
                case_tracker['MERGE'] += 1
            elif ep_pool.issubset(old_ep_pool):
                # split old ep
                if ep_uri not in splitted_eps:
                    splitted_eps[ep_uri] = set()
                splitted_eps[ep_uri].add(new_ep_URI)
                case_tracker['SPLIT'] += 1
        
        ep_new_index[new_ep_URI] = t_cluster
        for resource in t_cluster:
            ep_new_inv_index[resource] = new_ep_URI  
        case_tracker['CREATE NEW'] += 1

logging.info("Done! Generated {} entity pages.".format(len(ep_new_index)))
logging.info("Case tracker: {}".format(case_tracker))
```

```python
logging.info("Saving outputs to disk...")
with open(cwd+'/runs/run_'+str(current)+'/splitted_eps.pickle', 'wb') as outfile:
    pickle.dump(splitted_eps, outfile)
with open(cwd+'/runs/run_'+str(current)+'/merged_eps.pickle', 'wb') as outfile:
    pickle.dump(merged_eps, outfile)

with open(cwd+'/runs/run_'+str(current)+'/ep_old_index.pickle', 'wb') as outfile:
    pickle.dump(ep_old_index, outfile)
with open(cwd+'/runs/run_'+str(current)+'/ep_old_inv_index.pickle', 'wb') as outfile:
    pickle.dump(ep_old_inv_index, outfile)

with open(cwd+'/runs/run_'+str(current)+'/ep_index.pickle', 'wb') as outfile:
    pickle.dump(ep_new_index, outfile)
with open(cwd+'/runs/run_'+str(current)+'/ep_inv_index.pickle', 'wb') as outfile:
    pickle.dump(ep_new_inv_index, outfile)
```

```python
logging.info("Generating RDF graph...")
epm.generate_ep_graph(ep_new_index, save=True, return_graph=False, outpath=cwd+"/runs/run_"+str(current)+'/entity_pages.ttl', rdf_format='ttl')
logging.info("Done!")
```
