#!/bin/bash
# Figure 5 decomposition: final base case with spatially uniform electricity prices and grid charges (Go RES).
cd "$(dirname "$0")"
bash run_final_job2.sh uniform_spatial_costs uniform_spatial_costs_final/scenario_000 final/sensitivity/uniform_spatial_costs GRB_THREADS=12
