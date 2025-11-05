"""

    This file contains functions relating to the mathematical formulation of the model, i.e., the definition of constraints and the objective function, including also the definition of decision variables.

"""

using YAML, JuMP, Gurobi, Statistics
include("checks.jl")
"""
	base_define_variables(model::Model, data_structures::Dict)

Defines the variables for the model.

# Arguments
- model::Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function base_define_variables(model::Model, data_structures::Dict; include_vars::Vector{String}=String[])
    # If include_vars is empty, include all variables (default behavior)
    include_all = isempty(include_vars)

    @info "Creating variables. Mode: $(include_all ? "ALL" : "SELECTIVE: $(join(include_vars, ", "))")"

    m_tv_pairs =
        create_m_tv_pairs(data_structures["techvehicle_list"], data_structures["mode_list"])
    techvehicle_ids =
        create_tv_id_set(data_structures["techvehicle_list"], data_structures["mode_list"])
    t_v_pairs = create_v_t_set(data_structures["techvehicle_list"])
    p_r_k_pairs = create_p_r_k_set(data_structures["odpair_list"])
    p_r_k_e_pairs = create_p_r_k_e_set(data_structures["odpair_list"])
    p_r_k_n_pairs = create_p_r_k_n_set(data_structures["odpair_list"])
    p_r_k_g_pairs = create_p_r_k_g_set(data_structures["odpair_list"])
    if length(data_structures["detour_time_reduction_list"]) > 0
        geo_i_f_pairs = create_geo_i_f_pairs(
            data_structures["geographic_element_list"],
            data_structures["detour_time_reduction_list"],
        )
    end

    data_structures["m_tv_pairs"] = m_tv_pairs
    data_structures["techvehicle_ids"] = techvehicle_ids
    data_structures["t_v_pairs"] = t_v_pairs
    data_structures["p_r_k_pairs"] = p_r_k_pairs
    data_structures["p_r_k_e_pairs"] = p_r_k_e_pairs
    data_structures["p_r_k_n_pairs"] = p_r_k_n_pairs
    data_structures["p_r_k_g_pairs"] = p_r_k_g_pairs
    data_structures["r_k_pairs"] = create_r_k_set(data_structures["odpair_list"])
    if length(data_structures["fueling_infr_types_list"]) > 0
        data_structures["f_l_pairs"] = create_f_l_set(data_structures["fueling_infr_types_list"])
    end
    if length(data_structures["detour_time_reduction_list"]) > 0
        data_structures["geo_i_f_pairs"] = geo_i_f_pairs
    end

    # Extract geographic elements that are actually used in paths (optimization for objective function)
    data_structures["geo_elements_in_paths"] = extract_geoelements_from_paths(data_structures["path_list"])

    odpairs = data_structures["odpair_list"]
    path_list = data_structures["path_list"]
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    technologies = data_structures["technology_list"]
    mode_list = data_structures["mode_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    fuel_list = data_structures["fuel_list"]
    techvehicle_list = data_structures["techvehicle_list"]
    investment_period = data_structures["investment_period"]
    modeled_years = data_structures["modeled_years"]
    modeled_generations = data_structures["modeled_generations"]

    # Vehicle stock variables - only if "h" is in include_vars or include_all
    if include_all || "h" in include_vars
        @info "  Creating vehicle stock variables (h, h_exist, h_plus, h_minus)"
        @variable(
            model,
            h[
                y in modeled_years,
                r_id in [r.id for r ∈ odpairs],
                tv_id in techvehicle_ids,
                g in modeled_generations;
                g <= y,
            ] >= 0
        )
        @variable(
            model,
            h_exist[
                y in modeled_years,
                r_id in [r.id for r ∈ odpairs],
                tv_id in techvehicle_ids,
                g in modeled_generations;
                g <= y,
            ] >= 0
        )
        @variable(
            model,
            h_plus[
                y in modeled_years,
                r_id in [r.id for r ∈ odpairs],
                tv_id in techvehicle_ids,
                g in modeled_generations;
                g <= y,
            ] >= 0
        )
        @variable(
            model,
            h_minus[
                y in modeled_years,
                r_id in [r.id for r ∈ odpairs],
                tv_id in techvehicle_ids,
                g in modeled_generations;
                g <= y,
            ] >= 0
        )
    end

    # Fuel/energy consumption variables (s) and fueling infrastructure (q_fuel_infr_plus, n_fueling)
    if length(data_structures["fueling_infr_types_list"]) == 0
        if include_all || "s" in include_vars
            @info "  Creating energy consumption variables (s) - simple mode"
            @variable(model, s[y in modeled_years, p_r_k_g_pairs, tv_id in techvehicle_ids, g in modeled_generations] >= 0)
        end

        if include_all || "q_fuel_infr" in include_vars || "q_fuel_infr_plus" in include_vars
            @info "  Creating fuel infrastructure variables (q_fuel_infr_plus) - simple mode"
            @variable(
                model,
                q_fuel_infr_plus[
                    y in collect(y_init:investment_period:Y_end),
                    f_id in [f.id for f ∈ fuel_list],
                    geo_id in [geo.id for geo ∈ geographic_element_list],
                ] >= 0
            )
        end

        if include_all || "n_fueling" in include_vars
            @info "  Creating fueling event variables (n_fueling) - simple mode"
            @variable(
                model,
                n_fueling[y in y_init:Y_end, p_r_k_g_pairs, f_id in [f.id for f ∈ fuel_list], g in g_init:Y_end] >= 0
            )
        end

        # Detour time variables - only in simple fueling mode
        if (include_all || "detour_time" in include_vars) && data_structures["detour_time_reduction_list"] != []
            @info "  Creating detour time variables (detour_time, x_c, z, vot_dt) - simple mode"
            # create a selection by track detour time and include l
            # f_l_for_dt = create_detour_time_reduction_for_relevant(data_structures["fueling_infr_types_list"])
            data_structures["f_l_for_dt"] = f_l_for_dt
            @variable(
                model,
                detour_time[
                    y in y_init:Y_end,
                    p_r_k in p_r_k_g_pairs,
                    f_id in [f.id for f ∈ fuel_list],
                ] >= 0
            )
            # @variable(model, x_a[y in y_init:Y_end, gif_pair in geo_i_f_pairs], Bin)
            # @variable(model, x_b[y in y_init:Y_end, gif_pair in geo_i_f_pairs], Bin)
            @variable(model, x_c[y in y_init:investment_period:Y_end, gif_pair in geo_i_f_pairs], Bin)

            @variable(
                model,
                z[y in y_init:Y_end, gif_pair in geo_i_f_pairs, p_r_k_g in p_r_k_g_pairs] >= 0
            )
            @variable(model, vot_dt[y in y_init:Y_end, gif_pair in geo_i_f_pairs] >= 0)
        end
    else
        # Complex fueling mode (with fueling infrastructure types)
        f_l_by_route, f_l_not_by_route = create_q_by_route(data_structures)

        if include_all || "q_fuel_infr" in include_vars || "q_fuel_infr_plus" in include_vars
            @info "  Creating fuel infrastructure variables (q_fuel_infr_plus) - complex mode"
            @variable(
                model,
                q_fuel_infr_plus[
                    y in collect(y_init:investment_period:Y_end),
                    f_l in data_structures["f_l_pairs"],
                    geo_id in [geo.id for geo ∈ geographic_element_list],
                ] >= 0
            )
        end

        if include_all || "s" in include_vars
            @info "  Creating energy consumption variables (s) - complex mode"
            @variable(model, s[y in modeled_years, p_r_k_g in p_r_k_g_pairs, tv_id in techvehicle_ids, f_l in data_structures["f_l_pairs"], g in modeled_generations] >= 0)
        end

        if include_all || "n_fueling" in include_vars
            @info "  Creating fueling event variables (n_fueling) - complex mode"
            @variable(
                model,
                n_fueling[y in y_init:Y_end, p_r_g_k in p_r_k_g_pairs, f_l in data_structures["f_l_pairs"], g in g_init:Y_end] >= 0
            )
        end

        if (include_all || "detour_time" in include_vars) && data_structures["detour_time_reduction_list"] != []
            @info "  Creating detour time variables (detour_time, x_c, a, z, vot_dt) - complex mode"
            f_l_for_dt = create_detour_time_reduction_for_relevant(data_structures["fueling_infr_types_list"])
            data_structures["f_l_for_dt"] = f_l_for_dt
            geo_i_f_l = create_geo_i_f_l_pairs(data_structures["detour_time_reduction_list"])
            data_structures["geo_i_f_l"] = geo_i_f_l 
            @variable(
                model,
                detour_time[
                    y in y_init:Y_end,
                    p_r_k in p_r_k_g_pairs,
                    f_l in f_l_for_dt,
                ] >= 0
            )
            # @variable(model, x_a[y in y_init:Y_end, gif_pair in geo_i_f_pairs], Bin)
            # @variable(model, x_b[y in y_init:Y_end, gif_pair in geo_i_f_pairs], Bin)
            @variable(model, x_c[y in y_init:investment_period:Y_end, gifl_pair in geo_i_f_l], Bin)
            @variable(model, a[y in y_init:investment_period:Y_end, gifl_pair in geo_i_f_l], Bin)

    
            @variable(
                model,
                z[y in y_init:Y_end, gif_pair in geo_i_f_l, p_r_k_g in p_r_k_g_pairs] >= 0
            )
            @variable(model, vot_dt[y in y_init:Y_end, gif_pair in geo_i_f_l] >= 0)

        else
            data_structures["geo_i_f_l"] = []
        end
    end
    # Additional fuel infrastructure variables for by-route fueling
    if (include_all || "q_fuel_infr" in include_vars || "q_fuel_infr_plus" in include_vars) && length(data_structures["fueling_infr_types_list"]) != 0
        f_l_by_route, f_l_not_by_route = create_q_by_route(data_structures)
        data_structures["f_l_by_route"] = f_l_by_route
        data_structures["f_l_not_by_route"] = f_l_not_by_route
        if length(f_l_by_route) > 0
            @info "  Creating by-route fuel infrastructure variables (q_fuel_infr_plus_by_route, q_fuel_infr_plus_diff, q_fuel_abs)"
            @variable(
                model,
                q_fuel_infr_plus_by_route[y in collect(y_init:investment_period:Y_end), r_id in [r.id for r in odpairs],f_l in f_l_by_route, geo_id in [geo.id for geo in geographic_element_list]] >= 0
            )
            if haskey(model.obj_dict, :q_fuel_infr_plus)
                unregister(model, :q_fuel_infr_plus)
            end
            @variable(model, q_fuel_infr_plus_diff[y in collect(y_init:investment_period:Y_end), f_l in f_l_for_dt, [geo.id for geo in geographic_element_list]] >= 0)
            @variable(model, q_fuel_infr_plus[y in collect(y_init:investment_period:Y_end), f_l in f_l_not_by_route, [geo.id for geo in geographic_element_list]] >= 0)
            @variable(model, q_fuel_abs[y in collect(y_init:investment_period:Y_end), p_r_k_g_pairs, f_l in f_l_not_by_route, g in modeled_generations] >= 0)
        end
        if include_all || "soc" in include_vars
            @info "  Creating state of charge variables (soc) with generation filtering (g <= y)"
            # Only create variables for valid (y, g) pairs where g <= y (vehicles purchased in year y can operate in year y)
            # Use modeled_years and modeled_generations for efficiency with time_step > 1
            @variable(model, soc[y in modeled_years, p_r_k_g_pairs, tv in techvehicle_ids, f_l in f_l_not_by_route, g in filter(g -> g <= y, modeled_generations)] >= 0)

        end
        if include_all || "travel_time" in include_vars
            @info "  Creating travel time variables (travel_time) with generation filtering (g <= y)"
            # Only create variables for valid (y, g) pairs where g <= y (vehicles purchased in year y can operate in year y)
            # Use modeled_years and modeled_generations for efficiency with time_step > 1
            @variable(model, travel_time[y in modeled_years, p_r_k_g_pairs, tv in techvehicle_ids, f_l in f_l_not_by_route, g in filter(g -> g <= y, modeled_generations)] >= 0)
        end
        if include_all || "extra_break_time" in include_vars
            @info "  Creating extra break time slack variables (extra_break_time) with generation filtering (g <= y)"
            # Only create variables for valid (y, g) pairs where g <= y (vehicles purchased in year y can operate in year y)
            # Use modeled_years and modeled_generations for efficiency with time_step > 1
            @variable(model, extra_break_time[y in modeled_years, p_r_k_g_pairs, tv in techvehicle_ids, f_l in f_l_not_by_route, g in filter(g -> g <= y, modeled_generations)] >= 0)
        end
    end
    

    # Flow/transport variables
    if include_all || "f" in include_vars
        @info "  Creating flow/transport variables (f)"
        @variable(
            model,
            f[y in modeled_years, p_r_k_pairs, m_tv_pairs, g in modeled_generations; g <= y] >= 0
        )
    end

    # Budget penalty variables
    if include_all || "budget_penalties" in include_vars
        @info "  Creating budget penalty variables (budget_penalty_plus, budget_penalty_minus, budget_penalty_yearly_plus, budget_penalty_yearly_minus)"
        @variable(
            model,
            budget_penalty_plus[y in modeled_years, r_id in [r.id for r ∈ odpairs]] >= 0
        )
        @variable(
            model,
            budget_penalty_minus[y in modeled_years, r_id in [r.id for r ∈ odpairs]] >= 0
        )
        @variable(
            model,
            budget_penalty_yearly_plus[y in modeled_years, r_id in [r.id for r ∈ odpairs]] >= 0
        )
        @variable(
            model,
            budget_penalty_yearly_minus[y in modeled_years, r_id in [r.id for r ∈ odpairs]] >= 0
        )
    end

    # Mode infrastructure variables
    if include_all || "q_mode_infr" in include_vars
        @info "  Creating mode infrastructure variables (q_mode_infr_plus)"
        @variable(
            model,
            q_mode_infr_plus[
                y in collect(y_init:investment_period:Y_end),
                m_id in [m.id for m ∈ mode_list],
                geo_id in [geo.id for geo ∈ geographic_element_list],
            ] >= 0
        )
    end

    # Supply infrastructure variables
    if (include_all || "q_supply_infr" in include_vars) && data_structures["supplytype_list"] != []
        @info "  Creating supply infrastructure variables (q_supply_infr)"
        supplytype_list = data_structures["SupplyType"]
        @variable(
            model,
            q_supply_infr[y in collect(y_init:investment_period:Y_end), st_id in [st.id for s ∈ supplytype_list], geo_id in [geo.id for geo ∈ geographic_element_list]] >= 0
        )
    end

    @info "Variable creation complete!"
end

"""
	constraint_demand_coverage(model::JuMP.Model, data_structures::Dict)

Creates constraint for demand coverage.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_demand_coverage(model::JuMP.Model, data_structures)
    
    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in data_structures["odpair_list"],
        ],
        sum(
            model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
            mv ∈ data_structures["m_tv_pairs"] for g ∈ data_structures["g_init"]:y if mv[1] == 1
        ) == r.F[y-data_structures["y_init"]+1] * (1/1000)
    )
    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in data_structures["odpair_list"],
        ],
        sum(
            model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
            mv ∈ data_structures["m_tv_pairs"] for g ∈ data_structures["g_init"]:y if mv[1] == 2
        ) == 0
    )
    @info "Constraint for demand coverage created successfully"
end

"""
	constraint_vehicle_sizing(model::JuMP.Model, data_structures::Dict)

Creates constraint for vehicle sizing.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_vehicle_sizing(model::JuMP.Model, data_structures::Dict)
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    vehicletypes = data_structures["vehicletype_list"]
    technologies = data_structures["technology_list"]
    regiontypes = data_structures["regiontype_list"]
    modes = data_structures["mode_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    g_init = data_structures["g_init"]
    Y_end = data_structures["Y_end"]
    y_init = data_structures["y_init"]
    products = data_structures["product_list"]
    r_k_pairs = Set((r.id, k.id) for r ∈ odpairs for k ∈ r.paths)
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    p_r_k_e_pairs = data_structures["p_r_k_e_pairs"]
    p_r_k_n_pairs = data_structures["p_r_k_n_pairs"]
    paths = data_structures["path_list"]
    gamma = data_structures["gamma"]
    alpha_h = data_structures["alpha_h"]
    beta_h = data_structures["beta_h"]
    alpha_f = data_structures["alpha_f"]
    beta_f = data_structures["beta_f"]
    odpairs = data_structures["odpair_list"]
    

    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in odpairs,
            mv in data_structures["m_tv_pairs"],
            g in data_structures["g_init"]:data_structures["Y_end"];
            modes[findfirst(m -> m.id == mv[1], modes)].quantify_by_vehs && g <= y,
        ],
        model[:h][y, r.id, mv[2], g] >= sum(
            (
                k.length / (
                    data_structures["techvehicle_list"][findfirst(
                        v0 -> v0.id == mv[2],
                        data_structures["techvehicle_list"],
                    )].W[g-g_init+1] * data_structures["techvehicle_list"][findfirst(
                        v0 -> v0.id == mv[2],
                        data_structures["techvehicle_list"],
                    )].AnnualRange[g-g_init+1]
                )
            ) * 1000 * model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths
        )
    )
    # for y in y_init:Y_end, r in odpairs, mv in m_tv_pairs, g in g_init:Y_end
    #     if modes[findfirst(m -> m.id == mv[1], modes)].quantify_by_vehs && g <= y
    #         fix(model[:h_plus][y, r.id, mv[2], g], 0,force=true)
    #         fix(model[:h_minus][y, r.id, mv[2], g], 0, force=true)
    #         fix(model[:h][y, r.id, mv[2], g], 0, force=true)
    #         fix(model[:h_exist][y, r.id, mv[2], g], 0, force=true)
    #     end
    # end


    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in odpairs,
            mv in data_structures["m_tv_pairs"],
            g in data_structures["g_init"]:data_structures["Y_end"];
            !data_structures["mode_list"][findfirst(
                m -> m.id == mv[1],
                data_structures["mode_list"],
            )].quantify_by_vehs && g <= y,
        ],
        model[:h][y, r.id, mv[2], g] == 0
    )
    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in odpairs,
            mv in data_structures["m_tv_pairs"],
            g in data_structures["g_init"]:data_structures["Y_end"];
            !data_structures["mode_list"][findfirst(
                m -> m.id == mv[1],
                data_structures["mode_list"],
            )].quantify_by_vehs && g <= y,
        ],
        model[:h_minus][y, r.id, mv[2], g] == 0
    )
    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in odpairs,
            mv in data_structures["m_tv_pairs"],
            g in data_structures["g_init"]:data_structures["Y_end"];
            !data_structures["mode_list"][findfirst(
                m -> m.id == mv[1],
                data_structures["mode_list"],
            )].quantify_by_vehs && g <= y,
        ],
        model[:h_plus][y, r.id, mv[2], g] == 0
    )
    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in odpairs,
            mv in data_structures["m_tv_pairs"],
            g in data_structures["g_init"]:data_structures["Y_end"];
            !data_structures["mode_list"][findfirst(
                m -> m.id == mv[1],
                data_structures["mode_list"],
            )].quantify_by_vehs && g <= y,
        ],
        model[:h_exist][y, r.id, mv[2], g] == 0
    )
    @info "Constraint for vehicle stock sizing created successfully"

end

"""
	constraint_vehicle_aging(model::JuMP.Model, data_structures::Dict)

Creates constraints for vehicle aging.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data

# Returns
- model::JuMP.Model: JuMP model with the constraints added
"""
function constraint_vehicle_aging(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    g_init = data_structures["g_init"]
    techvehicles = data_structures["techvehicle_list"]
    modes = data_structures["mode_list"]
    # Define all combinations of indices as a collection of tuples
    all_indices = [
        (y, g, r, tv) for y ∈ y_init:Y_end, g ∈ g_init:Y_end, r ∈ odpairs,
        tv ∈ techvehicles
    ]

    selected_indices = filter(t -> t[2] <= t[1], all_indices)

    for (y, g, r, tv) ∈ selected_indices
        @constraint(
            model,
            model[:h][y, r.id, tv.id, g] ==
            model[:h_exist][y, r.id, tv.id, g] - model[:h_minus][y, r.id, tv.id, g] +
            model[:h_plus][y, r.id, tv.id, g]
        )
    end

    # If pre_age_sell is false, prevent early retirement before vehicle reaches its lifetime
    pre_age_sell = data_structures["pre_age_sell"]
    if !pre_age_sell
        # Constrain h_minus to 0 for all cases where (y - g) < Lifetime
        no_early_retirement = filter(
            t -> t[2] <= t[1] && (t[1] - t[2]) < t[4].Lifetime[t[2]-g_init+1],
            selected_indices,
        )
        for (y, g, r, tv) ∈ no_early_retirement
            @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
        end
        @info "Pre-age sell disabled: h_minus constrained to 0 for $(length(no_early_retirement)) vehicle combinations before reaching lifetime"
    end

    # case a: g > y || y - g > Lifetime
    valid_subset_rest = filter(t -> t[1] < t[2], selected_indices)

    # Add constraints for valid_subset_rest
    for (y, g, r, tv) ∈ valid_subset_rest
        @constraint(model, model[:h][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_exist][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
    end

    #case b: g <= y && y - g > Lifetime && y != y_init

    subset_caseb = filter(
        t ->
            t[2] <= t[1] && (t[1] - t[2]) > t[4].Lifetime[t[2]-g_init+1] && t[1] != y_init,
        selected_indices,
    )

    for (y, g, r, tv) ∈ subset_caseb
        @constraint(model, model[:h][y, r.id, tv.id, g] == 0)
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] == model[:h][y-1, r.id, tv.id, g]
        )
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
    end

    # case 2 : g < y && y - g <= Lifetime && y == y_init && g < y_init
    valid_subset_case2 = filter(
        t ->
            t[2] < t[1] &&
                (t[1] - t[2]) <= t[4].Lifetime[t[2]-g_init+1] &&
                t[1] == y_init &&
                t[2] < y_init,
        all_indices,
    )
    for (y, g, r, tv) ∈ valid_subset_case2
        stock_index = findfirst(
            ivs -> ivs.year_of_purchase == g && ivs.techvehicle.id == tv.id,
            r.vehicle_stock_init,
        )

        # Handle missing initial stock gracefully (e.g., for generations before InitialVehicleStock range)
        if stock_index !== nothing
            @constraint(
                model,
                model[:h_exist][y, r.id, tv.id, g] == r.vehicle_stock_init[stock_index].stock
            )
        else
            # No initial stock for this generation - set to zero
            @constraint(model, model[:h_exist][y, r.id, tv.id, g] == 0)
        end

        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
        # @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
    end

    # case 3: g == y && y - g <= Lifetime && y == y_init ( -> g == y_init)

    valid_subset_case3 = filter(
        t ->
            t[2] == t[1] && (t[1] - t[2]) <= t[4].Lifetime[t[2]-g_init+1] && t[1] == y_init,
        all_indices,
    )
    for (y, g, r, tv) ∈ valid_subset_case3
        @constraint(model, model[:h_exist][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
    end

    # case 4: g < y && y - g <= Lifetime && y != y_init && g > y_init
    valid_subset_case4 = filter(
        t ->
            t[2] < t[1] &&
                (t[1] - t[2]) <= t[4].Lifetime[t[2]-g_init+1] &&
                t[1] != y_init &&
                t[2] > y_init,
        all_indices,
    )

    for (y, g, r, tv) ∈ valid_subset_case4
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] == model[:h][y-1, r.id, tv.id, g]
        )
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
    end
    # case 8: g < y && y - g <= Lifetime && y != y_init && g == y_init
    valid_subset_case8 = filter(
        t ->
            t[2] < t[1] &&
                (t[1] - t[2]) <= t[4].Lifetime[t[2]-g_init+1] &&
                t[1] != y_init &&
                t[2] == y_init,
        all_indices,
    )

    for (y, g, r, tv) ∈ valid_subset_case8
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] == model[:h][y-1, r.id, tv.id, g]
        )
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
    end

    # case 5: g < y && y - g <= Lifetime && y != y_init && g == y_init
    valid_subset_case5 = filter(
        t ->
            t[2] < t[1] &&
                (t[1] - t[2]) <= t[4].Lifetime[t[2]-g_init+1] &&
                t[1] != y_init &&
                t[2] == y_init,
        all_indices,
    )

    for (y, g, r, tv) ∈ valid_subset_case5
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] == model[:h][y-1, r.id, tv.id, g]
        )
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
    end

    # case 6: g == y && y - g <= Lifetime && y != y_init
    valid_subset_case6 = filter(
        t ->
            t[2] == t[1] && (t[1] - t[2]) <= t[4].Lifetime[t[2]-g_init+1] && t[1] != y_init,
        all_indices,
    )

    for (y, g, r, tv) ∈ valid_subset_case6
        @constraint(model, model[:h_exist][y, r.id, tv.id, g] == 0)
    end

    # case 10: g < y && y - g <= Lifetime && y > y_init && g < y_init
    valid_subset_case10 = filter(
        t ->
            t[2] < t[1] &&
                (t[1] - t[2]) <= t[4].Lifetime[t[2]-g_init+1] &&
                t[1] > y_init &&
                t[2] < y_init,
        all_indices,
    )
    for (y, g, r, tv) ∈ valid_subset_case10
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] == model[:h][y-1, r.id, tv.id, g]
        )
    end

    # case 12: g != y && g < y
    valid_subset_case12 = filter(
        t -> t[2] != t[1] && t[2] < t[1],
        all_indices,
    )
    for (y, g, r, tv) ∈ valid_subset_case12
        @constraint(
            model,
            model[:h_plus][y, r.id, tv.id, g] == 0
        )
    end
end

"""
	constraint_vehicle_purchase(model::JuMP.Model, data_structures::Dict)

Creates constraints for monetary budget for vehicle purchase by route.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_monetary_budget(model::JuMP.Model, data_structures::Dict)
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    y_init = data_structures["y_init"]
    f_l_by_route = data_structures["f_l_by_route"]
    geographic_element_list = data_structures["geographic_element_list"]
    investment_period = data_structures["investment_period"]
    Y_end = data_structures["Y_end"]
    odpair_list = data_structures["odpair_list"]
    investment_years = y_init:investment_period:Y_end
    fueling_infr_types_list = data_structures["fueling_infr_types_list"]
    # @constraint(
    #     model,
    #     [r in odpairs],
    #     sum([
    #         (model[:h_plus][y, r.id, v.id, g] * v.capital_cost[y-y_init+1]) for
    #         y ∈ data_structures["y_init"]:data_structures["Y_end"] for v ∈ techvehicles for
    #         g ∈ data_structures["g_init"]:y
    #     ]) + sum(model[:q_fuel_infr_plus_by_route][y, r.id, f_l, geo.id] for f_l in f_l_by_route for geo in geographic_element_list for y ∈ data_structures["y_init"]:investment_period:data_structures["Y_end"]) <=
    #     r.financial_status.monetary_budget_purchase_ub *  
    #     mean(r.F) * 
    #     data_structures["Y"] *
    #     (1 / r.financial_status.monetary_budget_purchase_time_horizon) 
    #      + sum(
    #         model[:budget_penalty_plus][y, r.id] for
    #         y ∈ data_structures["y_init"]:data_structures["Y_end"]
    #     )
    # )
    # @constraint(
    #     model,
    #     [r in odpairs],
    #     sum([
    #         (model[:h_plus][y, r.id, v.id, g] * v.capital_cost[y-y_init+1]) for
    #         y ∈ data_structures["y_init"]:data_structures["Y_end"] for v ∈ techvehicles for
    #         g ∈ g_init:y
    #     ]) * (1) 
    #     + sum(model[:q_fuel_infr_plus_by_route][y, r.id, f_l, geo.id] for f_l in f_l_by_route for geo in geographic_element_list for y ∈ data_structures["y_init"]:investment_period:data_structures["Y_end"])
    #         >=
    #     r.financial_status.monetary_budget_purchase_lb *
    #     mean(r.F) * 
    #     data_structures["Y"] *
    #     (1 / r.financial_status.monetary_budget_purchase_time_horizon) 
    #     - sum(
    #         model[:budget_penalty_minus][y, r.id] for
    #         y ∈ data_structures["y_init"]:data_structures["Y_end"]
    #     ) 
    # )

    # for r ∈ odpairs
    #     # y_set = generate_exact_length_subsets(
    #     #     data_structures["y_init"],
    #     #     data_structures["Y_end"],
    #     #     r.financial_status.monetary_budget_purchase_time_horizon,
    #     # )
    #     y_set = create_blocks(
    #             data_structures["y_init"],
    #             data_structures["Y_end"],
    #             r.financial_status.monetary_budget_purchase_time_horizon,      
    #     )
    #     if r.id == 20
    #         println(r.financial_status.monetary_budget_purchase_time_horizon)
    #         println(y_set)
    #     end
    #     @constraint(
    #         model,
    #         [y0 in y_set],
    #         sum(
    #             model[:h_plus][y, r.id, v.id, g] 
    #              * v.capital_cost[y-y_init+1] 
    #             for y ∈ y0 for
    #             v ∈ techvehicles for g ∈ g_init:y
    #         )  
    #         <=
    #          r.financial_status.monetary_budget_purchase_ub * length(y_0) *
    #         sum(
    #             r.F[(y0[1]-data_structures["y_init"]+1):(y0[1]-data_structures["y_init"]+r.financial_status.monetary_budget_purchase_time_horizon)],
    #         )
    #         + sum(model[:budget_penalty_yearly_plus][y, r.id] for y ∈ y0) 
    #     )
    #     @constraint(
    #         model,
    #         [y0 in y_set],
    #         sum(
    #             model[:h_plus][y, r.id, v.id, g] 
    #              * v.capital_cost[y-y_init+1] 
    #             for y ∈ y0 for v ∈ techvehicles for g ∈ g_init:y
    #         ) >=
    #          r.financial_status.monetary_budget_purchase_lb * length(y_0) *
    #         sum(
    #             r.F[(y0[1]-data_structures["y_init"]+1):(y0[1]-data_structures["y_init"]+r.financial_status.monetary_budget_purchase_time_horizon)],
    #         )
    #           - sum(model[:budget_penalty_yearly_minus][y, r.id] for y ∈ y0)
    #     )
    # end

    for y in y_init:Y_end
        if y in investment_years
            @constraint(
                model,
                [r in odpairs],
                sum(
                    model[:h_plus][y, r.id, v.id, g]
                        * v.capital_cost[y-y_init+1]
                    for v ∈ techvehicles for g ∈ filter(g -> g <= y, modeled_generations)
                )
                #+ sum(model[:q_fuel_infr_plus_by_route][y, r.id, f_l, geo.id]* fueling_infr_types_list[findfirst(item -> item.id == f_l[2], fueling_infr_types_list)].cost_per_kW[y-y_init+1]  for r in odpair_list for f_l in f_l_by_route for geo in geographic_element_list)
                <=
                    (r.financial_status.monetary_budget_purchase_ub/ r.financial_status.monetary_budget_purchase_time_horizon) * r.F[y-y_init+1]
                    + model[:budget_penalty_yearly_plus][y, r.id]
            )
            @constraint(
                model,
                [r in odpairs],
                sum(
                    model[:h_plus][y, r.id, v.id, g]
                        * v.capital_cost[y-y_init+1]
                    for v ∈ techvehicles for g ∈ filter(g -> g <= y, modeled_generations)
                )
                #+ sum(model[:q_fuel_infr_plus_by_route][y, r.id, f_l, geo.id] * fueling_infr_types_list[findfirst(item -> item.id == f_l[2], fueling_infr_types_list)].cost_per_kW[y-y_init+1] for r in odpair_list for f_l in f_l_by_route for geo in geographic_element_list)
                >=
                    (r.financial_status.monetary_budget_purchase_ub/ r.financial_status.monetary_budget_purchase_time_horizon) * r.F[y-y_init+1]
                    - model[:budget_penalty_yearly_minus][y, r.id]
            )
        else
            @constraint(
                model,
                [r in odpairs],
                sum(
                    model[:h_plus][y, r.id, v.id, g]
                        * v.capital_cost[y-y_init+1]
                    for v ∈ techvehicles for g ∈ filter(g -> g <= y, modeled_generations)
                )
                <=
                    (r.financial_status.monetary_budget_purchase_ub/ r.financial_status.monetary_budget_purchase_time_horizon) * r.F[y-y_init+1]
                    + model[:budget_penalty_yearly_plus][y, r.id]
            )
            @constraint(
                model,
                [ r in odpairs],
                sum(
                    model[:h_plus][y, r.id, v.id, g]
                        * v.capital_cost[y-y_init+1]
                    for v ∈ techvehicles for g ∈ filter(g -> g <= y, modeled_generations)
                )
                >=
                    (r.financial_status.monetary_budget_purchase_ub/ r.financial_status.monetary_budget_purchase_time_horizon) * r.F[y-y_init+1]
                    - model[:budget_penalty_yearly_minus][y, r.id]
            )
        end

    end

    
end


function constraint_n_fueling_upper_bound(model::JuMP.Model, data_structures::Dict)
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    f_l_pairs = data_structures["f_l_pairs"]
    g_init = data_structures["g_init"]
    Y_end = data_structures["Y_end"]
    y_init = data_structures["y_init"]

    @constraint(
        model,
        [
            y in (y_init+1):Y_end,
            p_r_k_g in p_r_k_g_pairs,
            f_l in f_l_pairs,
            g in g_init:Y_end;
            g <= y,
        ],
        model[:n_fueling][y, p_r_k_g, f_l, g] - model[:n_fueling][y-1, p_r_k_g, f_l, g]  <= model[:n_fueling][y-1, p_r_k_g, f_l, g] * 0.1
    )
    @constraint(
        model,
        [
            y in (y_init+1):Y_end,
            f_l in f_l_pairs,
           f_l[1] == 1
        ],
        sum(model[:n_fueling][y, p_r_k_g, f_l, g] for p_r_k_g in p_r_k_g_pairs for g in g_init:y) - sum(model[:n_fueling][y-1, p_r_k_g, f_l, g] for p_r_k_g in p_r_k_g_pairs for g in g_init:y)  <= 0
    )
end
"""
	constraint_vehicle_purchase(model::JuMP.Model, data_structures::Dict)

Constraints for the sizing of fueling infrastructure at nodes and edges.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_fueling_infrastructure(model::JuMP.Model, data_structures::Dict)
    technologies = data_structures["technology_list"]

    p_r_k_n_pairs = data_structures["p_r_k_n_pairs"]
    p_r_k_e_pairs = data_structures["p_r_k_e_pairs"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    techvehicles = data_structures["techvehicle_list"]
    fuel_list = data_structures["fuel_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    initialfuelinginfr_list = data_structures["initialfuelinginfr_list"]
    gamma = data_structures["gamma"]
    investment_period = data_structures["investment_period"]
    investment_years = collect(data_structures["y_init"]:investment_period:data_structures["Y_end"])  # List of years where x_c is defined
    f_l_pairs = data_structures["f_l_pairs"]
    g_init = data_structures["g_init"]
    Y_end = data_structures["Y_end"]
    fueling_infr_types_list = data_structures["fueling_infr_types_list"]
    y_init = data_structures["y_init"]
    financial_status_list = data_structures["financial_status_list"]

    # PERFORMANCE OPTIMIZATION: Pre-filter p_r_k_g_pairs by geographic element
    # This reduces inner loop iterations by 90%+ (from O(n_all) to O(n_geo))
    @info "Pre-building p_r_k_g_by_geo dictionary for efficient filtering..."
    p_r_k_g_by_geo = Dict{Int, Vector{Tuple}}()
    for geo in geographic_element_list
        p_r_k_g_by_geo[geo.id] = [p_r_k_g for p_r_k_g in p_r_k_g_pairs if p_r_k_g[4] == geo.id]
    end
    @info "✓ Pre-filtering complete: $(length(geographic_element_list)) geo elements indexed"
    if length(data_structures["fueling_infr_types_list"]) == 0
        @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            f in fuel_list,
            geo in geographic_element_list,
        ],
        initialfuelinginfr_list[findfirst(
            i -> i.fuel.name == f.name && i.allocation == geo.id,
            initialfuelinginfr_list,
        )].installed_kW + sum(
            model[:q_fuel_infr_plus][y0, f.id, geo.id] for y0 ∈ data_structures["y_init"]:investment_period:y
        ) >= sum(
            gamma * 1000 * model[:s][y, p_r_k_g, tv.id, g] for g in g_init:y for p_r_k_g ∈ p_r_k_g_by_geo[geo.id] for
            tv ∈ techvehicles if tv.technology.fuel.name == f.name
        )
    )
    else
        f_l_by_route = data_structures["f_l_by_route"]
        f_l_not_by_route = data_structures["f_l_not_by_route"]
        
        for f_l in f_l_not_by_route 
            gamma_l = fueling_infr_types_list[findfirst(item -> item.id == f_l[2], fueling_infr_types_list)].gamma
            if isa(gamma_l, AbstractVector)
                factor_gamma = [1/(γ * 8760) for γ in gamma_l]
            else
                factor_gamma = [1/(gamma_l * 8760) for y in data_structures["y_init"]:data_structures["Y_end"]]
            end
            
            for geo in geographic_element_list
                if findfirst(
                    i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo.id,
                    initialfuelinginfr_list,
                ) == nothing
                    @constraint(
                        model,
                        [
                            y in data_structures["y_init"]:data_structures["Y_end"],
                        ],
                        sum(
                            model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 ∈ data_structures["y_init"]:investment_period:y
                        ) >= sum(
                            factor_gamma[y - data_structures["y_init"] + 1] *1000* model[:s][y, p_r_k_g, tv.id, f_l, g] for g in g_init:y for p_r_k_g ∈ p_r_k_g_by_geo[geo.id] for
                            tv ∈ techvehicles if tv.technology.fuel.id == f_l[1]
                        )
                    )
                else
                    @constraint(
                        model,
                        [
                            y in data_structures["y_init"]:data_structures["Y_end"],
                        ],
                        initialfuelinginfr_list[findfirst(
                            i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo.id,
                            initialfuelinginfr_list,
                        )].installed_kW + sum(
                            model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 ∈ data_structures["y_init"]:investment_period:y
                        ) >= sum(
                            factor_gamma[y - data_structures["y_init"] + 1] *1000* model[:s][y, p_r_k_g, tv.id, f_l, g] for g in g_init:y for p_r_k_g ∈ p_r_k_g_by_geo[geo.id] for
                            tv ∈ techvehicles if tv.technology.fuel.id == f_l[1]
                        )
                    )
                end
            end
        end

        # Only process by-route infrastructure if it exists
        if haskey(model.obj_dict, :q_fuel_infr_plus_by_route)
            for f_l in f_l_by_route
                gamma_l = fueling_infr_types_list[findfirst(item -> item.id == f_l[2], fueling_infr_types_list)].gamma
                if isa(gamma_l, AbstractVector)
                    factor_gamma = [1/(γ * 8760) for γ in gamma_l]
                else
                    factor_gamma = [1/(gamma_l * 8760) for y in data_structures["y_init"]:data_structures["Y_end"]]
                end
                for geo in geographic_element_list
                    for financial_status in financial_status_list

                        if findfirst(
                                i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo.id && i.income_class.id == financial_status.id && i.by_income_class,
                                initialfuelinginfr_list,
                            ) == nothing

                            @constraint(
                                model,
                                [
                                    y in data_structures["y_init"]:data_structures["Y_end"],
                                    r ∈ data_structures["odpair_list"]; r.financial_status.id == financial_status.id
                                ],
                                sum(
                                    model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 ∈ data_structures["y_init"]:investment_period:y
                                ) >= sum(
                                    factor_gamma[y - data_structures["y_init"] + 1] *1000* model[:s][y, p_r_k_g, tv.id, f_l, g] for g in g_init:y for p_r_k_g ∈ p_r_k_g_by_geo[geo.id] for
                                    tv ∈ techvehicles if tv.technology.fuel.id == f_l[1] && p_r_k_g[2] == r.id
                                )
                            )
                        else
                            init_infr = initialfuelinginfr_list[findfirst(
                                i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo.id && i.income_class.id == financial_status.id && i.by_income_class,
                                initialfuelinginfr_list,
                            )].installed_kW
                            println(init_infr)
                            println(financial_status.name)
                            @constraint(
                                model,
                                [
                                    y in data_structures["y_init"]:data_structures["Y_end"],
                                    r ∈ data_structures["odpair_list"];r.financial_status.id == financial_status.id
                                ],
                                init_infr + sum(
                                    model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 ∈ data_structures["y_init"]:investment_period:y
                                ) >= sum(
                                    factor_gamma[y - data_structures["y_init"] + 1] * 1000 * model[:s][y, p_r_k_g, tv.id, f_l, g] for g in g_init:y for p_r_k_g ∈ p_r_k_g_by_geo[geo.id] for
                                    tv ∈ techvehicles if tv.technology.fuel.id == f_l[1] && p_r_k_g[2] == r.id
                                )
                            )
                        end
                    end
                end
            end
        end
    end
    
end

function constraint_constant_fueling_since_yinit(model::JuMP.Model, data_structures::Dict)
    echnologies = data_structures["technology_list"]
    y_init = data_structures["y_init"]
    p_r_k_n_pairs = data_structures["p_r_k_n_pairs"]
    p_r_k_e_pairs = data_structures["p_r_k_e_pairs"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    techvehicles = data_structures["techvehicle_list"]
    fuel_list = data_structures["fuel_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    initialfuelinginfr_list = data_structures["initialfuelinginfr_list"]
    gamma = data_structures["gamma"]
    investment_period = data_structures["investment_period"]
    investment_years = collect(data_structures["y_init"]:investment_period:data_structures["Y_end"])  # List of years where x_c is defined
    odpairs = data_structures["odpair_list"]
    if length(data_structures["fueling_infr_types_list"]) == 0

        @constraint(
            model,
            [
                y in data_structures["y_init"]:data_structures["Y_end"],
                f in fuel_list,
                geo in geographic_element_list,
            ],
            initialfuelinginfr_list[findfirst(
                i -> i.fuel.name == f.name && i.allocation == geo.id,
                initialfuelinginfr_list,
            )].installed_kW + sum(
                model[:q_fuel_infr_plus][y_init, f.id, geo.id]
            ) >= sum(
                gamma * model[:s][y, p_r_k_g, tv.id] for p_r_k_g ∈ p_r_k_g_pairs for
                tv ∈ techvehicles if p_r_k_g[4] == geo.id && tv.technology.fuel.name == f.name
            )
        )
    else
        f_l_by_route = data_structures["f_l_by_route"]
        f_l_not_by_route = data_structures["f_l_not_by_route"]
        @constraint(
            model,
            [
                y in data_structures["y_init"]:data_structures["Y_end"],
                f_l in f_l_not_by_route,
                geo in geographic_element_list,
            ],
            initialfuelinginfr_list[findfirst(
                i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo.id,
                initialfuelinginfr_list,
            )].installed_kW + sum(
                model[:q_fuel_infr_plus][y_init, f_l, geo.id]
            ) >= sum(
                1000 * gamma * model[:s][y, p_r_k_g, tv.id, f_l, g] for p_r_k_g ∈ p_r_k_g_pairs for
                tv ∈ techvehicles if p_r_k_g[4] == geo.id && tv.technology.fuel.id == f_l[1]
            )
        )

        # Only add by-route constraint if variable exists
        if haskey(model.obj_dict, :q_fuel_infr_plus_by_route)
            @constraint(
                model,
                [
                    y in data_structures["y_init"]:data_structures["Y_end"],
                    r_id in [r.id for r ∈ odpairs],
                    f_l in f_l_by_route,
                    geo in geographic_element_list,
                ],
                sum(
                    model[:q_fuel_infr_plus_by_route][y_init, r_id, f_l, geo.id]
                ) >= sum(
                    gamma * model[:s][y, p_r_k_g, tv.id, f_l, g] for p_r_k_g ∈ p_r_k_g_pairs for
                    tv ∈ techvehicles if p_r_k_g[4] == geo.id && tv.technology.fuel.id == f_l[1] && p_r_k_g[1] == r_id
                )
            )
        end
    end
end

function constraint_fueling_infrastructure_init(model::JuMP.Model, data_structures::Dict)
    technologies = data_structures["technology_list"]

    p_r_k_n_pairs = data_structures["p_r_k_n_pairs"]
    p_r_k_e_pairs = data_structures["p_r_k_e_pairs"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    techvehicles = data_structures["techvehicle_list"]
    fuel_list = data_structures["fuel_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    initialfuelinginfr_list = data_structures["initialfuelinginfr_list"]
    gamma = data_structures["gamma"]
    investment_period = data_structures["investment_period"]
    investment_years = collect(data_structures["y_init"]:investment_period:data_structures["Y_end"])  # List of years where x_c is defined
    Y_end = data_structures["Y_end"]

    @constraint(
        model,
        [
            f in fuel_list,
            geo in geographic_element_list,
        ],
        sum(
            model[:q_fuel_infr_plus][y0, f.id, geo.id] for y0 ∈ (data_structures["y_init"] + 1):investment_period:Y_end
        ) 
        == 0
    )
end


function constraint_fueling_cap_constant(model::JuMP.Model, data_structures::Dict)
    echnologies = data_structures["technology_list"]
    y_init = data_structures["y_init"]
    p_r_k_n_pairs = data_structures["p_r_k_n_pairs"]
    p_r_k_e_pairs = data_structures["p_r_k_e_pairs"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    techvehicles = data_structures["techvehicle_list"]
    fuel_list = data_structures["fuel_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    initialfuelinginfr_list = data_structures["initialfuelinginfr_list"]
    gamma = data_structures["gamma"]
    investment_period = data_structures["investment_period"]
    investment_years = collect(data_structures["y_init"]:investment_period:data_structures["Y_end"])  # List of years where x_c is defined
 

    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            f in fuel_list[2:2],
            geo in geographic_element_list,
        ],
        initialfuelinginfr_list[findfirst(
            i -> i.fuel.name == f.name && i.allocation == geo.id,
            initialfuelinginfr_list,
        )].installed_kW + sum(
            model[:q_fuel_infr_plus][y_init, f.id, geo.id]
        ) == sum(
            gamma * model[:s][y, p_r_k_g, tv.id] for p_r_k_g ∈ p_r_k_g_pairs for
            tv ∈ techvehicles if p_r_k_g[4] == geo.id && tv.technology.fuel.name == f.name
        )
    )
end

function constraint_supply_infrastructure(model::JuMP.Model, data_structures::Dict)
    technologies = data_structures["technology_list"]

    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    techvehicles = data_structures["techvehicle_list"]
    fuel_list = data_structures["fuel_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    initsupplyinfr_list = data_structures["initsupplyinfr_list"]
    gamma = data_structures["gamma"]
    supplytype_list = data_structures["supplytype_list"]
    investment_period = data_structures["investment_period"]

    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            l in supplytype_list,
            geo in geographic_element_list,
        ],
        initsupplyinfr_list[findfirst(
            i -> i.supply_type.name == l.name && i.allocation == geo.id,
            initsupplyinfr_list,
        )].installed_kW + sum(
            model[:q_supply_infr][y0, l.id, geo.id] for y0 ∈ data_structures["y_init"]:y
        ) >= sum(
            gamma * model[:s][y, p_r_k_g, tv.id] for p_r_k_g ∈ p_r_k_g_pairs for
            tv ∈ techvehicles for f in fuel_list if p_r_k_g[4] == geo.id && tv.technology.fuel.name == f.name && l.fuel.name == f.name 
        )
    )
end

"""
   constraint_mode_infrastructure(model::JuMP.Model, data_structures::Dict)

Constraints for sizing of mode infrastructure at nodes and edges.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_mode_infrastructure(model::JuMP.Model, data_structures::Dict)
    path_list = data_structures["path_list"]
    initialmodeinfr_list = data_structures["initialmodeinfr_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    investment_period = data_structures["investment_period"]
    investment_years = collect(data_structures["y_init"]:investment_period:data_structures["Y_end"])  # List of years where x_c is defined

    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            m in data_structures["mode_list"],
            # m in [data_structures["mode_list"][1]],
            geo in geographic_element_list,
        ],
        initialmodeinfr_list[findfirst(
            i -> i.mode.id == m.id && i.allocation == geo.id,
            initialmodeinfr_list,
        )].installed_ukm + sum(
            model[:q_mode_infr_plus][y0, m.id, geo.id] for y0 ∈ data_structures["y_init"]:investment_period:y 
        ) >=
        data_structures["gamma"] * sum(
            model[:f][y, p_r_k, m_tv, g] for p_r_k ∈ data_structures["p_r_k_pairs"] for
            m_tv ∈ data_structures["m_tv_pairs"] if
            geo.id in path_list[findfirst(p -> p.id == p_r_k[3], path_list)].sequence
        ) * 1000
    )
end

"""
	constraint_fueling_demand(model::JuMP.Model, data_structures::Dict)

Constraints for fueling demand at nodes and edges.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_fueling_demand(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    gamma = data_structures["gamma"]
    paths = data_structures["path_list"]
    products = data_structures["product_list"]
    r_k_pairs = data_structures["r_k_pairs"]
    f_l_pairs = data_structures["f_l_pairs"]

    # PERFORMANCE OPTIMIZATION: Use dictionary for O(1) path lookups
    path_dict = data_structures["path_dict"]


    if length(data_structures["fueling_infr_types_list"]) == 0
        @constraint(
            model,
            [y in y_init:Y_end, p in products, r_k in r_k_pairs, v in techvehicles],
            # Single O(1) lookup instead of 4+ O(n) findfirst calls - access dictionary directly
            sum(
                model[:s][y, (p.id, r_k[1], r_k[2], el.id), v.id] for
                el ∈ path_dict[r_k[2]].sequence
                if el == path_dict[r_k[2]].sequence[1] || el == path_dict[r_k[2]].sequence[length(path_dict[r_k[2]].sequence)]
            ) == sum(
                (
                    (v.spec_cons[g-g_init+1]) / v.W[g-g_init+1]  *
                    path_dict[r_k[2]].length
                ) * model[:f][y, (p.id, r_k[1], r_k[2]), (v.vehicle_type.mode.id, v.id), g] for
                g ∈ filter(g -> g <= y, modeled_generations)
            )
        )
    else
        @constraint(
            model,
            [y in y_init:Y_end, p in products, r_k in r_k_pairs, g in modeled_generations, v in techvehicles, f_l in f_l_pairs; g <= y && f_l[1] == v.technology.fuel.id],
            # Single O(1) lookup instead of 3+ O(n) findfirst calls - access dictionary directly
            sum(
                model[:s][y, (p.id, r_k[1], r_k[2], el.id), v.id, f_l, g]
                for el in path_dict[r_k[2]].sequence
                # if el.id == odpairs[findfirst(r0 -> r0.id == r_k[1], odpairs)].origin.id ||
                #    el.id == odpairs[findfirst(r0 -> r0.id == r_k[1], odpairs)].destination.id
            ) >= (
                (v.spec_cons[g - g_init + 1]) / v.W[g - g_init + 1] * path_dict[r_k[2]].length
            ) * model[:f][y, (p.id, r_k[1], r_k[2]), (v.vehicle_type.mode.id, v.id), g]
            - 0.5 * (
                v.tank_capacity[g - g_init + 1] * path_dict[r_k[2]].length / (v.W[g - g_init + 1] * v.AnnualRange[g - g_init + 1])
            ) * model[:f][y, (p.id, r_k[1], r_k[2]), (v.vehicle_type.mode.id, v.id), g]
        )
    end
end

function constraint_spatial_flexibility(model::JuMP.Model, data_structures::Dict)
    spatial_flexibility_edges_list = data_structures["spatial_flexibility_edges_list"]

    if spatial_flexibility_edges_list != []
        y_init = data_structures["y_init"]
        Y_end = data_structures["Y_end"]
        g_init = data_structures["g_init"]
        modeled_generations = data_structures["modeled_generations"]
        odpairs = data_structures["odpair_list"]
        techvehicles = data_structures["techvehicle_list"]
        gamma = data_structures["gamma"]
        paths = data_structures["path_list"]
        products = data_structures["product_list"]
        r_k_pairs = data_structures["r_k_pairs"]
        f_l_pairs = data_structures["f_l_pairs"]

        # Pre-index spatial flexibility edges by (generation, tech_vehicle_id, path_id) for O(1) lookup
        # This avoids repeated filtering inside nested loops
        edge_index = Dict{Tuple{Int, Int, Int}, Vector{Any}}()
        for edge in spatial_flexibility_edges_list
            key = (edge.generation, edge.tech_vehicle.id, edge.path.id)
            if !haskey(edge_index, key)
                edge_index[key] = []
            end
            push!(edge_index[key], edge)
        end

        # Pre-filter r_k_pairs by path to avoid repeated filtering in constraint conditions
        r_k_by_path = Dict{Int, Vector{Any}}()
        for r_k in r_k_pairs
            path_id = r_k[2]
            if !haskey(r_k_by_path, path_id)
                r_k_by_path[path_id] = []
            end
            push!(r_k_by_path[path_id], r_k)
        end

        # Create constraints with pre-indexed lookups
        for g in modeled_generations
            for tv in techvehicles
                tv_id = tv.id
                spec_cons_idx = g - g_init + 1
                spec_cons_val = tv.spec_cons[spec_cons_idx]
                W_val = tv.W[spec_cons_idx]
                energy_factor = spec_cons_val / W_val
                mode_id = tv.vehicle_type.mode.id

                for path in paths
                    path_id = path.id

                    # Direct lookup instead of filtering
                    key = (g, tv_id, path_id)
                    if !haskey(edge_index, key)
                        continue  # No matching edges for this combination
                    end

                    matching_edges = edge_index[key]
                    r_k_for_path = get(r_k_by_path, path_id, [])

                    if isempty(r_k_for_path)
                        continue  # No r_k pairs use this path
                    end

                    for matching_set in matching_edges
                        # Pre-collect sequence element IDs (avoid repeated .id access)
                        seq_ids = [el.id for el in matching_set.sequence]
                        set_length = matching_set.length

                        @constraint(
                            model, [y in y_init:Y_end, p in products, r_k in r_k_for_path, f_l in f_l_pairs; g <= y],
                            sum(model[:s][y, (p.id, r_k[1], path_id, el_id), tv_id, f_l, g] for el_id in seq_ids) >=
                            energy_factor * set_length * model[:f][y, (p.id, r_k[1], path_id), (mode_id, tv_id), g]
                        )
                    end
                end
            end
        end

    end
end


function constraint_fueling_demand_to_origin(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    gamma = data_structures["gamma"]
    paths = data_structures["path_list"]
    products = data_structures["product_list"]
    r_k_pairs = data_structures["r_k_pairs"]
    f_l_pairs = data_structures["f_l_pairs"]


    if length(data_structures["fueling_infr_types_list"]) == 0
 
        @constraint(
            model,
            [y in y_init:Y_end, p in products, r_k in r_k_pairs, v in techvehicles],
            sum(
                model[:s][y, (p.id, r_k[1], r_k[2], el.id), v.id] for
                el ∈ paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence
                if el != findfirst(k0 -> k0.id == r_k[2], paths).sequence[length(el.sequence)]
            ) >= sum(
                (
                    (v.spec_cons[g-g_init+1]) / v.W[g-g_init+1] *
                    paths[findfirst(p0 -> p0.id == r_k[2], paths)].length
                ) * model[:f][y, (p.id, r_k[1], r_k[2]), (v.vehicle_type.mode.id, v.id), g]
                )
        )
    else
        @constraint(
            model,
            [y in y_init:Y_end, p in products, r_k in r_k_pairs, v in techvehicles, g in g_init:Y_end, f_l in f_l_pairs; g <= y],
            sum(
                model[:s][y, (p.id, r_k[1], r_k[2], el.id), f_l, g] for
                el ∈ paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence
                if el != findfirst(k0 -> k0.id == r_k[2], paths).sequence[length(el.sequence)] && f_l[0] == v.technology.fuel.id
            ) >= sum(
                (
                    (v.spec_cons[g-g_init+1]) / v.W[g-g_init+1] *
                    paths[findfirst(p0 -> p0.id == r_k[2], paths)].length
                ) * model[:f][y, (p.id, r_k[1], r_k[2]), (v.vehicle_type.mode.id, v.id), g]
            )
        )
    end
end




"""
	constraint_vehicle_stock_shift(model::JuMP.Model, data_structures::Dict)

Constraints for vehicle stock turnover.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_vehicle_stock_shift(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    alpha_h = data_structures["alpha_h"]
    beta_h = data_structures["beta_h"]
    technologies = data_structures["technology_list"]
    vehicletypes = data_structures["vehicletype_list"]

    # for y = y_init
    # @constraint(
    #     model,
    #     [r in odpairs, t in technologies],
    #     (
    #         sum(
    #             model[:h][y_init, r.id, tv.id, g] for g ∈ filter(g -> g <= y_init, modeled_generations)
    #             for tv ∈ techvehicles if g <= y_init && tv.technology.id == t.id
    #         ) - sum(
    #             model[:h_exist][y_init, r.id, tv.id, g] for g ∈ filter(g -> g <= y_init, modeled_generations)
    #             for tv ∈ techvehicles if g <= y_init - 1 && tv.technology.id == t.id
    #         )
    #     ) <=
    #     alpha_h * sum(
    #         model[:h][y_init, r.id, tv.id, g] for g ∈ filter(g -> g <= y_init, modeled_generations) for
    #         tv ∈ techvehicles
    #     ) +
    #     beta_h * sum(
    #         model[:h_exist][y_init, r.id, tv.id, g] for
    #         g ∈ filter(g -> g <= y_init-1, modeled_generations) for tv ∈ techvehicles if tv.technology.id == t.id
    #     )
    # )

    # @constraint(
    #     model,
    #     [r in odpairs, t in technologies],
    #     -(
    #         sum(
    #             model[:h][y_init, r.id, tv.id, g] for g ∈ filter(g -> g <= y_init, modeled_generations)
    #             for tv ∈ techvehicles if g <= y_init && tv.technology.id == t.id
    #         ) - sum(
    #             model[:h_exist][y_init, r.id, tv.id, g] for g ∈ filter(g -> g <= y_init, modeled_generations) for
    #             tv ∈ techvehicles if g <= y_init - 1 && tv.technology.id == t.id
    #         )
    #     ) <=
    #     alpha_h * sum(
    #         model[:h][y_init, r.id, tv.id, g] for g ∈ filter(g -> g <= y_init, modeled_generations) for
    #         tv ∈ techvehicles
    #     ) +
    #     beta_h * sum(
    #         model[:h_exist][y_init, r.id, tv.id, g] for
    #         g ∈ filter(g -> g <= y_init-1, modeled_generations) for tv ∈ techvehicles if tv.technology.id == t.id
    #     )
    # )

    # for  y > y_init
    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, t in technologies],
        (
            sum(
                model[:h][y, r.id, tv.id, g] for g ∈ filter(g -> g <= y, modeled_generations) for
                tv ∈ techvehicles if tv.technology.id == t.id
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ filter(g -> g <= y-1, modeled_generations) for
                tv ∈ techvehicles if tv.technology.id == t.id
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv.id, g] for g ∈ filter(g -> g <= y, modeled_generations) for tv ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g] for g ∈ filter(g -> g <= y-1, modeled_generations) for
            tv ∈ techvehicles if tv.technology.id == t.id
        )
    )

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, t in technologies],
        -(
            sum(
                model[:h][y, r.id, tv.id, g] for g ∈ filter(g -> g <= y, modeled_generations) for
                tv ∈ techvehicles if tv.technology.id == t.id
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ filter(g -> g <= y-1, modeled_generations) for
                tv ∈ techvehicles if tv.technology.id == t.id
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv.id, g] for g ∈ filter(g -> g <= y, modeled_generations) for tv ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g] for g ∈ filter(g -> g <= y-1, modeled_generations) for
            tv ∈ techvehicles if tv.technology.id == t.id
        )
    )
end


"""
	constraint_vehicle_stock_shift_vehicle_type(model::JuMP.Model, data_structures::Dict)

Constraints for vehicle stock turnover.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_vehicle_stock_shift_vehicle_type(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    alpha_h = data_structures["alpha_h"]
    beta_h = data_structures["beta_h"]
    technologies = data_structures["technology_list"]
    vehicletypes = data_structures["vehicletype_list"]

    # for y = y_init
    # TODO: uncomment
    # @constraint(
    #     model,
    #     [r in odpairs, tv in techvehicles],
    #     (
    #         sum(
    #             model[:h][y_init, r.id, tv.id, g] for g ∈ filter(g -> g <= y_init, modeled_generations)
    #         ) - sum(
    #             model[:h_exist][y_init, r.id, tv.id, g] for g ∈ filter(g -> g <= y_init-1, modeled_generations)
    #         )
    #     ) <=
    #     alpha_h * sum(
    #         model[:h][y_init, r.id, tv0.id, g] for g ∈ filter(g -> g <= y_init, modeled_generations) for tv0 ∈ techvehicles
    #     ) +
    #     beta_h * sum(
    #         model[:h_exist][y_init, r.id, tv.id, g] for
    #         g ∈ filter(g -> g <= y_init-1, modeled_generations)
    #     )
    # )

    # @constraint(
    #     model,
    #     [r in odpairs, tv in techvehicles],
    #     -(
    #         sum(
    #             model[:h][y_init, r.id, tv.id, g] for g ∈ filter(g -> g <= y_init, modeled_generations)
    #         ) - sum(
    #             model[:h_exist][y_init, r.id, tv.id, g] for g ∈ filter(g -> g <= y_init-1, modeled_generations)
    #         )
    #     ) <=
    #     alpha_h * sum(
    #         model[:h][y_init, r.id, tv0.id, g] for g ∈ filter(g -> g <= y_init, modeled_generations) for tv0 ∈ techvehicles
    #     ) +
    #     beta_h * sum(
    #         model[:h_exist][y_init, r.id, tv.id, g] for g ∈ filter(g -> g <= y_init-1, modeled_generations)
    #     )
    # )

    # for  y > y_init
    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, tv in techvehicles],
        (
            sum(
                model[:h][y, r.id, tv.id, g] for g ∈ filter(g -> g <= y, modeled_generations)
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ filter(g -> g <= y-1, modeled_generations)
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv0.id, g] for g ∈ filter(g -> g <= y, modeled_generations) for tv0 ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g] for g ∈ filter(g -> g <= y-1, modeled_generations)
        )
    )

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, tv in techvehicles],
        -(
            sum(
                model[:h][y, r.id, tv.id, g] for g ∈ filter(g -> g <= y, modeled_generations)
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ filter(g -> g <= y-1, modeled_generations)
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv0.id, g] for g ∈ filter(g -> g <= y, modeled_generations) for tv0 ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g] for g ∈ filter(g -> g <= y-1, modeled_generations)
        )
    )
end

function constraint_a(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    gifl_pair = data_structures["geo_i_f_l"]

    investment_period = data_structures["investment_period"]
    println(gifl_pair)
    @constraint(model,
    [y in y_init:investment_period:Y_end, gifl in gifl_pair],
        model[:a][y, gifl] == sum(model[:x_c][y, gifl_higher] 
                        for gifl_higher in gifl_pair
                        if gifl_higher[1] == gifl[1]   # same geo
                        && gifl_higher[3] == gifl[3]  # same fuel
                        && gifl_higher[4] == gifl[4]  # same type
                        && gifl_higher[2] >= gifl[2]) # higher-or-equal level
    )
    @constraint(model,
            [y in y_init:investment_period:(Y_end-1), gifl in gifl_pair],
            model[:a][y, gifl] <= model[:a][y+investment_period, gifl]
        )

end
"""
	constraint_mode_shift(model::JuMP.Model, data_structures::Dict)

Constraints for the rate of the mode shfit.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_mode_shift(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    alpha_f = data_structures["alpha_f"]
    beta_f = data_structures["beta_f"]
    modes = data_structures["mode_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, m in modes],
        (
            sum(
                model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
                mv ∈ m_tv_pairs for g ∈ filter(g -> g <= y, modeled_generations) if mv[1] == m.id
            ) - sum(
                model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
                g ∈ filter(g -> g <= y-1, modeled_generations) for mv ∈ m_tv_pairs if mv[1] == m.id
            )
        ) <=
        alpha_f * sum(
            model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for g ∈ filter(g -> g <= y, modeled_generations)
            for mv ∈ m_tv_pairs
        ) +
        beta_f * sum(
            model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
            mv ∈ m_tv_pairs for g ∈ filter(g -> g <= y-1, modeled_generations) if mv[1] == m.id
        )
    )

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, m in modes],
        -(
            sum(
                model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
                mv ∈ m_tv_pairs for g ∈ filter(g -> g <= y, modeled_generations) if mv[1] == m.id
            ) - sum(
                model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
                g ∈ filter(g -> g <= y-1, modeled_generations) for mv ∈ m_tv_pairs if mv[1] == m.id
            )
        ) <=
        alpha_f * sum(
            model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for g ∈ filter(g -> g <= y, modeled_generations)
            for mv ∈ m_tv_pairs
        ) +
        beta_f * sum(
            model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
            mv ∈ m_tv_pairs for g ∈ filter(g -> g <= y-1, modeled_generations) if mv[1] == m.id
        )
    )
end

"""
    constraint_mode_share(model::JuMP.Model, data_structures::Dict)

If share are given for specific modes, this function will create constraints for the share of the modes. When this constraint is active, it can be a source of infeasibility for the model as it may be not possible to reach certain mode shares due to restrictions in the shift of modes (see parametrization of parameters alpha_f and beta_f). Especially also when constraints for minimum/maximum mode shares are active.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_mode_share(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    mode_share_list = data_structures["mode_share_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    odpairs = data_structures["odpair_list"]

    @constraint(
        model,
        [el in mode_share_list],
        sum(
            model[:f][el.year, (r.product.id, r.id, k.id), mv, g] for p_r_k ∈ p_r_k_pairs
            for mv ∈ m_tv_pairs for k ∈ r.paths for g ∈ filter(g -> g <= el.year, modeled_generations) if
            mv[1] == el.mode.id && r.region.id in [rt.id for rt ∈ el.region_type]
        ) ==
        el.share * sum(
            r.F[el.year-y_init+1] for
            r ∈ odpairs if r.region.id in [rt.id for rt ∈ el.region_type]
        )
    )
end

"""
    constraint_max_mode_share(model::JuMP.Model, data_structures::Dict)

If share are given for specific modes, this function will create constraints for the share of the modes. When this constraint is active, it can be a source of infeasibility for the model as it may be not possible to reach certain mode shares due to restrictions in the shift of modes (see parametrization of parameters alpha_f and beta_f). Or when multiple constraints for the mode share are active.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_max_mode_share(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    max_mode_share_list = data_structures["max_mode_share_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    odpairs = data_structures["odpair_list"]

    @constraint(
        model,
        [el in max_mode_share_list],
        sum(
            model[:f][el.year, (r.product.id, r.id, k.id), mv, g] for p_r_k ∈ p_r_k_pairs
            for mv ∈ m_tv_pairs for k ∈ r.paths for g ∈ filter(g -> g <= el.year, modeled_generations) if
            mv[1] == el.mode.id && r.region.id in [rt.id for rt ∈ el.region_type]
        ) <=
        el.share * sum(
            r.F[el.year-y_init+1] for
            r ∈ odpairs if r.region.id in [rt.id for rt ∈ el.region_type]
        )
    )
end

"""
    constraint_min_mode_share(model::JuMP.Model, data_structures::Dict)

If share are given for specific modes, this function will create constraints for the share of the modes. When this constraint is active, it can be a source of infeasibility for the model as it may be not possible to reach certain mode shares due to restrictions in the shift of modes (see parametrization of parameters alpha_f and beta_f). Or when multiple constraints for the mode share are active.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_min_mode_share(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    min_mode_share_list = data_structures["min_mode_share_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    odpairs = data_structures["odpair_list"]

    @constraint(
        model,
        [el in min_mode_share_list],
        sum(
            model[:f][el.year, (r.product.id, r.id, k.id), mv, g] for p_r_k ∈ p_r_k_pairs
            for mv ∈ m_tv_pairs for k ∈ r.paths for g ∈ filter(g -> g <= el.year, modeled_generations) if
            mv[1] == el.mode.id && r.region.id in [rt.id for rt ∈ el.region_type]
        ) >=
        el.share * sum(
            r.F[el.year-y_init+1] for
            r ∈ odpairs if r.region.id in [rt.id for rt ∈ el.region_type]
        )
    )
end

"""
    constraint_market_share(model::JuMP.Model, data_structures::Dict)

If share are given for specific vehicle types, this function will create constraints for the newly bought vehicle share of vehicles the modes.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_market_share(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    market_share_list = data_structures["market_share_list"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    odpairs = data_structures["odpair_list"]

    @constraint(
        model,
        [el in market_share_list],
        sum(
            model[:h_plus][el.year, r.id, el.type.id, g] for r ∈ odpairs for
            g ∈ filter(g -> g <= el.year, modeled_generations)
        ) ==
        el.market_share * sum(
            model[:h_plus][el.year, r.id, tv.id, g] for r ∈ odpairs for
            tv ∈ data_structures["techvehicle_list"] for
            g ∈ filter(g -> g <= el.year, modeled_generations) if tv.vehicle_type.mode.id == el.type.vehicle_type.mode.id
        )
    )

end

"""
    constraint_emissions_by_mode(model::JuMP.Model, data_structures::Dict)

Emissions given per mode for a specific year. Attention: This constraint may be a source for infeasibility if mode or technology shift cannot be achieved due to restrictions in the shift of modes (see parametrization of parameters alpha_f and beta_f), or due to the lifetimes of technologies as well as the lack of available low emission or zero emission technologies.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_emissions_by_mode(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    emission_constraints_by_mode_list = data_structures["emission_constraints_by_mode_list"]
    mode_list = data_structures["mode_list"]
    odpairs = data_structures["odpair_list"]
    for el ∈ emission_constraints_by_mode_list
        m0 = mode_list[findfirst(m -> m.id == el.mode.id, mode_list)]
        if m0.quantify_by_vehs
            @constraint(
                model,
                [el in emission_constraints_by_mode_list],
                sum(
                    model[:s][el.year, (r.product.id, r.id, k.id, geo), tv.id] *
                    tv.technology.fuel.emission_factor for
                    r ∈ data_structures["odpair_list"] for k ∈ r.paths for
                    tv ∈ data_structures["techvehicle_list"] for
                    geo ∈ k.sequence if tv.vehicle_type.mode.id == el.mode.id
                ) <= el.emission
            )
        else
            @constraint(
                model,
                [el in emission_constraints_by_mode_list],
                sum(
                    model[:f][el.year, (r.product.id, r.id, k.id), mv, g] *
                    sum(k.length for k ∈ r.paths) *
                    m0.emission_factor *
                    10^(-3) for r ∈ odpairs for k ∈ r.paths for g ∈ filter(g -> g <= el.year, modeled_generations)
                ) <= el.emission
            )
        end
    end
end

"""
    constraint_def_n_fueling(model::JuMP.Model, data_structures::Dict)

Constraints for defining number of vehicles fueling at a location. The definition is for the determination of the detour time, and therefore only a necessary constraint for the model when the detour time is considered.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data

"""
function constraint_def_n_fueling(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    techvehicle_list = data_structures["techvehicle_list"]
    fuel_list = data_structures["fuel_list"]
    f_l_pairs = data_structures["f_l_pairs"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]

    if length(data_structures["fueling_infr_types_list"]) == 0

        @constraint(
            model,
            [y in y_init:Y_end, p_r_k_g in p_r_k_g_pairs, f in fuel_list, g in modeled_generations; g <= y],
            model[:n_fueling][y, p_r_k_g, f.id, g] >= sum(
                (1 / (tv.tank_capacity[1] * 0.8)) * model[:s][y, p_r_k_g, tv.id, g] for
                tv ∈ techvehicle_list if tv.technology.fuel.id == f.id
            )
        )
    else
        @constraint(
            model,
            [y in y_init:Y_end, p_r_k_g in p_r_k_g_pairs, f_l in f_l_pairs, g in modeled_generations; g<= y],
            model[:n_fueling][y, p_r_k_g, f_l, g] >=
                sum((1 / (tv.tank_capacity[g-g_init + 1] * 0.8)) * model[:s][y, p_r_k_g, tv.id, f_l, g] for tv in techvehicle_list if tv.technology.fuel.id == f_l[1])
        )
    end
end

"""
    constraint_detour_time(model::JuMP.Model, data_structures::Dict)

Constraints for the detour time of vehicles fueling at a location. The detour time is determined by the number of vehicles fueling at a location and the initial detour time. The detour time can be reduced by the installation of fueling infrastructure which increases the density. The reduction potentials for different locations and fuel types need to be defined in the input data.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data

"""
function constraint_detour_time(model::JuMP.Model, data_structures::Dict)
    geo_i_f_pairs = data_structures["geo_i_f_pairs"]
    fuel_list = data_structures["fuel_list"]
    techvehicle_list = data_structures["techvehicle_list"]
    detour_time_reduction_list = data_structures["detour_time_reduction_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    paths = data_structures["path_list"]
    gamma = data_structures["gamma"]
    geographic_element_list = data_structures["geographic_element_list"]
    init_detour_times_list = data_structures["init_detour_times_list"]
    g_init = data_structures["g_init"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]

    if length(data_structures["fueling_infr_types_list"]) == 0
 
        for p_r_k_g ∈ p_r_k_g_pairs
            
            geo_id = p_r_k_g[4]
            for f ∈ fuel_list
                matching_item = init_detour_times_list[findfirst(
                    elem -> elem.fuel.id == f.id && elem.location.id == geo_id,
                    init_detour_times_list,
                )]
                init_detour_time = matching_item.detour_time
                if findfirst(elem -> elem.fuel.id == f.id, detour_time_reduction_list) ==
                nothing
                    @constraint(
                        model,
                        [y in y_init:Y_end],
                        model[:detour_time][y, p_r_k_g, f.id] ==
                        sum(model[:n_fueling][y, p_r_k_g, f.id, g] for g in g_init:y) * init_detour_time * 1000
                    )

                else
                    selection = detour_time_reduction_list[findall(
                        elem -> elem.fuel.id == f.id && elem.location.id == geo_id,
                        detour_time_reduction_list,
                    )]

                    @constraint(
                        model,
                        [y in y_init:Y_end],
                        model[:detour_time][y, p_r_k_g, f.id] ==
                        sum(model[:n_fueling][y, p_r_k_g, f.id, g] ) * init_detour_time * 1000 - sum(
                            model[:z][y, g_id, p_r_k_g] *
                            init_detour_time *
                            selection[findfirst(
                                item -> item.reduction_id == g_id[2],
                                selection,
                            )].detour_time_reduction for
                            g_id ∈ geo_i_f_pairs if g_id[1] == geo_id && g_id[3] == f.id
                        )
                    )
                end
            end
        end
    else
        for p_r_k_g ∈ p_r_k_g_pairs
            f_l_for_dt = data_structures["f_l_for_dt"]
            geo_id = p_r_k_g[4]    
            geo_i_f_l_pairs = data_structures["geo_i_f_l"]
            if findfirst(
                elem -> elem.location.id == geo_id,
                init_detour_times_list,
            ) == nothing
                continue
            end
            for f_l ∈ f_l_for_dt
                matching_item = init_detour_times_list[findfirst(
                    elem -> elem.fuel.id == f_l[1] && elem.fuel_infr_type.id == f_l[2] && elem.location.id == geo_id,
                    init_detour_times_list,
                )]
                init_detour_time = matching_item.detour_time
                if findfirst(elem -> elem.fuel.id == f_l[1] && elem.fueling_type.id == f_l[2], detour_time_reduction_list) == nothing
                    # println("No detour time reduction found for fuel: ", f_l[1], " and fueling type: ", f_l[2], " at location: ", geo_id)
                    @constraint(
                        model,
                        [y in y_init:Y_end],
                        model[:detour_time][y, p_r_k_g, f_l] ==
                        sum(model[:n_fueling][y, p_r_k_g, f_l, g] for g in g_init:y) * 1000 * init_detour_time
                    )
                else
                    selection = detour_time_reduction_list[findall(
                        elem -> elem.fuel.id == f_l[1] && elem.location.id == geo_id && elem.fueling_type.id == f_l[2],
                        detour_time_reduction_list,
                    )]
                    
                    
                    @constraint(model, [y in y_init:Y_end], model[:detour_time][y, p_r_k_g, f_l] == 0)
                    
                    # the following constraint is only necessary when the detour time is considered
                    # @constraint(
                    #     model,
                    #     [y in y_init:Y_end],
                    #     model[:detour_time][y, p_r_k_g, f_l] ==
                    #     sum(model[:n_fueling][y, p_r_k_g, f_l, g] for g in g_init:y) * 1000 * init_detour_time - sum(
                    #         model[:z][y, g_id, p_r_k_g] *
                    #         init_detour_time *
                    #         selection[findfirst(
                    #             item -> item.reduction_id == g_id[2],
                    #             selection,
                    #         )].detour_time_reduction for
                    #         g_id ∈ geo_i_f_l_pairs if g_id[1] == geo_id && g_id[3] == f_l[1] && g_id[4] == f_l[2]
                    #     )
                    # )
                    # println([selection[findfirst(
                    #             item -> item.reduction_id == g_id[2],
                    #             selection,
                    #         )].detour_time_reduction for
                    #         g_id ∈ geo_i_f_l_pairs if g_id[1] == geo_id && g_id[3] == f_l[1] && g_id[4] == f_l[2]])
                end
            end
        end
    end 
end

function constraint_detour_time_2(model::JuMP.Model, data_structures::Dict)
    geo_i_f_pairs = data_structures["geo_i_f_pairs"]
    fuel_list = data_structures["fuel_list"]
    techvehicle_list = data_structures["techvehicle_list"]
    detour_time_reduction_list = data_structures["detour_time_reduction_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    paths = data_structures["path_list"]
    gamma = data_structures["gamma"]
    geographic_element_list = data_structures["geographic_element_list"]
    init_detour_times_list = data_structures["init_detour_times_list"]
    g_init = data_structures["g_init"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]

    if length(data_structures["fueling_infr_types_list"]) == 0
 
        for p_r_k_g ∈ p_r_k_g_pairs
            
            geo_id = p_r_k_g[4]
            for f ∈ fuel_list
                matching_item = init_detour_times_list[findfirst(
                    elem -> elem.fuel.id == f.id && elem.location.id == geo_id,
                    init_detour_times_list,
                )]
                init_detour_time = matching_item.detour_time
                if findfirst(elem -> elem.fuel.id == f.id, detour_time_reduction_list) ==
                nothing
                    @constraint(
                        model,
                        [y in y_init:Y_end],
                        model[:detour_time][y, p_r_k_g, f.id] ==
                        sum(model[:n_fueling][y, p_r_k_g, f.id, g] for g in g_init:y) * init_detour_time * 1000
                    )

                else
                    selection = detour_time_reduction_list[findall(
                        elem -> elem.fuel.id == f.id && elem.location.id == geo_id,
                        detour_time_reduction_list,
                    )]

                    @constraint(
                        model,
                        [y in y_init:Y_end],
                        model[:detour_time][y, p_r_k_g, f.id] ==
                        sum(model[:n_fueling][y, p_r_k_g, f.id, g] ) * init_detour_time * 1000 - sum(
                            model[:z][y, g_id, p_r_k_g] *
                            init_detour_time *
                            selection[findfirst(
                                item -> item.reduction_id == g_id[2],
                                selection,
                            )].detour_time_reduction for
                            g_id ∈ geo_i_f_pairs if g_id[1] == geo_id && g_id[3] == f.id
                        )
                    )
                end
            end
        end
    else
        for p_r_k_g ∈ p_r_k_g_pairs
            f_l_for_dt = data_structures["f_l_for_dt"]
            geo_id = p_r_k_g[4]    
            geo_i_f_l_pairs = data_structures["geo_i_f_l"]
            if findfirst(
                elem -> elem.location.id == geo_id,
                init_detour_times_list,
            ) == nothing
                continue
            end
            for f_l ∈ f_l_for_dt
                matching_item = init_detour_times_list[findfirst(
                    elem -> elem.fuel.id == f_l[1] && elem.fuel_infr_type.id == f_l[2] && elem.location.id == geo_id,
                    init_detour_times_list,
                )]
                init_detour_time = matching_item.detour_time
                # println("No detour time reduction found for fuel: ", f_l[1], " and fueling type: ", f_l[2], " at location: ", geo_id)
                @constraint(
                    model,
                    [y in y_init:Y_end],
                    model[:detour_time][y, p_r_k_g, f_l] ==
                    sum(model[:n_fueling][y, p_r_k_g, f_l, g] for g in g_init:y) * 1000 * init_detour_time
                )
              
                    # the following constraint is only necessary when the detour time is considered
                    # @constraint(
                    #     model,
                    #     [y in y_init:Y_end],
                    #     model[:detour_time][y, p_r_k_g, f_l] ==
                    #     sum(model[:n_fueling][y, p_r_k_g, f_l, g] for g in g_init:y) * 1000 * init_detour_time - sum(
                    #         model[:z][y, g_id, p_r_k_g] *
                    #         init_detour_time *
                    #         selection[findfirst(
                    #             item -> item.reduction_id == g_id[2],
                    #             selection,
                    #         )].detour_time_reduction for
                    #         g_id ∈ geo_i_f_l_pairs if g_id[1] == geo_id && g_id[3] == f_l[1] && g_id[4] == f_l[2]
                    #     )
                    # )
                    # println([selection[findfirst(
                    #             item -> item.reduction_id == g_id[2],
                    #             selection,
                    #         )].detour_time_reduction for
                    #         g_id ∈ geo_i_f_l_pairs if g_id[1] == geo_id && g_id[3] == f_l[1] && g_id[4] == f_l[2]])
                
            end
        end
    end 
end

"""
    constraint_lin_z_nalpha(model::JuMP.Model, data_structures::Dict)

Constraints for the linearization of the product of the binary variable x and the number of vehicles fueling at a location. The linearization is necessary when the detour time is considered.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_lin_z_nalpha(model::JuMP.Model, data_structures::Dict)
    geo_id_pairs = data_structures["geo_i_f_pairs"]
    techvehicle_list = data_structures["techvehicle_list"]
    fuel_list = data_structures["fuel_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    paths = data_structures["path_list"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    init_detour_times_list = data_structures["init_detour_times_list"]
    detour_time_reduction_list = data_structures["detour_time_reduction_list"]
    g_init = data_structures["g_init"]
    gamma = data_structures["gamma"]
    geographic_element_list = data_structures["geographic_element_list"]
    investment_period = data_structures["investment_period"]
    investment_years = collect(y_init:investment_period:Y_end)  # List of years where x_c is defined
    M = 10^5

    if length(data_structures["fueling_infr_types_list"]) == 0
        for geo_i_f ∈ geo_id_pairs
            matching_item = detour_time_reduction_list[findfirst(
                item ->
                    item.reduction_id == geo_i_f[2] &&
                        item.location.id ==
                        geographic_element_list[findfirst(
                            item -> item.id == geo_i_f[1],
                            geographic_element_list,
                        )].id,
                detour_time_reduction_list,
            )]
            #reduction_val = matching_item.detour_time_reduction

            f = matching_item.fuel
            @constraint(
                model,
                [y in y_init:Y_end, p_r_k in p_r_k_g_pairs, v in techvehicle_list],
                model[:z][y, geo_i_f, p_r_k] <= sum(model[:n_fueling][y, p_r_k, f.id, g] for g in g_init:y) * 1000 
            )

            @constraint(
                model,
                [y in y_init:Y_end, p_r_k in p_r_k_g_pairs],
                model[:z][y, geo_i_f, p_r_k] <= M * model[:x_c][maximum([t for t in investment_years if t <= y]; init = y_init), geo_i_f]
            )

            @constraint(
                model,
                [y in y_init:Y_end, p_r_k in p_r_k_g_pairs],
                model[:z][y, geo_i_f, p_r_k] >=
                1000 * sum(model[:n_fueling][y, p_r_k, f.id, g] for g in g_init:y) - M * (1 - model[:x_c][maximum([t for t in investment_years if t <= y]; init = y_init), geo_i_f])
            )
        end 
    else
        geo_i_f_l_pairs = data_structures["geo_i_f_l"]       
        for geo_i_f ∈ geo_i_f_l_pairs
            matching_item = detour_time_reduction_list[findfirst(
                item ->
                    item.reduction_id == geo_i_f[2] &&
                        item.location.id ==
                        geographic_element_list[findfirst(
                            item -> item.id == geo_i_f[1],
                            geographic_element_list,
                        )].id && item.fueling_type.id == geo_i_f[4],
                detour_time_reduction_list,
            )]
            #reduction_val = matching_item.detour_time_reduction

            f = matching_item.fuel
            l = matching_item.fueling_type.id 
            @constraint(
                model,
                [y in y_init:Y_end, p_r_k in p_r_k_g_pairs, v in techvehicle_list],
                model[:z][y, geo_i_f, p_r_k] <= sum(model[:n_fueling][y, p_r_k, (f.id, l), g] for g in g_init:y) * 1000
            )

            @constraint(
                model,
                [y in y_init:Y_end, p_r_k in p_r_k_g_pairs],
                model[:z][y, geo_i_f, p_r_k] <= M * model[:x_c][maximum([t for t in investment_years if t <= y]; init = y_init), geo_i_f]
            )

            @constraint(
                model,
                [y in y_init:Y_end, p_r_k in p_r_k_g_pairs],
                model[:z][y, geo_i_f, p_r_k] >=
                1000 * sum(model[:n_fueling][y, p_r_k, (f.id, l), g] for g in g_init:y) - M * (1 - model[:x_c][maximum([t for t in investment_years if t <= y]; init = y_init), geo_i_f])
            )

            # @constraint(
            #     model,
            #     [y in y_init:Y_end, p_r_k in p_r_k_g_pairs],
            #     model[:x_c][maximum([t for t in investment_years if t <= y]; init = y_init), geo_i_f] -->
            #         { model[:z][y, geo_i_f, p_r_k] ==
            #             1000 * sum(model[:n_fueling][y, p_r_k, (f.id, l), g] for g in g_init:y) }
            # )

            # @constraint(
            #     model,
            #     [y in y_init:Y_end, p_r_k in p_r_k_g_pairs],
            #     !model[:x_c][maximum([t for t in investment_years if t <= y]; init = y_init), geo_i_f] -->
            #         { model[:z][y, geo_i_f, p_r_k] == 0 }
            # )

        end 
    end 
end

"""
    constraint_detour_time_capacity_reduction(model::JuMP.Model, data_structures::Dict)

Constraints for the reduction of the detour time by the installation of fueling infrastructure. The reduction potentials for different locations and fuel types need to be defined in the input data.	


# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data

"""
function constraint_detour_time_capacity_reduction(model::JuMP.Model, data_structures::Dict)
    geo_id_pairs = data_structures["geo_i_f_pairs"]
    techvehicle_list = data_structures["techvehicle_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    paths = data_structures["path_list"]
    gamma = data_structures["gamma"]
    detour_time_reduction_list = data_structures["detour_time_reduction_list"]
    fuel_list = data_structures["fuel_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    investment_period = data_structures["investment_period"]
    investment_years = collect(y_init:investment_period:Y_end)  # List of years where x_c is defined
    initialfuelinginfr_list = data_structures["initialfuelinginfr_list"]
    M = 10^4

    global counter_ = 0
    if length(data_structures["fueling_infr_types_list"]) == 0
        
        for geo_i_f ∈ geo_id_pairs
            matching_item = detour_time_reduction_list[findfirst(
                item ->
                    item.reduction_id == geo_i_f[2] &&
                        item.location.id ==
                        geographic_element_list[findfirst(
                            item -> item.id == geo_i_f[1],
                            geographic_element_list,
                        )].id,
                detour_time_reduction_list,
            )]
            lb = matching_item.fueling_cap_lb  * (1/1000) + 0.0001
            ub = matching_item.fueling_cap_ub  * (1/1000)
            fuel_type = matching_item.fuel

            @constraint(
                model,
                [y in y_init:investment_period:Y_end],
                lb * model[:x_c][y, geo_i_f] <=
                sum(model[:q_fuel_infr_plus][y0, fuel_type.id, geo_i_f[1]] * (1/1000) for y0 ∈ y_init:investment_period:y)
            )
            @constraint(
                model,
                [y in y_init:investment_period:Y_end],
                sum(
                    model[:q_fuel_infr_plus][y0, fuel_type.id, geo_i_f[1]] * (1/1000) for y0 ∈ y_init:investment_period:y
                ) <= ub * model[:x_c][y, geo_i_f] + M * (1 - model[:x_c][y, geo_i_f])
            )
        end
    else 
        geo_i_f_l_pairs = data_structures["geo_i_f_l"]
        # println("geo_i_f_l_pairs: ", geo_i_f_l_pairs)
        for geo_i_f ∈ geo_i_f_l_pairs
            matching_item = detour_time_reduction_list[findfirst(
                item ->
                    item.reduction_id == geo_i_f[2] &&
                        item.location.id ==
                        geographic_element_list[findfirst(
                            item -> item.id == geo_i_f[1],
                            geographic_element_list,
                        )].id && item.fueling_type.id == geo_i_f[4],
                detour_time_reduction_list,
            )]
            lb = matching_item.fueling_cap_lb  * (1/1000) + 0.0001
            ub = matching_item.fueling_cap_ub  * (1/1000)
            fuel_type = matching_item.fuel
            f_l = (fuel_type.id, matching_item.fueling_type.id)
            # @constraint(
            #     model,
            #     [y in y_init:investment_period:Y_end],
            #     lb * model[:x_c][y, geo_i_f] <=  (initialfuelinginfr_list[findfirst(
            #                 i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo_i_f[1],
            #                 initialfuelinginfr_list,
            #             )].installed_kW +
            #     sum(model[:q_fuel_infr_plus][y0, f_l, geo_i_f[1]] for y0 ∈ y_init:investment_period:y)) * (1/1000)
            # )
            # @constraint(
            #     model,
            #     [y in y_init:investment_period:Y_end],
            #     (initialfuelinginfr_list[findfirst(
            #                 i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo_i_f[1],
            #                 initialfuelinginfr_list,
            #             )].installed_kW + sum(
            #         model[:q_fuel_infr_plus][y0, (geo_i_f[3], geo_i_f[4]), geo_i_f[1]] for y0 ∈ y_init:investment_period:y
            #     )) * (1/1000) <= ub * model[:x_c][y, geo_i_f] + M * (1 - model[:x_c][y, geo_i_f])
            # )
            @constraint(
                model,
                [y in y_init:investment_period:Y_end],
                model[:x_c][y, geo_i_f] --> {
                    lb <= (initialfuelinginfr_list[findfirst(
                            i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo_i_f[1],
                            initialfuelinginfr_list,
                        )].installed_kW + sum(model[:q_fuel_infr_plus][y0, f_l, geo_i_f[1]] for y0 in y_init:investment_period:y)) * (1/1000)
                }
            )

            @constraint(
                model,
                [y in y_init:investment_period:Y_end],
                model[:x_c][y, geo_i_f] --> {
                    (initialfuelinginfr_list[findfirst(
                            i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo_i_f[1],
                            initialfuelinginfr_list,
                        )].installed_kW + sum(model[:q_fuel_infr_plus][y0, f_l, geo_i_f[1]] for y0 in y_init:investment_period:y)) * (1/1000) <= ub
                }
            )

        end
    end 
end



function constraint_sum_x(model::JuMP.Model, data_structures::Dict)
    geo_id_pairs = data_structures["geo_i_f_pairs"]
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    paths = data_structures["path_list"]
    gamma = data_structures["gamma"]
    detour_time_reduction_list = data_structures["detour_time_reduction_list"]
    fuel_list = data_structures["fuel_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    investment_period = data_structures["investment_period"]
    if data_structures["fueling_infr_types_list"] == 0
        println("here")
        # for y == y_init
        @constraint(model, [y in y_init:investment_period:Y_end, geo in geographic_element_list, f in fuel_list], sum(model[:x_c][y, geo_i_f] for geo_i_f ∈ geo_id_pairs if geo_i_f[1] == geo.id && geo_i_f[3] == f.id) == 1)

    else
        # for y == y_init
        geo_i_f_l_pairs = data_structures["geo_i_f_l"]
        f_l_for_dt = data_structures["f_l_for_dt"]
        # println(f_l_for_dt)
        # println(geo_i_f_l_pairs)
        println("here 2")
        for f_l ∈ f_l_for_dt
            if findfirst(elem -> elem.fuel.id == f_l[1] && elem.fueling_type.id == f_l[2], detour_time_reduction_list) != nothing
                @constraint(model, [y in y_init:investment_period:Y_end, geo in geographic_element_list], sum(model[:x_c][y, geo_i_f] for geo_i_f ∈ geo_i_f_l_pairs if geo_i_f[1] == geo.id && geo_i_f[3] == f_l[1] && geo_i_f[4] == f_l[2]) == 1)
            end
        end
    end

end

function constraint_q_fuel_abs(model::JuMP.Model, data_structures::Dict)
    geo_i_f_pairs = data_structures["geo_i_f_pairs"]
    techvehicle_list = data_structures["techvehicle_list"]
    fuel_list = data_structures["fuel_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    paths = data_structures["path_list"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    init_detour_times_list = data_structures["init_detour_times_list"]
    detour_time_reduction_list = data_structures["detour_time_reduction_list"]
    g_init = data_structures["g_init"]
    gamma = data_structures["gamma"]
    geographic_element_list = data_structures["geographic_element_list"]
    f_l_for_dt = data_structures["f_l_for_dt"]
    geo_i_f_l_pairs = data_structures["geo_i_f_l"]
    f_l_pairs = data_structures["f_l_pairs"]
    init_fueling_infr_list = data_structures["initialfuelinginfr_list"]
    investment_period = data_structures["investment_period"]
    y_range = y_init:investment_period:Y_end
    if length(data_structures["fueling_infr_types_list"]) != 0
        for f_l ∈ f_l_pairs
            if f_l in f_l_for_dt
                
                if findfirst(elem -> elem.fuel.id == f_l[1] && elem.fueling_type.id == f_l[2], detour_time_reduction_list) != nothing
                    @constraint(
                        model,
                        [y in y_range, geo in geographic_element_list],
                        sum(model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 in y_init:investment_period:y) == sum(model[:x_c][y, geo_i_f] * detour_time_reduction_list[findfirst(
                            item -> item.reduction_id == geo_i_f[2] && item.fuel.id == f_l[1] && item.fueling_type.id == f_l[2] && item.location.id == geo.id,
                            detour_time_reduction_list)].fueling_cap_lb for geo_i_f in geo_i_f_l_pairs if geo_i_f[1] == geo.id && geo_i_f[3] == f_l[1] && geo_i_f[4] == f_l[2]) + 
                            sum(model[:q_fuel_infr_plus_diff][y0, f_l, geo.id] for y0 in y_init:investment_period:y) - init_fueling_infr_list[findfirst(
                            i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo.id,
                            init_fueling_infr_list,
                        )].installed_kW
                    )
                    # @constraint(
                    #     model,
                    #     [y in [2055, 2060], geo in geographic_element_list],
                    #     sum(model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 in y_init:investment_period:y) ==
                    #         sum(model[:q_fuel_infr_plus_diff][y0, f_l, geo.id] for y0 in y_init:investment_period:y)
                    # )

                end
            end
    
        end 
    
    end
end

function constraint_vot_dt(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    p_r_g_k = data_structures["p_r_k_g_pairs"]
    techvehicle_list = data_structures["techvehicle_list"]
    paths = data_structures["path_list"]
    speed_list = data_structures["speed_list"]
    odpair_list = data_structures["odpair_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    mode_list = data_structures["mode_list"]
    g_init = data_structures["g_init"]
    init_detour_times_list = data_structures["init_detour_times_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    detour_time_reduction_list = data_structures["detour_time_reduction_list"]
    investment_period = data_structures["investment_period"]
    investment_years = collect((y_init+ investment_period):investment_period:Y_end)  # List of years where x_c is defined

    M = 50000000

    f_l_for_dt = data_structures["f_l_for_dt"]
    geo_i_f_l_pairs = data_structures["geo_i_f_l"]
    
    for f_l ∈ f_l_for_dt
        for geo in geographic_element_list
            matching_item = init_detour_times_list[findfirst(
                elem -> elem.fuel.id == f_l[1] && elem.fuel_infr_type.id == f_l[2] && elem.location.id == geo.id,
                init_detour_times_list,
            )]
            init_detour_time = matching_item.detour_time
            if findfirst(elem -> elem.fuel.id == f_l[1] && elem.fueling_type.id == f_l[2] && elem.location.id == geo.id, detour_time_reduction_list) != nothing
                selection = detour_time_reduction_list[findall(
                    elem -> elem.fuel.id == f_l[1] && elem.location.id == geo.id && elem.fueling_type.id == f_l[2],
                    detour_time_reduction_list,
                )]
                for item in selection

                    # @constraint(
                    #     model,
                    #     [y in y_init:Y_end, gifl in geo_i_f_l_pairs; gifl[2] == item.reduction_id && gifl[3] == f_l[1] && gifl[4] == f_l[2] && gifl[1] == geo.id],
                    #     model[:vot_dt][y, gifl] <= init_detour_time * (1 - item.detour_time_reduction) *sum(model[:n_fueling][y, (r.product.id, r.id, r.paths[1].id, geo_elem.id), (gifl[3], gifl[4]), g] * r.financial_status.VoT for r in odpair_list for geo_elem in r.paths[1].sequence for p_r_k in p_r_g_k for g in g_init:y if geo_elem.id == gifl[1])
                    # )
                    # @constraint(
                    #     model,
                    #     [y in y_init:Y_end, gifl in geo_i_f_l_pairs; gifl[2] == item.reduction_id && gifl[3] == f_l[1] && gifl[4] == f_l[2] && gifl[1] == geo.id],
                    #     model[:vot_dt][y, gifl] <= M * model[:x_c][maximum([t for t in investment_years if t <= y]; init = y_init), gifl]
                    # )
                    # @constraint(
                    #     model,
                    #     [y in y_init:Y_end, gifl in geo_i_f_l_pairs; gifl[2] == item.reduction_id && gifl[3] == f_l[1] && gifl[4] == f_l[2] && gifl[1] == geo.id],
                    #     model[:vot_dt][y, gifl] >=
                    #     init_detour_time * (1 - item.detour_time_reduction) * sum(model[:n_fueling][y, (r.product.id, r.id, r.paths[1].id, geo_elem.id), (gifl[3], gifl[4]), g] * r.financial_status.VoT for r in odpair_list for geo_elem in r.paths[1].sequence for p_r_k in p_r_g_k for g in g_init:y if geo_elem.id == gifl[1]) - M * (1 - model[:x_c][maximum([t for t in investment_years if t <= y]; init = y_init), gifl] )
                    # )
                    for y in y_init:Y_end
                        for gifl in geo_i_f_l_pairs
                            if gifl[2] == item.reduction_id &&
                               gifl[3] == f_l[1] &&
                               gifl[4] == f_l[2] &&
                               gifl[1] == geo.id
                    
                                t_invest = maximum([t for t in investment_years if t <= y]; init = y_init)
                    
                                @constraint(model,
                                    model[:x_c][t_invest, gifl] --> {
                                        model[:vot_dt][y, gifl] >=
                                            init_detour_time * (1 - item.detour_time_reduction) *
                                            sum(
                                                model[:n_fueling][y, (r.product.id, r.id, r.paths[1].id, geo_elem.id), (gifl[3], gifl[4]), g] * r.financial_status.VoT * 1000
                                                for r in odpair_list
                                                for geo_elem in r.paths[1].sequence
                                                for g in g_init:y
                                                if geo_elem.id == gifl[1]
                                            )
                                    }
                                )
                                #@constraint(model, !model[:x_c][t_invest, gifl] => { model[:vot_dt][y, gifl] == 0 })
                            end
                        end
                    end
                    # @constraint(
                    #     model,
                    #     [y in y_init:Y_end, gifl in geo_i_f_l_pairs;
                    #     gifl[2] == item.reduction_id &&
                    #     gifl[3] == f_l[1] &&
                    #     gifl[4] == f_l[2] &&
                    #     gifl[1] == geo.id],

                    #     !model[:x_c][maximum([t for t in investment_years if t <= y]; init = y_init), gifl] --> {
                    #         model[:vot_dt][y, gifl] == 0
                    #     }
                    # )


                end
                # println([selection[findfirst(
                #             item -> item.reduction_id == g_id[2],
                #             selection,
                #         )].detour_time_reduction for
                #         g_id ∈ geo_i_f_l_pairs if g_id[1] == geo_id && g_id[3] == f_l[1] && g_id[4] == f_l[2]])

            end
        end
    end
end

"""
    constraint_travel_time(model::JuMP.Model, data_structures::Dict)

Defining travel time budget for each route.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_travel_time(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    techvehicle_list = data_structures["techvehicle_list"]
    paths = data_structures["path_list"]
    speed_list = data_structures["speed_list"]
    odpair_list = data_structures["odpair_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    mode_list = data_structures["mode_list"]
    g_init = data_structures["g_init"]
    
    @constraint(
        model,
        [y in y_init:Y_end, r in odpair_list, mv in m_tv_pairs],
        sum(model[:f][y, (r.product.id, r.id, k.id), mv, g] * k.length * (1/ speed_list[findfirst(
            s -> s.region_type.id == r.region_type.id &&
                s.vehicle_type.id == mv[2],
            speed_list,
        )].travel_speed) + mode_list[findfirst(item -> item.id == mv[1], mode_list)].waiting_time * model[:f][y, (r.product.id, r.id, k.id), mv, g] * 2 for k in r.paths for g in g_init:y)
        <= sum(model[:f][y, (r.product.id, r.id, k.id), mv, g] for k in r.paths for g in g_init:y) * r.travel_time_budget
    )
end


function constraint_slow_fast_expansion(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    geographic_element_list = data_structures["geographic_element_list"]
    investment_period = data_structures["investment_period"]
    investment_years = collect((y_init+ investment_period):investment_period:Y_end)  # List of years where x_c is defined
    fuel_list = data_structures["fuel_list"]
    fueling_infr_types_list = data_structures["fueling_infr_types_list"]
    f_l = data_structures["f_l_pairs"]
    ratio = 0.4
    error = 0.3 
    lb = 0.2
    ub = 0.7

    # @constraint(
    #     model,
    #     [y in investment_years, elem in geographic_element_list],
    #     sum(model[:q_fuel_infr_plus][y0, (l.fuel.id, l.id), elem.id]
    #         for y0 in y_init:investment_period:y
    #         for l in fueling_infr_types_list
    #         if l.fueling_type == "public_slow") <= 
    #     ub * sum(model[:q_fuel_infr_plus][y0, (l.fuel.id, l.id), elem.id]
    #         for y0 in y_init:investment_period:y
    #         for l in fueling_infr_types_list
    #         if l.fueling_type == "public_fast")
    # )

    # @constraint(
    #     model,
    #     [y in investment_years, elem in geographic_element_list],
    #     sum(model[:q_fuel_infr_plus][y0, (l.fuel.id, l.id), elem.id]
    #         for y0 in y_init:investment_period:y
    #         for l in fueling_infr_types_list
    #         if l.fueling_type == "public_slow") <= 
    #     lb * sum(model[:q_fuel_infr_plus][y0, (l.fuel.id, l.id), elem.id]
    #         for y0 in y_init:investment_period:y
    #         for l in fueling_infr_types_list
    #         if l.fueling_type == "public_fast")
    # )
     @constraint(model,
        [y in investment_years, elem in geographic_element_list],
        sum(model[:q_fuel_infr_plus][y0, (l.fuel.id, l.id), elem.id]
            for y0 in y_init:investment_period:y
            for l in fueling_infr_types_list
            if l.fueling_type == "public_slow")<= 
         2 * sum(model[:q_fuel_infr_plus][y0, (l.fuel.id, l.id), elem.id]
            for y0 in y_init:investment_period:y
            for l in fueling_infr_types_list
            if l.fueling_type == "public_fast")
     )

    #  @constraint(model,
    #     [y in investment_years, elem in geographic_element_list],
    #     sum(model[:q_fuel_infr_plus][y0, (l.fuel.id, l.id), elem.id]
    #         for y0 in y_init:investment_period:y
    #         for l in fueling_infr_types_list
    #         if l.fueling_type == "public_slow") <= 
    #     (4.6 + 0.2 * 4.6) * sum(model[:q_fuel_infr_plus][y0, (l.fuel.id, l.id), elem.id]
    #         for y0 in y_init:investment_period:y
    #         for l in fueling_infr_types_list
    #         if l.fueling_type == "public_fast")
    #  )

end

function constraint_expansion_speed(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    geographic_element_list = data_structures["geographic_element_list"]
    fuel_list = data_structures["fuel_list"]
    investment_period = data_structures["investment_period"]
    fueling_infr_expansion_list = data_structures["fueling_infr_expansion_list"]
    investment_years = collect((y_init+ investment_period):investment_period:Y_end)  # List of years where x_c is defined
    f_l = data_structures["f_l_pairs"]
    initialfuelinfr_list = data_structures["initialfuelinfr_list"]

    if length(data_structures["fueling_infr_types_list"]) == 0


        # for y == y_init
        @constraint(
            model, 
            [elem in fueling_infr_expansion_list],
            (
                sum(model[:q_fuel_infr_plus][y_init, elem.fuel.id, elem.location.id] ) 
                )
                - initialfuelinfr_list[findfirst(
                    i -> i.fuel.id == elem.fuel.id && i.allocation == elem.location.id,
                    initialfuelinfr_list,
                )].installed_kW
            <=
            elem.alpha *
            sum(initialfuelinfr_list[findfirst(
                i -> i.fuel.id == f0.id && i.allocation == elem.location.id,
                initialfuelinfr_list,
            )].installed_kW + model[:q_fuel_infr_plus][y_init, elem.fuel.id, elem.location.id] for f0 in fuel_list) +
            elem.beta * model[:initialfuelinfr_list[findfirst(
                i -> i.fuel.id == f.id && i.allocation == elem.location.id,
                initialfuelinfr_list,
            )].installed_kW]

        )
        @constraint(
            model, 
            [elem in fueling_infr_expansion_list],
            - (
                sum(model[:q_fuel_infr_plus][y_init, elem.fuel.id, elem.location.id] ) 
                )
                - initialfuelinfr_list[findfirst(
                    i -> i.fuel.id == elem.fuel.id && i.allocation == elem.location.id,
                    initialfuelinfr_list,
                )].installed_kW
            <=
            elem.alpha *
            sum(initialfuelinfr_list[findfirst(
                i -> i.fuel.id == f0.id && i.allocation == elem.location.id,
                initialfuelinfr_list,
            )].installed_kW + model[:q_fuel_infr_plus][y_init, elem.fuel.id, elem.location.id] for f0 in fuel_list) +
            elem.beta * model[:initialfuelinfr_list[findfirst(
                i -> i.fuel.id == f.id && i.allocation == elem.location.id,
                initialfuelinfr_list,
            )].installed_kW]

        )

        # for y > y_init
        @constraint(
            model, 
            [y in investment_years, elem in fueling_infr_expansion_list],
            (
                sum(model[:q_fuel_infr_plus][y0, elem.fuel.id, elem.location.id] for y0 in y_init:investment_years:y) 
                )
                - sum(model[:q_fuel_infr_plus][y0, elem.fuel.id, elem.location.id] for y0 in y_init:investment_years:(y-investment_years))
            <=
            elem.alpha *
            sum(initialfuelinfr_list[findfirst(
                i -> i.fuel.id == f0.id && i.allocation == elem.location.id,
                initialfuelinfr_list,
            )].installed_kW + model[:q_fuel_infr_plus][y0, elem.fuel.id, elem.location.id] for y0 in y_init:investment_years:y for f0 in fuel_list) +
            elem.beta * sum(model[:q_fuel_infr_plus][y0, elem.fuel.id, elem.location.id] for y0 in y_init:(y-investment_years))

        )
        @constraint(
            model, 
            [y in investment_years, elem in fueling_infr_expansion_list],
            - (
                sum(model[:q_fuel_infr_plus][y0, elem.fuel.id, elem.location.id] for y0 in y_init:investment_years:y) 
                )
                - sum(model[:q_fuel_infr_plus][y0, elem.fuel.id, elem.location.id] for y0 in y_init:investment_years:(y-investment_years))
            <=
            elem.alpha *
            sum(initialfuelinfr_list[findfirst(
                i -> i.fuel.id == f0.id && i.allocation == elem.location.id,
                initialfuelinfr_list,
            )].installed_kW + model[:q_fuel_infr_plus][y0, f0.id, elem.location.id] for y0 in y_init:investment_years:y for f0 in fuel_list) +
            elem.beta * sum(model[:q_fuel_infr_plus][y0, elem.fuel.id, elem.location.id] for y0 in y_init:(y-investment_years))

        )

    else
        @constraint(
            model, 
            [elem in fueling_infr_expansion_list],
            (
                sum(model[:q_fuel_infr_plus][y_init, (elem.fuel.id, elem.fuel_infr_type.id), elem.location.id] ) 
                )
                - model[:initialfuelinfr_list[findfirst(
                    i -> i.fuel.id == elem.fuel.id && elem.fuel_infr_type.id == geo.id && i.fuel_infr_type.id == elem.fuel_infr_type.id,
                    initialfuelinfr_list,
                )].installed_kW]
            <=
            elem.alpha *
            sum(:initialfuelinfr_list[findfirst(
                i -> i.fuel.id == f0.id && i.allocation == elem.location.id,
                initialfuelinfr_list,
            )].installed_kW + model[:q_fuel_infr_plus][y_init, f_l, elem.location.id] for f_l in f_l_pairs) +
            elem.beta * model[:initialfuelinfr_list[findfirst(
                i -> i.fuel.id == elem.fuel.id && elem.fuel_infr_type.id == geo.id && i.fuel_infr_type.id == elem.fuel_infr_type.id,
                initialfuelinfr_list,
            )].installed_kW]

        )
        @constraint(
            model, 
            [elem in fueling_infr_expansion_list],
            - (
                sum(model[:q_fuel_infr_plus][y_init, (elem.fuel.id, elem.fuel_infr_type.id), elem.location.id] ) 
                )
                - model[:initialfuelinfr_list[findfirst(
                    i -> i.fuel.id == elem.fuel.id && elem.fuel_infr_type.id == geo.id && i.fuel_infr_type.id == elem.fuel_infr_type.id,
                    initialfuelinfr_list,
                )].installed_kW]
            <=
            elem.alpha *
            sum(initialfuelinfr_list[findfirst(
                i -> i.fuel.id == f0.id && i.allocation == elem.location.id,
                initialfuelinfr_list,
            )].installed_kW + model[:q_fuel_infr_plus][y_init, f_l, elem.location.id] for f_l in f_l_pairs) +
            elem.beta * model[:initialfuelinfr_list[findfirst(
                i -> i.fuel.id == elem.fuel.id && elem.fuel_infr_type.id == geo.id && i.fuel_infr_type.id == elem.fuel_infr_type.id,
                initialfuelinfr_list,
            )].installed_kW]

        )

        # for y > y_init
        @constraint(
            model, 
            [y in investment_years, elem in fueling_infr_expansion_list],
            (
                sum(model[:q_fuel_infr_plus][y0, (elem.fuel.id, elem.fuel_infr_type.id), elem.location.id] for y0 in y_init:investment_years:y) 
                )
                - sum(model[:q_fuel_infr_plus][y0, (elem.fuel.id, elem.fuel_infr_type.id), elem.location.id] for y0 in y_init:investment_years:(y-investment_years))
            <=
            elem.alpha *
            sum(initialfuelinfr_list[findfirst(
                i -> i.fuel.id == f_l[1] && i.fuel_infr_type.id == f_l[2] && i.allocation == elem.location.id,
                initialfuelinfr_list,
            )].installed_kW + model[:q_fuel_infr_plus][y0, f_l, elem.location.id] for y0 in y_init:investment_years:y for f_l in f_l_pairs) +
            elem.beta * sum(model[:q_fuel_infr_plus][y0, (elem.fuel.id, elem.fuel_infr_type.id), elem.location.id] for y0 in y_init:(y-investment_years))

        )
        @constraint(
            model, 
            [y in investment_years, elem in fueling_infr_expansion_list],
            - (
                sum(model[:q_fuel_infr_plus][y0, (elem.fuel.id, elem.fuel_infr_type.id), elem.location.id] for y0 in y_init:investment_years:y) 
                )
                - sum(model[:q_fuel_infr_plus][y0, (elem.fuel.id, elem.fuel_infr_type.id), elem.location.id] for y0 in y_init:investment_years:(y-investment_years))
            <=
            elem.alpha *
            sum(initialfuelinfr_list[findfirst(
                i -> i.fuel.id == f_l[1] && i.fuel_infr_type.id == f_l[2] && i.allocation == elem.location.id,
                initialfuelinfr_list,
            )].installed_kW + model[:q_fuel_infr_plus][y0, f_l, elem.location.id] for y0 in y_init:investment_years:y for f_l in f_l_pairs) +
            elem.beta * sum(model[:q_fuel_infr_plus][y0, (elem.fuel.id, elem.fuel_infr_type.id), elem.location.id] for y0 in y_init:(y-investment_years))

        )
    end 

end

"""
    constraint_trip_ratio(model::JuMP.Model, data_structures::Dict)

Definition of the trip ratio constraints for the optimization model. The trip ratio is defined as the ratio of commuting trips to private trips, relating technology application and trips.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data

"""
function constraint_trip_ratio(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    trip_ratio_list = data_structures["tripratio_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    odpair_list = data_structures["odpair_list"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    geometric_element_list = data_structures["geographic_element_list"]
    techvehicle_list = data_structures["techvehicle_list"]

    for geo in geometric_element_list
        filtered_trip_ratios = filter(trip -> trip["origin"] == geo.name, trip_ratio_list)
        if length(filtered_trip_ratios) > 0
            share_private = filtered_trip_ratios[findfirst(elem -> elem["purpose"] == 2, filtered_trip_ratios)].share
            share_commuting = filtered_trip_ratios[findfirst(elem -> elem["purpose"] == 4, filtered_trip_ratios)].share
            @constraint(model, [y in y_init:Y_end, g in modeled_generations; g <= y],
                share_commuting * sum(model[:h][y, r.id, v.id, g] for r ∈ odpair_list for v ∈ techvehicle_list if r["purpose"] == 4)
                == share_private * sum(model[:h][y, r.id, v.id, g] for r ∈ odpair_list for v ∈ techvehicle_list if r["purpose"] == 2)
            )
        end
    end
end

function constraint_netzero_goal(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    netzero_goal_list = data_structures["netzero_goal_list"]
    odpairs = data_structures["odpair_list"]
    g_init = data_structures["g_init"]
    techvehicle_list = data_structures["techvehicle_list"]

    @constraint(
        model,
        [tv in techvehicle_list, r in odpairs, g_init in g_init:Y_end; tv.fuel.id == 1],
        (model[:h][Y_end, r.id, tv.id, g] <= 0)
    )
end


function constraint_maximum_fueling_infrastructure(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    maximum_fueling_capacity_by_fuel_list = data_structures["maximum_fueling_capacity_by_fuel_list"]
    f_l_pairs = data_structures["f_l_pairs"]
    f_l_by_route = data_structures["f_l_by_route"]
    f_l_not_by_route = data_structures["f_l_pairs"]
    odpairs = data_structures["odpair_list"]
    initialfuelinfr_list = data_structures["initialfuelinginfr_list"]
    investment_period = data_structures["investment_period"]


    for item in maximum_fueling_capacity_by_fuel_list
        fuel = item.fuel
        max_capacity = item.maximum_fueling_capacity
        if findfirst(
                i -> i.fuel.id == fuel.id && i.type.id == item.type.id && i.allocation == item.location.id,
                initialfuelinfr_list,
            ) == nothing
            if item.by_income_class && haskey(model.obj_dict, :q_fuel_infr_plus_by_route)
                @constraint(
                    model,
                    sum(model[:q_fuel_infr_plus_by_route][y, r.id, f_l, item.location.id] for r in odpairs for f_l in f_l_by_route for y in y_init:investment_period:Y_end if r.financial_status.id == item.income_class.id && f_l[1] == fuel.id && f_l[2] == item.type.id) <= max_capacity
                )
            elseif !item.by_income_class
                @constraint(
                    model,
                    sum(model[:q_fuel_infr_plus][y, f_l, item.location.id] for f_l in f_l_not_by_route for y in y_init:investment_period:Y_end if f_l[1] == fuel.id && f_l[2] == item.type.id) <= max_capacity
                )
            end
        else
            init_infr = initialfuelinfr_list[findfirst(
                i -> i.fuel.id == fuel.id && i.type.id == item.type.id && i.allocation == item.location.id,
                initialfuelinfr_list,
            )].installed_kW
            if item.by_income_class && haskey(model.obj_dict, :q_fuel_infr_plus_by_route)
                @constraint(
                    model,
                    sum(model[:q_fuel_infr_plus_by_route][y, r.id, f_l, item.location.id] for r in odpairs for f_l in f_l_by_route for y in y_init:investment_period:Y_end if r.financial_status.id == item.income_class.id &&f_l[1] == fuel.id && f_l[2] == item.type.id) + init_infr <= max_capacity
                )
            elseif !item.by_income_class
                @constraint(
                    model,
                    sum(model[:q_fuel_infr_plus][y, f_l, item.location.id] for f_l in f_l_not_by_route for y in y_init:investment_period:Y_end if f_l[1] == fuel.id && f_l[2] == item.type.id) + init_infr <= max_capacity
                )
            end

        end

    end
end


function constraint_maximum_fueling_infrastructure_by_year(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    maximum_fueling_capacity_by_fuel_by_year_list = data_structures["maximum_fueling_capacity_by_fuel_by_year_list"]
    f_l_pairs = data_structures["f_l_pairs"]
    f_l_by_route = data_structures["f_l_by_route"]
    f_l_not_by_route = data_structures["f_l_pairs"]
    odpairs = data_structures["odpair_list"]
    initialfuelinfr_list = data_structures["initialfuelinginfr_list"]
    investment_period = data_structures["investment_period"]
    fuelinginfr_type_list = data_structures["fueling_infr_types_list"]
    f_l_not_by_route = data_structures["f_l_not_by_route"]  
    f_l_by_route = data_structures["f_l_by_route"]
    odpair_list = data_structures["odpair_list"]
    for item in maximum_fueling_capacity_by_fuel_by_year_list
        fueling_type = item.fueling_type
        max_capacity = item.maximum_capacity
        year = item.year
        l = fueling_type.id
        fuel = fueling_type.fuel
        geo = item.location
        if !item.by_income_class
            if findfirst(
                i -> i.fuel.id == fuel.id && i.type.id == l && i.allocation == geo.id,
                initialfuelinfr_list,
            ) == nothing
                @constraint(
                    model,
                    sum(model[:q_fuel_infr_plus][y, (f_l), item.location.id] for y in y_init:investment_period:year for f_l in f_l_not_by_route if f_l[1] != 1)
                    # +  sum(model[:q_fuel_infr_plus_by_route][y, r.id, (f_l), item.location.id] for r in odpair_list for y in y_init:investment_period:year for f_l in f_l_by_route if f_l[1] != 1) 
                    == max_capacity
                )
            else
                init_infr = 0
                for l in [2, 3]
                    init_infr = initialfuelinfr_list[findfirst(
                        i -> i.fuel.id == fuel.id && i.type.id == l && i.allocation == item.location.id,
                        initialfuelinfr_list,
                    )].installed_kW + init_infr
                end
                @constraint(
                    model,
                    sum(model[:q_fuel_infr_plus][y, (f_l), item.location.id] for y in y_init:investment_period:year for f_l in f_l_not_by_route if f_l[1] != 1)
                    # +  sum(model[:q_fuel_infr_plus_by_route][y, r.id, (f_l), item.location.id] for r in odpair_list for y in y_init:investment_period:year for f_l in f_l_by_route if f_l[1] != 1) + init_infr 
                    == max_capacity
                )
            end
        else
            println("done")
            income_class_id = item.income_class.id

            if haskey(model.obj_dict, :q_fuel_infr_plus_by_route)
                @constraint(
                        model,
                        sum(model[:q_fuel_infr_plus_by_route][y, r.id, (f_l), item.location.id] for y in y_init:investment_period:year for r in odpair_list for f_l in f_l_by_route if r.financial_status.id == income_class_id)
                        == max_capacity
                    )
            end
            # if findfirst(
            #     i -> i.fuel.id == fuel.id && i.type.id == l && i.allocation == geo.id,
            #     initialfuelinfr_list,
            # ) == nothing
                
            # else
            #     init_infr = 0
            #     # for l in [2, 3]
            #     #     init_infr = initialfuelinfr_list[findfirst(
            #     #         i -> i.fuel.id == fuel.id && i.type.id == l && i.allocation == item.location.id,
            #     #         initialfuelinfr_list,
            #     #     )].installed_kW + init_infr
            #     # end
            #     @constraint(
            #         model,
            #         sum(model[:q_fuel_infr_plus_by_route][y, r.id, (f_l), item.location.id] for r in odpair_list for y in y_init:investment_period:year for f_l in f_l_by_route if f_l[1] == 0 && r.financial_status.id == income_class_id) + init_infr 
            #         == max_capacity
            #     )
            # end
        end
    end
end

function constraint_fueling_infrastructure_expansion_shift(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    fueling_infr_expansion_list = data_structures["fueling_infr_expansion_list"]
    investment_period = data_structures["investment_period"]
    investment_years_2 = collect((y_init+ investment_period):investment_period:Y_end)  # List of years where x_c is defined
    investment_years = collect(y_init:investment_period:Y_end)  # List of years where x_c is defined
    initialfuelinfr_list = data_structures["initialfuelinginfr_list"]
    f_l_pairs = data_structures["f_l_not_by_route"]
    f_l_by_route = data_structures["f_l_by_route"]
    geographic_element_list = data_structures["geographic_element_list"]
    alpha = 1.5 * investment_period
    beta = 1.5 * investment_period
    odpair_list = data_structures["odpair_list"]
    # @constraint(
    #     model,
    #     [y in investment_years_2, f_l in f_l_pairs, geo in geographic_element_list],
    #     sum(model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 in y_init:investment_period:y) 
    #     - sum(model[:q_fuel_infr_plus][y0 - investment_period, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period)) <=
    #     alpha * sum(model[:q_fuel_infr_plus][y0, f_l_0, geo.id] for y0 in y_init:investment_period:y for f_l_0 in f_l_pairs) +
    #     beta * sum(model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period))
    # )
    # @constraint(
    #     model,
    #     [y in investment_years_2, f_l in f_l_pairs, geo in geographic_element_list],
    #     - (sum(model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 in y_init:investment_period:y) 
    #     - sum(model[:q_fuel_infr_plus][y0 - investment_period, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period))) <=
    #     alpha * sum(model[:q_fuel_infr_plus][y0, f_l_0, geo.id] for y0 in y_init:investment_period:y for f_l_0 in f_l_pairs) +
    #     beta * sum(model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period))
    # )
    # @constraint(
    #     model,
    #     [y in investment_years_2, geo in geographic_element_list],
    #     sum(model[:q_fuel_infr_plus][y, f_l, geo.id] for f_l in f_l_pairs if f_l[1] != 1) + sum(model[:q_fuel_infr_plus_by_route][y, r.id, f_l, geo.id] for r in odpair_list for f_l in f_l_by_route) <= 1000000 * 2  # Adjusted to allow for growth in infrastructure over time
    # )
    # @constraint(
    #     model,
    #     [geo in geographic_element_list],
    #     sum(model[:q_fuel_infr_plus][2025, f_l, geo.id] for f_l in f_l_pairs if f_l[1] != 1)  + sum(model[:q_fuel_infr_plus_by_route][2025, r.id, f_l, geo.id] for r in odpair_list for f_l in f_l_by_route)  <= 1000000 # Adjusted to allow for growth in infrastructure over time
    # )
    if haskey(model.obj_dict, :q_fuel_infr_plus_by_route)
        @constraint(
            model,
            [geo in geographic_element_list],
            sum(model[:q_fuel_infr_plus][y_init, f_l, geo.id] for f_l in f_l_pairs if f_l[1] != 1 && f_l[2] != 1)
            + sum(model[:q_fuel_infr_plus_by_route][y_init, r.id, f_l, geo.id] for r in odpair_list for f_l in f_l_by_route)
            <= 1000 # Adjusted to allow for growth in infrastructure over time
        )
        investment_years_3 = collect((y_init+ 2*investment_period):investment_period:Y_end)  # List of years where x_c is defined
        @constraint(
            model,
            [y in investment_years_2, geo in geographic_element_list],
            sum(model[:q_fuel_infr_plus][y, f_l, geo.id] for f_l in f_l_pairs if f_l[1] != 1 && f_l[2] != 1)
            + sum(model[:q_fuel_infr_plus_by_route][y, r.id, f_l, geo.id] for r in odpair_list for f_l in f_l_by_route)
            - sum(model[:q_fuel_infr_plus][y-investment_period, f_l, geo.id] for f_l in f_l_pairs if f_l[1] != 1 && f_l[2] != 1)
            - sum(model[:q_fuel_infr_plus_by_route][y-investment_period, r.id, f_l, geo.id] for r in odpair_list for f_l in f_l_by_route)
            <= 0.2 * investment_period * (sum(item.installed_kW for item in initialfuelinfr_list if item.allocation == geo.id && item.fuel.id == 2) + sum(model[:q_fuel_infr_plus][y-investment_period, f_l, geo.id] for f_l in f_l_pairs if f_l[1] != 1 && f_l[2] != 1)
            + sum(model[:q_fuel_infr_plus_by_route][y-investment_period, r.id, f_l, geo.id] for r in odpair_list for f_l in f_l_by_route)
            )# Adjusted to allow for growth in infrastructure over time
        )
    else
        @constraint(
            model,
            [geo in geographic_element_list],
            sum(model[:q_fuel_infr_plus][y_init, f_l, geo.id] for f_l in f_l_pairs if f_l[1] != 1 && f_l[2] != 1)
            <= 1000 # Adjusted to allow for growth in infrastructure over time
        )
        investment_years_3 = collect((y_init+ 2*investment_period):investment_period:Y_end)  # List of years where x_c is defined
        @constraint(
            model,
            [y in investment_years_2, geo in geographic_element_list],
            sum(model[:q_fuel_infr_plus][y, f_l, geo.id] for f_l in f_l_pairs if f_l[1] != 1 && f_l[2] != 1)
            - sum(model[:q_fuel_infr_plus][y-investment_period, f_l, geo.id] for f_l in f_l_pairs if f_l[1] != 1 && f_l[2] != 1)
            <= 0.2 * investment_period * (sum(item.installed_kW for item in initialfuelinfr_list if item.allocation == geo.id && item.fuel.id == 2) + sum(model[:q_fuel_infr_plus][y-investment_period, f_l, geo.id] for f_l in f_l_pairs if f_l[1] != 1 && f_l[2] != 1)
            )# Adjusted to allow for growth in infrastructure over time
        )
    end
    y = y_init
    # for f_l in f_l_pairs
    #     for geo in geographic_element_list
            # @constraint(
            #         model,
            #         model[:q_fuel_infr_plus][y_init, f_l, geo.id] <=
            #         20000
                    
            #     )
            # @constraint(
            #     model,
            #     - model[:q_fuel_infr_plus][y_init, f_l, geo.id] <=
            #     20000
                
            # )
        #     if findfirst(
        #         i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo.id,
        #         initialfuelinfr_list,
        #     ) != nothing
        #         init_infr = initialfuelinfr_list[findfirst(
        #             i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo.id,
        #             initialfuelinfr_list,
        #         )].installed_kW
        #         init_infr_2 = sum(initialfuelinfr_list[findfirst(
        #             i -> i.fuel.id == f_l_0[1] && i.type.id == f_l_0[2] && i.allocation == geo.id,
        #             initialfuelinfr_list,
        #         )].installed_kW for f_l_0 in f_l_pairs if findfirst(
        #             i -> i.fuel.id == f_l_0[1] && i.type.id == f_l_0[2] && i.allocation == geo.id,
        #             initialfuelinfr_list,
        #         ) != nothing)
        #         @constraint(
        #             model,
        #             sum(model[:q_fuel_infr_plus][y_init, f_l, geo.id] + init_infr) - init_infr <=
        #             alpha * (init_infr_2 + (sum(model[:q_fuel_infr_plus][y_init, f_l_0, geo.id] for f_l_0 in f_l_pairs )))
        #             + beta * init_infr 
                    
        #         )
        #         @constraint(
        #             model,
        #             - sum(model[:q_fuel_infr_plus][y_init, f_l, geo.id]  + init_infr -  init_infr ) <=
        #             alpha * (sum(model[:q_fuel_infr_plus][y_init, f_l_0, geo.id] for f_l_0 in f_l_pairs ) + init_infr_2) 
        #             + beta * init_infr 
        #         )       
        #         continue                                                                                                       
        #     else 
        #         @constraint(
        #             model,
        #             sum(model[:q_fuel_infr_plus][y_init, f_l, geo.id]) <=
        #             alpha * sum(model[:q_fuel_infr_plus][y_init, f_l_0, geo.id] for f_l_0 in f_l_pairs) 
                    
        #         )
        #         @constraint(
        #             model,
        #             - sum(model[:q_fuel_infr_plus][y_init, f_l, geo.id]) <=
        #             alpha * sum(model[:q_fuel_infr_plus][y_init, f_l_0, geo.id] for f_l_0 in f_l_pairs) 
        #         )
                
                
        #    end
     #   end
    #end
    f_l_by_route_pairs = data_structures["f_l_by_route"]
    p_r_g_k = data_structures["p_r_k_g_pairs"]
    # odpair_list = data_structures["odpair_list"]

    # @constraint(
    #     model,
    #     [y in investment_years_2, r in odpair_list, f_l in f_l_by_route_pairs, geo in geographic_element_list],
    #     sum(model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 in y_init:investment_period:y) 
    #     - sum(model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period)) <=
    #     beta * sum(model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period))
    # )
    # @constraint(
    #     model,
    #     [y in investment_years_2, r in odpair_list, f_l in f_l_by_route_pairs, geo in geographic_element_list],
    #     sum(model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 in y_init:investment_period:y) 
    #     - sum(model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period)) <=
    #     beta * sum(model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period))
    # )
    
end

function constraint_to_fast_charging(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    f_l_pairs = data_structures["f_l_not_by_route"]
    geographic_elements = data_structures["geographic_element_list"]
    investment_period = data_structures["investment_period"]
    fueling_infr_types_list = data_structures["fueling_infr_types_list"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    techvehicle_list = data_structures["techvehicle_list"]
    for g in modeled_generations
        for v in techvehicle_list
            driving_range_veh = v.tank_capacity[g-g_init+1] * 0.8 * (1/v.spec_cons[g-g_init+1])
            for fuel_infr_type in fueling_infr_types_list
                if fuel_infr_type.fuel.id == v.technology.fuel.id &&
                   fuel_infr_type.fueling_type != "public_fast"
                    for r in odpairs
                        if r.paths[1].length > driving_range_veh
                            print("here")
                            for geo in r.paths[1].sequence
                                @constraint(
                                    model,
                                    [y in y_init:Y_end],
                                    model[:n_fueling][y, (r.product.id, r.id, k.id, geo.id), (fuel_infr_type.fuel.id, fuel_infr_type.id), g] == 0
                                )
                            end
                        end
                    end
                end
            end
        end
    end

end

function constraint_q_fuel_fossil(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    g_init = data_structures["g_init"]
    f_l_pairs = data_structures["f_l_not_by_route"]
    geographic_elements = data_structures["geographic_element_list"]
    investment_period = data_structures["investment_period"]
    @constraint(
        model,
        [y in y_init:investment_period: Y_end, f_l in f_l_pairs, geo in geographic_elements; f_l[1] == 1],
        (model[:q_fuel_infr_plus][y, f_l, geo.id] <= 0)
    )
end

function constraint_soc_max(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    techvehicle_list = data_structures["techvehicle_list"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    f_l_pairs = data_structures["f_l_not_by_route"]
    path_list = data_structures["path_list"]

    # Pre-build path lookup for efficiency
    path_dict = Dict(path.id => path for path in path_list)

    for g in modeled_generations
        @constraint(model, [y in y_init:Y_end, prkg in p_r_k_g_pairs, f_l in f_l_pairs, tv in techvehicle_list; g < y && tv.technology.fuel.id == f_l[1]],  # Changed g <= y to g < y
            model[:soc][y, prkg, tv.id, f_l, g] <= tv.tank_capacity[g-g_init+1] * (
                path_dict[prkg[3]].length / (tv.W[g-g_init+1] * tv.AnnualRange[g-g_init+1])
            ) * 1000 * model[:f][y, (prkg[1], prkg[2], prkg[3]), (tv.vehicle_type.mode.id, tv.id), g]
        )
    end
end

function constraint_soc_track(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    g_init = data_structures["g_init"]
    techvehicle_list = data_structures["techvehicle_list"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    path_list = data_structures["path_list"]
    product_list = data_structures["product_list"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    f_l_pairs = data_structures["f_l_not_by_route"]

    # Pre-build path lookup for efficiency
    path_dict = Dict(path.id => path for path in path_list)

    # Constraint 1: SOC at origin = tank_capacity * num_vehicles + charging at origin
    # geo == origin (prkg[4] is the origin node)
    for y in y_init:Y_end
        for prkg in p_r_k_g_pairs
            path_id = prkg[3]
            geo_id = prkg[4]
            path = path_dict[path_id]

            # Only process if this geo_id is the origin of this path
            if geo_id == path.sequence[1].id
                for tv in techvehicle_list
                    for f_l in f_l_pairs
                        # Check fuel type matches
                        if tv.technology.fuel.id == f_l[1]
                            for g in g_init:min(y-1, Y_end)  # g < y (vehicles operate year after purchase)
                                # Number of vehicles calculated from flow / (capacity * annual_range / path_length)
                                # NOTE: f is scaled by 1/1000, so we multiply by 1000 to get actual vehicles
                                num_vehicles = (
                                    path.length / (tv.W[g-g_init+1] * tv.AnnualRange[g-g_init+1])
                                ) * 1000 * model[:f][y, (prkg[1], prkg[2], prkg[3]), (tv.vehicle_type.mode.id, tv.id), g]

                                # SOC at origin: vehicles start with full tanks
                                # No need to charge at origin - they depart with full batteries
                                @constraint(
                                    model,
                                    model[:soc][y, prkg, tv.id, f_l, g] ==
                                    tv.tank_capacity[g-g_init+1] * num_vehicles
                                )
                            end
                        end
                    end
                end
            end
        end
    end

    # Constraint 2: SOC tracking along the route (geo != origin)
    # SOC[current] = SOC[previous] - energy_consumed * num_vehicles + charging
    for r in odpairs
        p = r.product
        # For each path in this OD pair
        for path in r.paths
            sequence = path.sequence
            nb_in_sequ = length(sequence)

            # For each node along the path (except origin)
            for i in 2:nb_in_sequ
                geo_curr = sequence[i]
                geo_prev = sequence[i-1]
                distance_increment = path.distance_from_previous[i]

                for y in y_init:Y_end
                    for tv in techvehicle_list
                        for f_l in f_l_pairs
                            # Check fuel type matches
                            if tv.technology.fuel.id == f_l[1]
                                for g in g_init:min(y-1, Y_end)  # g < y (vehicles operate year after purchase)
                                    spec_cons = tv.spec_cons[g-g_init+1]
                                    energy_consumed_per_vehicle = distance_increment * spec_cons
                                    # Number of vehicles calculated from flow
                                    # NOTE: f is scaled by 1/1000, so we multiply by 1000 to get actual vehicles
                                    num_vehicles = (
                                        path.length / (tv.W[g-g_init+1] * tv.AnnualRange[g-g_init+1])
                                    ) * 1000 * model[:f][y, (p.id, r.id, path.id), (tv.vehicle_type.mode.id, tv.id), g]

                                    @constraint(
                                        model,
                                        model[:soc][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g] ==
                                        model[:soc][y, (p.id, r.id, path.id, geo_prev.id), tv.id, f_l, g]
                                        - energy_consumed_per_vehicle * num_vehicles
                                        + model[:s][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g] * 1000
                                    )
                                end
                            end
                        end
                    end
                end
            end
        end
    end
end

function constraint_travel_time_track(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    g_init = data_structures["g_init"]
    techvehicle_list = data_structures["techvehicle_list"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    path_list = data_structures["path_list"]
    product_list = data_structures["product_list"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    f_l_pairs = data_structures["f_l_not_by_route"]
    speed_list = data_structures["speed_list"]

    # Pre-build path lookup for efficiency
    path_dict = Dict(path.id => path for path in path_list)

    # Constraint 1: SOC at origin = tank_capacity * num_vehicles + charging at origin
    # geo == origin (prkg[4] is the origin node)
    for y in y_init:Y_end
        for prkg in p_r_k_g_pairs
            path_id = prkg[3]
            geo_id = prkg[4]
            path = path_dict[path_id]

            # Only process if this geo_id is the origin of this path
            if geo_id == path.sequence[1].id
                for tv in techvehicle_list
                    for f_l in f_l_pairs
                        # Check fuel type matches
                        if tv.technology.fuel.id == f_l[1]
                            for g in g_init:min(y-1, Y_end)  # g < y
                                # Number of vehicles calculated from flow / (capacity * annual_range / path_length)
                                @constraint(
                                    model,
                                    model[:travel_time][y, prkg, tv.id, f_l, g] == 0
                                )
                            end
                        end
                    end
                end
            end
        end
    end


    # Constraint 2: SOC tracking along the route (geo != origin)
    # SOC[current] = SOC[previous] - energy_consumed * num_vehicles + charging
    speed = data_structures["speed_list"][1].travel_speed  # Assuming a constant speed for simplicity; modify as needed
    for r in odpairs
        p = r.product
        # For each path in this OD pair
        for path in r.paths
            sequence = path.sequence
            nb_in_sequ = length(sequence)

            # For each node along the path (except origin)
            for i in 2:nb_in_sequ
                geo_curr = sequence[i]
                geo_prev = sequence[i-1]
                distance_increment = path.distance_from_previous[i]

                for y in y_init:Y_end
                    for tv in techvehicle_list
                        for f_l in f_l_pairs
                            # Check fuel type matches
                            if tv.technology.fuel.id == f_l[1]
                                for g in g_init:min(y-1, Y_end)  # g < y
                                    # Total fleet travel time = sum of individual vehicle travel times
                                    # Number of vehicles in this generation
                                    numbers_vehicles = (
                                        path.length / (tv.W[g-g_init+1] * tv.AnnualRange[g-g_init+1])
                                    ) * 1000 * model[:f][y, (p.id, r.id, path.id), (tv.vehicle_type.mode.id, tv.id), g]

                                    # Check if extra_break_time variable exists
                                    if haskey(model.obj_dict, :extra_break_time)
                                        @constraint(
                                            model,
                                            model[:travel_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g] ==
                                            model[:travel_time][y, (p.id, r.id, path.id, geo_prev.id), tv.id, f_l, g]
                                            + (distance_increment / speed) * numbers_vehicles  # Total driving time = (distance/speed) * num_vehicles
                                            + model[:s][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g] * 1000 / tv.peak_fueling[g-g_init+1]  # Total charging time = total_energy (kWh) / power (kW)
                                            + model[:extra_break_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g]  # Additional slack for break time flexibility
                                        )
                                    else
                                        @constraint(
                                            model,
                                            model[:travel_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g] ==
                                            model[:travel_time][y, (p.id, r.id, path.id, geo_prev.id), tv.id, f_l, g]
                                            + (distance_increment / speed) * numbers_vehicles  # Total driving time = (distance/speed) * num_vehicles
                                            + model[:s][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g] * 1000 / tv.peak_fueling[g-g_init+1]  # Total charging time = total_energy (kWh) / power (kW)
                                        )
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
end

function constraint_mandatory_breaks(model::JuMP.Model, data_structures::Dict)
    """
    Enforce mandatory driver break regulations (EU: 4.5h driving → 45min break).

    Ensures that travel_time at break locations accounts for mandatory break duration.
    """

    # Check if mandatory breaks data exists
    if !haskey(data_structures, "mandatory_break_list")
        @info "No mandatory breaks data found. Skipping constraint_mandatory_breaks."
        return
    end

    # Check if travel_time variable exists
    if !haskey(model.obj_dict, :travel_time)
        @warn "travel_time variable not found. Skipping constraint_mandatory_breaks."
        return
    end

    # Extract data
    mandatory_breaks = data_structures["mandatory_break_list"]
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    techvehicle_list = data_structures["techvehicle_list"]
    odpair_list = data_structures["odpair_list"]
    f_l_pairs = data_structures["f_l_not_by_route"]

    # Create lookup: path_id -> list of breaks
    breaks_by_path = Dict{Int, Array{Any,1}}()
    for mb in mandatory_breaks
        if !haskey(breaks_by_path, mb.path_id)
            breaks_by_path[mb.path_id] = []
        end
        push!(breaks_by_path[mb.path_id], mb)
    end

    @info "Adding mandatory breaks constraints for $(length(mandatory_breaks)) breaks on $(length(breaks_by_path)) paths..."

    num_constraints = 0

    # For each OD pair and path with mandatory breaks
    for odpair in odpair_list
        p = odpair.product

        for path in odpair.paths
            # Skip if no breaks required for this path
            if !haskey(breaks_by_path, path.id)
                continue
            end

            breaks_for_path = breaks_by_path[path.id]

            # For each mandatory break on this path
            for mb in breaks_for_path
                break_geo_id = mb.latest_geo_id

                # Verify geo_id exists in path sequence
                geo_found = false
                for geo_element in path.sequence
                    if geo_element.id == break_geo_id
                        geo_found = true
                        break
                    end
                end

                if !geo_found
                    @warn "Break location geo_id=$(break_geo_id) not found in path $(path.id) sequence"
                    continue
                end

                # Add constraint for each year, tech vehicle, fuel-infra pair, generation
                for y in y_init:Y_end
                    for tv in techvehicle_list
                        for f_l in f_l_pairs
                            if tv.technology.fuel.id == f_l[1]
                                for g in g_init:min(y, Y_end)  # g <= y (vehicles purchased in year y can operate in year y)

                                    # Calculate number of vehicles (fleet size)
                                    num_vehicles = (
                                        path.length / (tv.W[g-g_init+1] * tv.AnnualRange[g-g_init+1])
                                    ) * 1000 * model[:f][y, (p.id, odpair.id, path.id), (tv.vehicle_type.mode.id, tv.id), g]

                                    # Minimum travel time per vehicle (includes break)
                                    min_time_per_vehicle = mb.time_with_breaks

                                    # Total fleet minimum travel time
                                    min_fleet_travel_time = min_time_per_vehicle * num_vehicles

                                    # Constraint: travel_time at break location >= minimum time with breaks
                                    @constraint(
                                        model,
                                        model[:travel_time][y, (p.id, odpair.id, path.id, break_geo_id), tv.id, f_l, g]
                                        >= min_fleet_travel_time
                                    )

                                    num_constraints += 1
                                end
                            end
                        end
                    end
                end
            end
        end
    end

    @info "✓ Mandatory breaks constraint added: $(num_constraints) constraints created"
end

function constraint_travel_time(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    g_init = data_structures["g_init"]
    techvehicle_list = data_structures["techvehicle_list"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    path_list = data_structures["path_list"]
    product_list = data_structures["product_list"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    f_l_pairs = data_structures["f_l_not_by_route"]

    
    
end


function constraint_policy_goal(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    techvehicle_list = data_structures["techvehicle_list"]
    modeled_years = data_structures["modeled_years"]

    # Find the first modeled year >= 2050 (or use Y_end if all years < 2050)
    year = findfirst(y -> y >= 2050, modeled_years)
    if year === nothing
        year = Y_end  # If no year >= 2050, use the end year
    else
        year = modeled_years[year]  # Get the actual year value
    end

    for y in year:Y_end, tv in techvehicle_list, r in odpairs, g in modeled_generations
        if g <= y && tv.technology.id == 1
            @constraint(model, model[:h][y, r.id, tv.id, g] == 0)
        end
    end

end

"""

	objective(model::Model, data_structures::Dict)

Definition of the objective function for the optimization model.

# Arguments
- model::Model: JuMP model
- data_structures::Dict: dictionary with the input data
- exclude_detour_time::Bool: whether to exclude detour time from objective (default: false)
- include_components::Dict: dictionary specifying which cost components to include (default: all true)
  Available components:
  - vot_dt: Value of time for detour time
  - budget_penalties: Budget penalty variables
  - fuel_energy_costs: Fuel and energy costs
  - vehicle_capital: Vehicle capital costs
  - vehicle_maintenance: Vehicle maintenance costs (annual and distance-based)
  - fueling_time: Time spent fueling
  - intangible_costs: Value of time for travel
  - detour_time: Detour time costs
  - mode_infr: Mode infrastructure costs
  - fuel_infr: Fuel infrastructure costs
"""
function objective(model::Model, data_structures::Dict, exclude_detour_time::Bool=false)
    @info "  Objective: Initializing data structures..."
    t_obj_start = time()

    # Detect which decision variables are defined in the model
    # This allows us to skip entire loop structures for undefined variables
    has_var = Dict(
        "vot_dt" => haskey(model.obj_dict, :vot_dt),
        "budget_penalty_plus" => haskey(model.obj_dict, :budget_penalty_plus),
        "budget_penalty_minus" => haskey(model.obj_dict, :budget_penalty_minus),
        "budget_penalty_yearly_plus" => haskey(model.obj_dict, :budget_penalty_yearly_plus),
        "budget_penalty_yearly_minus" => haskey(model.obj_dict, :budget_penalty_yearly_minus),
        "s" => haskey(model.obj_dict, :s),
        "h_plus" => haskey(model.obj_dict, :h_plus),
        "h" => haskey(model.obj_dict, :h),
        "f" => haskey(model.obj_dict, :f),
        "n_fueling" => haskey(model.obj_dict, :n_fueling),
        "detour_time" => haskey(model.obj_dict, :detour_time),
        "q_mode_infr_plus" => haskey(model.obj_dict, :q_mode_infr_plus),
        "q_supply_infr_plus" => haskey(model.obj_dict, :q_supply_infr_plus),
        "extra_break_time" => haskey(model.obj_dict, :extra_break_time)
    )

    @info "  Defined decision variables: $(join([k for (k,v) in has_var if v], ", "))"
    @info "  Skipping variables: $(join([k for (k,v) in has_var if !v], ", "))"
    t_obj_start = time()

    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    modeled_generations = data_structures["modeled_generations"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    fuel_list = data_structures["fuel_list"]
    gamma = data_structures["gamma"]
    discount_rate = data_structures["discount_rate"]
    paths = data_structures["path_list"]
    technologies = data_structures["technology_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    p_r_k_e_pairs = data_structures["p_r_k_e_pairs"]
    p_r_k_n_pairs = data_structures["p_r_k_n_pairs"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    geographic_element_list = data_structures["geographic_element_list"]
    geo_elements_in_paths = data_structures["geo_elements_in_paths"]  # Only geographic elements used in paths
    regiontypes = data_structures["regiontype_list"]
    modes = data_structures["mode_list"]
    if length(data_structures["fueling_infr_types_list"]) != 0
       fueling_infr_types_list = data_structures["fueling_infr_types_list"]
    end
    speed_list = data_structures["speed_list"]
    initialfuelinfr_list = data_structures["initialfuelinginfr_list"]
    initialmodeinfr_list = data_structures["initialmodeinfr_list"]
    investment_period = data_structures["investment_period"]
    investment_years = collect(y_init:investment_period:Y_end)  # List of years where x_c is defined
    print(investment_years)
    capital_cost_map = Dict(
        (v.id, y) => v.capital_cost[y-y_init+1] for v ∈ techvehicles for y ∈ y_init:Y_end
    )
    vehicle_subsidy_list = data_structures["vehicle_subsidy_list"]
    fueling_infr_types_list = data_structures["fueling_infr_types_list"]
    do_this = false
    # Initialize the total cost expression
    #total_cost_expr = @expression(model, 0)
    total_cost_expr = AffExpr(0)
    max_coeff = 1

    @info "    ✓ Data structures ready ($(round(time() - t_obj_start, digits=2))s)"
    @info "  Objective: Building cost expression (Y=$(Y_end-y_init+1) years, R=$(length(odpairs)) odpairs, V=$(length(techvehicles)) vehicles)..."
    t_loop_start = time()
    year_count = 0

    # Timing accumulators for each section
    t_vot_dt = 0.0
    t_budget_penalties = 0.0
    t_fuel_energy_costs = 0.0
    t_vehicle_capital = 0.0
    t_vehicle_maintenance = 0.0
    t_fueling_time = 0.0
    t_intangible_costs = 0.0
    t_detour_time = 0.0
    t_mode_infr = 0.0
    t_fuel_infr = 0.0
    t_extra_break_time = 0.0

    # Build the objective function more efficiently
    for y ∈ y_init:Y_end
        year_count += 1
        if year_count % 5 == 0
            elapsed = time() - t_loop_start
            rate = year_count / elapsed
            remaining = (Y_end - y_init + 1 - year_count) / rate
            @info "    Year $(year_count)/$(Y_end-y_init+1): $(round(elapsed, digits=1))s elapsed, ~$(round(remaining, digits=1))s remaining"
            @info "      VoT_DT=$(round(t_vot_dt,digits=1))s | Penalties=$(round(t_budget_penalties,digits=1))s | FuelEnergy=$(round(t_fuel_energy_costs,digits=1))s | VehCap=$(round(t_vehicle_capital,digits=1))s | VehMaint=$(round(t_vehicle_maintenance,digits=1))s | FuelTime=$(round(t_fueling_time,digits=1))s | Intangible=$(round(t_intangible_costs,digits=1))s | Detour=$(round(t_detour_time,digits=1))s | ModeInfr=$(round(t_mode_infr,digits=1))s | FuelInfr=$(round(t_fuel_infr,digits=1))s | ExtraBreak=$(round(t_extra_break_time,digits=1))s"
        end
        discount_factor = 1/((1 + discount_rate)^(y - y_init))

        # VoT DT component - only if vot_dt variable is defined
        t_sec = time()
        if has_var["vot_dt"] && data_structures["geo_i_f_l"] != []
            geo_i_f_pairs = data_structures["geo_i_f_l"]
            for geo_i_f ∈ geo_i_f_pairs
                add_to_expression!(
                    total_cost_expr,
                    model[:vot_dt][y, geo_i_f] * discount_factor
                )
            end
        end
        t_vot_dt += time() - t_sec

        # Budget penalties component - only if budget penalty variables are defined
        t_sec = time()
        if has_var["budget_penalty_plus"] || has_var["budget_penalty_minus"] || has_var["budget_penalty_yearly_plus"] || has_var["budget_penalty_yearly_minus"]
            for r ∈ odpairs
                if has_var["budget_penalty_plus"]
                    add_to_expression!(
                        total_cost_expr,
                        model[:budget_penalty_plus][y, r.id] *
                        data_structures["budget_penalty_plus"] * discount_factor,
                    )
                    max_coeff = max(max_coeff, data_structures["budget_penalty_plus"] * discount_factor)
                end
                if has_var["budget_penalty_minus"]
                    add_to_expression!(
                        total_cost_expr,
                        model[:budget_penalty_minus][y, r.id] *
                        data_structures["budget_penalty_minus"] * discount_factor,
                    )
                    max_coeff = max(max_coeff, data_structures["budget_penalty_plus"] * discount_factor)
                end
                if has_var["budget_penalty_yearly_plus"]
                    add_to_expression!(
                        total_cost_expr,
                        model[:budget_penalty_yearly_plus][y, r.id] *
                        data_structures["budget_penalty_yearly_plus"] * discount_factor * (1/r.financial_status.monetary_budget_purchase_time_horizon),
                    )
                    max_coeff = max(max_coeff, data_structures["budget_penalty_yearly_plus"] * discount_factor * (1/r.financial_status.monetary_budget_purchase_time_horizon))
                end
                if has_var["budget_penalty_yearly_minus"]
                    add_to_expression!(
                        total_cost_expr,
                        model[:budget_penalty_yearly_minus][y, r.id] *
                        data_structures["budget_penalty_yearly_minus"] * discount_factor * (1/r.financial_status.monetary_budget_purchase_time_horizon),
                    )
                    max_coeff = max(max_coeff, data_structures["budget_penalty_yearly_minus"] * discount_factor * (1/r.financial_status.monetary_budget_purchase_time_horizon))
                end
            end
        end
        t_budget_penalties += time() - t_sec

        # Extra break time penalty - penalize slack variable to discourage unnecessary breaks
        t_sec = time()
        if has_var["extra_break_time"] && length(data_structures["fueling_infr_types_list"]) > 0
            # Penalty: Value of Time × extra break time
            # This makes drivers value their time, so extra breaks are only taken when necessary
            f_l_pairs = data_structures["f_l_not_by_route"]
            techvehicle_ids = data_structures["techvehicle_ids"]

            for r ∈ odpairs
                vot = r.financial_status.VoT  # Value of time (€/hour)
                for (p, r_id, k) ∈ p_r_k_pairs
                    if r_id == r.id
                        for geo_id ∈ [geo.id for geo in data_structures["path_list"][findfirst(path -> path.id == k, data_structures["path_list"])].sequence]
                            for tv_id ∈ techvehicle_ids
                                for f_l ∈ f_l_pairs
                                    for g ∈ filter(g -> g <= y, modeled_generations)
                                        # Penalty = VoT × extra_break_time × discount_factor
                                        add_to_expression!(
                                            total_cost_expr,
                                            model[:extra_break_time][y, (p, r_id, k, geo_id), tv_id, f_l, g] * vot * discount_factor
                                        )
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
        t_extra_break_time += time() - t_sec

        # Vehicle and route-specific costs
        # Skip entire section if none of the relevant variables are defined
        if has_var["s"] || has_var["h_plus"] || has_var["h"] || has_var["f"] || has_var["n_fueling"] || has_var["detour_time"]
            t_sec = time()
            t_fuel_energy = 0.0
            t_vehicle_capital = 0.0
            t_vehicle_maintenance = 0.0
            t_fueling_time = 0.0
            t_intangible = 0.0
            t_detour_time = 0.0

            for v ∈ techvehicles
            if findfirst(
                elem -> elem.vehicle_type.id == v.vehicle_type.id && y in elem.years,
                vehicle_subsidy_list
            ) != nothing
                veh_sub = vehicle_subsidy_list[findfirst(
                    elem -> elem.vehicle_type.id == v.vehicle_type.id && y in elem.years,
                    vehicle_subsidy_list
                )]
            else
                veh_sub = 0
            end

            for r ∈ odpairs
                speed =
                    speed_list[findfirst(
                        s ->
                            (s.region_type.id == r.region_type.id) &&
                                (s.vehicle_type.id == v.vehicle_type.id),
                        speed_list,
                    )].travel_speed
                route_length = sum(k.length for k ∈ r.paths)

                
                capital_cost = capital_cost_map[(v.id, y)]



                for g ∈ filter(g -> g <= y, modeled_generations)
                    # Fuel/energy costs (most expensive - deeply nested loops) - only if s variable is defined
                    if has_var["s"]
                        t_fuel_sec = time()
                        fuel_cost_list = data_structures["fuel_cost_list"]
                        for k ∈ r.paths
                            for geo ∈ k.sequence
                                # Get location-specific fuel cost if available, otherwise use base cost
                                location_fuel_cost_idx = findfirst(fc ->
                                    fc.location.id == geo.id && fc.fuel.id == v.technology.fuel.id,
                                    fuel_cost_list
                                )
                                fuel_cost_per_kWh = if location_fuel_cost_idx !== nothing
                                    fuel_cost_list[location_fuel_cost_idx].cost_per_kWh[y-y_init+1]
                                else
                                    v.technology.fuel.cost_per_kWh[y-y_init+1]  # Fallback to base cost
                                end

                                if length(data_structures["fueling_infr_types_list"]) == 0
                                    # Simple mode: no fueling infrastructure types
                                    add_to_expression!(
                                        total_cost_expr,
                                        model[:s][y, (r.product.id, r.id, k.id, geo.id), v.id, g] * (1000) *
                                            (fuel_cost_per_kWh +  10^(-6) *v.technology.fuel.emission_factor[y-y_init+1] *
                                            geo.carbon_price[y-y_init+1]) * discount_factor
                                    )
                                else
                                    # Complex mode: with fueling infrastructure types
                                    f_l_pairs = data_structures["f_l_pairs"]
                                    for f_l in f_l_pairs
                                        if v.technology.fuel.id == f_l[1]
                                            current_fuel_infr_id = findfirst(i ->
                                                i.id == f_l[2],
                                                fueling_infr_types_list,
                                            )
                                            current_fuel_infr = fueling_infr_types_list[current_fuel_infr_id]
                                            add_to_expression!(
                                                total_cost_expr,
                                                model[:s][y, (r.product.id, r.id, k.id, geo.id), v.id, f_l, g] * (1000) *
                                                (current_fuel_infr.cost_per_kWh_network[y-y_init+1] + fuel_cost_per_kWh +  10^(-6) *v.technology.fuel.emission_factor[y-y_init+1] *
                                                geo.carbon_price[y-y_init+1]) * discount_factor
                                            )
                                            max_coeff = max(max_coeff, 1000 * (fuel_cost_per_kWh +  10^(-6) *v.technology.fuel.emission_factor[y-y_init+1] *
                                            geo.carbon_price[y-y_init+1]) * discount_factor)
                                        end
                                    end
                                end
                            end
                        end
                        t_fuel_energy_costs += time() - t_fuel_sec
                    end

                    # Vehicle capital costs - only if h_plus variable is defined
                    if has_var["h_plus"]
                        add_to_expression!(
                            total_cost_expr,
                            model[:h_plus][y, r.id, v.id, y] * (capital_cost - veh_sub),
                        )
                        max_coeff = max(max_coeff, (capital_cost - veh_sub) * discount_factor)
                    end
                    # add_to_expression!(
                    #     total_cost_expr,
                    #     model[:h_minus][y, r.id, v.id, y] * depreciated_inv_costs(capital_cost- veh_sub, y - g) * discount_factor,
                    # )

                    # Vehicle maintenance costs - only if h variable is defined
                    if has_var["h"] && y - g < v.Lifetime[g-g_init+1]
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] *
                            v.maintenance_cost_annual[g-g_init+1][y-g+1] *
                            discount_factor,
                        )
                        # add_to_expression!(
                        #     total_cost_expr,
                        #     model[:h][y, r.id, v.id, g] * regiontypes[findfirst(
                        #         rt -> rt.name == r.region_type.name,
                        #         regiontypes,
                        #     )].costs_fix[y-y+1] * discount_factor,
                        # )
                        max_coeff = max(max_coeff, v.maintenance_cost_annual[g-g_init+1][y-g+1] * discount_factor)
                    end

                    # TODO: add n_fueling by infrastructe 
                    # value of time

                    # the detour time reduction needs to go somewhere else

                    driving_range_veh = v.tank_capacity[g-g_init+1] * 0.8 * (1/v.spec_cons[g-g_init+1])

                    for k ∈ r.paths
                        # adding fueling time - only if n_fueling variable is defined
                        if has_var["n_fueling"] && data_structures["fueling_infr_types_list"] != 0
                            
                            for l ∈ fueling_infr_types_list
                                if l.id == 2
                                    peak_fueling_cap = v.peak_fueling[g-g_init+1]
                                    fueling_time = v.tank_capacity[g-g_init+1] * 0.8/ peak_fueling_cap
                                    # println("fueling_time: ", fueling_time, " ")
                                    
                                    f_l_pairs = data_structures["f_l_pairs"]
                                    for f_l in f_l_pairs
                                        if f_l[1] == v.technology.fuel.id && f_l[2] == l.id
                                            for geo in k.sequence 
                                                add_to_expression!(
                                                total_cost_expr,
                                                model[:n_fueling][y, (r.product.id, r.id, k.id, geo.id), f_l, g] * (1000) * fueling_time * r.financial_status.VoT * discount_factor
                                            )

                                            end
                                            
                                        end
                                    end
                                end
                                if l.id == 4 
                                    fueling_time = 7/60
                                    f_l_pairs = data_structures["f_l_pairs"]
                                    for f_l in f_l_pairs
                                        if f_l[1] == v.technology.fuel.id && f_l[2] == l.id
                                            for geo in k.sequence 
                                                add_to_expression!(
                                                    total_cost_expr,
                                                    model[:n_fueling][y, (r.product.id, r.id, k.id, geo.id), f_l, g] * (1000) * fueling_time * r.financial_status.VoT * discount_factor
                                                )

                                            end
                                        end
                                    end
                                end
                                if l.id == 4 && exclude_detour_time
                                    detour_time = 0.25
                                    f_l_pairs = data_structures["f_l_pairs"]
                                    for f_l in f_l_pairs
                                        if f_l[1] == v.technology.fuel.id && f_l[2] == l.id
                                            for geo in k.sequence 
                                                add_to_expression!(
                                                    total_cost_expr,
                                                    model[:n_fueling][y, (r.product.id, r.id, k.id, geo.id), (v.technology.fuel.id, l.id), g] * (1000) * detour_time * r.financial_status.VoT * discount_factor
                                                )

                                            end
                                        end
                                    end
                                end
                                if (l.id == 2 || l.id == 3) && exclude_detour_time && do_this
                                    f_l_pairs = data_structures["f_l_pairs"]

                                    for f_l in f_l_pairs

                                        if f_l[1] == v.technology.fuel.id && f_l[2] == l.id
                                            for geo in k.sequence 
                                                add_to_expression!(
                                                    total_cost_expr,
                                                    model[:n_fueling][y, (r.product.id, r.id, k.id, geo.id), (v.technology.fuel.id, l.id), g] * (1000) * (5/60) * r.financial_status.VoT * discount_factor
                                                )

                                            end
                                        end
                                    end
                                end
                            end
                        end

                        # Intangible costs and distance-based maintenance - only if f variable is defined
                        if has_var["f"]
                            vot = r.financial_status.VoT
                            los_wo_detour =
                                route_length / speed +
                                v.vehicle_type.mode.waiting_time[y-y_init+1]
                            intangible_costs = vot * los_wo_detour
                            add_to_expression!(
                                total_cost_expr,
                                discount_factor * intangible_costs * 1000 * model[:f][
                                    y,
                                    (r.product.id, r.id, k.id),
                                    (v.vehicle_type.mode.id, v.id),
                                    g,
                                ],
                            )

                            if y - g < v.Lifetime[g-g_init+1]
                                add_to_expression!(
                                    total_cost_expr,
                                    discount_factor * v.maintenance_cost_distance[g-g_init+1][y-g+1] * route_length* 1000 * model[:f][
                                        y,
                                        (r.product.id, r.id, k.id),
                                        (v.vehicle_type.mode.id, v.id),
                                        g,
                                    ] ,
                                )
                            end
                        end
                    end
                end
                # Detour time costs - only if detour_time variable is defined
                if has_var["detour_time"] && length(data_structures["detour_time_reduction_list"]) > 0
                    for k ∈ r.paths
                        for geo ∈ k.sequence
                            if length(data_structures["fueling_infr_types_list"]) == 0
                                add_to_expression!(
                                    total_cost_expr,
                                    discount_factor * model[:detour_time][
                                        y,
                                        (r.product.id, r.id, k.id, geo.id),
                                        v.technology.fuel.id,
                                    ] * r.financial_status.VoT,
                                )
                                max_coeff = max(max_coeff, r.financial_status.VoT * discount_factor)

                            else
                                f_l_for_dt = data_structures["f_l_for_dt"]
                                for f_l in f_l_for_dt
                                    if f_l[1] == v.technology.fuel.id 
                                        add_to_expression!(
                                            total_cost_expr,
                                            discount_factor * model[:detour_time][
                                                y,
                                                (r.product.id, r.id, k.id, geo.id),
                                                f_l,
                                            ] * r.financial_status.VoT, 
                                        )

                                    end
                                end
                            end 
                        end
                    end
                end
            end
        end
        end  # End of vehicle-route-specific costs if block

        # Mode infrastructure costs - only if q_mode_infr_plus variable is defined
        if has_var["q_mode_infr_plus"]
            for m ∈ modes
                for geo ∈ geographic_element_list
                    if y in investment_years
                        add_to_expression!(
                            total_cost_expr,
                            model[:q_mode_infr_plus][y, m.id, geo.id] *
                            m.infrastructure_expansion_costs[y-y_init+1] * discount_factor,
                        )
                        max_coeff = max(max_coeff, m.infrastructure_expansion_costs[y-y_init+1] * discount_factor)
                    end
                for y0 ∈ y_init:y
                    add_to_expression!(
                        total_cost_expr,
                        (
                            initialmodeinfr_list[findfirst(
                                i -> i.mode.id == m.id && i.allocation == geo.id,
                                initialmodeinfr_list,
                            )].installed_ukm + model[:q_mode_infr_plus][maximum(filter(t -> t <= y0, investment_years)), m.id, geo.id]
                        ) * m.infrastructure_om_costs[y-y_init+1] * discount_factor,
                    )
                    max_coeff = max(max_coeff, m.infrastructure_om_costs[y-y_init+1] * discount_factor)
                end
            end
            # if !m.quantify_by_vehs
            #     for mv ∈ m_tv_pairs
            #         if mv[1] == m.id
            #             for r ∈ odpairsconstraint_fueling_infrastructure_expansion_shift
            #                 route_length = sum(k.length for k ∈ r.paths)
            #                 speed = 20
            #                 los = route_length / speed + m.waiting_time[y-y_init+1]
            #                 vot = r.financial_status.VoT
            #                 intangible_costs = vot * los
            #                 for k ∈ r.paths
            #                     for g ∈ g_init:y
            #                         add_to_expression!(
            #                             total_cost_expr,
            #                             model[:f][y, (r.product.id, r.id, k.id), mv, g] * 
            #                             discount_factor * route_length *
            #                             (
            #                                 m.cost_per_ukm[y-y_init+1] * 1000000 +
            #                                 m.emission_factor[y-y_init+1] *
            #                                 10^(-6) * 
            #                                 create_emission_price_along_path(
            #                                     k,
            #                                     y - y_init + 1,
            #                                     data_structures,
            #                                 )
            #                             ),
            #                         )
            #                         add_to_expression!(
            #                             total_cost_expr,
            #                             intangible_costs * 100000 *
            #                             discount_factor * model[:f][y, (r.product.id, r.id, k.id), mv, g],
            #                         )
            #                     end
            #                 end
            #             end
            #         end
            #     end
            # end
        end
        end  # End of mode infrastructure if block

        # Fuel infrastructure costs - only if q_fuel_infr_plus variable is defined
        # Note: This uses different variable names depending on fueling_infr_types_list
        # When empty: q_fuel_infr_plus[y, f.id, geo.id]
        # When not empty: q_fuel_infr_plus[y, f_l, geo.id] where f_l is a tuple
        if haskey(model.obj_dict, :q_fuel_infr_plus)
            for f ∈ fuel_list
                for geo ∈ geo_elements_in_paths  # Only iterate over geographic elements in paths
                    if length(data_structures["fueling_infr_types_list"]) == 0
                        if y in investment_years
                            add_to_expression!(
                                total_cost_expr,
                                model[:q_fuel_infr_plus][y, f.id, geo.id] * f.cost_per_kW[y-y_init+1] * discount_factor,
                            )
                            max_coeff = max(max_coeff, f.cost_per_kW[y-y_init+1] * discount_factor)
                        end
                    for y0 ∈ y_init:y
                        add_to_expression!(
                            total_cost_expr,
                            (
                                initialfuelinfr_list[findfirst(
                                    i -> i.fuel.id == f.id && i.allocation == geo.id,
                                    initialfuelinfr_list,
                                )].installed_kW + model[:q_fuel_infr_plus][maximum(filter(t -> t <= y0, investment_years)), f.id, geo.id]
                            ) * f.fueling_infrastructure_om_costs[y-y_init+1] * discount_factor,
                        )
                        max_coeff = max(max_coeff, f.fueling_infrastructure_om_costs[y-y_init+1] * discount_factor)
                    end                
                else
                    f_l_by_route = data_structures["f_l_by_route"]
                    f_l_not_by_route = data_structures["f_l_not_by_route"]
                    #println("f_l_by_route: ", f_l_by_route)
                    for f_l in f_l_not_by_route
                        fueling_type_item = fueling_infr_types_list[findfirst(item -> item.id == f_l[2], fueling_infr_types_list)]

                        if y in investment_years && f_l[1] == f.id
                            add_to_expression!(
                                total_cost_expr,
                                model[:q_fuel_infr_plus][y, f_l, geo.id] * fueling_type_item.cost_per_kW[y-y_init+1] * discount_factor,
                            )
                            # if f_l in data_structures["f_l_for_dt"]
                                
                            #     add_to_expression!(
                            #         total_cost_expr,
                            #         model[:q_fuel_infr_plus_diff][y, f_l, geo.id] * fueling_type_item.cost_per_kW[y-y_init+1] * 100000,
                            #     )
                            # end
                        end
                        for y0 in y_init:y
                            if findfirst(
                                i -> i.fuel.id == f.id && i.allocation == geo.id,
                                initialfuelinfr_list,
                                ) != nothing
                                add_to_expression!(
                                    total_cost_expr,
                                    (
                                        initialfuelinfr_list[findfirst(
                                            i -> i.fuel.id == f.id && i.allocation == geo.id,
                                            initialfuelinfr_list,
                                        )].installed_kW + model[:q_fuel_infr_plus][maximum(filter(t -> t <= y0, investment_years)), f_l, geo.id]
                                    ) * f.fueling_infrastructure_om_costs[y-y_init+1]  * discount_factor,
                                )

                                max_coeff = max(max_coeff, f.fueling_infrastructure_om_costs[y-y_init+1] * discount_factor)

                                # Add FuelingInfrTypes-specific O&M costs
                                add_to_expression!(
                                    total_cost_expr,
                                    (
                                        initialfuelinfr_list[findfirst(
                                            i -> i.fuel.id == f.id && i.allocation == geo.id,
                                            initialfuelinfr_list,
                                        )].installed_kW + model[:q_fuel_infr_plus][maximum(filter(t -> t <= y0, investment_years)), f_l, geo.id]
                                    ) * fueling_type_item.om_costs[y-y_init+1] * discount_factor,
                                )

                                max_coeff = max(max_coeff, fueling_type_item.om_costs[y-y_init+1] * discount_factor)
                            else
                                add_to_expression!(
                                    total_cost_expr,
                                    (
                                        model[:q_fuel_infr_plus][maximum(filter(t -> t <= y0, investment_years)), f_l, geo.id]
                                    ) * f.fueling_infrastructure_om_costs[y-y_init+1] * discount_factor,
                                )

                                max_coeff = max(max_coeff, f.fueling_infrastructure_om_costs[y-y_init+1] * discount_factor)

                                # Add FuelingInfrTypes-specific O&M costs
                                add_to_expression!(
                                    total_cost_expr,
                                    (
                                        model[:q_fuel_infr_plus][maximum(filter(t -> t <= y0, investment_years)), f_l, geo.id]
                                    ) * fueling_type_item.om_costs[y-y_init+1] * discount_factor,
                                )

                                max_coeff = max(max_coeff, fueling_type_item.om_costs[y-y_init+1] * discount_factor)
                            end
                        end
                    end

                    # Network connection costs for charging infrastructure
                    # These are annual costs (€/kW) for grid connection capacity
                    if length(data_structures["network_connection_costs_list"]) > 0
                        network_costs = data_structures["network_connection_costs_list"]
                        # Find network cost for this location
                        network_cost_idx = findfirst(nc -> nc.location.id == geo.id, network_costs)
                        if network_cost_idx !== nothing
                            network_cost_item = network_costs[network_cost_idx]
                            # Only apply to electricity/charging infrastructure
                            for f_l in f_l_not_by_route
                                if f_l[1] == f.id  # Match the fuel type
                                    # Apply network cost to cumulative installed capacity
                                    for y0 in y_init:y
                                        if findfirst(
                                            i -> i.fuel.id == f.id && i.allocation == geo.id,
                                            initialfuelinfr_list,
                                        ) !== nothing
                                            # Total capacity = initial + all additions up to y0
                                            add_to_expression!(
                                                total_cost_expr,
                                                (
                                                    initialfuelinfr_list[findfirst(
                                                        i -> i.fuel.id == f.id && i.allocation == geo.id,
                                                        initialfuelinfr_list,
                                                    )].installed_kW + model[:q_fuel_infr_plus][maximum(filter(t -> t <= y0, investment_years)), f_l, geo.id]
                                                ) * network_cost_item.network_cost_per_kW[y-y_init+1] * discount_factor,
                                            )
                                            max_coeff = max(max_coeff, network_cost_item.network_cost_per_kW[y-y_init+1] * discount_factor)
                                        else
                                            # Only expansion capacity
                                            add_to_expression!(
                                                total_cost_expr,
                                                model[:q_fuel_infr_plus][maximum(filter(t -> t <= y0, investment_years)), f_l, geo.id] *
                                                network_cost_item.network_cost_per_kW[y-y_init+1] * discount_factor,
                                            )
                                            max_coeff = max(max_coeff, network_cost_item.network_cost_per_kW[y-y_init+1] * discount_factor)
                                        end
                                    end
                                end
                            end
                        end
                    end

                    # Only process by-route infrastructure costs if variable exists
                    if haskey(model.obj_dict, :q_fuel_infr_plus_by_route)
                        for f_l in f_l_by_route
                            fueling_type_item = fueling_infr_types_list[findfirst(item -> item.id == f_l[2], fueling_infr_types_list)]
                            for r in odpairs
                                if y in investment_years && f_l[1] == f.id
                                    add_to_expression!(
                                        total_cost_expr,
                                        model[:q_fuel_infr_plus_by_route][y, r.id, f_l, geo.id] * fueling_type_item.cost_per_kW[y-y_init+1] * discount_factor,
                                    )
                                    max_coeff = max(max_coeff, f.cost_per_kW[y-y_init+1] * discount_factor)
                                end
                                for y0 in y_init:y
                                    add_to_expression!(
                                        total_cost_expr,
                                        model[:q_fuel_infr_plus_by_route][maximum(filter(t -> t <= y0, investment_years)), r.id, f_l, geo.id]
                                        * f.fueling_infrastructure_om_costs[y-y_init+1] * discount_factor,
                                    )
                                end
                            end
                        end
                    end


                end

            end
        end
        end  # End of fuel infrastructure if block

        if data_structures["initialsupplyinfr_list"] !=0
            supplytype_list = data_structures["supplytype_list"]
            initialsupplyinfr_list = data_structures["initialsupplyinfr_list"]
            # for st in supplytype_list
            #     for geo in geographic_element_list
            #         if y in investment_years
            #             add_to_expression!(
            #                 total_cost_expr,
            #                 model[:q_supply_infr_plus][y, st.id, geo.id] * st.install_costs[y-y_init+1] * discount_factor,
            #             )
            #         end
            #         for y0 in y_init:y
            #             add_to_expression!(
            #                 total_cost_expr,
            #                 (
            #                     initialsupplyinfr_list[findfirst(
            #                         i -> i.supplytype.id == st.id && i.allocation == geo.id,
            #                         initialsupplyinfr_list,
            #                     )].installed_kW + model[:q_supply_infr_plus][maximum(filter(t -> t <= y0, investment_years)), st.id, geo.id]
            #                 ) * st.om_costs[y-y_init+1] * discount_factor,
            #             )
            #         end
            #     end
            # end

        end
    end
    # println("Max coefficient: ", max_coeff)

    t_loop_total = time() - t_loop_start
    @info "    ✓ Cost expression built ($(round(t_loop_total, digits=2))s, $(round(t_loop_total/60, digits=2)) minutes)"
    @info "  Objective: Setting objective in JuMP model..."
    t_set_start = time()

    @objective(model, Min, total_cost_expr)

    t_set_total = time() - t_set_start
    t_obj_total = time() - t_obj_start
    @info "    ✓ Objective set in JuMP ($(round(t_set_total, digits=2))s)"
    @info "  ✓ Total objective function time: $(round(t_obj_total, digits=2))s ($(round(t_obj_total/60, digits=2)) minutes)"
end
