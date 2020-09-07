For each XML dump, run src/build_subindex.py with appropriate arguments (use -h to get arguments required) to build each subindex.
Once all XML files are processed, run src/merge.py to merge all the subindices created in the previous step.
THe final index is now prepared. To search, run src/search.py with the index and queries file as arugments.