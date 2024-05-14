import requests
from rdflib import Graph, Namespace

def get_gnd_ttl_data(gndid, uri, graph):
    

    """
    not valid yet 
    Function creates new präfixes
    """

    # DODO Change fuction, that now new new präfixes are generated (see gnd_dataenrichment.ipynb)
    headers = {'Accept': 'text/turtle'} 
    gnd_url = f'http://d-nb.info/gnd/{gndid}/about/lds'
    response = requests.get(gnd_url, headers=headers)
    
    if response.status_code == 200:
        # Parse the Turtle data
        g = Graph()
        g.parse(data=response.text, format='turtle')

        # Define namespaces
        gndo = Namespace("https://d-nb.info/standards/elementset/gnd#")
        
        # Filter triples with predicate 'gndo' or 'd-nb'
        gndo_triples = [(s, p, o) for s, p, o in g if str(p).startswith(gndo) or str(p).startswith('http://d-nb.info/')]
        
        # Print filtered triples
        for triple in gndo_triples:
            if not isinstance(o, BNode):
                p = triple[1].replace('https://d-nb.info/standards/elementset/gnd#', 'gndo.')
                o = triple[2]
            # print(p)
            # print(o)
            # print('-----------------')
                graph.add((URIRef(uri), p, (Literal(o))))
            
    else:
        print(f"Request failed with status code {response.status_code}")