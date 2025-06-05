import os, pickle, pprint
from rdflib import Graph, URIRef, Namespace, Literal, XSD
from rdflib.namespace import RDF, OWL
with open('cm_tagme_pages_data.pickle', 'rb') as infile:
    cm_tagme_pages_data = pickle.load(infile)
cm_tagme_pages = Graph()

# define Namespaces
jl = Namespace("http://data.judaicalink.org/ontology/")
# bindings
cm_tagme_pages.bind('jl', jl)
# generate page, journal and visual representation triples
datapoint_count = 0
for datapoint in cm_tagme_pages_data:
    datapoint_count += 1
    page = URIRef("http://data.judaicalink.org/data/compact-memory/"+datapoint['full_page'])
    journal = URIRef("http://data.judaicalink.org/data/compact-memory/"+datapoint['journal'])
    journal_title = Literal(datapoint['journal_name'], datatype=XSD.string)
    if datapoint['issue'] != '':
        issue = URIRef("http://data.judaicalink.org/data/compact-memory/"+datapoint['issue'])
    else:
        issue = None
    pageview = URIRef("http://sammlungen.ub.uni-frankfurt.de/cm/periodical/pageview/"+datapoint['page'])
    journalview = URIRef("http://sammlungen.ub.uni-frankfurt.de/cm/periodical/pageview/"+datapoint['journal'])

    # populate graph
    if issue != None:
        cm_tagme_pages.add((page, jl.belongsToIssue, issue))
        cm_tagme_pages.add((issue, jl.belongsToJournal, journal))
    cm_tagme_pages.add((journal, jl.title, journal_title))


    cm_tagme_pages.add((page, jl.hasVisualRepresentation, pageview))
    cm_tagme_pages.add((journal, jl.hasVisualRepresentation, journalview))
print("Processed {} datapoints.".format(datapoint_count))
print("Generated {} triples in this dataset.".format(len(cm_tagme_pages)))
cm_tagme_pages.serialize(destination="cm_tagme_pages.ttl", format="ttl")
