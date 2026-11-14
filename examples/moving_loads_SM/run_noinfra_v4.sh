#!/bin/bash
# Option A: Go RES v4 with no charging-capacity additions in 2020/2024 (NO_INFRA_BEFORE=2028).
cd "$(dirname "$0")"
echo "noinfra2028 start $(date)" >> noinfra_v4.log
INPUT_FOLDER=uncertainty_scenarios_v2_night/scenario_000 RESULTS_DIR=v4/noinfra2028/scenario_000 KAPPA_PWR=0.5 KAPPA_SPACE=0.0005 NO_INFRA_BEFORE=2028 GRB_THREADS=32 julia --project=../.. SM_batch_v3.jl > logs_v4/noinfra2028.log 2>&1
echo "noinfra2028 exit=$? $(date +%H:%M) $(grep -m1 Termination logs_v4/noinfra2028.log)" >> noinfra_v4.log
