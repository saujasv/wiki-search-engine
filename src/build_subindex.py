import subprocess
import argparse
import os

argparser = argparse.ArgumentParser()
argparser.add_argument("src_prefix", type=str)
argparser.add_argument("xml_dump", type=str)
argparser.add_argument("index_path", type=str)
argparser.add_argument("index_stats", type=str)

args = argparser.parse_args()
while not os.path.exists(os.path.join(args.index_path, "postings")):
    print("Building index {}".format(args.index_path))
    subprocess.call(['python', os.path.join(args.src_prefix, "parse.py"), args.index_path, args.index_stats])