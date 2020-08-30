import sys
from xml.sax import parse
from xml.sax.xmlreader import XMLReader
from xml.sax.handler import ContentHandler
import Stemmer
import argparse

from page import Page, Field
from indexer import InvertedIndex
from nltk.corpus import stopwords

class WikiHandler(ContentHandler):
    def __init__(self, stemmer, stopwords, index):
        self.page = None
        self.field = None
        self.stemmer = stemmer
        self.buffer = list()
        self.index = index
        self.stopwords = stopwords
        self.count = 0

    def startElement(self, name, attributes):
        if name == "page":
            self.page = Page()
        elif name == "title":
            self.field = Field.title
        elif name == "redirect":
            self.page.process_field(Field.title, attributes.getValue("title").strip(), stemmer, stopwords)
        else:
            self.field = None

    def endElement(self, name):
        if name == "page":
            self.count += self.page.count
            self.index.update(self.page)
        elif name == "text":
            self.page.parse_text(''.join(self.buffer).strip(), self.stemmer, self.stopwords)
        elif self.field == Field.title:
            self.page.process_field(Field.title, ''.join(self.buffer), stemmer, stopwords)
        self.field = None
        self.buffer = list()

    def characters(self, content):
        self.buffer += content

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("xml_dump", type=str)
    argparser.add_argument("index_file", type=argparse.FileType('w'))
    argparser.add_argument("index_stats", type=argparse.FileType('w'))
    args = argparser.parse_args()

    index = InvertedIndex()
    stemmer = Stemmer.Stemmer('english')
    stopwords = list(stopwords.words('english'))
    handler = WikiHandler(stemmer, stopwords, index)

    parse(args.xml_dump, handler)
    index.write_to_file(args.index_file)
    args.index_stats.write("{}\n{}\n".format(handler.count, len(index.postings)))
