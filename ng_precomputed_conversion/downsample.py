#!/usr/bin/env python3
#SBATCH -t 4:00:00
#SBATCH -p day 
#SBATCH -o igneous_logs/downsample.o%j
#SBATCH -e igneous_logs/downsample.e%j
#SBATCH -J downsample_CloudVolume
#SBATCH --mail-type=END
#SBATCH --mem 32GB

# First generate tasks by running:
#   ./downsample.py create_task_queue
# You can submit this as a job to the o2 cluster by running:
#   sbatch downsample.py run_tasks_from_queue
# Run that command multiple times (4 to 16 times is reasonable) to process tasks in parallel

import sys

import igneous.task_creation as tc
from cloudvolume.lib import Bbox


queuepath = 'igneous_tasks'
bounds = None  # None will use full bounds


def create_task_queue():
    from taskqueue import TaskQueue
    tq = TaskQueue('fq://'+queuepath)
    cloud_path=input('Cloud Path:')
    tasks = tc.create_downsampling_tasks(
        cloud_path,
        mip=0,       # Starting mip
        num_mips=6,  # Final mip to downsample to
        bounds=bounds,
        compress=False,
        factor=(2, 2, 2)  # Downsample all 3 axes
    )
    tq.insert(tasks)
    print('Done adding {} tasks to queue at {}'.format(len(tasks), queuepath))


def run_tasks_from_queue():
    from taskqueue import TaskQueue
    tq = TaskQueue('fq://'+queuepath)
    print('Working on tasks from filequeue "{}"'.format(queuepath))
    tq.poll(
        verbose=True, # prints progress
        lease_seconds=3000,
        tally=True # makes tq.completed work, logs 1 byte per completed task
    )
    print('Done')


def run_tasks_locally(n_cores=4):
    from taskqueue import LocalTaskQueue
    tq = LocalTaskQueue(parallel=n_cores)
    tasks = tc.create_downsampling_tasks(
        cloud_path,
        mip=0,       # Starting mip
        num_mips=6,  # Final mip to downsample to
        bounds=bounds
    )
    tq.insert(tasks)
    print('Running in-memory task queue on {} cores'.format(n_cores))
    tq.execute()
    print('Done')


if __name__ == '__main__':
    l = locals()
    public_functions = [f for f in l if callable(l[f]) and f[0] != '_']
    if len(sys.argv) <= 1 or not sys.argv[1] in public_functions:
        from inspect import signature
        print('Functions available:')
        for f_name in public_functions:
            print('  '+f_name+str(signature(l[f_name])))
            docstring = l[f_name].__doc__
            if not isinstance(docstring, type(None)):
                print(docstring.strip('\n'))
        # TODO add an instruction here that says:
        # 'For example, run the following from your command line to call the function blah:'
        # 'python script_name.py blah arg1 arg2 kw1=kwarg1'
    else:
        func = l[sys.argv[1]]
        args = []
        kwargs = {}
        for arg in sys.argv[2:]:
            if '=' in arg:
                split = arg.split('=')
                kwargs[split[0]] = split[1]
            else:
                args.append(arg)
        func(*args, **kwargs)
