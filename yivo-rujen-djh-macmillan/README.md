judaicalink-crawler
===================

This directory contains simple converters for the YIVO, RUJEN and DJH
encyclopedias. The original CoffeeScript implementation has been
replaced by Python scripts using `rdflib`.

Each script reads the JSON exported by the crawler and writes a Turtle
file with the corresponding RDF data. Concepts are linked to their
encyclopedia specific concept scheme via `skos:inScheme` and each
scheme is described explicitly in the output.

Usage examples:

```
python yivo_json_to_rdf.py output.json yivo.ttl
python rujen_json_to_rdf.py rujen.json rujen.ttl
python djh_json_to_rdf.py djh.json djh.ttl
```
