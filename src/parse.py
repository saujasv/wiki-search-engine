import sys
from xml.sax import parse
from xml.sax.xmlreader import XMLReader
from xml.sax.handler import ContentHandler
import Stemmer

from page import Page, Field

class WikiHandler(ContentHandler):
    def __init__(self, stemmer):
        self.page = None
        self.field = None
        self.stemmer = stemmer
        self.buffer = list()

    def startElement(self, name, attributes):
        if name == "page":
            self.page = Page()
        elif name == "title":
            self.field = Field.title
        elif name == "redirect":
            self.page.set_field(Field.title, attributes.getValue("title").strip())
        elif name == "text":
            self.field = Field.text

    def endElement(self, name):
        if name == "page":
            self.page.index()
        elif name == "text":
            self.page.parse_text(''.join(self.buffer).strip(), self.stemmer)
            # print(self.buffer)
            # pass
        elif self.field:
            self.page.set_field(self.field, ''.join(self.buffer).strip())
        self.field = None
        self.buffer = list()

    def characters(self, content):
        self.buffer += content

class TestStemmer:
    def __init__(self):
        pass

    def stemWord(self, w):
        return w

if __name__ == "__main__":
    parse(sys.argv[1], WikiHandler(Stemmer.Stemmer('english')))