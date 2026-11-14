#!/bin/bash
# Full rerun of the final runs with MAX_OVERBUILD=0 (no capacity built ahead of demand), 4 in parallel.
# main_000 and mcs_only were run beforehand (copied from results/final_ob0); old results archived in results/final_ob10.
cd "$(dirname "$0")"
echo "queue start $(date)" >> queue_final_ob0.log
xargs -P 4 -L 1 bash run_final_job2.sh < jobs_final_ob0.txt
echo "queue done $(date)" >> queue_final_ob0.log
