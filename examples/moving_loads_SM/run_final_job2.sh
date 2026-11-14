#!/bin/bash
# Final base case settings with optional overrides.
# usage: run_final_job2.sh <label> <input folder> <results dir> [VAR=value ...]   (VAR= with empty value unsets VAR)
# Defaults: cumulative space cap 4e-3*B_e, no overbuild (capacity <= need until 2056), kappa_pwr 0.5, no per-period space cap.
cd "$(dirname "$0")"; mkdir -p logs_final
declare -A E=([KAPPA_PWR]=0.5 [KAPPA_SPACE]=Inf [KAPPA_SPACE_CUM]=0.004 [MAX_OVERBUILD]=0 [GRB_THREADS]=16)
for kv in "${@:4}"; do k=${kv%%=*}; v=${kv#*=}; if [ -z "$v" ]; then unset "E[$k]"; else E[$k]=$v; fi; done
args=(); for k in "${!E[@]}"; do args+=("$k=${E[$k]}"); done
echo "$1 start $(date +%H:%M) ${args[*]}" >> queue_final_sens.log
env "${args[@]}" INPUT_FOLDER=$2 RESULTS_DIR=$3 julia --project=../.. SM_batch_v3.jl > logs_final/$1.log 2>&1
echo "$1 exit=$? $(date +%H:%M) $(grep -m1 Termination logs_final/$1.log)" >> queue_final_sens.log
