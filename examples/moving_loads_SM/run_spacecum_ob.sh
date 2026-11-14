#!/bin/bash
# Go RES v4: cumulative space cap 4e-3*B_e charge points per node (stock), no per-period space cap, capacity <= 1.1 x need up to 2056.
cd "$(dirname "$0")"
echo "spacecum_ob start $(date)" >> spacecum_v4.log
INPUT_FOLDER=uncertainty_scenarios_v2_night/scenario_000 RESULTS_DIR=v4/spacecum_ob/scenario_000 KAPPA_PWR=0.5 KAPPA_SPACE=Inf KAPPA_SPACE_CUM=0.004 MAX_OVERBUILD=0.1 GRB_THREADS=16 julia --project=../.. SM_batch_v3.jl > logs_v4/spacecum_ob.log 2>&1
echo "spacecum_ob exit=$? $(date +%H:%M) $(grep -m1 Termination logs_v4/spacecum_ob.log)" >> spacecum_v4.log
