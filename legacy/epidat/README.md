# Epidat

Epidat is the "epigraphische Datenbank" of the Steinheim institute. It is a collection of epigraphical data.

## How does it work
A general overview can be found [here](http://www.steinheim-institut.de/cgi-bin/epidat).

There is also a beacon file for the GND identifiers. But since not all persons are being identified and linked by the GND we want all the persons.

### Scanning epigraphical data


The epigraphical data of all the gravestones in the database can be found [here](http://www.steinheim-institut.de/cgi-bin/epidat?info=howtoharvest).
This file gives a list of all the jewish cementaries. This site gives us a list of all the cementaries. 
Each cementary has a link for the full records. The link is an XML page, with the link pattern: http://www.steinheim-institut.de/cgi-bin/epidat?info=resources-{cementary}.
In the XML tree there is a list of all the records with the tombstones. The tag is called 'resource' with the attribute 'id' and 'href', giving the full link to the tombstone resource.
The link is followed. The pattern is: http://www.steinheim-institut.de:80/cgi-bin/epidat?id={tombstone-id}-teip5" (the suffix -teip5 serves and xml file).
The link pattern for a tombstone is: 'http://www.steinheim-institut.de/cgi-bin/epidat?id=hha-5050'.
The link pattern to display a tombstone resource is: 'http://www.steinheim-institut.de/cgi-bin/epidat?id=hha-5050'. Here the three letters contain the cementary code and the four digits the tombstone number.
The tombstone id is scraped and the found persons added to a dictionary. The tombstone is parsed with spacy for birth dates, locations and occupations.
Sometimes no persons could be found, e.g. if the inscription is withered away.
A dictionary with all the persons is created and then the ttl file is generated out of it.

Since the files are HTML or TEI-XML (not really XML, but it is a XML-like format), we need to use beautiful soup as a parser to extract the data.
Currently, we work with the old epidat version from 2006. The beta version is not stable yet can should be avoided until it is finished.



## How to use

Run the script `generator.py` in the folder `epidat`.
The script generates an uncompressed and a compressed ttl file.
There is no jupyter notebook for the script.
