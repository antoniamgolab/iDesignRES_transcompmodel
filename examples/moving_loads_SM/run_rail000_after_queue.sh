#!/bin/bash
# Rerun Go RES rail with constraint_mode_shift (first v3 rail run lacked it) once the rest-queue is done.
cd "$(dirname "$0")"
until grep -q "queue done" queue_v3_rest.log; do sleep 120; done
echo "rail_000 start $(date)"
INPUT_FOLDER=uncertainty_scenarios_v2_rail_night/scenario_000 RESULTS_DIR=v3/uncertainty_scenarios_rail/scenario_000 GRB_THREADS=32 julia --project=../.. SM_batch_v3.jl > logs_v3/rail_000.log 2>&1
echo "rail_000 exit=$? $(date +%H:%M) $(grep -m1 Termination logs_v3/rail_000.log)"
