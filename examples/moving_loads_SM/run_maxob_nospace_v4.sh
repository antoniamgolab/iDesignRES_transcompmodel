#!/bin/bash
# Go RES v4: capacity <= 1.1 x need per node/type/year AND no space limit (power limit kept).
cd "$(dirname "$0")"
echo "maxob10_nospace start $(date)" >> maxob_nospace_v4.log
INPUT_FOLDER=uncertainty_scenarios_v2_night/scenario_000 RESULTS_DIR=v4/maxob10_nospace/scenario_000 KAPPA_PWR=0.5 KAPPA_SPACE=Inf MAX_OVERBUILD=0.1 GRB_THREADS=32 julia --project=../.. SM_batch_v3.jl > logs_v4/maxob10_nospace.log 2>&1
echo "maxob10_nospace exit=$? $(date +%H:%M) $(grep -m1 Termination logs_v4/maxob10_nospace.log)" >> maxob_nospace_v4.log
