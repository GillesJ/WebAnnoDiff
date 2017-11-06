"""

compare_annotations.py

Author: Lukas Gienapp
Date: 06.11.2017

Script to parse WebAnno XMI data and find differences in annotations

Usage:
    $ python3 compare_annotations.py <file_1>.xmi <file_2>.xmi log.csv

"""
import xml.dom.minidom as md
import csv
import sys

class Document:
    """
    Class to represent a WebAnno Annotation in the XMI format
    
    Arguments:
        file_name - name of the XMI file which contains the annotation
    
    Variables:
        text - textual representation of the annotated text
        tagset - attributes used to describe a frame
        sentences - list of sentences this document consists of

    """
    def __init__(self, file_name):
        print("Constructing representation for '", file_name,"'")
        dom    = md.parse(file_name)
        self.text   = dom.getElementsByTagName('cas:Sofa')[0].getAttribute('sofaString')
        self.tagset = dom.getElementsByTagName('custom:Frame')[0].attributes.keys()
        
        # Dictionary views of the XMI items
        sentencesDict = [self.__convertAttributes__(node) for node in dom.getElementsByTagName('type4:Sentence')]
        framesDict    = [self.__convertAttributes__(node) for node in dom.getElementsByTagName('custom:Frame')]
        linksDict     = [self.__convertAttributes__(node) for node in dom.getElementsByTagName('custom:FELink')]
        elementsDict  = [self.__convertAttributes__(node) for node in dom.getElementsByTagName('custom:FE')]

        # Create link objects
        links = []
        for link in linksDict:
            element = [element for element in elementsDict if element["xmi:id"] == link["target"]][0]
            target = self.text[int(element["begin"]):int(element["end"])]
            links.append(Link(int(link["xmi:id"]), target, link["role"]))
        print(".   [!]",len(links),"links created")

        # Create frames objects
        frames = []
        for frame in framesDict:
            frame_links = [l for l in links if l.id in [int(x) for x in frame["FE"].split(' ') if x!='']]
            try:
                begin = int(frame["begin"])
                end = int(frame["end"])
                frames.append(Frame(begin, end, self.text[begin:end], frame_links, frame["Label"], frame["discontinuos"], frame["metaphorical"]))
            except:
                pass
        print(".   [!]",len(frames),"frames created")

        # Create sentence objects
        self.sentences = []
        for i, sentence in enumerate(sentencesDict):
            begin = int(sentence["begin"])
            end = int(sentence["end"])
            sentence_frames = [frame for frame in frames if frame.begin >= begin and frame.end <= end]
            self.sentences.append(Sentence(i+1,begin,end,sentence_frames))
        print(".   [!]",len(self.sentences),"sentences created")

    def __convertAttributes__(self, xmlSource):
        """ 
        Function to converts XML attributes into a dictionary 

        Arguments:
            xmlSource - XML attributes which are to be converted

        Returns:
            - dictionary view of the XML attributes
        """
        attributes = {}
        for attrName, attrValue in xmlSource.attributes.items():
            attributes[attrName] = attrValue
        return attributes

class Sentence:
    """ 
    Class to represent a sentence 

    Variables:
        id - number of this sentence in the text
        begin - position of the sentence start in the original text
        end - position of the sentecne end in the original text
        frames - list of frames contained in this sentence
    """
    def __init__(self, id, begin, end, frames):
        self.id = id
        self.begin = begin
        self.end = end
        self.frames = frames

    def __eq__(self, other):
        if self.begin == other.begin and self.end == other.end:
            if [x for x in self.frames if not x in other.frames] == [] and [x for x in other.frames if not x in self.frames] == []:
                return True
        return False

class Frame:
    """ 
    Class to represent a frame 

    Required Variables:
        begin - position of the frame start in the original text
        end - position of the frame end in the original text
        text - textual representation of the frame
        elements - array of elements this frame contains
        label - semantic lable of this frame
        discontinuos - determines wether the frame is discontinuos or not
        metaphorical - determines wether the frame is metaphorical or not
    """
    def __init__(self, begin, end, text, links, label, discontinuos, metaphorical):
        self.begin = begin
        self.end = end
        self.text = text
        self.links = links
        self.label = label
        self.discontinuos = discontinuos
        self.metaphorical = metaphorical

    def __eq__(self, other):
        if self.begin == other.begin and self.end == other.end and self.label == other.label and self.discontinuos == other.discontinuos and self.metaphorical == other.metaphorical:
            if [x for x in self.links if not x in other.links] == [] and [x for x in other.links if not x in self.links] == []:
                return True
        return False

class Link:
    """ 
    Class to represent a link 
    
    Variables:
        id - unique identifier
        target - token this link refers to
        role - semantic role of the link
    """
    def __init__(self, id, target, role):
        self.id = id
        self.target = target
        self.role = role

    def __eq__(self, other):
        if self.target == other.target and self.role == other.role:
            return True
        return False

    def __str__(self):
        return self.target+" ("+self.role+")"

class Comparison:
    """ 
    Class to provide functions which operate as comparators on annotation data

    Variables
        log - logfile which keeps tracks of file differences
    """
    def __init__(self, file1, file2):
        """
        Constructor

        Arguments
            file1 - name of the first file for the comparison
            file2 - name of the second file for the comparison
        """
        self.log = [["Sentence", "Frame", "Key", file1, file2]] + self.__compareDocuments__(Document(file1), Document(file2))

    def writeLog(self, name):
        print("Writing output to file...")
        """
        Function to save the comparison log as a csv file

        Arguments:
            name - file name to save the log under
        """
        with open(name,'w', encoding='utf-8') as logFile:
            wr = csv.writer(logFile)
            wr.writerows(self.log)

    def __compareDocuments__(self, document1, document2):
        """
        Function to compare the annotations of two documents and log differences

        Arguments:
            document1 - first document for comparison
            document2 - second document for comparison
        """
        print("Comparing documents...")
        log = []
        for sentence1, sentence2, i in ((document1.sentences[j], document2.sentences[j], j) for j in range(0, len(document1.sentences))):
            # Comparison in one direction
            for entry in self.__compareSentences__(sentence1, sentence2):
                log.append([i+1] + entry)
            # Comparison in other direction, flipped values in log
            for entry in self.__compareSentences__(sentence2, sentence1):
                log.append([i+1] + [entry[0], entry[1], entry[3], entry[2]])
        
        # Clear redundant entries from log
        log_cleaned = []
        for entry in log:
            entry_cleaned = []
            for value in entry:
                if isinstance(value, list) and len(value) == 1:
                    entry_cleaned.append(value[0])
                else:
                    entry_cleaned.append(value)
            if entry_cleaned[3] != entry_cleaned[4] and not entry_cleaned in log_cleaned and not [entry_cleaned[0], entry_cleaned[1], entry_cleaned[2], entry_cleaned[4], entry_cleaned[3]] in log_cleaned:
                log_cleaned.append(entry_cleaned)

        return log_cleaned


    def __compareSentences__(self, sentence1, sentence2):
        """
        Function to compare two sentences to each other and return a log of the differences

        Arguments:
            sentence1 - first sentence for the comparison
            sentence2 - second sentence for the comparison
        """
        log = []
        for frame1 in sentence1.frames:
                if not frame1 in sentence2.frames:
                    # If no equal frame is found in the other annotation, find out why
                    attributes = ((key, value1) for (key, value1) in frame1.__dict__.items())
                    frame2 = [frame for frame in sentence2.frames if frame1.begin == frame.begin and frame1.end == frame.end] or None
                    if frame2:
                        frame2 = frame2[0]
                        for key, value1 in attributes:
                            value2 = frame2.__dict__[key] 
                            if value1 != value2:
                                if key == "links":
                                    for link1 in value1:
                                        if link1 not in value2: 
                                            log.append([str(frame1.text), key, link1.__str__(), [l.__str__() for l in value2]])
                                else:
                                    log.append([str(frame1.text), str(key), str(value1), str(value2)])
        return log

def main():
    """ Main application routine """
    if len(sys.argv) != 4:
        print("Insufficient number of arguments!")
        return
    c = Comparison(sys.argv[1], sys.argv[2])
    c.writeLog(sys.argv[3])

if __name__ == '__main__':
    main()
