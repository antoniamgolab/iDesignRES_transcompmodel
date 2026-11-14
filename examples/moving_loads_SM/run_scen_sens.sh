#!/bin/bash
# Key-parameter variants for NECP/REPowerEU++/Trinity (scenarios 001-003) with the final base-case settings (run_final_job2.sh), 6 in parallel x 8 threads.
cd "$(dirname "$0")"
echo "scen_sens start $(date)" >> queue_final_sens.log
xargs -P 6 -L 1 bash run_final_job2.sh < jobs_scen_sens.txt
echo "scen_sens done $(date)" >> queue_final_sens.log
