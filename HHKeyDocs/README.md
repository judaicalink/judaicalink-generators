# Hamburger Schlüsseldokumente zur deutsch-jüdischen Geschichte

Hamburger Schlüsseldokumente zur deutsch-jüdischen Geschichte is an online source edition realized by the Institute for the History of German Jews

## How does it work

A general overview can be found [here](https://schluesseldokumente.net/ueber/technische-umsetzung).

## Scanning data

A list of all identifiers can be found [here](https://schluesseldokumente.net/person/gnd/beacon). An identifier pasted in https://schluesseldokumente.net/person/gnd/{identifier}.jsonld, will return a JSON-File of the person identified. A Record contains name, birthdate, deathdate, birthlocation, deathlocation and a description (and some more data).  Name, birthdate, deathdate, birthlocation and deathlocation are used to build a graph. Description is split  by blanks and the terms are compared to a list of job titels generatet in a [wikidata-SPARQL-query](https://w.wiki/8D4A).

## How to use

Run the script generator.py in the folder HHKeyDocs. The script generates a ttl file.
