#!/bin/bash
# Grid charge sensitivity: grid charges scaled uniformly x2.5 and x5
cd "$(dirname "$0")"; mkdir -p logs_final
for t in x2.5 x5; do
  echo "net$t start $(date +%H:%M)" >> queue_netcost.log
  INPUT_FOLDER=v4_gridconn150_net$t/scenario_000 RESULTS_DIR=final/sensitivity/gridcharge_$t KAPPA_PWR=0.5 KAPPA_SPACE=Inf KAPPA_SPACE_CUM=0.004 MAX_OVERBUILD=0 GRB_THREADS=16 julia --project=../.. SM_batch_v3.jl > logs_final/net_$t.log 2>&1
  echo "net$t exit=$? $(date +%H:%M) $(grep -m1 Termination logs_final/net_$t.log)" >> queue_netcost.log
done
echo "netscale done $(date)" >> queue_netcost.log
