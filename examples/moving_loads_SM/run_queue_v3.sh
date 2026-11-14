#!/bin/bash
# Overnight revision queue: waits for the kappa sweep, then runs jobs_v3.txt with 8 parallel Gurobi jobs (8 threads each).
cd "$(dirname "$0")"; mkdir -p logs_v3
while [ "$(tasklist //FI "IMAGENAME eq julia.exe" //NH | grep -c julia)" -gt 1 ]; do sleep 60; done
echo "queue start $(date)"
xargs -P 8 -L 1 bash -c 'INPUT_FOLDER=$1 RESULTS_DIR=$2 GRB_THREADS=8 julia --project=../.. SM_batch_v3.jl > logs_v3/$0.log 2>&1; echo "$0 exit=$? $(date +%H:%M) $(grep -m1 Termination logs_v3/$0.log)"' < jobs_v3.txt
echo "queue done $(date)"
