#!/bin/bash
# Go RES v4: cumulative space cap 4e-3*B_e charge points per node (stock), no per-period space cap.
cd "$(dirname "$0")"
echo "spacecum_noob start $(date)" >> spacecum_v4.log
INPUT_FOLDER=uncertainty_scenarios_v2_night/scenario_000 RESULTS_DIR=v4/spacecum_noob/scenario_000 KAPPA_PWR=0.5 KAPPA_SPACE=Inf KAPPA_SPACE_CUM=0.004 GRB_THREADS=16 julia --project=../.. SM_batch_v3.jl > logs_v4/spacecum_noob.log 2>&1
echo "spacecum_noob exit=$? $(date +%H:%M) $(grep -m1 Termination logs_v4/spacecum_noob.log)" >> spacecum_v4.log
