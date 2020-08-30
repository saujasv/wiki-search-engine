from indexer import InvertedIndex
import re
import Stemmer
import argparse
from nltk.corpus import stopwords

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("index_file", type=str)
    argparser.add_argument("query", type=str, nargs='+')
    args = argparser.parse_args()

    index = InvertedIndex.from_file(args.index_file)
    stemmer = Stemmer.Stemmer('english')
    stopwords = list(stopwords.words('english'))

    query_words = list()
    field = None
    for tok in args.query:
        tok = tok.lower()
        if ':' in tok:
            field, word = tok.split(':')
            if not word in stopwords:
                query_words.append((field, stemmer.stemWord(word)))
        else:
            query_words.append((field, stemmer.stemWord(tok)))
    
    print(query_words)

    print('\n'.join(["{}: {}".format(t, ' '.join(index.get_postings(t, f))) for f, t in query_words]))