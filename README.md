# WebAnnoDiff
Script to parse WebAnno XMI data and find differences in annotations

### Dependencies
Uses the python packages **csv** and **xml**. If you dont already have them installed, get them via **pip**.

### Usage
The script takes to xmi-export files from Webanno and puts out a log file in the .csv format. Invoke the script via:

    $ python3 compare_annotations.py <file_1>.xmi <file_2>.xmi <log>.csv
    
### Output
The script will save a log file under the specified name. This file ist structured in the following way (with an example line included):

 | Sentence | Frame | Key | Value File 1 | Value File 2 |
 |---|---|---|---|---|
 | 2 | geht es | Label | Communication | Feeling |
 
 Due to technical reasons, when comparing Frame Links, a 1-to-1-correspondence between the files cannot always be found. In this case, the script will log a list of possible links in the other file to leave it up to the user to decide for the match.
