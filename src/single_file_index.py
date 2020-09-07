from collections import Counter, defaultdict, OrderedDict
from page import Field
import os
import re
import json
import Stemmer
import argparse
from nltk.corpus import stopwords
import numpy as np
import heapq

BUCKETS = [
    r"^[,.0-9]",
    # r"^[3-9]",
    r"^[a]",
    r"^[bc]",
    r"^[de]",
    r"^[fg]",
    r"^[hi]",
    r"^[jk]",
    r"^[lm]",
    r"^[nop]",
    r"^[qr]",
    r"^[s]",
    r"^[tu]",
    r"^."
]

class SingleFileIndex:
    def __init__(self, index_prefix, n_docs=0, rebuild=True):
        self.postings = defaultdict(list)
        self.titles = dict()
        self.doclengths = dict()
        self.n_docs = n_docs
        self.index_prefix = index_prefix
        self.titles_path = os.path.join(index_prefix, "titles.txt")
        self.doclengths_path = os.path.join(index_prefix, "length.txt")
        self.postings_file = os.path.join(index_prefix, "postings")

        if not os.path.exists(self.index_prefix):
            os.mkdir(self.index_prefix)
        
        if rebuild:
            if os.path.exists(self.titles_path):
                os.remove(self.titles_path)
            
            if os.path.exists(self.doclengths_path):
                os.remove(self.doclengths_path)
            
            if os.path.exists(self.postings_file):
                os.remove(self.postings_file)
    
    def save_index(self):
        with open(os.path.join(self.index_prefix, "meta.json"), 'w') as f:
            metadata = {
                "n_docs": self.n_docs,
            }
            json.dump(metadata, f)
    
    @classmethod
    def load(cls, path):
        with open(os.path.join(path, "meta.json"), 'r') as f:
            metadata = json.load(f)
        
        return cls(path, metadata['n_docs'])
    
    def update(self, page, title, docid):
        self.n_docs += 1
        
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
            s = str(docid)
            for f in Field:
                if counts[f.value] > 0:
                    s += f.tag() + str(counts[f.value])
            self.postings[w].append(s)

        if docid in self.titles:
            raise Exception("duplicate docid" + str(docid))
        if docid in self.doclengths:
            raise Exception("duplicate docid" + str(docid))
        self.titles[docid] = title
        self.doclengths[docid] = np.sqrt(np.sum(np.square(list(page_counter.values()))))

    def write_to_disk(self):
        self.write_postings(self.postings_file)

        with open(self.titles_path, 'w') as f:
            f.write('\n'.join(["{}||{}".format(d, self.titles[d]) for d in sorted(self.titles.keys())]) + '\n')
        
        with open(self.doclengths_path, 'w') as f:
            f.write('\n'.join(["{}:{}".format(d, self.doclengths[d]) for d in sorted(self.doclengths.keys())]) + '\n')
    
    def write_postings(self, path):
        key_order = sorted(self.postings.keys())
        with open(path, 'w') as f:
            for k in key_order:
                f.write("{}:{}:{}\n".format(k, len(self.postings[k]), '|'.join(self.postings[k])))

    def load_postings(self):
        postings = defaultdict(list)
        df = defaultdict(int)
        try:
            for line in open(self.postings_file, 'r'):
                k, i, p = line.strip().split(':')
                postings[k] = p.split('|')
                df[k] = i
        except FileNotFoundError:
            return postings

        return postings, df

    def get_titles(self):
        titles = dict()
        with open(self.titles_path, 'r') as f:
            for line in f:
                docid, title = line.strip().split('||')
                titles[int(docid)] = title
        return titles

    def get_lengths(self):
        lengths = dict()
        with open(self.doclengths_path, 'r') as f:
            for line in f:
                docid, length = line.strip().split(':')
                lengths[int(docid)] = float(length)
        return lengths