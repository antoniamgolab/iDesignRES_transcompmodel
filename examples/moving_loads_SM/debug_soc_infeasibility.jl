"""
Debug script to identify exactly which SOC constraints cause infeasibility
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================

case_folder = "case_20251212_164653"
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# MAIN SCRIPT
# ============================================================================

@info "="^80
@info "DEBUG: SOC CONSTRAINT INFEASIBILITY ANALYSIS"
@info "="^80

script_dir = @__DIR__
input_path = joinpath(script_dir, "input_data", case_folder)

@info "Step 1: Reading input data..."
data_dict = get_input_data(input_path)

@info "Step 2: Parsing data structures..."
data_structures = parse_data(data_dict)

# Check what tech vehicles exist
@info "\n=== TECH VEHICLES ==="
tv_list = data_structures["techvehicle_list"]
for tv in tv_list
    @info "  TV $(tv.id): $(tv.vehicle_type.name) - fuel=$(tv.fuel.name), tank_capacity=$(tv.tank_capacity)"
end

# Check initial vehicles
@info "\n=== INITIAL VEHICLES ==="
init_veh = data_structures["initial_vehicle_stock_list"]
for iv in init_veh
    @info "  InitVeh: tv_id=$(iv.techvehicle.id), year=$(iv.year), num=$(iv.number)"
end

# Check if any BEVs in initial stock
bev_init = filter(iv -> iv.techvehicle.fuel.name == "electricity", init_veh)
@info "  BEVs in initial stock: $(length(bev_init))"

# Create model
timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
case_name = "debug_soc_$timestamp"

@info "\nStep 3: Creating model..."
model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)

# Configure solver
set_optimizer_attribute(model, "Method", 2)
set_optimizer_attribute(model, "MIPFocus", 1)
set_optimizer_attribute(model, "NumericFocus", 3)
set_optimizer_attribute(model, "MIPGap", 0.01)

# Add all constraints INCLUDING soc_track
@info "\nStep 4: Adding constraints..."

constraint_mandatory_breaks(model, data_structures)
@info "  + mandatory_breaks"

constraint_fueling_infrastructure(model, data_structures)
@info "  + fueling_infrastructure"

constraint_fueling_infrastructure_expansion_shift(model, data_structures)
@info "  + fueling_infrastructure_expansion_shift"

constraint_soc_track(model, data_structures)
@info "  + soc_track (THE CONSTRAINT WE'RE DEBUGGING)"

constraint_soc_max(model, data_structures)
@info "  + soc_max"

constraint_travel_time_track(model, data_structures)
@info "  + travel_time_track"

constraint_mode_shift(model, data_structures)
@info "  + mode_shift"

constraint_demand_coverage(model, data_structures)
@info "  + demand_coverage"

constraint_vehicle_sizing(model, data_structures)
@info "  + vehicle_sizing"

constraint_vehicle_aging(model, data_structures)
@info "  + vehicle_aging"

constraint_vehicle_stock_shift(model, data_structures)
@info "  + vehicle_stock_shift"

# Add objective
@info "\nStep 5: Adding objective..."
objective(model, data_structures, false)

# Solve
@info "\nStep 6: Solving..."
optimize!(model)

status = termination_status(model)
@info "\nTermination status: $status"

if status == MOI.INFEASIBLE
    @info "\n" * "="^80
    @info "MODEL IS INFEASIBLE - Computing IIS"
    @info "="^80

    compute_conflict!(model)

    # Count conflicts
    constraint_conflicts = 0
    bound_conflicts = 0

    @info "\n=== CONFLICTING CONSTRAINTS ==="

    for (F, S) in list_of_constraint_types(model)
        for ci in all_constraints(model, F, S)
            conflict_status = MOI.get(model, MOI.ConstraintConflictStatus(), ci)
            if conflict_status == MOI.IN_CONFLICT
                constraint_conflicts += 1
                # Get constraint name if available
                con_name = name(ci)
                if con_name == ""
                    con_name = "unnamed"
                end
                @info "  CONFLICT #$constraint_conflicts: $con_name"
                @info "    Type: $F in $S"
                # Try to show the constraint expression (limited output)
                try
                    con_obj = constraint_object(ci)
                    @info "    Func: $(con_obj.func)"
                    @info "    Set: $(con_obj.set)"
                catch e
                    @info "    (Could not get constraint details)"
                end
            end
        end
    end

    @info "\n=== SUMMARY ==="
    @info "Total constraint conflicts: $constraint_conflicts"

elseif status == MOI.OPTIMAL || status == MOI.LOCALLY_SOLVED
    @info "Model solved successfully!"
    @info "Objective value: $(objective_value(model))"
else
    @info "Unexpected status: $status"
end

@info "\nDone."
