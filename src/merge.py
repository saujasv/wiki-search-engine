from single_file_index import SingleFileIndex
from split_index import InvertedIndex
import argparse
import os

argparser = argparse.ArgumentParser()
argparser.add_argument("index_path", type=str)
argparser.add_argument("subindex_path", type=str)
argparser.add_argument("indices", type=str, nargs='+')

args = argparser.parse_args()

indices = [SingleFileIndex.load(os.path.join(args.subindex_path, path)) for path in args.indices]
merged = InvertedIndex.merge(args.index_path, indices)
merged.save_index()