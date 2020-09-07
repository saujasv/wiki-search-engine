from single_file_index import SingleFileIndex
from split_index import InvertedIndex
import argparse
import os

argparser = argparse.ArgumentParser()
argparser.add_argument("index_path", type=str)
argparser.add_argument("subindex_path", type=str)
argparser.add_argument("indices", type=str, nargs='+')

args = argparser.parse_args()

BUCKETS = [
    r"[\.–0-9\-,]",
    r"a",
    r"b",
    r"c",
    r"d",
    r"e",
    r"f",
    r"g",
    r"h",
    r"i",
    r"j",
    r"k",
    r"l",
    r"m",
    r"n",
    r"o",
    r"p",
    r"q",
    r"r",
    r"s",
    r"t",
    r"u",
    r"[vw]",
    r"[xyz]",
]

buckets = ["^" + c1 + c2 for c1 in BUCKETS for c2 in BUCKETS+[r"."]]
buckets.append(r"^[^,\.–0-9\-a-z]")

indices = [SingleFileIndex.load(os.path.join(args.subindex_path, path)) for path in args.indices]
merged = InvertedIndex.merge(args.index_path, indices, bucketing=buckets)
merged.save_index()