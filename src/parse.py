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
    def __init__(self, stemmer, stopword_list, index):
        self.page = None
        self.field = None
        self.stemmer = stemmer
        self.buffer = list()
        self.index = index
        self.stopwords = stopword_list
        self.title = None
        self.count = 0
        self.redirect = False

    def startElement(self, name, attributes):
        if name == "page":
            self.page = Page()
        elif name == "title":
            self.field = Field.title
        elif name == "redirect":
            self.redirect = True
        else:
            self.field = None

    def endElement(self, name):
        if name == "page":
            if not self.redirect:
                self.count += self.page.count
                self.page.process_field(Field.title, self.title, self.stemmer, self.stopwords)
                self.index.update(self.page, self.title)
            else:
                self.redirect = False
        elif name == "text":
            self.page.parse_text(''.join(self.buffer).strip(), self.stemmer, self.stopwords)
        elif self.field == Field.title:
            self.title = ''.join(self.buffer).strip()
        self.field = None
        self.buffer = list()

    def characters(self, content):
        self.buffer += content

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("xml_dump", type=str)
    argparser.add_argument("index_path", type=str)
    argparser.add_argument("index_stats", type=argparse.FileType('w'))
    args = argparser.parse_args()

    index = InvertedIndex(args.index_path, block_size=1000000)
    stemmer = Stemmer.Stemmer('english')
    stopword_list = list(stopwords.words('english'))
    handler = WikiHandler(stemmer, stopword_list, index)

    parse(args.xml_dump, handler)
    # index.write_to_file(args.index_file)
    index.write_block()
    index.save_index()
    args.index_stats.write("{}\n{}\n".format(handler.count, len(index.postings)))
