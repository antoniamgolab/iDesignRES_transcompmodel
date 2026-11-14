#!/bin/bash
# R6-4 counterfactuals on the v4 setup (cap, time-of-day prices, fixed objective), Go RES:
#   mcs_only              : no CCS anywhere, fleet free
#   mcs_only_fixed_flows  : no CCS, BEV road flows fixed to v4 Go RES -> identical route energy
# Starts after the v4 queue is done (2 jobs x 16 threads).
cd "$(dirname "$0")"
until grep -q "queue v4 (rest) done" queue_v4.log; do sleep 120; done
echo "mcs_only start $(date)"
MCS_ONLY=1 INPUT_FOLDER=uncertainty_scenarios_v2_night/scenario_000 RESULTS_DIR=v4/mcs_only/scenario_000 GRB_THREADS=16 \
  julia --project=../.. SM_batch_v3.jl > logs_v4/mcs_only.log 2>&1 &
MCS_ONLY=1 FIX_BEV_FLOWS_FROM=v4/uncertainty_scenarios/scenario_000 INPUT_FOLDER=uncertainty_scenarios_v2_night/scenario_000 \
  RESULTS_DIR=v4/mcs_only_fixed_flows/scenario_000 GRB_THREADS=16 julia --project=../.. SM_batch_v3.jl > logs_v4/mcs_only_fixed_flows.log 2>&1 &
wait
for l in mcs_only mcs_only_fixed_flows; do echo "$l $(date +%H:%M) $(grep -m1 Termination logs_v4/$l.log)"; done
echo "mcs_only done $(date)"
