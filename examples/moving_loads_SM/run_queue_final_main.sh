#!/bin/bash
# Runs jobs_final_main.txt, 3 in parallel.
cd "$(dirname "$0")"
echo "queue start $(date)" >> queue_final.log
xargs -P 3 -L 1 bash run_final_job.sh < jobs_final_main.txt
echo "queue done $(date)" >> queue_final.log
