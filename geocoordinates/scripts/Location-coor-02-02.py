# this code assigns the Geo-coordinates to the JudaicaLink cities
# 03/07/2018
# Maral Dadvar


from SPARQLWrapper import SPARQLWrapper2, XML, RDF, TURTLE
from rdflib import Namespace, URIRef, Graph, Literal
from rdflib.namespace import RDF

sparql = SPARQLWrapper2("http://localhost:3030/Datasets/sparql")

graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace("http://purl.org/dc/elements/1.1/")
geo = Namespace("http://www.opengis.net/ont/geosparql#")

graph.bind('skos', skos)
graph.bind('foaf', foaf)
graph.bind('jl', jl)
graph.bind('gndo', gndo)
graph.bind('owl', owl)
graph.bind('edm', edm)
graph.bind('dc', dc)
graph.bind('geo', geo)


def generator_gnd(city):
    city2 = "'" + city.encode('utf-8') + "'"
    print(city2)

    spar2 = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX gndo: <http://d-nb.info/standards/elementset/gnd#>
    PREFIX pro: <http://purl.org/hpi/patchr#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX edm: <http://www.europeana.eu/schemas/edm/>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dblp: <http://dblp.org/rdf/schema-2015-01-26#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX bibtex: <http://data.bibbase.org/ontology/#>
    PREFIX geo:<http://www.opengis.net/ont/geosparql#>

        select ?place ?coo ?geo ?same

        WHERE{{
          graph <https://data.judaicalink.org/data/gnd> {{

	       #?z gndo:placeOfBirth ?place.
           ?place gndo:preferredNameForThePlaceOrGeographicName {0}.
           ?place owl:sameAs ?same.
           ?place geo:hasGeometry ?geo.
           ?geo   geo:asWKT ?coo


          }}
          }}


        """.format(city2)

    sparql.setQuery(spar2)
    sparql.setReturnFormat(TURTLE)
    result = sparql.query().convert()

    graph.bind('skos', skos)
    graph.bind('foaf', foaf)
    graph.bind('jl', jl)
    graph.bind('gndo', gndo)
    graph.bind('owl', owl)

    print
    len(result.bindings)

    if (u"place", u"coo", u"same") in result:

        bindings = result[u"place", u"coo", u"same"]

        for b in bindings:
            print
            b

            coobase = b[u"coo"].value
            coo = coobase.replace('Point', '')
            coo = coo.strip()
            coo1 = coo.rsplit('(', 1)[1]
            coo2 = coo1.rsplit(')', 1)[0]
            coo2 = coo2.strip()
            lat = coo2.rsplit(' ', 1)[0]
            lon = coo2.rsplit(' ', 1)[1]

            gnd = b[u"place"].value
            same = b[u"same"].value

            cityuri = 'http://data.judaicalink.org/data/' + city.encode('utf-8')
            cityuri = cityuri.replace(' ', '')
            if '(' in cityuri:
                cityuri = cityuri.rsplit('(', 1)[0]
            print
            cityuri

            graph.add((URIRef(cityuri), RDF.type, skos.Concept))
            graph.add((URIRef(cityuri), jl.lat, (Literal(lat))))
            graph.add((URIRef(cityuri), jl.lon, (Literal(lon))))
            graph.add((URIRef(cityuri), geo.asWKT, (Literal(coobase))))
            graph.add((URIRef(cityuri), gndo.gndIdentifier, (URIRef(gnd))))
            graph.add((URIRef(cityuri), owl.sameAs, (URIRef(same))))
            graph.add((URIRef(cityuri), skos.prefLabel, (Literal(city))))

        return


sparql.setQuery("""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX gndo: <http://d-nb.info/standards/elementset/gnd#>
    PREFIX pro: <http://purl.org/hpi/patchr#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX edm: <http://www.europeana.eu/schemas/edm/>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dblp: <http://dblp.org/rdf/schema-2015-01-26#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX jl: <http://data.judaicalink.org/ontology/>
    PREFIX bibtex: <http://data.bibbase.org/ontology/#>
    PREFIX geo:<http://www.opengis.net/ont/geosparql#>

SELECT distinct ?y

from <https://data.judaicalink.org/data/bhr>
from <https://data.judaicalink.org/data/djh>
from <https://data.judaicalink.org/data/freimann-gnd>
from <https://data.judaicalink.org/data/gnd-persons>
from <https://data.judaicalink.org/data/rujen>
from <https://data.judaicalink.org/data/yivo>
from <https://data.judaicalink.org/data/ub-gnd>

WHERE {
    ?x ( jl:birthLocation | jl:deathLocation) ?y.
}


""")

sparql.setReturnFormat(XML)

results = sparql.query().convert()

if (u"y") in results:

    bindings = results[u"y"]

    for item in bindings:
        city = item[u"y"].value

        city = city.replace("'", '')
        city = city.replace("/", '')
        city = city.strip()

        print(city)
        generator_gnd(city)

graph.serialize(destination='city-geocoor-04-all.ttl', format="turtle")
