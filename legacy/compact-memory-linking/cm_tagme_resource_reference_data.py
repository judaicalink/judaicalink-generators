import os, json, pickle
import urllib.parse
def generate_res_ref_data(cm_mentions, ep_inverted_index, link_prob=0.6, rho=0.4, save=False, out_path=""):
    
    print("Generating resource and reference data with link probability={} and rho={}...".format(link_prob, rho))
    base_resource = 'http://data.judaicalink.org/data/dbpedia/'
    base_reference = 'http://data.judaicalink.org/data/cm-tagme/'
    ref_index = 1000000

    base_dbp = 'http://dbpedia.org/resource/'
    base_dbp_de = 'http://de.dbpedia.org/resource/'
    base_wiki_en = 'https://en.wikipedia.org/wiki/'
    base_wiki_de = 'https://de.wikipedia.org/wiki/'

    cm_jl_mentions = []

    for mention in cm_mentions:
        
        if mention[3] > link_prob and mention[4] > rho:

            resource_name = mention[6].replace(' ', '_')
            resource_uri = base_resource+resource_name

            entity_exists = False # check if this resource exists in jl, under any form. Use entity pages for this

            if resource_uri in resource2ep: # first check if the jl/dbpedia uri format for this resource is in the entity pages
            
                entity_exists = True
                
            else: # check other wikipedia/dbpedia uri formats for this resource
                wiki_en = base_wiki_en + urllib.parse.quote(resource_name)
                wiki_de = base_wiki_de + urllib.parse.quote(resource_name)
                dbp_de = base_dbp_de + resource_name
                dbp = base_dbp + resource_name

                alt_uris = [wiki_en, wiki_de, dbp_de, dbp]

                for alt_uri in alt_uris:
                    if alt_uri in resource2ep:
            
                        entity_page = resource2ep[alt_uri] # get entity_page for this resource
                        entity_exists = True
                        break

            if entity_exists and entity_page != "": # generate mention data
                cm_jl_mentions.append({
                    'resource': resource_uri,
                    'ref': base_reference+str(ref_index),
                    'spot': mention[0],
                    'start': mention[1],
                    'end': mention[2],
                    'link_prob': mention[3],
                    'rho': mention[4],
                    'journal_id': mention[7].split('_')[0],
                    'page_id': mention[7].replace('_', '-')
                })
                ref_index += 1
    
    print("Generated data for {} entity mentions from CM-tagme.".format(len(cm_jl_mentions)))
    
    if save is True:
        print("Saving data to {}...".format(out_path))
        with open(out_path, 'wb') as outfile:
            pickle.dump(cm_jl_mentions, outfile)
        print("Done!")
    
    return cm_jl_mentions
# load tagme output
cm_mentions = pickle.load(open("/data/cm/output/linker/cm_entities_tagme.pickle", 'rb'))

# load entity pages inverted index
resource2ep = pickle.load(open('ep_inv_index.pickle', 'rb'))
# generate data
res_ref_data = generate_res_ref_data(cm_mentions, resource2ep)
with open('cm_tagme_resource_reference_data.pickle', 'wb') as outfile:
    pickle.dump(res_ref_data, outfile)
