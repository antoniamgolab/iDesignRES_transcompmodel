# Tiny diagnostic: load the same data SM_batch loads, and print _charger_power.
# Should take <30 seconds.

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))
using YAML
include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

input_path = joinpath(@__DIR__, "input_data", "uncertainty_scenarios_v2", "scenario_000")
data_dict = get_input_data(input_path)
data_structures = parse_data(data_dict)

_fueling_infr_types = data_structures["fueling_infr_types_list"]
_charger_power = Dict{Int, Float64}()
for fit in _fueling_infr_types
    println("  fit.id = $(fit.id), fit.fueling_power[1] = $(fit.fueling_power[1])")
    _charger_power[fit.id] = fit.fueling_power[1]
end
println("\nFinal _charger_power dict: $(_charger_power)")

# Also show f_l_pairs
f_l_pairs = haskey(data_structures, "f_l_not_by_route") ? data_structures["f_l_not_by_route"] : data_structures["f_l_pairs"]
_elec_fl = [f_l for f_l in f_l_pairs if f_l[1] == 0]
println("\n_elec_fl = $(_elec_fl)")

# Compute what the constraint divisor would be for each
for f_l in _elec_fl
    d = _charger_power[f_l[2]]
    println("  for f_l=$(f_l): constraint divisor = _charger_power[$(f_l[2])] = $(d)")
end
