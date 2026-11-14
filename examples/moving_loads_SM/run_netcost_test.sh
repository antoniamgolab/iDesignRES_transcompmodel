#!/bin/bash
# Test runs: network tariffs converted consistently (opt1: per-kWh price adder, opt2: N_c*gamma_l*8760 per kW)
cd "$(dirname "$0")"; mkdir -p logs_final
for job in "netkwh final/sensitivity/net_opt1_perkwh 0" "netgamma final/sensitivity/net_opt2_gamma 1"; do
  set -- $job
  echo "$1 start $(date +%H:%M)" >> queue_netcost.log
  NETWORK_COST_PER_KWH=$3 INPUT_FOLDER=v4_gridconn150_$1/scenario_000 RESULTS_DIR=$2 KAPPA_PWR=0.5 KAPPA_SPACE=Inf KAPPA_SPACE_CUM=0.004 MAX_OVERBUILD=0 GRB_THREADS=16 julia --project=../.. SM_batch_v3.jl > logs_final/net_$1.log 2>&1
  echo "$1 exit=$? $(date +%H:%M) $(grep -m1 Termination logs_final/net_$1.log)" >> queue_netcost.log
done
echo "queue done $(date)" >> queue_netcost.log
