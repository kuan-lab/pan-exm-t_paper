#!/bin/bash

#SBATCH --job-name=prechunk.job
#SBATCH --time=8:00:00
#SBATCH --export=ALL
#SBATCH --output logs/prechunk-%j.out
#SBATCH --nodes=1                   # Use 1 node
#SBATCH --ntasks=1                  # 1 task
#SBATCH --cpus-per-task=32           # Allocate N CPUs for the task
#SBATCH --mem-per-cpu=30G           # Memory per CPU
module purge
module load Python/3.10.8-GCCcore-12.2.0

#source /home/atk42/envs/cloudvol/bin/activate
#env > slurm_env.txt
bash -c "source /home/atk42/envs/cloudvol/bin/activate"
python upload_fullres_aligned_FIBSEM_stack.py
