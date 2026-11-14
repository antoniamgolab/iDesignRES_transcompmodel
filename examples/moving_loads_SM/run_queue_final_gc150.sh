#!/bin/bash
# Runs jobs_final_gc150.txt, 4 in parallel.
cd "$(dirname "$0")"
echo "queue start $(date)" >> queue_final.log
xargs -P 4 -L 1 bash run_final_job.sh < jobs_final_gc150.txt
echo "queue done $(date)" >> queue_final.log
