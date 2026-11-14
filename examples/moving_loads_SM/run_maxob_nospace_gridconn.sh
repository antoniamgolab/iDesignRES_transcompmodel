#!/bin/bash
# Go RES v4: no overbuild (capacity <= 1.1 x need up to 2056), KAPPA_SPACE=Inf, one-off grid connection +250 EUR/kW (650 EUR/kW CAPEX).
cd "$(dirname "$0")"
echo "maxob_nospace_gridconn start $(date)" >> spacecum_v4.log
INPUT_FOLDER=v4_gridconn/scenario_000 RESULTS_DIR=v4/maxob2056_nospace_gridconn/scenario_000 KAPPA_PWR=0.5 KAPPA_SPACE=Inf MAX_OVERBUILD=0.1 GRB_THREADS=16 julia --project=../.. SM_batch_v3.jl > logs_v4/maxob_nospace_gridconn.log 2>&1
echo "maxob_nospace_gridconn exit=$? $(date +%H:%M) $(grep -m1 Termination logs_v4/maxob_nospace_gridconn.log)" >> spacecum_v4.log
