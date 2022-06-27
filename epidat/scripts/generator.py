"""
Generator for epidat. http://steinheim-institut.de/cgi-bin/epidat
By Benjamin Schnabel, 2022.
schnabel@hdm-stuttgart.de
# Licence of the data: CC-BY-SA 4.0
# https://creativecommons.org/licenses/by-sa/4.0/
"""

import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
import spacy
from SPARQLWrapper import RDF
from bs4 import BeautifulSoup
from rdflib import Namespace, URIRef, Graph, Literal
from rdflib.namespace import RDF
from spacy.matcher import Matcher, PhraseMatcher

file_name = 'epidat-final-01.ttl'
working_path = os.getcwd()
output_path = "/data/judaicalink/dumps/epi/current/"

graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace("http://purl.org/dc/elements/1.1/")

graph.bind('skos', skos)
graph.bind('foaf', foaf)
graph.bind('jl', jl)
graph.bind('gndo', gndo)
graph.bind('owl', owl)
graph.bind('edm', edm)
graph.bind('dc', dc)

personsDict = []

def compress_ttl(ttl):
    """
    Compress the ttl file.
    returns: compressed ttl file.
    """
    # compress the ttl file
    os.system("gzip -f " + ttl)
    # rename the compressed file
    os.rename(ttl + ".gz", ttl)

def move_ttl_file(ttl):
    """
    Move the ttl file to the correct folder.
    returns: the path of the ttl file.
    """
    # move the ttl file to the correct folder
    os.rename(working_path + ttl, output_path + ttl)


def spacy_parse(text):
    """
    Parse the text with spacy.
    returns: a list of tokens.
    """
    print("Parsing: ", text)
    dict = {}
    nlp = spacy.load('de_core_news_sm')
    pattern_birthLocation = [[{"TEXT": {"REGEX": "(Geb).*"}}, {"LOWER": "in"}, {"ENT_TYPE": "LOC"}],
                          [{"TEXT": {"REGEX": "(Geb).*"}}, {"ENT_TYPE": "LOC"}],
                          [{"TEXT": {"REGEX": "(Geb).*"}}, {}, {"ENT_TYPE": "LOC"}]]

    pattern_deathLocation = [[{"LOWER": "gest"}, {"IS_PUNCT": True}, {"LOWER": "in"}, {"ENT_TYPE": "LOC"}],
                            [{"LOWER": "gestorben"}, {"LOWER": "in"}, {"ENT_TYPE": "LOC"}]]

    date_regex = r"(\d{1,2}.\d{1,2}.\d{2,4})"
    year_regex = r"(\d{3,4})"
    full_date_regex = r"(\d{1,2}. \w+ .\d{2,4})"
    pattern_birthdate = [[{"TEXT": {"REGEX": "(Geb).*"}}, {"LOWER": "am"}, {"TEXT": {"REGEX": date_regex}}],
                         [{"TEXT": {"REGEX": "(Geb).*"}}, {"LOWER": "am"}, {"TEXT": {"REGEX": full_date_regex}}],
                         [{"TEXT": {"REGEX": "(Geb).*"}}, {"TEXT": {"REGEX": date_regex}}],
                         [{"TEXT": {"REGEX": "(Geb).*"}}, {"TEXT": {"REGEX": full_date_regex}}]]

    pattern_birthdate_alt = [[{"TEXT": {"REGEX": date_regex}}, {"TEXT": {"REGEX": "(geb).*"}}],
                             [{"TEXT": {"REGEX": full_date_regex}}, {"TEXT": {"REGEX": "(geb).*"}}],
                             [{"TEXT": {"REGEX": year_regex}}, {"TEXT": {"REGEX": "(geb).*"}}]]

    matcher = Matcher(nlp.vocab)
    matcher.add("geb_in", pattern_birthLocation)
    matcher.add("gest_in", pattern_deathLocation)
    matcher.add("geb_am", pattern_birthdate)
    matcher.add("geb_am_alt", pattern_birthdate_alt)

    occupations = ['Lehrer', 'Lehrerin', 'Rabbiner', 'Rabbi', 'Kaufmann', 'Händler', 'Händlerin', 'Tuchmacher', 'Tuchmacherin']
    dates = ['1900', '1.1.1900', '834', '31.1.2020', '31.12.2020', '1. März 1900']
    phrase_matcher = PhraseMatcher(nlp.vocab, attr="SHAPE")
    phrase_matcher.add("occupation",  [nlp(token) for token in occupations])

    occupation = []
    # Find the occupation of the person
    doc = nlp(text)
    for match_id, start, end in phrase_matcher(doc):
        span = str(doc[start:end])
        print("Matched based on token shape:", span)
        res = find_occupation(span)
        print(res)

        if res is True:
            occupation.append(span)

    matches = matcher(doc)

    for match_id, start, end in matches:
        string_id = nlp.vocab.strings[match_id]  # Get string representation
        span = doc[start:end]  # The matched span
        print("Patterns matched: ", string_id, start, end, span.text)
        if string_id == "geb_in":
            dict['birthLocation'] = str(span.text.split(" ")[-1])
            print("birthLocation: ", dict['birthLocation'])

        if string_id == "gest_in":
            dict['deathLocation'] = str(span.text.split(" ")[-1])
            print("deathLocation: ", dict['deathLocation'])

        if string_id == "geb_am":
            dict['birthDate'] = str(span.text.split(" ")[-1])
            print("birthDate: ", dict['birthDate'])

        if string_id == "geb_am_alt":
            dict['birthDate'] = str(span.text.split(" ")[-2])
            print("birthDate: ", dict['birthDate'])

    for ent in doc.ents:
        print(ent.label_, ent.text)

        if ent.label_ == "LOC" or ent.label_ == "MISC":

            location = ent.text

            # split the location with a comma and add a for loop

            if location.find(",") != -1:
                locations = location.split(", ")
                for loc in locations:
                    if loc in occupation:
                        occupation.remove(loc)
            elif location.find(" ") != -1:
                locations = location.split(" ")
                for loc in locations:
                    if loc in occupation:
                        occupation.remove(loc)
            elif location.find("/") != -1:
                            locations = location.split("/")
                            for loc in locations:
                                if loc in occupation:
                                    occupation.remove(loc)

            if location in occupation:
                occupation.remove(location)

    print("Occupation: ", occupation)
    if len(occupation) > 0:
        dict['occupation'] = occupation
        return dict
    else:
        return None

def scrape_index():
    """
    Scrape the index page of epidat.
    returns: a pandas dataframe with the result.
    """
    url = "http://www.steinheim-institut.de/cgi-bin/epidat?info=howtoharvest"
    #try:
    r = requests.get(url)
    tombstones = []

    if r.status_code == 200:
        # find all the locations
        bs4 = BeautifulSoup(r.text, "html.parser")
        # find all a href tags in the html, which start with "?info=resources"
        a_tags = bs4.find_all("a", href=lambda x: x and x.startswith("?info=resources"))
        # create a list of urls and add "http://www.steinheim-institut.de/cgi-bin/epidat" to the front of the url
        urls = ["http://www.steinheim-institut.de/cgi-bin/epidat" + a_tag.get("href") for a_tag in a_tags]

        # print every url
        for url in urls:
            #print(url)
            # download the url as xml file
            r = requests.get(url)
            if r.status_code == 200:
                # parse the result as xml file
                root = ET.fromstring(r.text)
                # find parameter id from each resource in the xml file
                ids = [resource.get("href") for resource in root.findall("resource")] # xml files as tp 5

                # print the ids
                for id in ids:
                    # finds all gravestones
                    id_url = str("http://www.steinheim-institut.de:80/cgi-bin/epidat?id=" + id + "")
                    tombstones.append(id)
                    print("ID: ", id)
                    read_xml_file(id)

    #except Exception as e:
    #    print("Could not fetch data. Connection lost. Script ended prematurely. Error: ", e)

def get_gnd_id(url):
    """
    Get the gnd id of the person.
    returns: the gnd id.
    """
    # get the gnd id
    r = requests.get(url)
    if r.status_code == 200:
        print("Scraping: " + url)
        soup = BeautifulSoup(r.text, "html.parser")
        if soup.find("object"):
            gnd_id = soup.find("object")["data"].split("/")[-1].replace(".preview", "")
            print("GND ID: ", gnd_id)
            return gnd_id
        else:
            return None


def find_alternative_names(name: str):
    """
    Get the name alternatives of the person.
    returns: a list of name alternatives.
    """
    # get the name alternatives

    name_alternatives = []
    # without  bracket there are no name alternatives

    # case 1 name in Brackets
    if "(" in name:
        #match = re.match(r'\(.*?\)', name)
        name_alternatives.append(name.split("(")[-1].replace(")", ""))
        name = name.split("(")[0]

    # case 2 name in square brackets
    if "[" in name:
        # match = re.match(r'\[.*?\]', name)
        name_alternatives.append(name.split("[")[-1].replace("]", ""))
        name = name.split("[")[0]

    # case 3 maiden name
    if "geb." in name:
        name_alternatives.append(name.split('geb.')[-1])
        name = name.split("geb.")[0]



        print("Name alternatives: ", name_alternatives)

    return name, name_alternatives


def find_spouse(name):
    """
    Get the spouse of the person.
    returns: the spouse.
    """
    # get the spouse
    spouse = ""
    # without  bracket there are no name alternatives
    if name.find("⚭") != -1:
        spouse = name.split("⚭")[1].split("(")[0].strip()
        return spouse
    else:
        return None


def find_occupation(occupation):
    """
    Get the occupation of the person.
    returns: the occupation.
    """

    occupations = [occupation]
    bad_words = ['Beruf', 'Berufsbezeichnung', 'Nationalsozialisten', 'Geb.', 'Geboren', 'Gest.', 'Gestorben']
    true_words = ['Schutzjude', 'Altwarenhändler', 'Kürschnermeister', 'Mützenmacher', 'Pferdehaarverarbeiter', 'Fellhändler', 'Metzger', 'Lotteriecollecteur', 'Lotterie-Collecteur']
    if "in" in occupation:
        occupations.append(occupation.replace("in", ''))

    for occupation in occupations:
        if occupation in bad_words:
            return False
        if occupation in true_words:
            return True

        try:
            request = requests.get('https://lobid.org/gnd/search?q=' +occupation +'&format=json') #%3AprofessionOrOccupation')
            if request.status_code == 200:
                results = request.json()

                # find the key "professionOrOccupationAsLiteral" in results dict
                for member in results['member']:
                    if 'gndSubjectCategory' in member:
                        for category in member['gndSubjectCategory']:
                            if category['label']  == "\"Einzelne Berufe, Tätigkeiten, Funktionen; Religionszugehörigkeit, Weltanschauung\"":
                                return True
                    elif 'type' in member:
                        for type in member['type']:
                            if "SubjectHeadingSensoStricto" == type:
                                return True
                    elif 'professionOrOccupationAsLiteral' in member:
                        return True
                    elif 'professionOrOccupation' in member:
                        if occupation in member['professionOrOccupation']:
                            return True
        except:
            return False
    return False

def read_xml_file(url):
    """
    Read the xml file and get the data.
    Main loop.
    returns: a dictionary with the data.
    """

    r = requests.get(url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'lxml') # TEI XMl, not a real XML!

        # find settlement in the xml file
        if soup.find("settlement") is not None:
            settlement = remove_characters_from_text(soup.find('settlement').contents[0].split(",")[0])

            """
            # find the text in the inscription, saved for later
            texts = soup.find_all('div', attrs={'type': 'textpart'})
            for text in texts:
                print(text.text) 
            """

            commentary = soup.find('div', attrs={'type': 'commentary', 'subtype': 'Prosopographie'})
            parse_dict = {}
            if commentary is not None:
                comment = commentary.find('p')
                if comment is not None:
                    print("Comment", comment.text)
                    parse_dict = spacy_parse(comment.text)

            persons = soup.find_all('person')
            # create a list of personDicts
            relation_list = []
            relations = soup.find_all('relation')
            for relation in relations:
                if relation.get('active'):
                    relation_list.append(relation.get('active').replace("#", ''))
                if relation.get('passive'):
                    relation_list.append(relation.get('passive').replace("#", ''))

            for person in persons:
                personDict = {}
                if parse_dict is not None:
                    personDict.update(parse_dict)
                # find attribute xml:id from each person in the xml file
                id = person.get("xml:id")
                sex = person.get("sex")

                # find persName in person
                name = remove_characters_from_text(person.find("persname").text, sex)
                if person.find('persname').get('ref') is not None:
                    gnd_id = person.find('persname').get('ref').split('/'[-1])
                    personDict['gnd_id'] = gnd_id

                name, alternativeNames = find_alternative_names(name)
                print('alternativeNames', alternativeNames)

                if len(alternativeNames) > 0:
                    print(alternativeNames)
                    personDict['alternativeNames'] = alternativeNames

                spouse = find_spouse(name)
                if spouse is not None:
                    name = name.split('⚭')[0]

                if person.find('death'):
                    death = person.find("death").get("when")
                    personDict['deathDate'] = death

                personDict['id'] = id
                personDict['sex'] = "male" if sex == 1 else "female"
                personDict['name'] = name

                personDict['deathLocation'] = settlement

                html_url = str("http://www.steinheim-institut.de/cgi-bin/epidat?id=" + id)
                personDict['describedAt'] = html_url
                #gnd_id = get_gnd_id(html_url)

                #personDict.update(get_person_data(url = str("http://www.steinheim-institut.de/cgi-bin/epidat?id="+id))) # alternative way to get the data from the id page
                print("Person: ", personDict)

                if len(relation_list) > 0:
                    if id in relation_list:
                        personDict['relations'] = relation_list
                personDict.update(personDict)

                personsDict.append(personDict)

    else:
        return None # empty tombstone


def get_beacon_file():
    """
    Get the beacon file from the epidat website.
    returns: text from the beacon file.
    """
    url = "http://steinheim-institut.de/daten/beacon.txt"   
    r = requests.get(url)
    if r.status_code == 200:
        return r.text
    else:
        return None


def remove_characters_from_text(string, sex=None):
    """
    Remove all characters from a string that are not alphanumeric.
    returns: string with only alphanumeric characters.
    """
    if sex == 1:
        string = string.replace("b. ", "ben ")
    elif sex == 2:
        string = string.replace("b. ", "bat ")

    string = string.replace("\n", "")
    string = string.replace("\r", "")
    string = string.replace("\t", "")
    string = string.replace("›", "")
    string = string.replace("#.:", "")
    string = string.replace("#.:", "")
    string = string.replace("[...]", "...")
    string = string.replace("de_", "de ")

    string = string.replace("SeGal", "")

    # replace all "  " with " " as long as there are more than one " "
    while string.count("  ") > 0:
        string = string.replace("  ", " ")
    # remove all " " at the beginning and end of the string
    string = string.strip()

    return string


def get_person_data(url):
    """
    Scrape the result from epidat.
    returns: a pandas dataframe with the result.
    """
    r = requests.get(url)
    if r.status_code == 200:
        print("Scraping: " + url)
        soup = BeautifulSoup(r.text, "html.parser")
        # find table in main
        table = soup.find("table")
        if table is None:
            return None
        # convert the table to a pandas dataframe
        personDict = {}

        # find all rows in table
        rows = table.find_all("tr")
        # find all columns in rows
        for row in rows:
            columns = row.find_all("td")
            if columns[0].text == "Begräbnisort":
                personDict["deathLocation"] = columns[1].text.split(",")[0].strip()
            elif columns[0].text == "Name":
                if "," in columns[1].text:
                    personDict["name"] = columns[1].text.split(",")[0].strip() + " " + columns[1].text.split(",")[-1].strip()
                else:
                    personDict["name"] = columns[1].text.strip()
            elif columns[0].text == "Sterbedatum":
                personDict["deathDate"] = columns[1].text
            elif columns[0].text.startswith("GND-ID"):
                # get the pobject data
                personDict["gndID"] = columns[1].find("object")["data"].split("/")[-1].replace(".preview", "")

            personDict["describedAt"] = url

        # find last a tag in the table
        a_tag = table.find_all("a")[-1]
        # get the href attribute of the a tag
        href = a_tag.get("href")
        epigraph_url = "http://steinheim-institut.de/cgi-bin/epidat" + href
        #print(epigraph_url)

        return personDict
    else:
        return None


def get_ids():
    """
    Get the ids from the beacon file, then scrapes the result.
    returns: nothing
    """
    id_list = []
    # find target as url
    result = get_beacon_file()
    personsDict = {}
    counter = 0
    for result_line in result.splitlines():
        if "#TARGET" in result_line:
            target = result_line.split(": ")[1]
            # replace {ID} with the id from the id_list

        # find all lines from result_line which do not include a "#"
        if not "#" in result_line:
            id = result_line
            id_list.append(id)
            #print(id)
            url = target.replace("{ID}", id)
            #print(url)
            result = get_person_data(url=url) # result is personDict
            counter += 1
            #print(result)
            personsDict[id] = result
            if counter >= 10:
                break
    return personsDict


def clean_url_string(string):
    """
    Clean the name of a person.
    returns: cleaned name.
    """
    string = string.replace('\'', '')
    string = string.replace('"', '')
    string = string.replace(',', '_')
    string = string.replace('<<', '')
    string = string.replace('>>', '')
    string = string.replace('|', '_')
    string = string.replace(' ', '')
    string = string.replace('<', '_')
    string = string.replace('>', '_')
    string = string.replace('.', '')
    string = string.replace('[', '')
    string = string.replace(']', '')
    return string


def generate_rdf(personsDict):
    """
    Generate RDF from the personsDict.
    returns: nothing
    """

    skos = Namespace("http://www.w3.org/2004/02/skos/core#")
    jl = Namespace("http://data.judaicalink.org/ontology/")
    foaf = Namespace("http://xmlns.com/foaf/0.1/")
    gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
    owl = Namespace("http://www.w3.org/2002/07/owl#")
    edm = Namespace("http://www.europeana.eu/schemas/edm/")
    dc = Namespace("http://purl.org/dc/elements/1.1/")
    dcterms = Namespace("http://purl.org/dc/terms/")

    graph.bind('skos', skos)
    graph.bind('foaf', foaf)
    graph.bind('jl', jl)
    graph.bind('gndo', gndo)
    graph.bind('owl', owl)
    graph.bind('edm', edm)
    graph.bind('dc', dc)

    for person in personsDict:
        name = remove_characters_from_text(person["name"])
        if name == "":
            name = "Anonymous"
            url_name = person['id']
        else:
            url_name = clean_url_string(name)

        uri = URIRef(f"http://data.judaicalink.org/data/epidat/{url_name}")

        graph.add((URIRef(uri), RDF.type, foaf.Person))
        graph.add((URIRef(uri), foaf.name, (Literal(name))))
        graph.add((URIRef(uri), skos.prefLabel, (Literal(name))))
        if 'alternativeNames' in person.keys():
            for alternativeName in person["alternativeNames"]:
                cleaned_name = remove_characters_from_text(alternativeName)
                graph.add((URIRef(uri), skos.altLabel, (Literal(cleaned_name))))
        if 'gndID' in person.keys():
            graph.add((URIRef(uri), gndo.gndIdentifier, (Literal(person["gndID"]))))
        if 'birthDate' in person.keys():
            graph.add((URIRef(uri), jl.birthDate, (Literal(person["birthDate"]))))
        if 'deathDate' in person.keys():
            if person['deathDate'] is not None and person['deathDate'] != "" and person['deathDate'] != "--":
                graph.add((URIRef(uri), jl.deathDate, (Literal(person["deathDate"]))))
        if 'deathLocation' in person.keys():
            graph.add((URIRef(uri), jl.deathLocation, (Literal(person["deathLocation"]))))
        if 'describedAt' in person.keys():
            graph.add((URIRef(uri), jl.describedAt, (Literal(person["describedAt"]))))
        if 'occupation' in person.keys() and len(person['occupation']) > 0:
            for occupation in person["occupation"]:
                graph.add((URIRef(uri), jl.occupation, (Literal(occupation))))

        if 'relations' in person.keys():
            relations = person["relations"]
            print(relations)

            # go through all the relations
            for relation in relations:

                #name = [ id for id in personsDict.keys() if personsDict[id] == relation]

                for person in personsDict:
                    if relation == person['id']:
                        print("Id: " + person['id'])
                        name = person['name']
                        print("Name: " + name)

                """
                if relation == person["id"]:
                    # name from the personDict by id

                    # find the id
                    name = personsDict['personID']
                    print(name)
                    graph.add((URIRef(uri), skos.related, (Literal(name))))
                """
        graph.add((URIRef(uri), dcterms.created, (Literal(datetime.now()))))


    graph.serialize(destination=file_name, format="turtle")

# runs the functions
#result = get_ids()
#result.to_csv("epidat.csv")
#print(result)

scrape_index()


print(personsDict)

generate_rdf(personsDict)

compress_ttl(file_name)
move_ttl_file(file_name)

print(len(personsDict), 'entries found')
print("done")