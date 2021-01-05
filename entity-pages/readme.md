# Entity Pages

This file describes the generation of Entity Pages for the Judaica Link dataset in the **`ep_generator.md`** script (Jupytext notebook). Generally speaking, the goal of Entity Pages is to explicitly group existing URI references in a dataset that belong together, i.e., that refer to the same entity. In the Linked Data paradigm, URI references that refer to the same entity are usually connected via an [owl:sameAs](https://www.w3.org/TR/owl-ref/#sameAs-def) property.  
Since the Judaica Link dataset might change over time, thus introducing new or deleting existing owl:sameAs statements, the script is designed to keep track of such changes and update entity pages accordingly. To this aim, the script creates a directory for each run, where output data are then stored. The same holds for log files.  
The **`ep_manager.py`** module contains all the functions used in the main script.

**`ep_generator.md`**  

INPUT: 
  * SPARQL queries  
  * `ep_old_index.pickle`: dictionary containing entity page information from the *previous* run of the script. This represents the status quo *before* the current run of the script. Example:  
  ```
  {
  "http://data.judaicalink.org/data/ep/1005301": [
        "http://catalogue.bnf.fr/ark:/12148/cb12423662g",
        "http://viaf.org/viaf/2561827",
        "http://www.isni.org/0000000122757563",
        ...
  ], ...
  }
  ```  
  * `ep_old_inv_index.pickle`: inverted dictionary w.r.t. to `ep_old_index.pickle`
  
OUTPUT(s):
  * `entity_pages.ttl`: RDF dataset mapping each entity page URI to all its corresponding URI references, for example: 
  ```
  <http://data.judaicalink.org/data/ep/1005301> owl:sameAs <http://catalogue.bnf.fr/ark:/12148/cb12423662g>,
        <http://viaf.org/viaf/2561827>,
        <http://www.isni.org/0000000122757563>,
        <http://www.wikidata.org/entity/Q1446587>,
        <https://de.wikipedia.org/wiki/Franz_Dumont>,
        <https://www.deutsche-digitale-bibliothek.de/entity/121069060>
        ...
  ```  
  
  * `ep_new_index.pickle`: dictionary containing entity page information from the *current* run of the script. This represents the status quo *after* the current run of the script. This data structure is used for generating the final .ttl file.  
  * `ep_new_inv_index.pickle`: inverted dictionary w.r.t. to `ep_new_index.pickle`
  * `merged_eps.pickle`: dictionary keeping track of merged entity pages, format `{new_ep: [old_ep_1, old_ep_2, ...]}` 
  * `splitted_eps.pickle`: dictionary keeping track of splitted entity pages.  
  
BEHAVIOR:

1. The script takes as input two SPARQL queries, along with entity page information from the previous run (`ep_old_index.pickle`, `ep_old_inv_index.pickle`). The first query returns all triples with an `owl:sameAs` predicate. The second one collects all other entities.  
2. Out of this, the script creates clusters ("pools" in the code) of resources, i.e. mutually exclusive sets of resources that belong together according to the stated `owl:sameAs` relationships. Resources that do not appear in any `owl:sameAs` statements are assigned to singleton sets.  
3. For each cluster of resources, a mapping with the previous entity pages status is produced by comparison. The mapping is the key to understand what changes the pool underwent w.r.t. the last run (old entity pages) and can result in 3 high-level cases:
      1. the mapping *is empty*, meaning that all resources from the current cluster are new, previously unknown in the dataset. A brand new entity page is minted and assigned to the cluster ("CREATE NEW" case).
      2. the current cluster maps to *exactly one* old entity page. This can lead to two subcases:  
          1. the current cluster matches exactly the old entity page cluster ("COPY" case) or it represents an update of the old cluster by new, previously unknown resources ("UPDATE" case): the old entity page URI reference is kept and either copied or updated;
          2. the current cluster is a subset of the old entity page cluster, thus the latter has to be splitted and a new entity page minted ("SPLIT" and "CREATE NEW").
      3. the current cluster maps to *more than one* old entity pages. A new entity page is minted ("CREATE NEW") and assigned to the current cluster, while each old entity page is either splitted or merged into the new one ("SPLIT", "MERGE" cases).  
4. The new updated Entity Pages RDF graph is created and stored along with all other outputs.
