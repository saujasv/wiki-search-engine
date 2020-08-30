from collections import Counter, defaultdict
from page import Field

class InvertedIndex:
    def __init__(self):
        self.postings = defaultdict(list)
        self.docid = 0
    
    def update(self, page):
        self.docid += 1
        
        counters = list()
        page_counter = Counter()
        for f in Field:
            field_counter = Counter()
            for w in page.fields[f.value]:
                field_counter[w] += 1
                page_counter[w] += 1
            counters.append(field_counter)
        
        for w in page_counter:
            counts = [field_counter[w] for field_counter in counters]
            s = str(self.docid)
            for f in Field:
                if counts[f.value] > 0:
                    s += f.tag() + str(counts[f.value])
            self.postings[w].append(s)
    
    def write_to_file(self, f):
        for k in sorted(self.postings.keys()):
            f.write("{}:{}\n".format(k, '|'.join(self.postings[k])))
    
    def get_postings(self, term, field=None):
        postings = self.postings[term]
        if field:
            postings = [p for p in postings if field in p]
        return postings
    
    @classmethod
    def from_file(cls, path):
        index = cls()
        for line in open(path, 'r'):
            key, postings = line.split(':')
            index.postings[key] = postings.split('|')
        return index