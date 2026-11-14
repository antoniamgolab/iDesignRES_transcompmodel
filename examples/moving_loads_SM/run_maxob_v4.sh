#!/bin/bash
# Go RES v4 with capacity <= 1.1 x need per node, type and year (no building ahead).
cd "$(dirname "$0")"
echo "maxob10 start $(date)" >> maxob_v4.log
INPUT_FOLDER=uncertainty_scenarios_v2_night/scenario_000 RESULTS_DIR=v4/maxob10/scenario_000 KAPPA_PWR=0.5 KAPPA_SPACE=0.0005 MAX_OVERBUILD=0.1 GRB_THREADS=32 julia --project=../.. SM_batch_v3.jl > logs_v4/maxob10.log 2>&1
echo "maxob10 exit=$? $(date +%H:%M) $(grep -m1 Termination logs_v4/maxob10.log)" >> maxob_v4.log
