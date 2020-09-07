#/bin/bash

./src/subindex.sh $1 $3
python src/merge.py $2 $3 `cat $1 | cut -d\| -f2`