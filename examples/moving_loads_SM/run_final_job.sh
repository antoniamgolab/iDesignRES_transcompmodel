#!/bin/bash
# Final base case: cumulative space cap 4e-3*B_e, no overbuild (capacity <= need until 2056), kappa_pwr 0.5, CAPEX incl. one-off grid connection (from input folder).
# usage: run_final_job.sh <label> <input folder> <results dir>
cd "$(dirname "$0")"; mkdir -p logs_final
echo "$1 start $(date +%H:%M)" >> queue_final.log
INPUT_FOLDER=$2 RESULTS_DIR=$3 KAPPA_PWR=0.5 KAPPA_SPACE=Inf KAPPA_SPACE_CUM=0.004 MAX_OVERBUILD=0 GRB_THREADS=16 julia --project=../.. SM_batch_v3.jl > logs_final/$1.log 2>&1
echo "$1 exit=$? $(date +%H:%M) $(grep -m1 Termination logs_final/$1.log)" >> queue_final.log
