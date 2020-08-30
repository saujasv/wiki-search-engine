from enum import Enum
import re
import Stemmer

class Field(Enum):
    title = 0
    infobox = 1
    categories = 2
    links = 3
    references = 4
    body = 5

    def tag(self):
        return self.name[0]

class Page:
    def __init__(self):
        self.fields = [list() for f in Field]
    
    def set_field(self, field, value):
        if field is None:
            return
        else:
            try:
                self.fields[field.value] = value
            except IndexError:
                raise ValueError("Invalid field provided")
    
    def add_to_field(self, field, value):
        if field is None:
            return
        else:
            try:
                self.fields[field.value].append(value)
            except IndexError:
                raise ValueError("Cannot add to field")

    def parse_template(self, template):
        template_text = ""
        for kvp in template.split('|')[1:]:
            if '=' in kvp:
                key, *value = kvp.split('=')
                if not 'url' in key and not 'doi' in key:
                    template_text += ' '.join(value)
        return template_text

    def process_field(self, field, field_text, stemmer, stopwords):
        punctuation_regex = re.compile(r"[!\"#$%&\'\(\)\*\+,\-./:;—<=>\?@[\\\]\^_`\{\|\}~]")
        number_regex = re.compile(r"[0-9.,]+")
        # range_regex = re.compile(r"[0-9.,–\-]+")

        for tok in field_text.split():
            w = tok.lower().strip('!\"#$%&\'()\*+,-./:;—<=>?@[\\]\^_`{|}~')
            if w in stopwords:
                continue
            elif number_regex.fullmatch(w):
                if field == Field.references:
                    continue
                if len(w) <= 4:
                    self.fields[field.value].append(w)
            elif len(w) >= 3:
                if not punctuation_regex.search(w):
                    self.fields[field.value].append(stemmer.stemWord(w))

    def process_internal_link(self, mo):
        return mo.group(1) + mo.group(2).split('|')[-1] + mo.group(3)
    
    def parse_text(self, text, stemmer, stopwords):
        fields = ["" for f in Field]

        # Remove comments
        text = re.sub(r"(?=<!--).*?-->", "", text)

        # Remove math formulae
        text = re.sub(r"(?=<math>).*?</math>", "", text)

        # Remove tags
        text = re.sub(r"</?[^>/]*/?>", "", text)

        # Remove all non-infobox and non-reference templates that are not nested
        text = re.sub(r"{{(?!([Ii]nfobox|[Cc]ite))[^{}]+}}", "", text)

        # Remove all non-infobox and non-reference templates that are at a second level of nesting
        text = re.sub(r"{{(?!([Ii]nfobox|[Cc]ite))[^{}]+}}", "", text)

        # Extract external links
        for mo in re.finditer(r"\[(?!\[)([^\]]+)\](?!\])", text):
            fields[Field.links.value] += ' '.join(mo.group(1).split()[1:]) + ' '
        text = re.sub(r"\[(?!\[)[^\]]+\](?!\])", "", text)

        # Extract categories
        for mo in re.finditer(r"\[\[:?[Cc]ategory:([^\]]+)\]\]", text):
            fields[Field.categories.value] += mo.group(1) + " "
        text = re.sub(r"\[\[:?[Cc]ategory:[^\]]+\]\]", "", text)

        text = re.sub(r"(\w*)\[\[([^\]]+)\]\](\w*)", self.process_internal_link, text)

        # Extract references
        for mo in re.finditer(r"{{([Cc]ite [^{}]+)}}", text):
            fields[Field.references.value] += self.parse_template(mo.group(1)) + " "
        text = re.sub(r"{{[Cc]ite [^{}]+}}", "", text)

        # Extract infoboxes
        for mo in re.finditer(r"{{([Ii]nfobox [^{}]+)}}", text):
            fields[Field.infobox.value] += self.parse_template(mo.group(1)) + " "
        text = re.sub(r"{{[Ii]nfobox [^{}]+}}", "", text)

        # Remove file references
        text = re.sub(r"\[\[:?[Ff]ile:[^\]]+\]\]", "", text)

        # Only the body is left
        fields[Field.body.value] = text

        for f in Field:
            self.process_field(f, fields[f.value], stemmer, stopwords)