from enum import Enum
from tokenize import tokenize
import re
import Stemmer

class Field(Enum):
    title = 1
    text = 2
    infobox = 3
    categories = 4
    links = 5
    references = 6
    body = 7

class Page:
    def __init__(self, title=[], text=[], body = [], infobox=[], categories=[], links=[], references=[]):
        self.title = title
        self.body = body
        self.infobox = infobox
        self.categories = categories
        self.links = links
        self.references = references
    
    def set_field(self, field, value):
        if field is None:
            return

        if field == Field.title:
            self.title = value
        elif field == Field.text:
            self.text = value
        elif field == Field.infobox:
            self.infobox = value
        elif field == Field.categories:
            self.categories = value
        elif field == Field.links:
            self.links = value
        elif field == Field.references:
            self.references = value
        else:
            raise ValueError("Invalid field provided")
    
    def add_to_field(self, field, value):
        if field is None:
            return

        if field == Field.body:
            self.body.append(value)
        elif field == Field.infobox:
            self.infobox.append(value)
        elif field == Field.categories:
            self.categories.append(value)
        elif field == Field.links:
            self.links.append(value)
        elif field == Field.references:
            self.references.append(value)
        else:
            raise ValueError("Cannot add to field")
    
    def parse_citation(self, token_stream, stemmer):
        mode = 'key'
        while True:
            tok, tag = next(token_stream)
            if tag == 'close_braces':
                return token_stream
            elif tag == 'equal':
                mode = 'value'
            elif tag == 'bar':
                mode = 'key'
            elif tag == 'word' and mode == 'value':
                self.references.append(stemmer.stemWord(tok.lower()))
            elif tag == 'open_double_square' and mode == 'value':
                token_stream = self.parse_link(token_stream, Field.references, stemmer)
            elif tag == 'open_braces':
                tok, tag = next(token_stream)
                while tag != 'close_braces':
                    tok, tag = next(token_stream)
    
    def parse_reference(self, token_stream, stemmer):
        while True:
            tok, tag = next(token_stream)
            if tok == "</ref>":
                return token_stream
            elif tag == 'word':
                self.references.append(stemmer.stemWord(tok.lower()))
            elif tag == 'open_double_square':
                token_stream = self.parse_link(token_stream, Field.references, stemmer)
            elif tag == 'open_braces':
                tok, tag = next(token_stream)
                if re.match(r'[Cc]ite', tok):
                    token_stream = self.parse_citation(token_stream, stemmer)
                else:
                    while tag != 'close_braces':
                        tok, tag = next(token_stream)

    
    def parse_link(self, token_stream, field, stemmer):
        tok, tag = next(token_stream)
        first_tok = tok
        if first_tok == ':':
            tok, tag = next(token_stream)
        if re.match(r'[Cc]ategory', tok):
            tok, tag = next(token_stream)
            if tok == ':':
                tok, tag = next(token_stream)
                while tag != 'close_double_square':
                    self.categories.append(stemmer.stemWord(tok.lower()))
                    tok, tag = next(token_stream)
            else:
                self.add_to_field(field, stemmer.stemWord(tok.lower()))
                while tag != 'close_double_square':
                    self.add_to_field(field, stemmer.stemWord(tok.lower()))
                    tok, tag = next(token_stream)
        elif re.match(r'[Ff]ile', tok):
            tok, tag = next(token_stream)
            if tok == ':':
                tok, tag = next(token_stream)
                while tag != 'close_double_square':
                    tok, tag = next(token_stream)
            else:
                self.add_to_field(field, stemmer.stemWord(tok.lower()))
                while tag != 'close_double_square':
                    self.add_to_field(field, stemmer.stemWord(tok.lower()))
                    tok, tag = next(token_stream)
        elif tag == 'word':
            buffer = [tok]
            tok, tag = next(token_stream)
            while tag != 'close_double_square':
                if tag == 'bar':
                    buffer = list()
                else:
                    buffer.append(tok)
                tok, tag = next(token_stream)
            for w in buffer:
                self.add_to_field(field, stemmer.stemWord(w.lower()))
        return token_stream

    def parse_infobox(self, token_stream, stemmer):
        mode = 'key'
        while True:
            tok, tag = next(token_stream)
            if tag == 'close_braces':
                return token_stream
            elif tag == 'equal':
                mode = 'value'
            elif tag == 'bar':
                mode = 'key'
            elif tag == 'word' and mode == 'value':
                self.infobox.append(stemmer.stemWord(tok.lower()))
            elif tag == 'open_double_square' and mode == 'value':
                token_stream = self.parse_link(token_stream, Field.infobox, stemmer)
            elif tag == 'open_braces':
                tok, tag = next(token_stream)
                if re.match(r'[Cc]ite', tok):
                    token_stream = self.parse_citation(token_stream, stemmer)
                else:
                    while tag != 'close_braces':
                        tok, tag = next(token_stream)
            elif tag == 'open_tag' and re.match(r'<ref[^>]*>', tok):
                token_stream = self.parse_reference(token_stream, stemmer)
    
    def parse_text(self, text, stemmer):
        token_stream = tokenize(text)

        while True:
            try:
                tok, tag = next(token_stream)
                if tag == 'open_braces':
                    tok, tag = next(token_stream)
                    if re.match(r'[Ii]nfobox', tok):
                        token_stream = self.parse_infobox(token_stream, stemmer)
                    elif re.match(r'[Cc]ite', tok):
                        token_stream = self.parse_reference(token_stream, stemmer)
                    else:
                        while tag != 'close_braces':
                            tok, tag = next(token_stream)
                elif tag == 'open_double_square':
                    token_stream = self.parse_link(token_stream, Field.body, stemmer)
                elif tag == 'word':
                    self.body.append(stemmer.stemWord(tok.lower()))
                elif tag == 'open_tag' and re.match(r'<ref[^>]*>', tok):
                    token_stream = self.parse_reference(token_stream, stemmer)
            except StopIteration:
                break
    
    def index(self):
        # print("page done")
        pass