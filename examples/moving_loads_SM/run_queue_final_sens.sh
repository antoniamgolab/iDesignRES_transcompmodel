#!/bin/bash
# Robustness / sensitivity batch with the final base case: waits for the base-case queue (queue_final.log), then runs jobs_final_sens.txt, 4 in parallel.
cd "$(dirname "$0")"
until grep -q "queue done" queue_final.log; do sleep 60; done
echo "queue start $(date)" >> queue_final_sens.log
xargs -P 4 -L 1 bash run_final_job2.sh < jobs_final_sens.txt
echo "queue done $(date)" >> queue_final_sens.log
