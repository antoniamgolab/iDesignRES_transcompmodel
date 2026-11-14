#!/bin/bash
# PRIORITY: Go RES with +250 EUR/kW one-time grid-connection cost on CCS and MCS capex (v4 settings otherwise).
cd "$(dirname "$0")"
echo "gridconn_250 start $(date)" >> gridconn_v4.log
INPUT_FOLDER=v4_gridconn/scenario_000 RESULTS_DIR=v4/gridconn_250/scenario_000 KAPPA_PWR=0.5 KAPPA_SPACE=0.0005 GRB_THREADS=16 julia --project=../.. SM_batch_v3.jl > logs_v4/gridconn_250.log 2>&1
echo "gridconn_250 exit=$? $(date +%H:%M) $(grep -m1 Termination logs_v4/gridconn_250.log)" >> gridconn_v4.log
