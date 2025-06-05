import os, json, pprint, csv, pickle
def generate_pages_data(metadata, cm_tagme_res_ref_data, save=False, out_path=""):
    
    print("Generating pages data...")
    
    cm_tagme_pages = []
    for mention in cm_tagme_res_ref_data:
        try:
            full_page = mention['page_id'].replace('_', '-')
            page = mention['page_id'].split('--')[1].split('-')[1]
            journal = mention['journal_id']

            meta = metadata[page]
            journal_name = meta[5]
            issue = ""
            if meta[4] == 'journal issue':
                issue = meta[0].strip('|').split('||')[-2]
            cm_tagme_pages.append({
                'full_page': full_page,
                'page': page,
                'journal': journal,
                'journal_name': journal_name,
                'issue': issue
            })
        except KeyError: # for the journal "Séance du comité de direction du...", id 11014679 there's no entry in the metadata
            pass
        
    print("Generated data for {} pages.".format(len(cm_tagme_pages)))
    if save is True:
        print("Saving data to {}...".format(out_path))
        with open(out_data, 'wb') as outfile:
            pickle.dump(cm_tagme_pages, outfile)
        print("Done!")
    
    return cm_tagme_pages
with open('CM_Seiten_Metadaten.csv', 'r') as infile:
    metadata = list(csv.reader(infile, delimiter="\t"))
metadata = {line[0]: line[1:] for line in metadata}
cm_tagme_res_ref_data = pickle.load(open('cm_tagme_resource_reference_data.pickle', 'rb'))
cm_tagme_pages = generate_pages_data(metadata, cm_tagme_res_ref_data, True, 'cm_pages_data.pickle')
