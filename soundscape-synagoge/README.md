# Soundscape Synagoge

Soundscape Synagogue provides information on the musical heritage of Jewish communities in Europe. Here you will find knowledge on Jewish cantors of the past and present, as well as information on various traditions of Jewish-liturgical music, including texts, images, sound recordings and films. Some contents are freely accessible and may be used with reference to the source. New content is added on a regular basis.

European Center for Jewish Music
Hannover University of Music, Drama and Media

Copyright CC 4.0 BY-NC-SA

# How to use
* Run the script `generator.py` in the folder `soundscape-synagoge`.
* The script generates an uncompressed and a compressed ttl file.
* There is no jupyter notebook for the script.

# How does it work

The generator reads list of all the identifies for the persons from the API, https://www.soundscape-synagoge.de/api/person/all/base.
The result is a list with the identifier from the API call.
This list is passed to get the data from the persons to the API https://www.soundscape-synagoge.de/api/person/list.
This returns a list with a dict for each person.
The dic is being processed to create a ttl file.
The ttl file is being compressed and saved to the folder `sosy` in the `data` folder.

The script generate a log file for better debugging purposes. The log level can be set in the generator.py file.


There is a lot of extra information for each person, in json format. But it is not used in JudaicaLink. However, it could be usefull in the future.
Currently, there are 120 entities in the ttl file.
