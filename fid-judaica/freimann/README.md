# FID Judaica contextualization  - Freimann dataset 

#### Generated by: Maral Dadvar

This folder explains the contextualization process of the authors of Freimann dataset with their GND-id. 
The provided dataset contained only the authors with Tn, which means those who either didn't have an id or the id was not correct. 


The file Tn-gnd-uni.rdf contains the common authors between GND and Tn UB, which have no duplicates, and are based on the stated occupation in the
python script in the script folder (Tn-GNDID-01.py)

The file Tn-gnd-multi.rdf contains the common authors between GND and Tn UB, which have multiple entries for the same name, and are also
based on the stated occupation in the python script in the script folder (Tn-GNDID-01.py)

The uni file will be used in the first step to enrich the Tn UB authors. 

The file Tn-authors-context-GND-uni.rdf is the file generated from the script Tn-contex-GND-uni.py and is the Tn authors enriched with GND id, using the
Tn-gnd-uni.rdf file. 

The file Tn-authors-context-GND-multi.rdf is the file generated from the script Tn-contex-GND-multi.py and is the Tn authors enriched with GND id,but 
the authors with multiple entries, using the Tn-gnd-multi.rdf file.

The file Tn-gnd-uni2.rdf contains the common authors between GND and Tn UB, which have no duplicates, but are based on no occupation in
python script in the script folder (Tn-GNDID-02.py)

The file Tn-gnd-multi2.rdf contains the common authors between GND and Tn UB, which have multiple entries for the same name but based on no 
occupation in the python script in the script folder (Tn-GNDID-02.py)

The file Tn-authors-context-GND-uni2.rdf is the file generated from the script Tn-contex-GND-uni.py and is the Tn authors enriched with GND id, 
using the Tn-gnd-uni-2.rdf file. 

The file Tn-authors-context-GND-multi-2.rdf is the file generated from the script Tn-contex-GND-multi.py and 
is the Tn authors enriched with GND id, using the Tn-gnd-multi-2.rdf file. 


The Tn-authors-context-GND-uni-date.ttl is the same file as Tn-authors-context-GND-uni.rdf but the date of the publication is added to the file
using the Tn-Date-02.py script in C:\Users\Maral\Desktop\Tn-Tp\scripts

The Tn-authors-context-GND-multi-date.ttl is the same file as Tn-authors-context-GND-multi.rdf but the date of the publication is added to the file
using the Tn-Date-02.py script in C:\Users\Maral\Desktop\Tn-Tp\scripts.


The Tn-authors-context-GND-multi-datefiltering.ttl is the same file as Tn-authors-context-GND-multi.rdf but is based on the date of birth of
authors, and is filtered if the publication date is smaller than the birthdate using the Tn-Date-filtering.py 
script in C:\Users\Maral\Desktop\Tn-Tp\scripts.


The file Tn-gnd-multi-2-multi.rdf contains the common authors between GND and Tn UB, which have multiple entries for the same name, but based on 
Tn-gnd-multi-2.rdf file on which the occupation filter is applied using the script (Tn-GNDID-03.py)

The file Tn-gnd-multi-2-uni.rdf contains the common authors between GND and Tn UB, which have unique entries for the same name, but based on 
Tn-gnd-multi-2.rdf file on which the occupation filter is applied using the script (Tn-GNDID-03.py)  

The final results were sent to the UB colleagues for evaluation. After the evaluation, the final results might have been subjected to 
some changes and improvements. 

Moreover, during the project, some of the authors' id who was manually identified by the UB colleagues were added to the dataset. 



