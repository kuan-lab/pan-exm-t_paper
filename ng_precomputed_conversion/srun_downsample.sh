#!/bin/bash

#SBATCH --job-name=downsample.job
#SBATCH --time=4:00:00
#SBATCH --export=ALL
#SBATCH --output logs/downsample-%j.out
#SBATCH --nodes=1                   # Use 1 node
#SBATCH --ntasks=1                  # 1 task
#SBATCH --cpus-per-task=32           # Allocate N CPUs for the task
#SBATCH --mem-per-cpu=10G           # Memory per CPU
#SBATCH --partition=day

module purge
module load Python/3.10.8-GCCcore-12.2.0

#source /home/atk42/envs/cloudvol/bin/activate
#env > slurm_env.txt
bash -c "source /home/atk42/envs/cloudvol/bin/activate"
cd /home/atk42/repos/cloudvolume-igneous-scripts/240921_upload_FIBSEM
srun python downsample.py run_tasks_from_queue
