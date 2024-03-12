# Footprints - Jewish Books through Time and Place

Footprints traces the history and movement of Jewish books since the inception of print. 

The history of the book is an important part of humanities scholarship. Especially as more books are digitized, scholars, librarians, collectors, and others have become increasingly attuned to the significance of individual books as objects with their own unique story. Jewish books in particular tell a fascinating story about the spread of knowledge and faith in a global Diaspora.

Every literary work represents a moment in time and space where an idea was conceived and documented. But the history of a book continues long after composition as it is bought, sold, shared, read, confiscated, stored, or even discarded. This history is the essence of Footprints.


## How does it work

The Api Root can be found [here](https://footprints.ctl.columbia.edu/api/). 
currently used: 
* "book": "https://footprints.ctl.columbia.edu/api/book/",
* "person": "https://footprints.ctl.columbia.edu/api/person/",
* "place": "https://footprints.ctl.columbia.edu/api/place/"

## Scanning data

All pages for the Entities person, book and place are called and relevevant data is written into a turtle-file. If a VIAF-Identifier is given, Data is enriched with GND-Identifier

## How to use

Run the script generator.py in the folder footprints. The script generates a ttl file.
