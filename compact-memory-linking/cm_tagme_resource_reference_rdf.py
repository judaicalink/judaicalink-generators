import os, pickle, json, pprint
from rdflib import Graph, URIRef, Namespace, Literal, XSD
from rdflib.namespace import RDF, OWL
with open('cm_tagme_resource_reference_data.pickle', 'rb') as infile:
    data = pickle.load(infile)
# instantiate graphs
cm_tagme_resources = Graph()
cm_tagme_references = Graph()

# define Namespaces
jl = Namespace("http://data.judaicalink.org/ontology/")

# bindings
cm_tagme_resources.bind('rdf', RDF)
cm_tagme_references.bind('rdf', RDF)
cm_tagme_resources.bind('jl', jl)
cm_tagme_references.bind('jl', jl)
# may take a while...
mention_count = 0
for mention in data:
    
    mention_count += 1
    resource = URIRef(mention['resource'])
    reference = URIRef(mention['ref'])
    spot = Literal(mention['spot'])
    page = URIRef("http://data.judaicalink.org/data/compact-memory/"+mention['page_id'])
    start = Literal(mention['start'])
    end = Literal(mention['end'])
    link_prob = Literal(mention['link_prob'], datatype=XSD.float)
    rho = Literal(mention['rho'], datatype=XSD.float)
    # populate datasets    
    cm_tagme_resources.add((resource, jl.hasReference, reference))

    cm_tagme_references.add((reference, RDF.type, jl.Reference))
    cm_tagme_references.add((reference, jl.isOnPage, page))
    cm_tagme_references.add((reference, jl.hasSpot, spot))
    cm_tagme_references.add((reference, jl.hasStart, start))
    cm_tagme_references.add((reference, jl.hasEnd, end))
    cm_tagme_references.add((reference, jl.hasLinkProb, link_prob))
    cm_tagme_references.add((reference, jl.hasRho, rho))

print("Processed {} mentions.".format(mention_count))
print("Generated {} triples for resources.".format(len(cm_tagme_resources)))
print("Generated {} triples for references.".format(len(cm_tagme_references)))
cm_tagme_resources.serialize(destination="cm_tagme_resources.ttl", format="ttl")
cm_tagme_references.serialize(destination="cm_tagme_references.ttl", format="ttl")
