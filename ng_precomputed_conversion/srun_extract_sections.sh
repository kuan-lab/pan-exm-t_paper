#!/bin/bash

#SBATCH --job-name=extract_sections.job
#SBATCH --time=3:00:00
#SBATCH --export=ALL
#SBATCH --output logs/extract_sections-%j.out
#SBATCH --nodes=1                   # Use 1 node
#SBATCH --ntasks=1                  # 1 task
#SBATCH --cpus-per-task=1           # Allocate N CPUs for the task
#SBATCH --mem-per-cpu=500G          # Memory per CPU
#SBATCH --partition=day

module purge
module load Python/3.10.8-GCCcore-12.2.0

bash -c "source /home/atk42/envs/cloudvol/bin/activate"
cd /home/atk42/repos/cloudvolume-igneous-scripts/241004_panExM
srun python extract_sections.py
