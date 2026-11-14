#!/bin/bash
# Revision queue v4 (2026-10-14): corrected objective, time-of-day prices, BET sales-share cap (SM_batch_v3.jl).
# jobs_v4_rest.txt: label input_folder results_dir kappa_pwr kappa_space. 8 parallel jobs x 8 Gurobi threads.
cd "$(dirname "$0")"; mkdir -p logs_v4
echo "queue v4 (rest) start $(date)"
xargs -P 8 -L 1 bash -c 'INPUT_FOLDER=$1 RESULTS_DIR=$2 KAPPA_PWR=$3 KAPPA_SPACE=$4 GRB_THREADS=8 julia --project=../.. SM_batch_v3.jl > logs_v4/$0.log 2>&1; echo "$0 exit=$? $(date +%H:%M) $(grep -m1 Termination logs_v4/$0.log)"' < jobs_v4_rest.txt
echo "queue v4 (rest) done $(date)"
