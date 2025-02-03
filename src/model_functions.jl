"""

    This file contains functions relating to the mathematical formulation of the model, i.e., the definition of constraints and the objective function, including also the definition of decision variables.

"""

using YAML, JuMP, Gurobi
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
    @info m_tv_pairs
    techvehicle_ids =
        create_tv_id_set(data_structures["techvehicle_list"], data_structures["mode_list"])
    t_v_pairs = create_v_t_set(data_structures["techvehicle_list"])
    p_r_k_pairs = create_p_r_k_set(data_structures["odpair_list"])
    p_r_k_e_pairs = create_p_r_k_e_set(data_structures["odpair_list"])
    p_r_k_n_pairs = create_p_r_k_n_set(data_structures["odpair_list"])
    p_r_k_g_pairs = create_p_r_k_g_set(data_structures["odpair_list"])
    if haskey(data_structures, "detour_time_reduction_list")
        geo_i_f_pairs = create_geo_i_f_pairs(
            data_structures["geographic_element_list"],
            data_structures["detour_time_reduction_list"],
        )
        println("geo_i_f_pairs", geo_i_f_pairs)
    end 
    println(m_tv_pairs)

    data_structures["m_tv_pairs"] = m_tv_pairs
    data_structures["techvehicle_ids"] = techvehicle_ids
    data_structures["t_v_pairs"] = t_v_pairs
    data_structures["p_r_k_pairs"] = p_r_k_pairs
    data_structures["p_r_k_e_pairs"] = p_r_k_e_pairs
    data_structures["p_r_k_n_pairs"] = p_r_k_n_pairs
    data_structures["p_r_k_g_pairs"] = p_r_k_g_pairs
    data_structures["r_k_pairs"] = create_r_k_set(data_structures["odpair_list"])
    if haskey(data_structures, "detour_time_reduction_list")
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
    @variable(model, s[y in y_init:Y_end, p_r_k_g_pairs, tv_id in techvehicle_ids] >= 0)
    @variable(
        model,
        q_fuel_infr_plus[
            y in y_init:Y_end,
            f_id in [f.id for f ∈ fuel_list],
            geo_id in [geo.id for geo ∈ geographic_element_list],
        ] >= 0
    )
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
        q_mode_infr_plus[
            y in y_init:Y_end,
            m_id in [m.id for m ∈ mode_list],
            geo_id in [geo.id for geo ∈ geographic_element_list],
        ] >= 0
    )
    @variable(
        model, n_fueling[y in y_init:Y_end, p_r_k_g_pairs, f_id in [f.id for f in fuel_list]] >= 0
    )
    if haskey(data_structures, "detour_time_reduction_list")
        @variable(
            model, 
            detour_time[y in y_init:Y_end, p_r_k in p_r_k_g_pairs, f_id in [f.id for f in fuel_list]] >= 0
        )
        @variable(model, x_a[y in y_init:Y_end, gif_pair in geo_i_f_pairs], Bin)
        @variable(model, x_b[y in y_init:Y_end, gif_pair in geo_i_f_pairs], Bin)
        @variable(model, x_c[y in y_init:Y_end, gif_pair in geo_i_f_pairs], Bin)
        # @variable(model, x_a[y in y_init:Y_end, geo_id in [geo.id for geo ∈ geographic_element_list]], Bin)
        # @variable(model, x_b[y in y_init:Y_end, geo_id in [geo.id for geo ∈ geographic_element_list]], Bin)
        # @variable(model, x_c[y in y_init:Y_end, geo_id in [geo.id for geo ∈ geographic_element_list]], Bin)

        @variable(model, z[y in y_init:Y_end, gif_pair in geo_i_f_pairs, p_r_k_g in p_r_k_g_pairs] >= 0)
        # only if reduction is defined, else there is a standard waiting time defined 
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
            mv ∈ data_structures["m_tv_pairs"] for g ∈ data_structures["g_init"]:y
        ) == r.F[y-data_structures["y_init"]+1]
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
            ) * model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths
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
    # TODO: implement the constraint in a more efficient way compared to the og script 
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

    # Use filter to apply the condition
    valid_subset = filter(
        t -> t[2] <= t[1] && (t[1] - t[2]) > t[4].Lifetime[t[2]-g_init+1],
        all_indices,
    )

    for (y, g, r, tv) ∈ valid_subset
        @constraint(
            model,
            model[:h][y, r.id, tv.id, g] ==
            model[:h_exist][y, r.id, tv.id, g] - model[:h_minus][y, r.id, tv.id, g] +
            model[:h_plus][y, r.id, tv.id, g]
        )
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_exist][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
    end
    # Convert valid_subset into a set
    valid_subset_set = Set(valid_subset)

    # Define the second subset: y - g == Lifetime, excluding valid_subset
    valid_subset_equal_exclusive = filter(
        t ->
            t[2] <= t[1] &&
                (t[1] - t[2]) == t[4].Lifetime[t[2]-g_init+1] &&
                !(t in valid_subset_set),
        all_indices,
    )

    # Add constraints for valid_subset_equal_exclusive
    for (y, g, r, tv) ∈ valid_subset_equal_exclusive
        @constraint(
            model,
            model[:h][y, r.id, tv.id, g] ==
            model[:h_exist][y, r.id, tv.id, g] - model[:h_minus][y, r.id, tv.id, g]
        )
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
    end

    # Define subset for y - g == Lifetime and y == y_init
    valid_subset_equal_exclusive_y_init = filter(
        t ->
            t[2] <= t[1] &&
                (t[1] - t[2]) == t[4].Lifetime[t[2]-g_init+1] &&
                t[1] == y_init &&
                !(t in valid_subset_set),
        all_indices,
    )

    # Add constraints for valid_subset_equal_exclusive_y_init
    for (y, g, r, tv) ∈ valid_subset_equal_exclusive_y_init
        stock_index = findfirst(
            ivs -> ivs.year_of_purchase == g && ivs.techvehicle.id == tv.id,
            r.vehicle_stock_init,
        )
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] == r.vehicle_stock_init[stock_index].stock
        )
    end
    # Define subset for in-between years (y - g == Lifetime but not y_init)
    valid_subset_equal_exclusive_inbetw = filter(
        t ->
            t[2] <= t[1] &&
                (t[1] - t[2]) == t[4].Lifetime[t[2]-g_init+1] &&
                !(t in valid_subset_set) &&
                !(t in valid_subset_equal_exclusive_y_init),
        all_indices,
    )

    # Add constraints for valid_subset_equal_exclusive_inbetw
    for (y, g, r, tv) ∈ valid_subset_equal_exclusive_inbetw
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] == model[:h][y-1, r.id, tv.id, g]
        )
    end

    # Define remaining subset: Lifetime satisfied but not y_init or in-between
    valid_subset_equal_exclusive_rest = filter(
        t ->
            t[2] <= t[1] &&
                (t[1] - t[2]) == t[4].Lifetime[t[2]-g_init+1] &&
                !(t in valid_subset_set) &&
                !(t in valid_subset_equal_exclusive_y_init) &&
                !(t in valid_subset_equal_exclusive_inbetw),
        all_indices,
    )

    # Add constraints for valid_subset_equal_exclusive_rest
    for (y, g, r, tv) ∈ valid_subset_equal_exclusive_rest
        @constraint(model, model[:h_exist][y, r.id, tv.id, g] == 0)
    end
    # Update the valid_subset_equal_exclusive set
    valid_subset_equal_exclusive_set = Set(valid_subset_equal_exclusive)

    # Define subset for g == y (same year)
    valid_subset_equal_g_y = filter(
        t ->
            t[1] == t[2] &&
                !(t in valid_subset_equal_exclusive_set) &&
                !(t in valid_subset_set),
        all_indices,
    )

    # Add constraints for valid_subset_equal_g_y
    for (y, g, r, tv) ∈ valid_subset_equal_g_y
        @constraint(
            model,
            model[:h][y, r.id, tv.id, g] == model[:h_plus][y, r.id, tv.id, g]
        )
        @constraint(model, model[:h_exist][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
    end

    # Define subset for g < y, excluding earlier subsets
    valid_subset_g_less_y_exclusive = filter(
        t ->
            t[2] < t[1] &&
                !(t in valid_subset_set) &&
                !(t in valid_subset_equal_exclusive_set) &&
                !(t in valid_subset_equal_g_y),
        all_indices,
    )

    # Add constraints for valid_subset_g_less_y_exclusive
    for (y, g, r, tv) ∈ valid_subset_g_less_y_exclusive
        @constraint(
            model,
            model[:h][y, r.id, tv.id, g] ==
            model[:h_exist][y, r.id, tv.id, g] - model[:h_minus][y, r.id, tv.id, g]
        )
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
    end

    # Define subset for g < y and y == y_init
    valid_subset_g_less_y_exclusive_2 = filter(
        t ->
            t[2] < t[1] &&
                t[1] == y_init &&
                !(t in valid_subset_set) &&
                !(t in valid_subset_equal_exclusive_set) &&
                !(t in valid_subset_equal_g_y),
        all_indices,
    )

    # Add constraints for valid_subset_g_less_y_exclusive_2
    for (y, g, r, tv) ∈ valid_subset_g_less_y_exclusive_2
        stock_index = findfirst(
            ivs -> ivs.year_of_purchase == g && ivs.techvehicle.id == tv.id,
            r.vehicle_stock_init,
        )
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] == r.vehicle_stock_init[stock_index].stock
        )
    end

    valid_subset_g_less_y_exclusive_3 = filter(
        t ->
            t[2] < t[1] &&
                t[1] > y_init &&
                !(t in valid_subset_g_less_y_exclusive_2) &&
                !(t in valid_subset_set) &&
                !(t in valid_subset_equal_exclusive_set) &&
                !(t in valid_subset_equal_g_y),
        all_indices,
    )

    for (y, g, r, tv) ∈ valid_subset_g_less_y_exclusive_3
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] ==
            model[:h][y-1, r.id, tv.id, g] - model[:h_minus][y, r.id, tv.id, g]
        )
    end
    # Define remaining subset: Lifetime satisfied but excluding all previous subsets
    valid_subset_rest = filter(
        t ->
            (t[1] - t[2]) == t[4].Lifetime[t[2]-g_init+1] &&
                !(t in valid_subset_set) &&
                !(t in valid_subset_equal_exclusive_set) &&
                !(t in valid_subset_equal_g_y) &&
                !(t in valid_subset_g_less_y_exclusive),
        all_indices,
    )

    # Add constraints for valid_subset_rest
    for (y, g, r, tv) ∈ valid_subset_rest
        @constraint(model, model[:h][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_exist][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
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
    vehicle_subsidy_list = data_structures["vehicle_subsidy_list"]
    # @constraint(
    #     model,
    #     [r in odpairs],
    #     sum([
    #         (model[:h_plus][y, r.id, v.id, g] * v.capital_cost[g-g_init+1])
    #         for y in data_structures["y_init"]:data_structures["Y_end"] for 
    #         v in techvehicles for g in data_structures["g_init"]:y
    #     ])  <= 
    #     r.financial_status.monetary_budget_purchase_ub *r.F[20] *
    #     (data_structures["Y_end"] - data_structures["y_init"] + 1) *(1/r.financial_status.monetary_budget_purchase_time_horizon)+ sum(
    #         model[:budget_penalty_plus][y, r.id] for y in data_structures["y_init"]:data_structures["Y_end"]
    #     )
    # )
    # @constraint(
    #     model,
    #     [r in odpairs],
    #     sum([
    #         (model[:h_plus][y, r.id, v.id, g] * v.capital_cost[g-g_init+1]) 
    #          for y ∈ data_structures["y_init"]:data_structures["Y_end"] for
    #         v ∈ techvehicles for g ∈ g_init:y
    #     ]) >=
    #     r.financial_status.monetary_budget_purchase_lb *r.F[20] *
    #     (data_structures["Y_end"] - data_structures["y_init"] + 1)*(1/r.financial_status.monetary_budget_purchase_time_horizon) - sum(
    #         model[:budget_penalty_minus][y, r.id] for
    #         y ∈ data_structures["y_init"]:data_structures["Y_end"]
    #     )
    # )
    #     @constraint(
    #     model,
    #     [r in odpairs],
    #     sum([
    #         (model[:h_plus][y, r.id, v.id, g] * v.capital_cost[g-g_init+1])
    #         for y in data_structures["y_init"]:data_structures["Y_end"] for 
    #         v in techvehicles for g in data_structures["g_init"]:y
    #     ])  <= 
    #     r.financial_status.monetary_budget_purchase_ub *r.F[20] *
    #     (data_structures["Y_end"] - data_structures["y_init"] + 1) *(1/r.financial_status.monetary_budget_purchase_time_horizon)+ sum(
    #         model[:budget_penalty_plus][y, r.id] for y in data_structures["y_init"]:data_structures["Y_end"]
    #     )
    # )
    # @constraint(
    #     model,
    #     [r in odpairs],
    #     sum([
    #         (model[:h_plus][y, r.id, v.id, g] * v.capital_cost[g-g_init+1]) 
    #          for y ∈ data_structures["y_init"]:data_structures["Y_end"] for
    #         v ∈ techvehicles for g ∈ g_init:y
    #     ]) >=
    #     r.financial_status.monetary_budget_purchase_lb *r.F[20] *
    #     (data_structures["Y_end"] - data_structures["y_init"] + 1)*(1/r.financial_status.monetary_budget_purchase_time_horizon) - sum(
    #         model[:budget_penalty_minus][y, r.id] for
    #         y ∈ data_structures["y_init"]:data_structures["Y_end"]
    #     )
    # )
    # for r in odpairs 
    #     y_set = generate_exact_length_subsets(data_structures["y_init"], data_structures["Y_end"], r.financial_status.monetary_budget_purchase_time_horizon)
    #     @constraint(model, [y0 in y_set], sum(
    #         model[:h_plus][y, r.id, v.id, g] * v.capital_cost[g-g_init+1] for y in y0 for v in techvehicles for g in g_init:y
    #     ) <= r.financial_status.monetary_budget_purchase_ub * r.F[20] * + sum(
    #         model[:budget_penalty_plus][y, r.id] for y in y0
    #     ))
    #     @constraint(model, [y0 in y_set], sum(
    #         model[:h_plus][y, r.id, v.id, g] * v.capital_cost[g-g_init+1] for y in y0 for v in techvehicles for g in g_init:y
    #     ) >= r.financial_status.monetary_budget_purchase_lb *r.F[20] * - sum(
    #         model[:budget_penalty_minus][y, r.id] for y in y0
    #     ))
    # end

    for r in odpairs 
        y_set = generate_exact_length_subsets(data_structures["y_init"], data_structures["Y_end"], r.financial_status.monetary_budget_purchase_time_horizon)
        @constraint(model, [y0 in y_set], sum(
            model[:h_plus][y, r.id, v.id, g] for y in y0 for v in techvehicles for g in g_init:y
        ) <= 1 * r.F[20]+ sum(
            model[:budget_penalty_plus][y, r.id] for y in y0
        ))
        @constraint(model, [y0 in y_set], sum(
            model[:h_plus][y, r.id, v.id, g] for y in y0 for v in techvehicles for g in g_init:y
        ) >= 1 * r.F[20] - sum(
            model[:budget_penalty_minus][y, r.id] for y in y0
        ))
    end
    @constraint(
        model,
        [r in odpairs],
        sum([
            model[:h_plus][y, r.id, v.id, g] 
            for y in data_structures["y_init"]:data_structures["Y_end"] for 
            v in techvehicles for g in data_structures["g_init"]:y
        ])  <= 
        r.F[20] *
        (data_structures["Y_end"] - data_structures["y_init"] + 1) *(1/r.financial_status.monetary_budget_purchase_time_horizon)+ sum(
            model[:budget_penalty_plus][y, r.id] for y in data_structures["y_init"]:data_structures["Y_end"]
        )
    )
    @constraint(
        model,
        [r in odpairs],
        sum(
            model[:h_plus][y, r.id, v.id, g]
             for y ∈ data_structures["y_init"]:data_structures["Y_end"] for
            v ∈ techvehicles for g ∈ g_init:y
        ) >=
        r.F[20] *
        (data_structures["Y_end"] - data_structures["y_init"] + 1)*(1/r.financial_status.monetary_budget_purchase_time_horizon) - sum(
            model[:budget_penalty_minus][y, r.id] for
            y ∈ data_structures["y_init"]:data_structures["Y_end"]
        )
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
            model[:q_fuel_infr_plus][y0, f.id, geo.id] for y0 ∈ data_structures["y_init"]:y
        ) >= sum(
            gamma * model[:s][y, p_r_k_g, tv.id] for p_r_k_g ∈ p_r_k_g_pairs for
            tv ∈ techvehicles if p_r_k_g[4] == geo.id && tv.technology.fuel.name == f.name
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
    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            m in data_structures["mode_list"],
            geo in geographic_element_list,
        ],
        initialmodeinfr_list[findfirst(
            i -> i.mode.id == m.id && i.allocation == geo.id,
            initialmodeinfr_list,
        )].installed_ukm + sum(
            model[:q_mode_infr_plus][y0, m.id, geo.id] for y0 ∈ data_structures["y_init"]:y
        ) >=
        data_structures["gamma"] * sum(
            model[:f][y, p_r_k, m_tv, g] for p_r_k in data_structures["p_r_k_pairs"] for
            m_tv ∈ data_structures["m_tv_pairs"] if
            geo.id in path_list[findfirst(p -> p.id == p_r_k[3], path_list)].sequence
        )
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
    println("r_k_pairs: ", r_k_pairs)
    @constraint(
        model,
        [y in y_init:Y_end, p in products, r_k in r_k_pairs, v in techvehicles],
        sum(
            model[:s][y, (p.id, r_k[1], r_k[2], el.id), v.id] for
            el ∈ paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence
        ) >= sum(
            (
                (v.spec_cons[g-g_init+1]) /
                v.W[g-g_init+1] * paths[findfirst(p0 -> p0.id == r_k[2], paths)].length
            ) * model[:f][y, (p.id, r_k[1], r_k[2]), (v.vehicle_type.mode.id, v.id), g]
            for g ∈ g_init:y
        )
    )
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
    alpha_h = data_structures["alpha_h"]
    beta_h = data_structures["beta_h"]
    technologies = data_structures["technology_list"]
    vehicletypes = data_structures["vehicletype_list"]

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, t in technologies],
        (
            sum(
                model[:h][y, r.id, tv.id, g] for g ∈ g_init:y for v ∈ vehicletypes for
                tv ∈ techvehicles if g <= y && tv.technology.id == t.id
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:y for v ∈ vehicletypes for
                tv ∈ techvehicles if g <= y - 1 && tv.technology.id == t.id
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv.id, g] for g ∈ g_init:(y-1) for tv ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g] for v ∈ vehicletypes for g ∈ g_init:(y-1) for
            tv ∈ techvehicles if tv.technology.id == t.id
        )
    )

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, t in technologies],
        -(
            sum(
                model[:h][y, r.id, tv.id, g] for g ∈ g_init:y for v ∈ vehicletypes for
                tv ∈ techvehicles if g <= y && tv.technology.id == t.id
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:y for v ∈ vehicletypes for
                tv ∈ techvehicles if g <= y - 1 && tv.technology.id == t.id
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv.id, g] for g ∈ g_init:(y-1) for tv ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g] for v ∈ vehicletypes for g ∈ g_init:(y-1) for
            tv ∈ techvehicles if tv.technology.id == t.id
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
            model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for m0 ∈ modes for
            mv ∈ m_tv_pairs for k ∈ r.paths for g ∈ g_init:(y-1)
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
            model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for m0 ∈ modes for
            mv ∈ m_tv_pairs for k ∈ r.paths for g ∈ g_init:(y-1)
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

    @constraint(
        model,
        [el in market_share_list],
        sum(
            model[:h_plus][el.year, r.id, el.type.id, g] for r ∈ odpairs for
            g ∈ g_init:(el.year)
        ) ==
        el.share * sum(
            model[:h_plus][el.year, r.id, tv.id, g] for r ∈ odpairs for
            tv ∈ data_structures["techvehicle_list"] for
            g ∈ g_init:(el.year) if tv.vehicle_type.mode.id == el.type.vehicle_type.mode.id
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
                    (1 / 1000) *
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
                    10^(-3)
                    for r ∈ odpairs for
                    k ∈ r.paths for g ∈ g_init:y
                ) <= el.emission
            )
        end
    end
end

function constraint_def_n_fueling(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    techvehicle_list = data_structures["techvehicle_list"]
    fuel_list = data_structures["fuel_list"]
    @constraint(model, [y in y_init:Y_end, p_r_k_g in p_r_k_g_pairs, f in fuel_list], model[:n_fueling][y, p_r_k_g, f.id] == sum((1/tv.battery_capacity[1]) * model[:s][y, p_r_k_g, tv.id] for tv in techvehicle_list if tv.technology.fuel.id == f.id))
end


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
    
    for p_r_k_g in p_r_k_g_pairs
        geo_id = p_r_k_g[4]
        for f in fuel_list
            matching_item = init_detour_times_list[findfirst(elem -> elem.fuel.id == f.id && elem.location.id == geo_id, init_detour_times_list)]
                init_detour_time = matching_item.detour_time
            if findfirst(elem -> elem.fuel.id == f.id, detour_time_reduction_list) == nothing
                
                @constraint(model, [y in y_init:Y_end], model[:detour_time][y, p_r_k_g, f.id] == model[:n_fueling][y, p_r_k_g, f.id]*init_detour_time)
            else
                selection = detour_time_reduction_list[findall(elem -> elem.fuel.id == f.id && elem.location.id == geo_id, detour_time_reduction_list)]

                @constraint(model, [y in y_init:Y_end], model[:detour_time][y, p_r_k_g, f.id] == model[:n_fueling][y, p_r_k_g, f.id]*init_detour_time
                - sum(model[:z][y, g_id, p_r_k_g] * init_detour_time * selection[findfirst(item -> item.reduction_id == g_id[2], selection)].detour_time_reduction for g_id in geo_i_f_pairs if g_id[1] == geo_id && g_id[3] == f.id))
                for sel in selection
                    println("sel: ", sel.detour_time_reduction)
                end
            end


        # if findfirst(elem -> elem.fuel.id == f.id, detour_time_reduction_list) == nothing
        #     @constraint(model, [y in y_init:Y_end, geo_id in [geo.id for geo ∈ geographic_element_list], p_r_k in p_r_k_pairs, tv in techvehicle_list], model[:detour_time][y, geo_id, p_r_k, f.id] == sum(model[:n_fueling][y, (p_r_k[1], p_r_k[2], p_r_k[3], geo_id), tv.id] for tv in techvehicle_list if (p_r_k[1], p_r_k[2], p_r_k[3], geo_id) in p_r_k_g_pairs && tv.technology.fuel.id == f.id)) 
        #     #* init_detour_times_list[findfirst(elem -> (elem.location.id == geo_id) && (elem.fuel.id == tv.technology.fuel.id), init_detour_times_list)].detour_time)
        
        # else
            
        #     @constraint(model, [y in y_init:Y_end, geo_id in [geo.id for geo ∈ geographic_element_list], p_r_k in p_r_k_pairs], model[:detour_time][y, geo_id, p_r_k, f.id] == sum( model[:n_fueling][y, (p_r_k[1], p_r_k[2], p_r_k[3], geo_id), tv.id] for tv in techvehicle_list if (p_r_k[1], p_r_k[2], p_r_k[3], geo_id) in p_r_k_g_pairs && tv.technology.fuel.id == f.id))
        #     #* init_detour_times_list[findfirst(elem -> (elem.location.id == geo_id) && (elem.fuel.id == f.id), init_detour_times_list)].detour_time)
            
        #     #- sum(model[:z][y, g_id, (p_r_k[1], p_r_k[2], p_r_k[3], geo_id), tv.id] for g_id in geo_i_f_pairs for tv in techvehicle_list if (p_r_k[1], p_r_k[2], p_r_k[3], geo_id) in p_r_k_g_pairs && tv.technology.fuel.id == f.id))
        end
    end
end

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
    M = 10^8
    for geo_i_f in geo_id_pairs
        matching_item =detour_time_reduction_list[findfirst(item -> item.reduction_id == geo_i_f[2] && item.location.id == geographic_element_list[findfirst(item -> item.id == geo_i_f[1], geographic_element_list)].id, detour_time_reduction_list)] 
        #reduction_val = matching_item.detour_time_reduction
  
        f = matching_item.fuel
        @constraint(model, [y in y_init:Y_end, p_r_k in p_r_k_g_pairs, v in techvehicle_list], model[:z][y, geo_i_f, p_r_k] <= model[:n_fueling][y, p_r_k, f.id] )

        @constraint(model, [y in y_init:Y_end, p_r_k in p_r_k_g_pairs], model[:z][y, geo_i_f, p_r_k] <= M * model[:x_c][y, geo_i_f]) 

        @constraint(model, [y in y_init:Y_end, p_r_k in p_r_k_g_pairs], model[:z][y, geo_i_f, p_r_k] >= model[:n_fueling][y, p_r_k, f.id] - M * (1 - model[:x_c][y, geo_i_f]))
    end 
    
end

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
    # initialfuelinginfr_list = data_structures["initialfuelinginfr_list"]
    M = 10^8

    # @constraint(model, [y in y_init:Y_end, geo in geographic_element_list], lb * model[:x_c][y, geo.id] <= sum(model[:q_fuel_infr_plus][y0, f.id, geo.id] for y0 in y_init:y for f in fuel_list))

    # @constraint(model, [y in y_init:Y_end, geo in geographic_element_list], sum(model[:q_fuel_infr_plus][y0, f.id, geo.id] for y0 in y_init:y for f in fuel_list) <= ub * model[:x_c][y, geo.id] + M * (1 - model[:x_c][y, geo.id]))

    # @constraint(model, [y in y_init:Y_end, geo in geographic_element_list], sum(model[:q_fuel_infr_plus][y0, f.id, geo.id] for y0 in y_init:y for f in fuel_list) <= M*model[:x_a][y, geo.id])

    # @constraint(model, [y in y_init:Y_end, geo in geographic_element_list], ub - sum(model[:q_fuel_infr_plus][y0, f.id, geo.id] for y0 in y_init:y for f in fuel_list) <= M*model[:x_b][y, geo.id])

    # @constraint(model, [y in y_init:Y_end, geo in geographic_element_list], model[:x_c][y, geo.id] >= model[:x_a][y, geo.id] + model[:x_b][y, geo.id] - 1)

    global counter_ = 0
    for geo_i_f in geo_id_pairs
        matching_item =detour_time_reduction_list[findfirst(item -> item.reduction_id == geo_i_f[2] && item.location.id == geographic_element_list[findfirst(item -> item.id == geo_i_f[1], geographic_element_list)].id, detour_time_reduction_list)] 
        lb = matching_item.fueling_cap_lb
        ub = matching_item.fueling_cap_ub
        fuel_type = matching_item.fuel
        
        println(geo_i_f, lb, ub)
        println("lb ", lb)
        println("ub ", ub)

        @constraint(model, [y in y_init:Y_end], lb * model[:x_c][y, geo_i_f] <= sum(model[:q_fuel_infr_plus][y0, fuel_type.id, geo_i_f[1]] for y0 in y_init:y))
        @constraint(model, [y in y_init:Y_end], sum(model[:q_fuel_infr_plus][y0, fuel_type.id, geo_i_f[1]] for y0 in y_init:y) <= ub * model[:x_c][y, geo_i_f] + M * (1 - model[:x_c][y, geo_i_f]))
        @constraint(model, [y in y_init:Y_end], sum(model[:q_fuel_infr_plus][y0, fuel_type.id, geo_i_f[1]] for y0 in y_init:y) <= M*model[:x_a][y, geo_i_f])
        @constraint(model, [y in y_init:Y_end], ub - sum(model[:q_fuel_infr_plus][y0, fuel_type.id, geo_i_f[1]] for y0 in y_init:y) <= M*model[:x_b][y,geo_i_f])
        @constraint(model, [y in y_init:Y_end], model[:x_c][y, geo_i_f] >= model[:x_a][y, geo_i_f] + model[:x_b][y, geo_i_f] - 1)

        # Y_end = 2030
        # geo_i_f = (12, 0, 2)
        # @constraint(model, [y in y_init:Y_end], lb * model[:x_c][y, geo_i_f] <= 300)
        # @constraint(model, [y in y_init:Y_end], 300 <= ub * model[:x_c][y, geo_i_f] + M * (1 - model[:x_c][y, geo_i_f]))
        # @constraint(model, [y in y_init:Y_end], 300 <= M*model[:x_a][y, geo_i_f])
        # @constraint(model, [y in y_init:Y_end], ub - 300 <= M*model[:x_b][y,geo_i_f])
        # @constraint(model, [y in y_init:Y_end], model[:x_c][y, geo_i_f] >= model[:x_a][y, geo_i_f] + model[:x_b][y, geo_i_f] - 1)

        # y_init = 2031
        # Y_end = 2045
        # geo_i_f = (12, 1, 2)
        # @constraint(model, [y in y_init:Y_end], lb * model[:x_c][y, geo_i_f] <= 60000)
        # @constraint(model, [y in y_init:Y_end], 60000 <= ub * model[:x_c][y, geo_i_f] + M * (1 - model[:x_c][y, geo_i_f]))
        # @constraint(model, [y in y_init:Y_end], 60000 <= M*model[:x_a][y, geo_i_f])
        # @constraint(model, [y in y_init:Y_end], ub - 60000 <= M*model[:x_b][y,geo_i_f])
        # @constraint(model, [y in y_init:Y_end], model[:x_c][y, geo_i_f] >= model[:x_a][y, geo_i_f] + model[:x_b][y, geo_i_f] - 1)
        # global counter_ += 1
        # if counter_ > 4
        #     break
        # end


    end



    for f in fuel_list
        if findfirst(elem -> elem.fuel.id == f.id, detour_time_reduction_list) == nothing
            continue
        else
            # @constraint(model, [y in y_init:Y_end, geo_i in geo_id_pairs; geo_i[3] == f.id],  initialfuelinginfr_list[findfirst(
            #     i -> i.fuel.name == f.name && i.allocation == geo_i[1],
            #     initialfuelinginfr_list,
            # )].installed_kW + sum(model[:q_fuel_infr_plus][y0, f.id, geo_i[1]] for y0 in y_init:y) - detour_time_reduction_list[findfirst(item -> item.reduction_id == geo_i[2] && item.location.id == geographic_element_list[findfirst(item -> item.id == geo_i[1], geographic_element_list)].id, detour_time_reduction_list)].fueling_cap_lb <= 1000000000000000000000000000000000 * model[:x][y, geo_i])
            # @constraint(model, [y in y_init:Y_end, geo_i in geo_id_pairs; geo_i[3] == f.id], detour_time_reduction_list[findfirst(item -> item.reduction_id == geo_i[2] && item.location.id == geographic_element_list[findfirst(item -> item.id == geo_i[1], geographic_element_list)].id, detour_time_reduction_list)].fueling_cap_ub - (initialfuelinginfr_list[findfirst(
            #     i -> i.fuel.name == f.name && i.allocation == geo_i[1],
            #     initialfuelinginfr_list,
            # )].installed_kW + sum(model[:q_fuel_infr_plus][y0, f.id, geo_i[1]] for y0 in y_init:y))<= 1000000000000000000000000000000000 * (1-model[:x][y, geo_i]))

            # @constraint(model, [y in y_init:Y_end, geo_i in geo_id_pairs; geo_i[3] == f.id],  initialfuelinginfr_list[findfirst(
            #     i -> i.fuel.name == f.name && i.allocation == geo_i[1],
            #     initialfuelinginfr_list,
            # )].installed_kW + sum(model[:q_fuel_infr_plus][y0, f.id, geo_i[1]] for y0 in y_init:y) - detour_time_reduction_list[findfirst(item -> item.reduction_id == geo_i[2] && item.location.id == geographic_element_list[findfirst(item -> item.id == geo_i[1], geographic_element_list)].id, detour_time_reduction_list)].fueling_cap_lb <= M * model[:x_a][y, geo_i])
            # @constraint(model, [y in y_init:Y_end, geo_i in geo_id_pairs; geo_i[3] == f.id], detour_time_reduction_list[findfirst(item -> item.reduction_id == geo_i[2] && item.location.id == geographic_element_list[findfirst(item -> item.id == geo_i[1], geographic_element_list)].id, detour_time_reduction_list)].fueling_cap_ub - (initialfuelinginfr_list[findfirst(
            #     i -> i.fuel.name == f.name && i.allocation == geo_i[1],
            #     initialfuelinginfr_list,
            # )].installed_kW + sum(model[:q_fuel_infr_plus][y0, f.id, geo_i[1]] for y0 in y_init:y))<= M * (1-model[:x_b][y, geo_i]))
            # @constraint(model, [y in y_init:Y_end, geo_i in geo_id_pairs; geo_i[3] == f.id], model[:x_c][y, geo_i] >= model[:x_a][y, geo_i] + model[:x_b][y, geo_i] - 1)
            # @constraint(model, [y in y_init:Y_end, geo_i in geo_id_pairs; geo_i[3] == f.id], detour_time_reduction_list[findfirst(item -> item.reduction_id == geo_i[2] && item.location.id == geographic_element_list[findfirst(item -> item.id == geo_i[1], geographic_element_list)].id, detour_time_reduction_list)].fueling_cap_lb  * model[:x_c][y, geo_i] <= initialfuelinginfr_list[findfirst(
            #     i -> i.fuel.name == f.name && i.allocation == geo_i[1],
            #     initialfuelinginfr_list,
            # )].installed_kW + sum(model[:q_fuel_infr_plus][y0, f.id, geo_i[1]] for y0 in y_init:y))
            # @constraint(model, [y in y_init:Y_end, geo_i in geo_id_pairs; geo_i[3] == f.id], detour_time_reduction_list[findfirst(item -> item.reduction_id == geo_i[2] && item.location.id == geographic_element_list[findfirst(item -> item.id == geo_i[1], geographic_element_list)].id, detour_time_reduction_list)].fueling_cap_ub  * model[:x_c][y, geo_i] + (1-model[:x_c][y, geo_i]) * M >= initialfuelinginfr_list[findfirst(
            #     i -> i.fuel.name == f.name && i.allocation == geo_i[1],
            #     initialfuelinginfr_list,
            # )].installed_kW + sum(model[:q_fuel_infr_plus][y0, f.id, geo_i[1]] for y0 in y_init:y))

        

            # @constraint(model, [y in y_init:Y_end, geo_i in geo_id_pairs],  initialfuelinginfr_list[findfirst(
            #     i -> i.fuel.name == f.name && i.allocation == geo_i[1],
            #     initialfuelinginfr_list,
            # )].installed_kW + sum(model[:q_fuel_infr_plus][y0, f.id, geo_i[1]] for y0 in y_init:y) - 100 <= 1000000000000000000000000000000000 * model[:x][y, geo_i])
            # @constraint(model, [y in y_init:Y_end, geo_i in geo_id_pairs], 800000 - (initialfuelinginfr_list[findfirst(
            #     i -> i.fuel.name == f.name && i.allocation == geo_i[1],
            #     initialfuelinginfr_list,
            # )].installed_kW + sum(model[:q_fuel_infr_plus][y0, f.id, geo_i[1]] for y0 in y_init:y))<= 1000000000000000000000000000000000 * (1-model[:x][y, geo_i]))
        end
        
    end
    #@constraint(model, [y in y_init:Y_end], model[:x][y, (12, 1, 2)] + model[:x][y, (12, 0, 2)]<= 1)
end

function constraint_all_x(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    geographic_element_list = data_structures["geographic_element_list"]
    detour_time_reduction_list = data_structures["detour_time_reduction_list"]
    geo_i_f = data_structures["geo_i_f_pairs"]
    fuel_list = data_structures["fuel_list"]
    for g in geographic_element_list
        for f in fuel_list
            if findfirst(elem -> elem.fuel.id == f.id, detour_time_reduction_list) == nothing
                continue
            else
                selection = detour_time_reduction_list[findall(elem -> elem.fuel.id == f.id && elem.location.id == g.id, detour_time_reduction_list)]
                @constraint(model, [y in y_init:Y_end], sum(model[:x_c][y, (g.id, s.reduction.id, f.id)] for s in selection) <=1)
            end
        end
    end


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
    speed_list = data_structures["speed_list"]
    initialfuelinfr_list = data_structures["initialfuelinginfr_list"]
    initialmodeinfr_list = data_structures["initialmodeinfr_list"]
    capital_cost_map = Dict(
        (v.id, g) => v.capital_cost[g-g_init+1] for v ∈ techvehicles for g ∈ g_init:Y_end
    )
    vehicle_subsidy_list = data_structures["vehicle_subsidy_list"]

    # Initialize the total cost expression
    #total_cost_expr = @expression(model, 0)
    total_cost_expr = AffExpr(0)
    fuel_cost = 1

    # Build the objective function more efficiently
    for y ∈ y_init:Y_end
        for r ∈ odpairs
            add_to_expression!(
                total_cost_expr,
                model[:budget_penalty_plus][y, r.id] *
                data_structures["budget_penalty_plus"],
            )
            add_to_expression!(
                total_cost_expr,
                model[:budget_penalty_minus][y, r.id] *
                data_structures["budget_penalty_minus"],
            )
        end
        for v ∈ techvehicles
            for r ∈ odpairs
                speed =
                    speed_list[findfirst(
                        s ->
                            (s.region_type.id == r.region_type.id) &&
                                (s.vehicle_type.id == v.vehicle_type.id),
                        speed_list,
                    )].travel_speed
                route_length = sum(k.length for k ∈ r.paths)

                for k ∈ r.paths

                    for geo ∈ k.sequence
                        
                        add_to_expression!(
                            total_cost_expr,
                            model[:s][y, (r.product.id, r.id, k.id, geo.id), v.id] *
                            fuel_cost +
                            10^(-3) *
                            model[:s][y, (r.product.id, r.id, k.id, geo.id), v.id] *
                            v.technology.fuel.emission_factor[y-y_init+1] *
                            geo.carbon_price[y-y_init+1],
                        )
                    end
                end

                for g ∈ g_init:y
                    capital_cost = capital_cost_map[(v.id, g)]

                    add_to_expression!(
                        total_cost_expr,
                        model[:h_plus][y, r.id, v.id, g] * capital_cost
                    )
                    add_to_expression!(
                        total_cost_expr,
                        model[:h_minus][y, r.id, v.id, g] *
                        capital_cost * (1 - 0.1)^(y - g),
                    )

                    if y - g <= v.Lifetime[g-g_init+1]
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] *
                            v.maintenance_cost_annual[g-g_init+1][y-g+1],
                        )
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] *
                            v.maintenance_cost_distance[g-g_init+1][y-g+1] *
                            route_length,
                        )
                    end
                    if y - g == v.Lifetime[g-g_init+1] && r.region_type.name == "urban"
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] * regiontypes[findfirst(
                                rt -> rt.name == "urban",
                                regiontypes,
                            )].costs_fix[y-y+1],
                        )
                    else
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] * regiontypes[findfirst(
                                rt -> rt.name == "rural",
                                regiontypes,
                            )].costs_fix[y-y+1],
                        )
                    end
                    driving_range =
                        0.8 * v.battery_capacity[g-g_init+1] * (1 / v.spec_cons[g-g_init+1])
                    if driving_range < route_length
                        fueling_time = 0
                    else
                        fueling_time =
                            v.battery_capacity[g-g_init+1] / v.peak_charging[g-g_init+1]
                            # println("fueling time: ", fueling_time, route_length, driving_range)
                    end
                    # value of time

                    # the detour time reduction needs to go somewhere els
                    for k ∈ r.paths
                        vot = r.financial_status.VoT
                        los_wo_detour = route_length / speed + v.vehicle_type.mode.waiting_time[y-y_init+1]
                        intangible_costs = vot * los_wo_detour
                        add_to_expression!(total_cost_expr, intangible_costs * model[:f][y, (r.product.id, r.id, k.id), (v.vehicle_type.mode.id, v.id), g])
                    end
                
                end
                if haskey(data_structures, "detour_time_reduction_list")

                    for k in r.paths
                        for geo in k.sequence
                            add_to_expression!(
                                total_cost_expr,
                                model[:detour_time][y, (r.product.id, r.id, k.id, geo.id), v.technology.fuel.id] * r.financial_status.VoT
                            )
                        end
                    end
                end
            end
        end
        for m ∈ modes
            for geo ∈ geographic_element_list
                add_to_expression!(
                    total_cost_expr,
                    model[:q_mode_infr_plus][y, m.id, geo.id] *
                    m.infrastructure_expansion_costs[y-y_init+1],
                )
                for y0 ∈ y_init:y
                    add_to_expression!(
                        total_cost_expr,
                        (
                            initialmodeinfr_list[findfirst(
                                i -> i.mode.id == m.id && i.allocation == geo.id,
                                initialmodeinfr_list,
                            )].installed_ukm + model[:q_mode_infr_plus][y0, m.id, geo.id]
                        ) * m.infrastructure_om_costs[y-y_init+1],
                    )
                end
            end
            if !m.quantify_by_vehs
                for mv ∈ m_tv_pairs
                    if mv[1] == m.id
                        
                        for r ∈ odpairs
                            route_length = sum(k.length for k ∈ r.paths)
                            speed = 20
                            los = route_length / speed + m.waiting_time[y-y_init+1]
                            vot = r.financial_status.VoT
                            intangible_costs = vot * los
                            for k ∈ r.paths
                                for g ∈ g_init:y
                                    add_to_expression!(
                                        total_cost_expr,
                                            model[:f][y, (r.product.id, r.id, k.id), mv, g] *
                                            route_length * 
                                            (
                                                m.cost_per_ukm[y-y_init+1] +  m.emission_factor[y - y_init + 1] *
                                                10^(-3) 
                                                * create_emission_price_along_path(k, y - y_init + 1, data_structures)
                                            ) 
                                    )
                                    add_to_expression!(
                                        total_cost_expr,
                                        intangible_costs *
                                            model[:f][y, (r.product.id, r.id, k.id), mv, g] 
                                    )
                                end
                            end
                        end                        
                    end
                end
            end
        end
        for f ∈ fuel_list
            for geo ∈ geographic_element_list
                add_to_expression!(
                    total_cost_expr,
                    model[:q_fuel_infr_plus][y, f.id, geo.id] *
                    f.cost_per_kW[y-y_init+1],
                )
                for y0 ∈ y_init:y
                    add_to_expression!(
                        total_cost_expr,
                        (
                            initialfuelinfr_list[findfirst(
                                i -> i.fuel.id == f.id && i.allocation == geo.id,
                                initialfuelinfr_list,
                            )].installed_kW  + model[:q_fuel_infr_plus][y0, f.id, geo.id]
                        ) * f.fueling_infrastructure_om_costs[y-y_init+1],
                    )
                end
            end
        end
    end
    @objective(model, Min, total_cost_expr)
end