# this code extarcts the content of the encyclopedia page into a csv file.
# 25/July/2017
# Maral Dadvar


import csv
import re
from rdflib import Namespace, Graph
from rdflib.namespace import OWL

output = open('../output/Encycoutput.csv', 'w')

output.writelines([str('fn'), ',', str('ln'), ',', str('geb'), ',', str('gest'), ',', str('BHR'), '\n'])

graph = Graph()

ma = Namespace("http://maral.wisslab.org/rdf/schema#")
Springer = Namespace("http://lod.springer.com/data/ontology/schema#")

graph.bind('ma', ma)
graph.bind('Springer', Springer)
graph.bind('owl', OWL)

data = csv.reader(open('./new1-cleaned.csv'))
fields = data.next()
eventdic = {}

for row in data:

    fn = ''
    ln = ''
    geb = ''
    gest = ''
    bhr1 = False
    bhr2 = False
    misc1 = ''
    misc2 = ''
    misc3 = ''
    misc4 = ''
    misc5 = ''
    misc6 = ''

    items = zip(fields, row)
    item = {}
    for (name, value) in items:
        item[name] = value.strip()

    firstname = item['fn'].strip()
    fn = firstname.rsplit('[', 1)[0]
    fn = fn.replace('[', '')
    fn = fn.replace(']', '')

    lastname = item['ln'].strip()

    if 'gest.' in lastname:
        ln = ''
    elif 'geb.' in lastname:
        ln = ''

    else:
        ln = lastname.rsplit('[', 1)[0]
        ln = ln.replace('[', '')
        ln = ln.replace(']', '')

    misc1 = item['misc1'].strip()
    misc2 = item['misc2'].strip()
    misc3 = item['misc3'].strip()
    misc4 = item['misc4'].strip()
    misc5 = item['misc5'].strip()
    misc6 = item['misc6'].strip()

    if 'geb.' in misc1:
        geb = re.findall(r'\d{4}', misc1)

    elif 'geb.' in lastname:
        geb = re.findall(r'\d{4}', lastname)

    elif 'geb.' in misc2:

        geb = re.findall(r'\d{4}', misc2)
    elif 'geb.' in misc3:

        geb = re.findall(r'\d{4}', misc3)
    elif 'geb.' in misc4:

        geb = re.findall(r'\d{4}', misc4)
    elif 'geb.' in misc5:

        geb = re.findall(r'\d{4}', misc5)
    elif 'geb.' in misc6:

        geb = re.findall(r'\d{4}', misc6)

    if len(geb) == 2:
        geb = geb[0] + '-' + geb[1]
    elif len(geb) > 2:
        geb = geb[0]

    if 'gest.' in misc1:
        gest = re.findall(r'\d{4}', misc1)

    elif 'gest.' in lastname:
        gest = re.findall(r'\d{4}', lastname)

    elif 'gest.' in misc2:

        gest = re.findall(r'\d{4}', misc2)
    elif 'gest.' in misc3:

        gest = re.findall(r'\d{4}', misc3)
    elif 'gest.' in misc4:

        gest = re.findall(r'\d{4}', misc4)
    elif 'gest.' in misc5:

        gest = re.findall(r'\d{4}', misc5)
    elif 'gest.' in misc6:

        gest = re.findall(r'\d{4}', misc6)

    if len(gest) == 2:
        gest = gest[0] + '-' + gest[1]
    elif len(gest) > 2:
        gest = gest[0]

    if '[BHR1]' in misc1:
        bhr1 = True

    elif '[BHR1]' in lastname:
        bhr1 = True

    elif '[BHR1]' in firstname:
        bhr1 = True

    elif '[BHR1]' in misc2:
        bhr1 = True

    elif '[BHR1]' in misc3:
        bhr1 = True

    elif '[BHR1]' in misc4:
        bhr1 = True

    elif '[BHR1]' in misc5:
        bhr1 = True

    elif '[BHR1]' in misc6:
        bhr1 = True

    if '[BHR2]' in misc1:
        bhr2 = True

    elif '[BHR2]' in lastname:
        bhr2 = True

    elif '[BHR2]' in firstname:
        bhr2 = True

    elif '[BHR2]' in misc2:
        bhr2 = True

    elif '[BHR2]' in misc3:
        bhr2 = True

    elif '[BHR2]' in misc4:
        bhr2 = True

    elif '[BHR2]' in misc5:
        bhr2 = True

    elif '[BHR2]' in misc6:
        bhr2 = True
    # else:
    # bhr2 = False

    print(fn, ln, geb, gest, bhr1, bhr2)

    if bhr1 == True:

        output.writelines([str(fn), ',', str(ln), ',', str(geb), ',', str(gest), ',', str('BHR1'), '\n'])

    elif bhr2 == True:

        output.writelines([str(fn), ',', str(ln), ',', str(geb), ',', str(gest), ',', str('BHR2'), '\n'])

output.close()

# graph.add((URIRef(eventurl), RDF.type, URIRef('http://lod.springer.com/data/ontology/class/Conference') ))
# graph.add((URIRef(eventurl), Springer.hasSeries,(URIRef(seriesurl)) ))
# graph.add((URIRef(eventurl), Springer.confName, Literal(conf) ))
# graph.add((URIRef(eventurl), OWL.sameAs , URIRef(sameeventurl) ))
# graph.serialize(destination='output5.rdf', format="turtle")


# graph.serialize(destination='output5.rdf', format="turtle")
