#/bin/bash

for line in `cat $1`
do
    data=`echo $line | cut -d\| -f1`
    index=`echo $line | cut -d\| -f2`
    python build_subindex.py . $3/$data $2/$index $2/$index/stats.txt &
done