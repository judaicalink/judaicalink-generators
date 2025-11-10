# Linking Compact Memory to Judaica Link
The scripts generate both raw data and RDF datasets for linking entities (mainly persons and places) in Compact Memory to Judaica Link. Entities have been extracted from [Compact Memory](http://sammlungen.ub.uni-frankfurt.de/cm) using [TAGME](https://tagme.d4science.org/tagme/) (Ferragina and Scaiella, 2010), a tool that links textual mentions to Wikipedia entities. Additionally, using Compact Memory's metadata, we produce the corresponding RDF triples for identifying journals, issues and pages.   
The adopted procedure is as follows: taking as input the results provided by TAGME, we 1) expand it by producing DBpedia and Wikidata URLs for each found entity, 2) check for the presence of the entity in Judaica Link, and 3) link consequently, using resources of JudaicaLink which have an Entity Page. The process is two-step: first we produce raw data (scripts **`cm_tagme_resource_reference_data.py`** and **`cm_tagme_pages_data.py`**) and then generate the corresponding RDF datasets (scripts **`cm_tagme_resource_reference_rdf.py`** and **`cm_tagme_pages_rdf.py`**) from the raw data.  
CAVEAT:  
  * the `cm_tagme_resource_reference_data.py` script must be run _before_ the `cm_tagme_pages_data.py` as the latter takes as input the output of the former;  
  * the (output of) `cm_tagme_resource_reference_data.py` script depends on the current state of the Entity Pages (see [code](https://github.com/wisslab/judaicalink-generators/tree/master/entity-pages) and [data]()).

For each linked mention extracted by TAGME, we produce the following data:  
  * the URI of the resource in JudaicaLink
  * the text of the mention found in Compact Memory, along with its position (start, end)
  * confidence scores for the mention, provided by TAGME (link probability and rho)
  * reference to the page, issue and journal in Compact Memory where the mention has been found
  * reference to the Visual Library of the Frankfurt University Library where the original source (pdf) of each page can be accesssed (if available) 
 
This described procedure results in 3 cross-referenced subgraphs:  
  * **`cm_tagme_resources.ttl`**, where each resource (entity) is linked to all its references in Compact Memory;    
  * **`cm_tagme_references.ttl`**, where each reference is described (start, end, confidence, page, etc., see below);     
  * **`cm_pages.ttl`**, where each page in Compact Memory is described and referenced to its journal, issue, and visual representation in the Visual Library.  


### Raw Data Generation
**`cm_tagme_resource_reference_data.py`**  
_BEHAVIOR_ : the script produces raw data for generating the RDF dataset of entity mentions in Compact Memory. Please notice that since reference URIs are minted on the spot, this script cannot be reused. Moreover, by tuning the two parameters "link probability" and "rho" (provided by TAGME), a different number of references will be created;  
_INPUT_ :  
  1. entities extracted from the Compact Memory textual corpus using TAGME, `cm_entities_tagme.pickle`   
  2. Entity Pages inverted index `ep_inv_index.pickle`;  

_OUTPUT_ : list of dictionaries, each dict contains data for a mention ("spot") in Compact Memory (100-200 MB). Example of output:  
```
{'end': 1282,
 'journal_id': '2710055',
 'link_prob': 0.7148148417472839,
 'page_id': '2710055-2710056-2710057--019-2710121',
 'ref': 'http://data.judaicalink.org/data/cm-tagme/1000000',
 'resource': 'http://data.judaicalink.org/data/dbpedia/Franz_Mehring',
 'rho': 0.4602566361427307,
 'spot': 'Franz Mehring',
 'start': 1269}
```
 
**`cm_pages_data.py`**  
*BEHAVIOR*: The script produces raw data for generating the RDF dataset with metadata about journals, issues and pages in Compact Memory (limited to those pages where a mention has been found, dependency with previous script);  
*INPUT*:  
  1. Compact Memory metadata `CM_Seiten_Metadaten.csv`  
  2. resource and reference data `cm_tagme_resource_reference_data.pickle`, generated from the script `cm_tagme_resource_reference_data.py`;  
  
*OUTPUT*: list of dictionaries, each dict contains data about the page, the issue and the journal, for pages in Compact Memory where a mention has been found. Example of output:  
```
{'full_page': '2710055-2710056-2710057--019-2710121',
 'issue': '2710057',
 'journal': '2710055',
 'journal_name': 'Der neue Anfang',
 'page': '2710121'}
```
  

### RDF Data Generation   
**`cm_tagme_resource_reference_rdf.py`**  
*BEHAVIOR*: The script generates a) triples linking each resource to all its references in text and b) triples documenting each reference;   
*INPUT*: resource and reference raw data, `cm_tagme_resource_reference_data.pickle`;  
*OUTPUT*: two RDF dataset, `cm_tagme_resources.ttl` and `cm_tagme_references.ttl`.    
  Example resource:  
```
  <http://data.judaicalink.org/data/dbpedia/Max_Brod> jl:hasReference <http://data.judaicalink.org/data/cm-tagme/1001369>,
        <http://data.judaicalink.org/data/cm-tagme/1001382>,
        <http://data.judaicalink.org/data/cm-tagme/1001644>,
        <http://data.judaicalink.org/data/cm-tagme/1001727>,
        <http://data.judaicalink.org/data/cm-tagme/1001960>,
        ...
```
   Example reference:
```
   <http://data.judaicalink.org/data/cm-tagme/1001369> a jl:Reference ;
        jl:hasEnd 2879 ;
        jl:hasLinkProb "1"^^xsd:float ;
        jl:hasRho "0.5427975058555603"^^xsd:float ;
        jl:hasSpot "Max Brod" ;
        jl:hasStart 2871 ;
        jl:isOnPage <http://data.judaicalink.org/data/compact-memory/2895450-2895491-2895495-2900791--04528-2900907> .
```  


**`cm_pages_rdf.py`**  
*BEHAVIOR*: The script generates RDF triples describing metadata of pages, journals and issues of Compact Memory, along with links to Visual Library for pages (where available);  
*INPUT*: pages raw data `cm_pages_data.pickle`;   
*OUTPUT*: RDF dataset for pages, `cm_pages.ttl`.  
Example output data for a journal:  
```
<http://data.judaicalink.org/data/compact-memory/2580773> jl:hasVisualRepresentation <http://sammlungen.ub.uni-frankfurt.de/cm/periodical/pageview/2580773> ;
    jl:title "Bericht über das Schuljahr ... der Stiftischen Realschule mit Lyzeum der Israelitischen Religionsgesellschaft in Frankfurt am Main"^^xsd:string .
```  
Example output data for a page:
```
<http://data.judaicalink.org/data/compact-memory/2710055-2710056-2710057--019-2710121> jl:belongsToIssue <http://data.judaicalink.org/data/compact-memory/2710057> ;
    jl:hasVisualRepresentation <http://sammlungen.ub.uni-frankfurt.de/cm/periodical/pageview/2710121> .
```  