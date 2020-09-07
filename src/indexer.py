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

class InvertedIndex:
    def __init__(self, index_prefix, buckets=BUCKETS, block_size=10000000, docid=0):
        self.postings = defaultdict(list)
        self.title_buffer = list()
        self.doclength_buffer = list()
        self.docid = docid
        self.buckets = buckets
        self.block_size = block_size
        self.current_postings_count = 0
        self.index_prefix = index_prefix
        self.titles_path = os.path.join(index_prefix, "titles.txt")
        self.doclengths_path = os.path.join(index_prefix, "length.txt")
        self.index_files = [os.path.join(index_prefix, str(i) + ".index") for i, b in enumerate(buckets)]
        self.posting_regexes = [re.compile(r) for r in [r"t([0-9]+)", r"i([0-9]+)", r"c([0-9]+)", r"l([0-9]+)", r"r([0-9]+)", r"b([0-9]+)"]]
        self.weight_vector = np.array([.3, .2, .15, .05, .05, .25])
    
    def save_index(self):
        with open(os.path.join(self.index_prefix, "meta.json"), 'w') as f:
            metadata = {
                "docid": self.docid,
                "buckets": self.buckets,
                "block_size": self.block_size
            }
            json.dump(metadata, f)
    
    @classmethod
    def load(cls, path):
        with open(os.path.join(path, "meta.json"), 'r') as f:
            metadata = json.load(f)
        
        return cls(path, metadata['buckets'], metadata['block_size'], metadata['docid'])
    
    def update(self, page, title):
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
            self.current_postings_count += 1

        self.title_buffer.append(title)
        self.doclength_buffer.append(np.sqrt(np.sum(np.square(list(page_counter.values())))))
        
        if self.current_postings_count > self.block_size:
            self.write_block()
            self.postings = defaultdict(list)
            self.current_postings_count = 0
            self.title_buffer = list()
            self.doclength_buffer = list()
    
    def load_single_file_postings(self):
        if len(self.index_files) > 1:
            raise Exception("Trying to load multi-file index")

        postings = OrderedDict()
        df = OrderedDict()
        try:
            for line in open(self.index_files[0], 'r'):
                k, i, p = line.strip().split(':')
                postings[k] = p.split('|')
                df[k] = int(i)
        except FileNotFoundError:
            return postings

        return postings, df
    
    @classmethod
    def merge(cls, path, indices):
        merged = cls(path)
        for index in indices:
            if len(index.index_files) > 1:
                raise Exception("Can merge only single-file indices.")
        
        for index in indices:
            idx_postings, idx_df = index.load_single_file_postings()
            ordered_keys = list(idx_postings.keys())
            n_keys = len(ordered_keys)

            i = 0
            for j, b in enumerate(merged.buckets):
                if not re.match(b, ordered_keys[i]):
                    continue
                
                curr_file = merged.index_files[j]
                curr_postings = merged.postings_from_file(curr_file)
                
                while re.match(b, ordered_keys[i]):
                    curr_postings[ordered_keys[i]].extend(idx_postings.postings[ordered_keys[i]])
                    i += 1
                    if i >= n_keys:
                        break

                merged.write_to_file(curr_file, curr_postings)
                if i >= n_keys:
                    break
        
        return merged

    def write_block(self):
        ordered_keys = sorted(self.postings.keys())
        n_keys = len(ordered_keys)
        if n_keys == 0:
            return

        print("writing block")
        # print(ordered_keys[0], len(ordered_keys[0]), ordered_keys[0] == ' ', self.postings[ordered_keys[0]])

        i = 0
        for j, b in enumerate(self.buckets):
            if not re.match(b, ordered_keys[i]):
                # print('next_bucket')
                continue
            
            curr_file = self.index_files[j]
            curr_postings = self.postings_from_file(curr_file)
            
            while re.match(b, ordered_keys[i]):
                curr_postings[ordered_keys[i]].extend(self.postings[ordered_keys[i]])
                i += 1
                if i >= n_keys:
                    break

            self.write_to_file(curr_file, curr_postings)
            if i >= n_keys:
                break
        
        with open(self.titles_path, 'a') as f:
            f.write('\n'.join(self.title_buffer) + '\n')
        
        with open(self.doclengths_path, 'a') as f:
            f.write('\n'.join(map(str, self.doclength_buffer)) + '\n')
    
    def write_to_file(self, path, postings=None, order=None):
        # print("writing to file")
        if postings is None:
            postings = self.postings
        key_order = sorted(postings.keys()) if order is None else order
        with open(path, 'w') as f:
            for k in key_order:
                f.write("{}:{}:{}\n".format(k, len(postings[k]), '|'.join(postings[k])))
            # print("written to file")
    
    def parse_posting(self, posting):
        docid = int(re.match(r"^[0-9]+", posting).group())
        mos = [r.search(posting) for r in self.posting_regexes]
        tf = [0 if mo is None else int(mo.group(1)) for mo in mos]
        return docid, np.array(tf)
    
    def get_postings(self, terms, field=None):
        n_terms = len(terms)
        if n_terms == 0:
            return

        term_list = sorted(list(enumerate(terms)), key=lambda x: x[1])
        i = 0
        postings = list()

        for j, b in enumerate(self.buckets):
            if not re.match(b, term_list[i][1]):
                continue

            curr_file = self.index_files[j]
            curr_postings, curr_df = self.postings_and_df_from_file(curr_file)

            while re.match(b, term_list[i][1]):
                postings.append((term_list[i][0], curr_postings[term_list[i][1]], int(curr_df[term_list[i][1]])))
                i += 1
                if i >= n_terms:
                    break
            
            if i >= n_terms:
                break
        
        return map(lambda x: (x[1], x[2]), sorted(postings, key=lambda x: x[0]))

    def postings_and_df_from_file(self, path):
        postings = defaultdict(list)
        df = defaultdict(int)
        try:
            for line in open(path, 'r'):
                k, i, p = line.strip().split(':')
                postings[k] = p.split('|')
                df[k] = i
        except FileNotFoundError:
            return postings

        return postings, df

    def postings_from_file(self, path):
        postings = defaultdict(list)
        try:
            for line in open(path, 'r'):
                k, i, p = line.strip().split(':')
                postings[k] = p.split('|')
        except FileNotFoundError:
            return postings

        return postings
    
    def get_top_k(self, k, postings, mask=None):
        score_vectors = defaultdict(lambda: np.zeros(6))
        if mask:
            for i, (p_list, df) in enumerate(postings):
                idf = np.log(self.docid/df)
                for p in p_list:
                    doc, tf = self.parse_posting(p)
                    score_vectors[doc] += idf * (np.multiply(mask[i], tf))
        else:
            for i, (p_list, df) in enumerate(postings):
                idf = np.log(self.docid/df)
                for p in p_list:
                    doc, tf = self.parse_posting(p)
                    score_vectors[doc] += idf * tf


        docs = list(sorted(score_vectors.keys()))
        lengths = self.get_lengths(docs)
        scores = defaultdict(int)
        if mask:
            for d in docs:
                scores[d] = (np.dot(score_vectors[d], self.weight_vector))
        else:
            for d in docs:
                scores[d] = (1 / lengths[d]) * (np.dot(score_vectors[d], self.weight_vector))

        return heapq.nlargest(k, scores.items(), key=lambda x: x[1])

    def get_titles(self, docids):
        titles = dict()
        docs = sorted(docids)
        n_docs = len(docids)
        with open(self.titles_path, 'r') as f:
            i = 0
            j = 0
            for line in f:
                i += 1
                if i == docs[j]:
                    titles[docs[j]] = line.strip()
                    j += 1
                    if j >= n_docs:
                        break
        return titles

    def get_lengths(self, docids):
        lengths = defaultdict(float)
        docs = sorted(docids)
        n_docs = len(docids)
        with open(self.doclengths_path, 'r') as f:
            i = 0
            j = 0
            for line in f:
                i += 1
                if i == docs[j]:
                    lengths[docs[j]] = float(line.strip())
                    j += 1
                    if j >= n_docs:
                        break
        return lengths
    
    def search(self, query_string, k=10, stemmer=None, stopword_list=None):
        punct_regex = re.compile(r"[!\"#$%&\'\(\)\*\+,\-./:;—<=>\?@[\\\]\^_`\{\|\}~]")
        if stemmer is None:
            stemmer = Stemmer.Stemmer('english')
        if stopword_list is None:
            stopword_list = list(stopwords.words('english'))
        
        query = list()
        field = None
        field_query = False
        for tok in query_string.split():
            if ':' in tok:
                field, word = tok.split(':')
                field_query = True
                query.extend([(field, q.lower()) for q in punct_regex.split(word) if len(q) >= 3])
            else:
                query.extend([(field, q.lower()) for q in punct_regex.split(tok) if len(q) >= 3])
        
        processed_query = [(f, stemmer.stemWord(q)) for f, q in query if not q in stopword_list]
        query_terms = list(map(lambda x: x[1], processed_query))
        if field_query:
            field_mask = [np.array([1 if f.tag() == qf else 0 for f in Field]) for qf, _ in processed_query]
            top_docs = self.get_top_k(k, self.get_postings(query_terms), field_mask)
        else:
            top_docs = self.get_top_k(k, self.get_postings(query_terms))
        
        titles = self.get_titles(list(map(lambda x: x[0], top_docs)))

        return ["{}, {}".format(d, titles[d]) for d, s in top_docs if s > 0]