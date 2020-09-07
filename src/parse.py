import sys
from xml.sax import parse
from xml.sax.xmlreader import XMLReader
from xml.sax.handler import ContentHandler
import Stemmer
import argparse

from page import Page, Field
from split_index import InvertedIndex
from single_file_index import SingleFileIndex
from nltk.corpus import stopwords

class WikiHandler(ContentHandler):
    def __init__(self, stemmer, stopword_list, index):
        self.page = None
        self.field = None
        self.id_tag = False
        self.title_tag = False
        self.revision_tag = False
        self.stemmer = stemmer
        self.buffer = list()
        self.index = index
        self.stopwords = stopword_list
        self.title = None
        self.id = -1
        self.count = 0
        self.redirect = False

    def startElement(self, name, attributes):
        if name == "page":
            self.page = Page()
        elif name == "title":
            self.title_tag = True
        elif name == "redirect":
            self.redirect = True
        elif name == "revision":
            self.revision_tag = True
        elif name == "id" and not self.revision_tag:
            self.id_tag = True
        else:
            self.field = None

    def endElement(self, name):
        if name == "page":
            if not self.redirect:
                self.count += self.page.count
                self.page.process_field(Field.title, self.title, self.stemmer, self.stopwords)
                if self.id == -1:
                    raise Exception("invalid docid")
                self.index.update(self.page, self.title, self.id)
            else:
                self.redirect = False
        elif name == "text":
            self.page.parse_text(''.join(self.buffer).strip(), self.stemmer, self.stopwords)
        elif name == "title" and self.title_tag:
            self.title = ''.join(self.buffer).strip()
            self.title_tag = False
        elif name == "id" and self.id_tag:
            self.id = int(''.join(self.buffer).strip())
            self.id_tag = False
        elif name == "revision" and self.revision_tag:
            self.revision_tag = False
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

    index = SingleFileIndex(args.index_path)
    stemmer = Stemmer.Stemmer('english')
    stopword_list = list(stopwords.words('english'))
    handler = WikiHandler(stemmer, stopword_list, index)

    parse(args.xml_dump, handler)
    index.write_to_disk()
    index.save_index()
    args.index_stats.write("{}\n{}\n".format(handler.count, len(index.postings)))
