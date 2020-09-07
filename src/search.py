from split_index import InvertedIndex
import re
import Stemmer
import argparse
from nltk.corpus import stopwords

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("index_path", type=str)
    argparser.add_argument("queries_file", type=argparse.FileType('r'))
    args = argparser.parse_args()

    index = InvertedIndex.load(args.index_path)
    stemmer = Stemmer.Stemmer('english')
    stopword_list = list(stopwords.words('english'))

    for line in args.queries_file:
        print(*index.search(line.strip(), stemmer=stemmer, stopword_list=stopword_list), sep='\n', end='\n')
        print()