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
function base_define_variables(model::Model, data_structures::Dict)
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
    @variable(
        model,
        h[
            y in y_init:Y_end,
            r_id in [r.id for r ∈ odpairs],
            tv_id in techvehicle_ids,
            g in g_init:Y_end;
            g <= y,
        ] >= 0
    )
    @variable(
        model,
        h_exist[
            y in y_init:Y_end,
            r_id in [r.id for r ∈ odpairs],
            tv_id in techvehicle_ids,
            g in g_init:Y_end;
            g <= y,
        ] >= 0
    )
    @variable(
        model,
        h_plus[
            y in y_init:Y_end,
            r_id in [r.id for r ∈ odpairs],
            tv_id in techvehicle_ids,
            g in g_init:Y_end;
            g <= y,
        ] >= 0
    )
    @variable(
        model,
        h_minus[
            y in y_init:Y_end,
            r_id in [r.id for r ∈ odpairs],
            tv_id in techvehicle_ids,
            g in g_init:Y_end;
            g <= y,
        ] >= 0
    )
    if length(data_structures["fueling_infr_types_list"]) == 0
        @variable(model, s[y in y_init:Y_end, p_r_k_g_pairs, tv_id in techvehicle_ids, g in g_init:Yend] >= 0)

        @variable(
            model,
            q_fuel_infr_plus[
                y in collect(y_init:investment_period:Y_end),
                f_id in [f.id for f ∈ fuel_list],
                geo_id in [geo.id for geo ∈ geographic_element_list],
            ] >= 0
        )
        @variable(
            model,
            n_fueling[y in y_init:Y_end, p_r_k_g_pairs, f_id in [f.id for f ∈ fuel_list], g in g_init:Y_end] >= 0
        )#
        if data_structures["detour_time_reduction_list"] != []
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
        f_l_by_route, f_l_not_by_route = create_q_by_route(data_structures)
         @variable(
            model,
            q_fuel_infr_plus[
                y in collect(y_init:investment_period:Y_end),
                f_l in data_structures["f_l_pairs"],
                geo_id in [geo.id for geo ∈ geographic_element_list],
            ] >= 0
        )
        @variable(model, s[y in y_init:Y_end, p_r_k_g in p_r_k_g_pairs, tv_id in techvehicle_ids, f_l in data_structures["f_l_pairs"], g in g_init:Y_end] >= 0)
        @variable(
            model,
            n_fueling[y in y_init:Y_end, p_r_g_k in p_r_k_g_pairs, f_l in data_structures["f_l_pairs"], g in g_init:Y_end] >= 0
        )
        if data_structures["detour_time_reduction_list"] != []
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
    
            @variable(
                model,
                z[y in y_init:Y_end, gif_pair in geo_i_f_l, p_r_k_g in p_r_k_g_pairs] >= 0
            )
            @variable(model, vot_dt[y in y_init:Y_end, gif_pair in geo_i_f_l] >= 0)

        end
    end
    if length(data_structures["fueling_infr_types_list"]) != 0
        f_l_by_route, f_l_not_by_route = create_q_by_route(data_structures)
        data_structures["f_l_by_route"] = f_l_by_route
        data_structures["f_l_not_by_route"] = f_l_not_by_route        
        if length(f_l_by_route) > 0
            @variable(
                model,
                q_fuel_infr_plus_by_route[y in collect(y_init:investment_period:Y_end), r_id in [r.id for r in odpairs],f_l in f_l_by_route, geo_id in [geo.id for geo in geographic_element_list]] >= 0
            )
            unregister(model, :q_fuel_infr_plus)
            # delete!(model, q_fuel_infr_plus)
            @variable(model, q_fuel_infr_plus_diff[y in collect(y_init:investment_period:Y_end), f_l in f_l_for_dt, [geo.id for geo in geographic_element_list]] >= 0)
            @variable(model, q_fuel_infr_plus[y in collect(y_init:investment_period:Y_end), f_l in f_l_not_by_route, [geo.id for geo in geographic_element_list]] >= 0)
            @variable(model, q_fuel_abs[y in y_init:investment_period:Y_end, p_r_k_g_pairs, f_l in f_l_not_by_route, g in g_init:Y_end] >= 0)
        end
    end 
    @variable(
        model,
        f[y in y_init:Y_end, p_r_k_pairs, m_tv_pairs, g in g_init:Y_end; g <= y] >= 0
    )
    @variable(
        model,
        budget_penalty_plus[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs]] >= 0
    )
    @variable(
        model,
        budget_penalty_minus[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs]] >= 0
    )
    @variable(
        model, 
        budget_penalty_yearly_plus[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs]] >= 0
    )
    @variable(
        model, 
        budget_penalty_yearly_minus[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs]] >= 0
    )
    @variable(
        model,
        q_mode_infr_plus[
            y in collect(y_init:investment_period:Y_end),
            m_id in [m.id for m ∈ mode_list],
            geo_id in [geo.id for geo ∈ geographic_element_list],
        ] >= 0
    )

    
    if data_structures["supplytype_list"] != []
        supplytype_list = data_structures["SupplyType"]
        @variable(
            model,
            q_supply_infr[y in collect(y_init:investment_period:Y_end), st_id in [st.id for s ∈ supplytype_list], geo_id in [geo.id for geo ∈ geographic_element_list]] >= 0
        )
    end
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
        model[:h][y, r.id, mv[2], g] == sum(
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

        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] == r.vehicle_stock_init[stock_index].stock
        )

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
    y_init = data_structures["y_init"]
    @constraint(
        model,
        [r in odpairs],
        sum([
            (model[:h_plus][y, r.id, v.id, g] * v.capital_cost[y-y_init+1]) for
            y ∈ data_structures["y_init"]:data_structures["Y_end"] for v ∈ techvehicles for
            g ∈ data_structures["g_init"]:y
        ])* (1/10000) <=
        r.financial_status.monetary_budget_purchase_ub * 
        mean(r.F) * 
        data_structures["Y"] *
        (1 / r.financial_status.monetary_budget_purchase_time_horizon) 
        * (1/10000) + sum(
            model[:budget_penalty_plus][y, r.id] for
            y ∈ data_structures["y_init"]:data_structures["Y_end"]
        )* (1/10000)
    )
    @constraint(
        model,
        [r in odpairs],
        sum([
            (model[:h_plus][y, r.id, v.id, g] * v.capital_cost[y-y_init+1]) for
            y ∈ data_structures["y_init"]:data_structures["Y_end"] for v ∈ techvehicles for
            g ∈ g_init:y
        ]) * (1/10000) >=
        r.financial_status.monetary_budget_purchase_lb *
        mean(r.F) * 
        data_structures["Y"] *
        (1 / r.financial_status.monetary_budget_purchase_time_horizon) * (1/10000)
        - sum(
            model[:budget_penalty_minus][y, r.id] for
            y ∈ data_structures["y_init"]:data_structures["Y_end"]
        ) * (1/10000)
    )

    for r ∈ odpairs
        y_set = generate_exact_length_subsets(
            data_structures["y_init"],
            data_structures["Y_end"],
            r.financial_status.monetary_budget_purchase_time_horizon,
        )
        @constraint(
            model,
            [y0 in y_set],
            sum(
                model[:h_plus][y, r.id, v.id, g] * v.capital_cost[y-y_init+1] for y ∈ y0 for
                v ∈ techvehicles for g ∈ g_init:y
            ) * (1/10000) <=
            r.financial_status.monetary_budget_purchase_ub * mean(
                r.F[(y0[1]-data_structures["y_init"]+1):(y0[1]-data_structures["y_init"]+r.financial_status.monetary_budget_purchase_time_horizon)],
            ) * (1/10000)
            + sum(model[:budget_penalty_yearly_plus][y, r.id] for y ∈ y0) * (1/10000)
        )
        @constraint(
            model,
            [y0 in y_set],
            sum(
                model[:h_plus][y, r.id, v.id, g] * v.capital_cost[y-y_init+1] for y ∈ y0 for
                v ∈ techvehicles for g ∈ g_init:y
            ) * (1/10000) >=
            r.financial_status.monetary_budget_purchase_lb * mean(
                r.F[(y0[1]-data_structures["y_init"]+1):(y0[1]-data_structures["y_init"]+r.financial_status.monetary_budget_purchase_time_horizon)],
            )* (1/10000)
             - sum(model[:budget_penalty_yearly_minus][y, r.id] for y ∈ y0) * (1/10000)
        )
    end

    # # probe: frequency of purchase constraint 
    # nb_of_people_per_household = 2.7    #source wikipedia
    # motorization_rate = 553/1000    #source wikipedia
    
    # trips_per_person_per_day = 3
    # house_hold_trips_per_year = 365 * trips_per_person_per_day * nb_of_people_per_household
    # yearly_trips = trips_per_person_per_day * 365
    # for r ∈ odpairs
    #     y_set = generate_exact_length_subsets(
    #         data_structures["y_init"],
    #         data_structures["Y_end"],
    #         r.financial_status.monetary_budget_purchase_time_horizon,
    #     )
    #     @constraint(
    #         model,
    #         [y0 in y_set],
    #         sum(
    #             model[:h_plus][y, r.id, v.id, g] for y ∈ y0 for
    #             v ∈ techvehicles for g ∈ g_init:y
    #         ) <= 
    #         (1 + 0.3) * (1/r.financial_status.monetary_budget_purchase_time_horizon)
    #     )
    #     @constraint(
    #         model,
    #         [y0 in y_set],
    #         sum(
    #             model[:h_plus][y, r.id, v.id, g] for y ∈ y0 for
    #             v ∈ techvehicles for g ∈ g_init:y
    #         ) >=
    #         (1-0.3) * (1/r.financial_status.monetary_budget_purchase_time_horizon)
    #     )
    # end
    
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
            gamma * 1000 * model[:s][y, p_r_k_g, tv.id, g] for g in g_init:y for p_r_k_g ∈ p_r_k_g_pairs for
            tv ∈ techvehicles if p_r_k_g[4] == geo.id && tv.technology.fuel.name == f.name
        )
    )
    else
        f_l_by_route = data_structures["f_l_by_route"]
        f_l_not_by_route = data_structures["f_l_not_by_route"]
        
        for f_l in f_l_not_by_route 
            gamma_l = fueling_infr_types_list[findfirst(item -> item.id == f_l[2], fueling_infr_types_list)].gamma
            if isa(gamma_l, AbstractVector)
                factor_gamma = [1 / (γ * 8760) for γ in gamma_l]
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
                            factor_gamma[y - data_structures["y_init"] + 1] *1000* model[:s][y, p_r_k_g, tv.id, f_l, g] for g in g_init:y for p_r_k_g ∈ p_r_k_g_pairs for
                            tv ∈ techvehicles if p_r_k_g[4] == geo.id && tv.technology.fuel.id == f_l[1] 
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
                            factor_gamma[y - data_structures["y_init"] + 1] *1000* model[:s][y, p_r_k_g, tv.id, f_l, g] for g in g_init:y for p_r_k_g ∈ p_r_k_g_pairs for
                            tv ∈ techvehicles if p_r_k_g[4] == geo.id && tv.technology.fuel.id == f_l[1]
                        )
                    )
                end
            end
        end
        for f_l in f_l_by_route
            gamma_l = fueling_infr_types_list[findfirst(item -> item.id == f_l[2], fueling_infr_types_list)].gamma
            if isa(gamma_l, AbstractVector)
                factor_gamma = [1 / (γ * 8760) for γ in gamma_l]
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
                            r_id in [r.id for r ∈ data_structures["odpair_list"]],
                        ],
                        sum(
                            model[:q_fuel_infr_plus_by_route][y0, r_id, f_l, geo.id] for y0 ∈ data_structures["y_init"]:investment_period:y
                        ) >= sum(
                            factor_gamma[y - data_structures["y_init"] + 1] *1000* model[:s][y, p_r_k_g, tv.id, f_l, g] for g in g_init:y for p_r_k_g ∈ p_r_k_g_pairs for
                            tv ∈ techvehicles if p_r_k_g[4] == geo.id && tv.technology.fuel.id == f_l[1] && p_r_k_g[2] == r_id 
                        )
                    )
                else
                    @constraint(
                        model,
                        [
                            y in data_structures["y_init"]:data_structures["Y_end"],
                            r_id in [r.id for r ∈ data_structures["odpair_list"]],
                        ],
                        initialfuelinginfr_list[findfirst(
                            i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo.id,
                            initialfuelinginfr_list,
                        )].installed_kW + sum(
                            model[:q_fuel_infr_plus_by_route][y0, r_id, f_l, geo.id] for y0 ∈ data_structures["y_init"]:investment_period:y
                        ) >= sum(
                            factor_gamma[y - data_structures["y_init"] + 1] * 1000* model[:s][y, p_r_k_g, tv.id, f_l, g] for g in g_init:y for p_r_k_g ∈ p_r_k_g_pairs for
                            tv ∈ techvehicles if p_r_k_g[4] == geo.id && tv.technology.fuel.id == f_l[1] && p_r_k_g[2] == r_id 
                        )
                    )
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
                if el == paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence[1] || el == paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence[length(paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence)]
            ) == sum(
                (
                    (v.spec_cons[g-g_init+1]) / v.W[g-g_init+1]  *
                    paths[findfirst(p0 -> p0.id == r_k[2], paths)].length
                ) * model[:f][y, (p.id, r_k[1], r_k[2]), (v.vehicle_type.mode.id, v.id), g] for
                g ∈ g_init:y
            )
        )
    else
        @constraint(
            model,
            [y in y_init:Y_end, p in products, r_k in r_k_pairs, g in g_init:Y_end, v in techvehicles; g <= y],   
            sum(
                model[:s][y, (p.id, r_k[1], r_k[2], el.id), v.id, f_l, g]
                for el in values(paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence) for f_l in f_l_pairs
                if (
                    el.id == odpairs[findfirst(r0 -> r0.id == r_k[1], odpairs)].origin.id ||
                    el.id == odpairs[findfirst(r0 -> r0.id == r_k[1], odpairs)].destination.id
                ) && f_l[1] == v.technology.fuel.id && f_l[2] != 0) 
                + sum(
                model[:s][y, (p.id, r_k[1], r_k[2], el.id), v.id, f_l, g]
                for el in values(paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence) for f_l in f_l_pairs
                if (
                    el.id == odpairs[findfirst(r0 -> r0.id == r_k[1], odpairs)].destination.id
                ) && f_l[1] == v.technology.fuel.id && f_l[2] == 0)     # 0 = work place charging - can only happen at destination
             >= sum(
                (
                    (v.spec_cons[g - g_init + 1]) / v.W[g - g_init + 1] *paths[findfirst(p0 -> p0.id == r_k[2], paths)].length
                ) * model[:f][y, (p.id, r_k[1], r_k[2]), (v.vehicle_type.mode.id, v.id), g]
                for g in g_init:y 
            )
        )
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
            ) == sum(
                (
                    (v.spec_cons[g-g_init+1]) / v.W[g-g_init+1] *
                    paths[findfirst(p0 -> p0.id == r_k[2], paths)].length
                ) * model[:f][y, (p.id, r_k[1], r_k[2]), (v.vehicle_type.mode.id, v.id), g] for
                g ∈ g_init:y
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
            ) == sum(
                (
                    (v.spec_cons[g-g_init+1]) / v.W[g-g_init+1] *
                    paths[findfirst(p0 -> p0.id == r_k[2], paths)].length
                ) * model[:f][y, (p.id, r_k[1], r_k[2]), (v.vehicle_type.mode.id, v.id), g] for
                g ∈ g_init:y
            )
        )
    end
end

function fueling_flexibility(model::JuMP.Model, data_structures::Dict)
    #  
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
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    alpha_h = data_structures["alpha_h_t"]
    beta_h = data_structures["beta_h_t"]
    technologies = data_structures["technology_list"]
    vehicletypes = data_structures["vehicletype_list"]

    # for y = y_init
    @constraint(
        model,
        [r in odpairs, t in technologies],
        (
            sum(
                model[:h][y_init, r.id, tv.id, g] for g ∈ g_init:y_init
                for tv ∈ techvehicles if g <= y_init && tv.technology.id == t.id
            ) - sum(
                model[:h_exist][y_init, r.id, tv.id, g] for g ∈ g_init:y_init
                for tv ∈ techvehicles if g <= y_init - 1 && tv.technology.id == t.id
            )
        ) <=
        alpha_h * sum(
            model[:h][y_init, r.id, tv.id, g] for g ∈ g_init:y_init for
            tv ∈ techvehicles
        ) +
        beta_h * sum(
            model[:h_exist][y_init, r.id, tv.id, g] for
            g ∈ g_init:(y_init-1) for tv ∈ techvehicles if tv.technology.id == t.id
        )
    )

    @constraint(
        model,
        [r in odpairs, t in technologies],
        -(
            sum(
                model[:h][y_init, r.id, tv.id, g] for g ∈ g_init:y_init 
                for tv ∈ techvehicles if g <= y_init && tv.technology.id == t.id
            ) - sum(
                model[:h_exist][y_init, r.id, tv.id, g] for g ∈ g_init:y_init for
                tv ∈ techvehicles if g <= y_init - 1 && tv.technology.id == t.id
            )
        ) <=
        alpha_h * sum(
            model[:h][y_init, r.id, tv.id, g] for g ∈ g_init:y_init for
            tv ∈ techvehicles
        ) +
        beta_h * sum(
            model[:h_exist][y_init, r.id, tv.id, g] for
            g ∈ g_init:(y_init-1) for tv ∈ techvehicles if tv.technology.id == t.id
        )
    )

    # for  y > y_init
    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, t in technologies],
        (
            sum(
                model[:h][y, r.id, tv.id, g] for g ∈ g_init:y for
                tv ∈ techvehicles if tv.technology.id == t.id
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:(y-1) for
                tv ∈ techvehicles if tv.technology.id == t.id
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv.id, g] for g ∈ g_init:y for tv ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:(y-1) for
            tv ∈ techvehicles if tv.technology.id == t.id
        )
    )

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, t in technologies],
        -(
            sum(
                model[:h][y, r.id, tv.id, g] for g ∈ g_init:y for
                tv ∈ techvehicles if tv.technology.id == t.id
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:(y-1) for
                tv ∈ techvehicles if tv.technology.id == t.id
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv.id, g] for g ∈ g_init:y for tv ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:(y-1) for
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
    #             model[:h][y_init, r.id, tv.id, g] for g ∈ g_init:y_init
    #         ) - sum(
    #             model[:h_exist][y_init, r.id, tv.id, g] for g ∈ g_init:(y_init-1)
    #         )
    #     ) <=
    #     alpha_h * sum(
    #         model[:h][y_init, r.id, tv0.id, g] for g ∈ g_init:y_init for tv0 ∈ techvehicles
    #     ) +
    #     beta_h * sum(
    #         model[:h_exist][y_init, r.id, tv.id, g] for
    #         g ∈ g_init:(y_init-1)
    #     )
    # )

    # @constraint(
    #     model,
    #     [r in odpairs, tv in techvehicles],
    #     -(
    #         sum(
    #             model[:h][y_init, r.id, tv.id, g] for g ∈ g_init:y_init
    #         ) - sum(
    #             model[:h_exist][y_init, r.id, tv.id, g] for g ∈ g_init:(y_init-1)
    #         )
    #     ) <=
    #     alpha_h * sum(
    #         model[:h][y_init, r.id, tv0.id, g] for g ∈ g_init:y_init for tv0 ∈ techvehicles
    #     ) +
    #     beta_h * sum(
    #         model[:h_exist][y_init, r.id, tv.id, g] for g ∈ g_init:(y_init-1)
    #     )
    # )

    # for  y > y_init
    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, tv in techvehicles],
        (
            sum(
                model[:h][y, r.id, tv.id, g] for g ∈ g_init:y
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:(y-1)
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv0.id, g] for g ∈ g_init:y for tv0 ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:(y-1)
        )
    )

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, tv in techvehicles],
        -(
            sum(
                model[:h][y, r.id, tv.id, g] for g ∈ g_init:y
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:(y-1) 
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv0.id, g] for g ∈ g_init:y for tv0 ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:(y-1)
        )
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
                mv ∈ m_tv_pairs for g ∈ g_init:y if mv[1] == m.id
            ) - sum(
                model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
                g ∈ g_init:(y-1) for mv ∈ m_tv_pairs if mv[1] == m.id
            )
        ) <=
        alpha_f * sum(
            model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for g ∈ g_init:y
            for mv ∈ m_tv_pairs
        ) +
        beta_f * sum(
            model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
            mv ∈ m_tv_pairs for g ∈ g_init:(y-1) if mv[1] == m.id
        )
    )

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, m in modes],
        -(
            sum(
                model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
                mv ∈ m_tv_pairs for g ∈ g_init:y if mv[1] == m.id
            ) - sum(
                model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
                g ∈ g_init:(y-1) for mv ∈ m_tv_pairs if mv[1] == m.id
            )
        ) <=
        alpha_f * sum(
            model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for g ∈ g_init:y
            for mv ∈ m_tv_pairs
        ) +
        beta_f * sum(
            model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
            mv ∈ m_tv_pairs for g ∈ g_init:(y-1) if mv[1] == m.id
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
    odpairs = data_structures["odpair_list"]

    @constraint(
        model,
        [el in mode_share_list],
        sum(
            model[:f][el.year, (r.product.id, r.id, k.id), mv, g] for p_r_k ∈ p_r_k_pairs
            for mv ∈ m_tv_pairs for k ∈ r.paths for g ∈ g_init:(el.year) if
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
    odpairs = data_structures["odpair_list"]

    @constraint(
        model,
        [el in max_mode_share_list],
        sum(
            model[:f][el.year, (r.product.id, r.id, k.id), mv, g] for p_r_k ∈ p_r_k_pairs
            for mv ∈ m_tv_pairs for k ∈ r.paths for g ∈ g_init:(el.year) if
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
    odpairs = data_structures["odpair_list"]

    @constraint(
        model,
        [el in min_mode_share_list],
        sum(
            model[:f][el.year, (r.product.id, r.id, k.id), mv, g] for p_r_k ∈ p_r_k_pairs
            for mv ∈ m_tv_pairs for k ∈ r.paths for g ∈ g_init:(el.year) if
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
    odpairs = data_structures["odpair_list"]
    #println("market_share_list: ", market_share_list)
    @constraint(
        model,
        [el in market_share_list],
        sum(
            model[:h_plus][el.year, r.id, el.type.id, g] for r ∈ odpairs for
            g ∈ g_init:(el.year)
        ) ==
        el.market_share * sum(
            model[:h_plus][el.year, r.id, tv.id, g] for r ∈ odpairs for
            tv ∈ data_structures["techvehicle_list"] for
            g ∈ g_init:(el.year) if tv.vehicle_type.mode.id == el.type.vehicle_type.mode.id
        )
    )
    # @constraint(
    #     model,
    #     sum(
    #         model[:h][2050, r.id, tv.id, g] for r ∈ odpairs for
    #         g ∈ g_init:2050 for tv ∈ data_structures["techvehicle_list"]
    #         if tv.technology.id == 1
    #     ) <=
    #     0 
    # )
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
    emission_constraints_by_mode_list = data_structures["emission_constraints_by_mode_list"]
    mode_list = data_structures["mode_list"]
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
                    model[:f][y, (r.product.id, r.id, k.id), mv, g] *
                    sum(k.length for k ∈ r.paths) *
                    m.emission_factor *
                    10^(-3) for r ∈ odpairs for k ∈ r.paths for g ∈ g_init:y
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

    if length(data_structures["fueling_infr_types_list"]) == 0

        @constraint(
            model,
            [y in y_init:Y_end, p_r_k_g in p_r_k_g_pairs, f in fuel_list, g in g_init:Y_end; g <= y],
            model[:n_fueling][y, p_r_k_g, f.id, g] >= sum(
                (1 / tv.tank_capacity[1]) * model[:s][y, p_r_k_g, tv.id, g] for
                tv ∈ techvehicle_list if tv.technology.fuel.id == f.id
            )
        )
    else
        @constraint(
            model,
            [y in y_init:Y_end, p_r_k_g in p_r_k_g_pairs, f_l in f_l_pairs, g in g_init:Y_end; g<= y],
            model[:n_fueling][y, p_r_k_g, f_l, g] >= 
                sum((1 / tv.tank_capacity[g-g_init + 1]) * model[:s][y, p_r_k_g, tv.id, f_l, g] for tv in techvehicle_list if tv.technology.fuel.id == f_l[1])
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
                    println("No detour time reduction found for fuel: ", f_l[1], " and fueling type: ", f_l[2], " at location: ", geo_id)
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
                    @constraint(
                        model,
                        [y in y_init:Y_end],
                        model[:detour_time][y, p_r_k_g, f_l] ==
                        0
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
                println("No detour time reduction found for fuel: ", f_l[1], " and fueling type: ", f_l[2], " at location: ", geo_id)
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
        # for y == y_init
        @constraint(model, [y in y_init:investment_period:Y_end, geo in geographic_element_list, f in fuel_list], sum(model[:x_c][y, geo_i_f] for geo_i_f ∈ geo_id_pairs if geo_i_f[1] == geo.id && geo_i_f[3] == f.id) == 1)

    else
        # for y == y_init
        geo_i_f_l_pairs = data_structures["geo_i_f_l"]
        f_l_for_dt = data_structures["f_l_for_dt"]
        println(f_l_for_dt)
        println(geo_i_f_l_pairs)
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
                init_detour_time = init_detour_times_list[findfirst(
                    elem -> elem.fuel.id == f_l[1] && elem.fuel_infr_type.id == f_l[2],
                    init_detour_times_list,
                )].detour_time
                if findfirst(elem -> elem.fuel.id == f_l[1] && elem.fueling_type.id == f_l[2], detour_time_reduction_list) != nothing
                    @constraint(
                        model,
                        [y in y_range, geo in geographic_element_list],
                        sum(model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 in y_init:investment_period:y) == sum(model[:x_c][y, geo_i_f] * detour_time_reduction_list[findfirst(
                            item -> item.reduction_id == geo_i_f[2] && item.fuel.id == f_l[1] && item.fueling_type.id == f_l[2] && item.location.id == geo.id,
                            detour_time_reduction_list)].fueling_cap_lb for geo_i_f in geo_i_f_l_pairs if geo_i_f[1] == geo.id && geo_i_f[3] == f_l[1] && geo_i_f[4] == f_l[2]) + 
                            sum(model[:q_fuel_infr_plus_diff][y0, f_l, geo.id] for y0 in y_init:investment_period:y)
                    )
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
                                                for p_r_k in p_r_g_k
                                                for g in g_init:y
                                                if geo_elem.id == gifl[1]
                                            )
                                    }
                                )
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

    @constraint(
        model,
        [y in investment_years, elem in geographic_element_list],
        sum(model[:q_fuel_infr_plus][y0, (l.fuel.id, l.id), elem.id]
            for y0 in y_init:investment_period:y
            for l in fueling_infr_types_list
            if l.fueling_type == "public_slow") <= 
        lb * sum(model[:q_fuel_infr_plus][y0, (l.fuel.id, l.id), elem.id]
            for y0 in y_init:investment_period:y
            for l in fueling_infr_types_list
            if l.fueling_type == "public_fast")
    )

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
    geometric_element_list = data_structures["geographic_element_list"]
    techvehicle_list = data_structures["techvehicle_list"]

    for geo in geometric_element_list
        filtered_trip_ratios = filter(trip -> trip["origin"] == geo.name, trip_ratio_list)
        if length(filtered_trip_ratios) > 0
            share_private = filtered_trip_ratios[findfirst(elem -> elem["purpose"] == 2, filtered_trip_ratios)].share
            share_commuting = filtered_trip_ratios[findfirst(elem -> elem["purpose"] == 4, filtered_trip_ratios)].share
            @constraint(model, [y in y_init:Y_end, g in g_init:Y_end; g <= y],
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
        (model[:h][2050, r.id, tv.id, g] <= 0)
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
            if item.by_income_class
                @constraint(
                    model,
                    sum(model[:q_fuel_infr_plus_by_route][y, r.id, f_l, item.location.id] for r in odpairs for f_l in f_l_by_route for y in y_init:investment_period:Y_end if r.financial_status.id == item.income_class.id &&f_l[1] == fuel.id && f_l[2] == item.type.id) <= max_capacity
                )
            else 
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
            if item.by_income_class
                @constraint(
                    model,
                    sum(model[:q_fuel_infr_plus_by_route][y, r.id, f_l, item.location.id] for r in odpairs for f_l in f_l_by_route for y in y_init:investment_period:Y_end if r.financial_status.id == item.income_class.id &&f_l[1] == fuel.id && f_l[2] == item.type.id) + init_infr <= max_capacity 
                )
            else 
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

    for item in maximum_fueling_capacity_by_fuel_by_year_list
        fueling_type = item.fueling_type
        max_capacity = item.maximum_capacity
        year = item.year
        fuel = fueling_type.fuel
        l = fueling_type.id
        if findfirst(
            i -> i.fuel.id == fuel.id && i.type.id == l && i.allocation == item.location.id,
            initialfuelinfr_list,
        ) == nothing
            @constraint(
                model,
                sum(model[:q_fuel_infr_plus][y, (fuel.id, l), item.location.id] for y in y_init:investment_period:year) == max_capacity
            )
        else
            init_infr = initialfuelinfr_list[findfirst(
                i -> i.fuel.id == fuel.id && i.type.id == l && i.allocation == item.location.id,
                initialfuelinfr_list,
            )].installed_kW
            @constraint(
                model,
                sum(model[:q_fuel_infr_plus][y, (fuel.id, l), item.location.id] for y in y_init:investment_period:year) + init_infr == max_capacity
            )
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
    geographic_element_list = data_structures["geographic_element_list"]
    alpha = 0.1 * investment_period
    beta = 0.1 * investment_period
    @constraint(
        model,
        [y in investment_years_2, f_l in f_l_pairs, geo in geographic_element_list],
        sum(model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 in y_init:investment_period:y) 
        - sum(model[:q_fuel_infr_plus][y0 - investment_period, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period)) <=
        alpha * sum(model[:q_fuel_infr_plus][y0, f_l_0, geo.id] for y0 in y_init:investment_period:y for f_l_0 in f_l_pairs) +
        beta * sum(model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period))
    )
    @constraint(
        model,
        [y in investment_years_2, f_l in f_l_pairs, geo in geographic_element_list],
        - (sum(model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 in y_init:investment_period:y) 
        - sum(model[:q_fuel_infr_plus][y0 - investment_period, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period))) <=
        alpha * sum(model[:q_fuel_infr_plus][y0, f_l_0, geo.id] for y0 in y_init:investment_period:y for f_l_0 in f_l_pairs) +
        beta * sum(model[:q_fuel_infr_plus][y0, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period))
    )
    # y = y_init

    for f_l in f_l_pairs
        for geo in geographic_element_list
            if findfirst(
                i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo.id,
                initialfuelinfr_list,
            ) != nothing
                init_infr = initialfuelinfr_list[findfirst(
                    i -> i.fuel.id == f_l[1] && i.type.id == f_l[2] && i.allocation == geo.id,
                    initialfuelinfr_list,
                )].installed_kW
                init_infr_2 = sum(initialfuelinfr_list[findfirst(
                    i -> i.fuel.id == f_l_0[1] && i.type.id == f_l_0[2] && i.allocation == geo.id,
                    initialfuelinfr_list,
                )].installed_kW for f_l_0 in f_l_pairs if findfirst(
                    i -> i.fuel.id == f_l_0[1] && i.type.id == f_l_0[2] && i.allocation == geo.id,
                    initialfuelinfr_list,
                ) != nothing)
                @constraint(
                    model,
                    sum(model[:q_fuel_infr_plus][y_init, f_l, geo.id] + init_infr) - init_infr <=
                    alpha * (init_infr_2 + (sum(model[:q_fuel_infr_plus][y_init, f_l_0, geo.id] for f_l_0 in f_l_pairs ))) 
                    
                )
                @constraint(
                    model,
                    - sum(model[:q_fuel_infr_plus][y_init, f_l, geo.id]  + init_infr -  init_infr ) <=
                    alpha * (sum(model[:q_fuel_infr_plus][y_init, f_l_0, geo.id] for f_l_0 in f_l_pairs ) + init_infr_2) 
                )
            else 
                @constraint(
                    model,
                    sum(model[:q_fuel_infr_plus][y_init, f_l, geo.id]) <=
                    alpha * sum(model[:q_fuel_infr_plus][y_init, f_l_0, geo.id] for f_l_0 in f_l_pairs) 
                )
                @constraint(
                    model,
                    - sum(model[:q_fuel_infr_plus][y_init, f_l, geo.id]) <=
                    alpha * sum(model[:q_fuel_infr_plus][y_init, f_l_0, geo.id] for f_l_0 in f_l_pairs) 
                )
            end
        end
    end
    f_l_by_route_pairs = data_structures["f_l_by_route"]
    p_r_g_k = data_structures["p_r_k_g_pairs"]
    odpair_list = data_structures["odpair_list"]

    @constraint(
        model,
        [y in investment_years_2, r in odpair_list, f_l in f_l_by_route_pairs, geo in geographic_element_list],
        sum(model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 in y_init:investment_period:y) 
        - sum(model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period)) <=
        beta * sum(model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period))
    )
    @constraint(
        model,
        [y in investment_years_2, r in odpair_list, f_l in f_l_by_route_pairs, geo in geographic_element_list],
        sum(model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 in y_init:investment_period:y) 
        - sum(model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period)) <=
        beta * sum(model[:q_fuel_infr_plus_by_route][y0, r.id, f_l, geo.id] for y0 in (y_init+investment_period):investment_period:(y-investment_period))
    )
    
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


function constraint_policy_goal(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    g_init = data_structures["g_init"]
    techvehicle_list = data_structures["techvehicle_list"]
    year = 2050 
    
    @constraint(
            model,
            [y in year:Y_end, tv in techvehicle_list, r in odpairs, g in g_init:Y_end; g <= y && tv.technology.id == 1],
            (model[:h][y, r.id, tv.id, g]  <= 0)
        )
end

"""

	objective(model::Model, data_structures::Dict)

Definition of the objective function for the optimization model.

# Arguments
- model::Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function objective(model::Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
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

    # Initialize the total cost expression
    #total_cost_expr = @expression(model, 0)
    total_cost_expr = AffExpr(0)
    max_coeff = 1
    scale_factor = (1/1)
    # Build the objective function more efficiently
    for y ∈ y_init:Y_end
        discount_factor = 1/((1 + discount_rate)^(y - y_init))

        if data_structures["geo_i_f_l"] != []
            geo_i_f_pairs = data_structures["geo_i_f_l"]
            for geo_i_f ∈ geo_i_f_pairs
                add_to_expression!(
                    total_cost_expr,
                    model[:vot_dt][y, geo_i_f] * discount_factor
                )
            end
        end
        # discount_factor = 1
        # println(discount_factor)
        for r ∈ odpairs
            add_to_expression!(
                total_cost_expr,
                model[:budget_penalty_plus][y, r.id] *
                data_structures["budget_penalty_plus"] * discount_factor,
            )
            max_coeff = max(max_coeff, data_structures["budget_penalty_plus"] * discount_factor)
            add_to_expression!(
                total_cost_expr,
                model[:budget_penalty_minus][y, r.id] *
                data_structures["budget_penalty_minus"] * discount_factor * scale_factor,
            )
            max_coeff = max(max_coeff, data_structures["budget_penalty_plus"] * discount_factor)

            add_to_expression!(
                total_cost_expr,
                model[:budget_penalty_yearly_plus][y, r.id] *
                data_structures["budget_penalty_yearly_plus"] * discount_factor * (1/r.financial_status.monetary_budget_purchase_time_horizon) * scale_factor,
            )
            max_coeff = max(max_coeff, data_structures["budget_penalty_yearly_plus"] * discount_factor * (1/r.financial_status.monetary_budget_purchase_time_horizon))
            add_to_expression!(
                total_cost_expr,
                model[:budget_penalty_yearly_minus][y, r.id] *
                data_structures["budget_penalty_yearly_minus"] * discount_factor * (1/r.financial_status.monetary_budget_purchase_time_horizon) * scale_factor,
            )
            max_coeff = max(max_coeff, data_structures["budget_penalty_yearly_minus"] * discount_factor * (1/r.financial_status.monetary_budget_purchase_time_horizon))
        end
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

                

                for g ∈ g_init:y
                    for k ∈ r.paths
                        for geo ∈ k.sequence
                            if length(data_structures["fueling_infr_types_list"]) == 0
                                fuel_cost = geo.fuel_cost[y-y_init+1]
                                add_to_expression!(
                                    total_cost_expr,
                                    model[:s][y, (r.product.id, r.id, k.id, geo.id), v.id, g] * (1000) *
                                        (v.technology.fuel.cost_per_kWh[y-y_init+1] +  10^(-6) *v.technology.fuel.emission_factor[y-y_init+1] *
                                        geo.carbon_price[y-y_init+1]) * discount_factor * scale_factor
                                    
                                )
                                max_coeff = max(max_coeff, (v.technology.fuel.cost_per_kWh[y-y_init+1] +  10^(-6) *v.technology.fuel.emission_factor[y-y_init+1] *
                                        geo.carbon_price[y-y_init+1]) * discount_factor * scale_factor)
                            else
                                f_l_pairs = data_structures["f_l_pairs"]
                                for f_l in f_l_pairs
                                    if v.technology.fuel.id == f_l[1]
                                        # println(length(v.technology.fuel.cost_per_kWh), " ", length(v.technology.fuel.emission_factor), " ", length(geo.carbon_price))
                                        l = v.technology.fuel.cost_per_kWh[y-y_init+1]
                                        l = v.technology.fuel.emission_factor[y-y_init+1]
                                        l = geo.carbon_price[y-y_init+1]
                                        add_to_expression!(
                                        total_cost_expr,
                                        model[:s][y, (r.product.id, r.id, k.id, geo.id), v.id, f_l, g] * (1000) *
                                        (v.technology.fuel.cost_per_kWh[y-y_init+1] +  10^(-6) *v.technology.fuel.emission_factor[y-y_init+1] *
                                        geo.carbon_price[y-y_init+1]) * discount_factor * scale_factor
                                    )
                                        max_coeff = max(max_coeff, 1000 * (v.technology.fuel.cost_per_kWh[y-y_init+1] +  10^(-6) *v.technology.fuel.emission_factor[y-y_init+1] *
                                        geo.carbon_price[y-y_init+1]) * discount_factor * scale_factor  )

                                    end 
                                end
                            end
                        end
                    end
                    add_to_expression!(
                        total_cost_expr,
                        model[:h_plus][y, r.id, v.id, y] * (capital_cost - veh_sub)* discount_factor * scale_factor,
                    )
                    max_coeff = max(max_coeff, (capital_cost - veh_sub) * discount_factor)
                    # add_to_expression!(
                    #     total_cost_expr,
                    #     model[:h_minus][y, r.id, v.id, y] * depreciated_inv_costs(capital_cost- veh_sub, y - g) * discount_factor,
                    # )

                    if y - g < v.Lifetime[g-g_init+1]
                        # println(length(v.maintenance_cost_annual[g-g_init+1]), " ",  length(v.maintenance_cost_annua))
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] *
                            v.maintenance_cost_annual[g-g_init+1][y-g+1] * 
                            discount_factor * scale_factor,
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

                    driving_range_veh = v.tank_capacity[g-g_init+1] * (1/v.spec_cons[g-g_init+1])
                    
                    for k ∈ r.paths
                        # adding fueling time 
                        if data_structures["fueling_infr_types_list"] != 0
                            
                            for l ∈ fueling_infr_types_list
                                if l.additional_fueling_time
                                    peak_fueling_cap = v.peak_fueling[g-g_init+1]
                                    fueling_time = v.tank_capacity[g-g_init+1] / peak_fueling_cap
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
                                                    model[:n_fueling][y, (r.product.id, r.id, k.id, geo.id), (v.technology.fuel.id, l.id), g] * (1000) * fueling_time * r.financial_status.VoT * discount_factor
                                                )

                                            end
                                        end
                                    end
                                elseif l.id == 3
                                    fueling_time = 4/60
                                    f_l_pairs = data_structures["f_l_pairs"]
                                    for f_l in f_l_pairs

                                        if f_l[1] == v.technology.fuel.id && f_l[2] == l.id
                                            for geo in k.sequence 
                                                add_to_expression!(
                                                    total_cost_expr,
                                                    model[:n_fueling][y, (r.product.id, r.id, k.id, geo.id), (v.technology.fuel.id, l.id), g] * (1000) * fueling_time * r.financial_status.VoT * discount_factor * scale_factor
                                                )
                                                max_coeff = max(max_coeff, (1000) * fueling_time * r.financial_status.VoT * discount_factor)

                                            end
                                        end
                                    end
                                end
                            end
                        end
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
                if length(data_structures["detour_time_reduction_list"]) > 0
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
            #             for r ∈ odpairs
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
        for f ∈ fuel_list
            for geo ∈ geographic_element_list
                if data_structures["fueling_infr_types_list"] == 0
                    if y in investment_years
                        add_to_expression!(
                            total_cost_expr,
                            model[:q_fuel_infr_plus][y, f.id, geo.id] * f.cost_per_kW[y-y_init+1] * discount_factor * scale_factor,
                        )
                        max_coeff = max(max_coeff, f.cost_per_kW[y-y_init+1] * discount_factor * scale_factor)
                    end
                    for y0 ∈ y_init:y
                        add_to_expression!(
                            total_cost_expr,
                            (
                                initialfuelinfr_list[findfirst(
                                    i -> i.fuel.id == f.id && i.allocation == geo.id,
                                    initialfuelinfr_list,
                                )].installed_kW + model[:q_fuel_infr_plus][maximum(filter(t -> t <= y0, investment_years)), f.id, geo.id]
                            ) * f.fueling_infrastructure_om_costs[y-y_init+1] * discount_factor * scale_factor,
                        )
                        max_coeff = max(max_coeff, f.fueling_infrastructure_om_costs[y-y_init+1] * discount_factor)
                    end                
                else
                    f_l_by_route = data_structures["f_l_by_route"]
                    f_l_not_by_route = data_structures["f_l_not_by_route"]
                    println("f_l_by_route: ", f_l_by_route)
                    for f_l in f_l_not_by_route
                        if y in investment_years && f_l[1] == f.id
                            add_to_expression!(
                                total_cost_expr,
                                model[:q_fuel_infr_plus][y, f_l, geo.id] * f.cost_per_kW[y-y_init+1] * discount_factor,
                            )
                            max_coeff = max(max_coeff, f.cost_per_kW[y-y_init+1] * discount_factor)
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
                            else
                                add_to_expression!(
                                    total_cost_expr,
                                    (
                                        model[:q_fuel_infr_plus][maximum(filter(t -> t <= y0, investment_years)), f_l, geo.id]
                                    ) * f.fueling_infrastructure_om_costs[y-y_init+1] * discount_factor,
                                )
                                max_coeff = max(max_coeff, f.fueling_infrastructure_om_costs[y-y_init+1] * discount_factor)
                            end
                        end
                    end
                
                    for f_l in f_l_by_route
                        for r in odpairs
                            if y in investment_years && f_l[1] == f.id
                                add_to_expression!(
                                    total_cost_expr,
                                    model[:q_fuel_infr_plus_by_route][y, r.id, f_l, geo.id] * f.cost_per_kW[y-y_init+1] * discount_factor,
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
    println("Max coefficient: ", max_coeff)
    @objective(model, Min, total_cost_expr)
end
