#!/bin/bash
# Go RES alone with the BET sales-share cap (check before starting the rest of jobs_v4.txt).
cd "$(dirname "$0")"
echo "main_000 start $(date)"
INPUT_FOLDER=uncertainty_scenarios_v2_night/scenario_000 RESULTS_DIR=v4/uncertainty_scenarios/scenario_000 GRB_THREADS=32 julia --project=../.. SM_batch_v3.jl > logs_v4/main_000.log 2>&1
echo "main_000 exit=$? $(date +%H:%M) $(grep -m1 Termination logs_v4/main_000.log)"
