#!/bin/bash
#SBATCH -A research
#SBATCH --qos=medium
#SBATCH -n 30
#SBATCH --mem-per-cpu=4096
#SBATCH --time=1-00:00:00
#SBATCH --mail-type=END
#SBATCH --mail-user=saujas.vaduguru@research.iiit.ac.in

cp -r data /scratch
./index.sh paths.txt ./full_index /scratch /scratch/data