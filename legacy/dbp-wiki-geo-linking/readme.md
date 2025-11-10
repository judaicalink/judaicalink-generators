# DBpedia and Wikipedia Locations linking

This script takes all datasets in Judaicalink that contain information about locations AND a link to Geonames and extracts from Geonames the corresponding Wikipedia and DBpedia links.

INPUT:
  * city-geocoor-05
  * geo-interlinks
  * bhr-final-05
  * djh.ttl
  * generated_persons_GND_enriched
  * Haskala_enriched
  * HirschFamily
  * ubffm-authors
  
OUTPUT:  
`dbp_wiki_geo_linking.ttl`, links between Judaicalink resources and DB/Wikipedia, for example:
``` 
<http://data.judaicalink.org/data/Achenkirch> owl:sameAs <http://dbpedia.org/resource/Achenkirch>,
        <http://en.wikipedia.org/wiki/Achenkirch>,
        <http://ru.wikipedia.org/wiki/Ахенкирх> .
```