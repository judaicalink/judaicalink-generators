from rdflib import Graph, URIRef
from rdflib.namespace import OWL
# FUNCTIONS FOR POOL GENERATION (Preprocessing)

def get_next_index(index):
    next_i = None
    if index == {}:
        next_i = 0
    else:
        idxs = {i for i in index.keys()}
        last_i = max(idxs)
        next_i = last_i + 1

    return next_i


def create_new_pool(index, inv_index, res_1, res_2, next_i=None):
    if next_i is None:
        new_pool_i = get_next_ep_index(index)
    else:
        new_pool_i = next_i
    index[new_pool_i] = {res_1, res_2}
    inv_index[res_1] = new_pool_i
    inv_index[res_2] = new_pool_i
    return index, inv_index

def create_new_singleton_pool(index, inv_index, resource, next_i=None):
    if next_i is None:
        new_pool_i = get_next_ep_index(index)
    else:
        new_pool_i = next_i
    index[new_pool_i] = {resource}
    inv_index[resource] = new_pool_i
    return index, inv_index

def update_pool(index, inv_index, pool_i, new_res):
    index[pool_i].add(new_res)
    inv_index[new_res] = pool_i
    return index, inv_index



def merge_pools(ep_1, ep_2, index, inv_index, next_i):
    new_pool_i = get_next_index(index)
    # populate new ep with resources from ep_1 and ep_2
    new_pool = {new_pool_i: index[ep_1].union(index[ep_2])}
    # update inverted index
    for resource in new_pool[new_pool_i]:
        inv_index[resource] = new_pool_i
    # update index
    index.update(new_pool)
    del index[ep_1]
    del index[ep_2]
    
    return index, inv_index


# FUNCTIONS FOR ENTITY PAGE GENERATION

def get_next_ep_index(index):
    next_idx = None
    if index == {}:
        next_idx = 1000000
    else:
        idxs = {int(ep_uri.split('/')[-1]) for ep_uri in index.keys()}
        last_idx = max(idxs)
        next_idx = last_idx + 1

    return next_idx


def create_new_ep(index, inv_index, res_1, res_2, next_i=None):
    if next_i is None:
        new_ep_uri = "http://data.judaicalink.org/data/ep/"+str(get_next_ep_index(index))
    else:
        new_ep_uri = "http://data.judaicalink.org/data/ep/"+str(next_i)
    index[new_ep_uri] = {res_1, res_2}
    inv_index[res_1] = new_ep_uri
    inv_index[res_2] = new_ep_uri
    return index, inv_index

def generate_ep_graph(index, save=False, return_graph=False, outpath="", rdf_format=''):
    ep_graph = Graph()
    ep_graph.bind('owl', OWL)
    for ep_uri, aliases in index.items():
        for alias in aliases:
            s = URIRef(ep_uri)
            o = URIRef(alias)
            ep_graph.add((s, OWL.sameAs, o))
            
    if save is True:
        ep_graph.serialize(outpath, rdf_format)
        
    if return_graph is True:
        return ep_graph