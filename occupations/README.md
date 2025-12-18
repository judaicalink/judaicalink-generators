# Occupations Dataset

This dataset provides a normalized and reusable representation of **occupations** derived from
literal values used in the JudaicaLink knowledge graph (property `jl:occupation`).

The goal of this dataset is to turn frequently used occupation strings (e.g. *Rabbiner*,
*Historiker*, *Verleger*) into **stable SKOS concepts** with persistent URIs that can be:

- linked consistently in Pubby and other frontends,
- enriched with external authority data (EP, GND, DBpedia),
- reused across datasets and applications.

---

## Dataset Overview

- **Slug:** `occupations`
- **Base URI:** `http://data.judaicalink.org/data/occupation/`
- **Concept type:** `skos:Concept`
- **Ontology:** <https://ontology.judaicalink.org/judaicalink-ontology.ttl>

Each occupation is represented as a SKOS concept with at least:

- `skos:prefLabel` (original occupation literal)
- `dcterms:source` (this dataset)

Optional enrichment links may include:

- `skos:exactMatch` → Entity Pages (EP)
- `skos:exactMatch` → GND
- `owl:sameAs` → DBpedia

---

## Data Source

The dataset is generated from the **union graph** of the JudaicaLink triple store.

All distinct literal values of:

