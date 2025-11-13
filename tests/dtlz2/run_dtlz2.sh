#!/bin/bash

python /sciclone/home/ksuresh/scr10/scheduler_epic/tests/dtlz2/test_slurm_multi_objectives_dtlz2.py --objectives 3 --parameters 50 --trials 100 --slurm_template /sciclone/home/ksuresh/scr10/scheduler_epic/tests/slurm/slurm.template --name dtlz2-3-50-100 > dtlz2-3-50-100.log 2>dtklz2-3-50-100.err
python /sciclone/home/ksuresh/scr10/scheduler_epic/tests/dtlz2/test_slurm_multi_objectives_dtlz2.py --objectives 4 --parameters 50 --trials 50 --slurm_template /sciclone/home/ksuresh/scr10/scheduler_epic/tests/slurm/slurm.template --name dtlz2-4-50-50 > dtlz2-4-50-50.log 2>dtklz2-4-50-50.err
python /sciclone/home/ksuresh/scr10/scheduler_epic/tests/dtlz2/test_slurm_multi_objectives_dtlz2.py --objectives 5 --parameters 50 --trials 50 --slurm_template /sciclone/home/ksuresh/scr10/scheduler_epic/tests/slurm/slurm.template --name dtlz2-5-50-50 > dtlz2-5-50-50.log 2>dtklz2-5-50-50.err

python /sciclone/home/ksuresh/scr10/scheduler_epic/tests/dtlz2/test_slurm_multi_objectives_dtlz2.py --objectives 3 --parameters 100 --trials 100 --slurm_template /sciclone/home/ksuresh/scr10/scheduler_epic/tests/slurm/slurm.template --name dtlz2-3-100-100 > dtlz2-3-100-100.log 2>dtklz2-3-100-100.err
