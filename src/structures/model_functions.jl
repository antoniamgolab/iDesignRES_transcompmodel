"""

    This file contains functions relating to the mathematical formulation of the model, i.e., the definition of constraints and the objective function, including also the definition of decision variables.

"""

using YAML, JuMP, Gurobi
include("checks.jl")
include("structs.jl")


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

    data_structures["m_tv_pairs"] = m_tv_pairs
    data_structures["techvehicle_ids"] = techvehicle_ids
    data_structures["t_v_pairs"] = t_v_pairs
    data_structures["p_r_k_pairs"] = p_r_k_pairs
    data_structures["p_r_k_e_pairs"] = p_r_k_e_pairs
    data_structures["p_r_k_n_pairs"] = p_r_k_n_pairs
    data_structures["r_k_pairs"] = create_r_k_set(data_structures["odpair_list"])

    odpairs = data_structures["odpair_list"]
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    technologies = data_structures["technology_list"]
    edge_list = data_structures["edge_list"]
    node_list = data_structures["node_list"]

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
    @variable(model, s_e[y in y_init:Y_end, p_r_k_e_pairs, tv_id in techvehicle_ids] >= 0)
    @variable(model, s_n[y in y_init:Y_end, p_r_k_n_pairs, tv_id in techvehicle_ids] >= 0)
    @variable(
        model,
        q_fuel_infr_plus_e[
            y in y_init:Y_end,
            t_id in [t.id for t ∈ technologies],
            [e.id for e ∈ edge_list],
        ] >= 0
    )
    @variable(
        model,
        q_fuel_infr_plus_n[
            y in y_init:Y_end,
            t_id in [t.id for t ∈ technologies],
            [n.id for n ∈ node_list],
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
        ) >= r.F[y-data_structures["y_init"]+1]
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
    edge_list = data_structures["edge_list"]
    regiontypes = data_structures["regiontype_list"]
    node_list = data_structures["node_list"]
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
        (y, g, r, tv) for y ∈ y_init:Y_end, g ∈ g_init:Y_end, r ∈ odpairs, tv ∈ techvehicles
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
    @constraint(
        model,
        [r in odpairs],
        sum([
            (model[:h_plus][y, r.id, v.id, g] * v.capital_cost[g-g_init+1]) for
            y ∈ data_structures["y_init"]:data_structures["Y_end"] for v ∈ techvehicles for
            g ∈ data_structures["g_init"]:y
        ]) - sum([
            (
                model[:h_minus][y, r.id, v.id, g] *
                v.capital_cost[g-g_init+1] *
                depreciation_factor(y, g)
            ) for y ∈ data_structures["y_init"]:data_structures["Y_end"] for
            v ∈ techvehicles for g ∈ data_structures["g_init"]:y
        ]) <=
        r.financial_status.monetary_budget_purchase_ub *
        (data_structures["Y_end"] - data_structures["y_init"] + 1) + sum(
            model[:budget_penalty_plus][y, r.id] for
            y ∈ data_structures["y_init"]:data_structures["Y_end"]
        )
    )
    @constraint(
        model,
        [r in odpairs],
        sum([
            (model[:h_plus][y, r.id, v.id, g] * v.capital_cost[g-g_init+1]) for
            y ∈ data_structures["y_init"]:data_structures["Y_end"] for v ∈ techvehicles for
            g ∈ g_init:y
        ]) >=
        r.financial_status.monetary_budget_purchase_lb *
        3 *
        (data_structures["Y_end"] - data_structures["y_init"] + 1) - sum(
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
    edge_list = data_structures["edge_list"]
    node_list = data_structures["node_list"]
    p_r_k_n_pairs = data_structures["p_r_k_n_pairs"]
    p_r_k_e_pairs = data_structures["p_r_k_e_pairs"]
    techvehicles = data_structures["techvehicle_list"]

    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            t in technologies,
            e in edge_list,
        ],
        sum(
            model[:q_fuel_infr_plus_e][y0, t.id, e.id] for y0 ∈ data_structures["y_init"]:y
        ) >= sum(
            model[:s_e][y, p_r_k_e, tv.id] for p_r_k_e ∈ p_r_k_e_pairs for
            tv ∈ techvehicles if p_r_k_e[4] == e.id && tv.technology.id == t.id
        )
    )

    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            t in technologies,
            n in node_list,
        ],
        sum(
            model[:q_fuel_infr_plus_n][y0, t.id, n.id] for y0 ∈ data_structures["y_init"]:y
        ) >= sum(
            model[:s_n][y, p_r_k_n, tv.id] for p_r_k_n ∈ p_r_k_n_pairs for
            tv ∈ techvehicles if p_r_k_n[4] == n.name && tv.technology.id == t.id
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

    @constraint(
        model,
        [y in y_init:Y_end, p in products, r_k in r_k_pairs, v in techvehicles],
        sum(
            model[:s_e][y, (p.id, r_k[1], r_k[2], el), v.id] for
            el ∈ paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence if
            typeof(el) == Int
        ) + sum(
            model[:s_n][y, (p.id, r_k[1], r_k[2], el), v.id] for
            el ∈ paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence if
            typeof(el) == String
        ) >= sum(
            (
                (gamma * v.spec_cons[g-g_init+1]) /
                (v.W[g-g_init+1] * paths[findfirst(p0 -> p0.id == r_k[2], paths)].length)
            ) * model[:f][y, (p.id, r_k[1], r_k[2]), (tv.vehicle_type.mode.id, tv.id), g]
            for g ∈ g_init:y for tv ∈ techvehicles if tv.vehicle_type.id == v.id
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
            model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for g ∈
                                                                                g_init:y for
            mv ∈ m_tv_pairs
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
            model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for g ∈
                                                                                g_init:y for
            mv ∈ m_tv_pairs
        ) +
        beta_f * sum(
            model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for m0 ∈ modes for
            mv ∈ m_tv_pairs for k ∈ r.paths for g ∈ g_init:(y-1)
        )
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
    gamma = data_structures["gamma"]
    paths = data_structures["path_list"]
    edge_list = data_structures["edge_list"]
    node_list = data_structures["node_list"]
    technologies = data_structures["technology_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    p_r_k_e_pairs = data_structures["p_r_k_e_pairs"]
    p_r_k_n_pairs = data_structures["p_r_k_n_pairs"]
    regiontypes = data_structures["regiontype_list"]
    modes = data_structures["mode_list"]

    capital_cost_map = Dict(
        (v.id, g) => v.capital_cost[g-g_init+1] for v ∈ techvehicles for g ∈ g_init:Y_end
    )

    # Initialize the total cost expression
    #total_cost_expr = @expression(model, 0)
    total_cost_expr = AffExpr(0)
    fuel_cost = 1

    # Build the objective function more efficiently
    for y ∈ y_init:Y_end
        for r ∈ odpairs
            add_to_expression!(
                total_cost_expr,
                model[:budget_penalty_plus][y, r.id] * 1000000000,
            )
            add_to_expression!(total_cost_expr, model[:budget_penalty_minus][y, r.id])
        end
        for v ∈ techvehicles
            for r ∈ odpairs

                # path length
                route_length = sum(k.length for k ∈ r.paths)
                if r.region_type.name == "urban"
                    speed = 30
                else
                    speed = 60
                end

                for k ∈ r.paths
                    for el ∈ k.sequence
                        if typeof(el) == Int
                            add_to_expression!(
                                total_cost_expr,
                                model[:s_e][y, (r.product.id, r.id, k.id, el), v.id] *
                                fuel_cost,
                            )
                        elseif typeof(el) == String
                            add_to_expression!(
                                total_cost_expr,
                                model[:s_n][y, (r.product.id, r.id, k.id, el), v.id] *
                                fuel_cost,
                            )
                        end
                    end
                end

                for g ∈ g_init:y
                    capital_cost = capital_cost_map[(v.id, g)]

                    add_to_expression!(
                        total_cost_expr,
                        model[:h_plus][y, r.id, v.id, g] * capital_cost,
                    )

                    if y - g <= v.Lifetime[g-g_init+1]
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] *
                            v.maintnanace_cost_annual[g-g_init+1][y-g+1],
                        )
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] *
                            v.maintnance_cost_distance[g-g_init+1][y-g+1] *
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
                        charging_time = 0
                    else
                        charging_time =
                            v.battery_capacity[g-g_init+1] / v.peak_charging[g-g_init+1]
                    end
                    # value of time
                    vot = r.financial_status.VoT
                    los = route_length / speed + charging_time

                    intangible_costs = vot * los
                    add_to_expression!(
                        total_cost_expr,
                        intangible_costs * sum(
                            model[:f][y, (r.product.id, r.id, k.id), mv, g] *
                            k.length *
                            v.W[g-g_init+1] for k ∈ r.paths for
                            mv ∈ m_tv_pairs if mv[2] == v.id
                        ),
                    )
                end
            end
        end
        for m ∈ modes
            if !m.quantify_by_vehs
                for mv ∈ m_tv_pairs
                    if mv[1] == m.id
                        add_to_expression!(
                            total_cost_expr,
                            sum(
                                model[:f][y, (r.product.id, r.id, k.id), mv, g] *
                                sum(k.length for k ∈ r.paths) *
                                m.cost_per_ukm[y-y_init+1] for r ∈ odpairs for k ∈ r.paths
                                for g ∈ g_init:y
                            ),
                        )
                        # adding intangible_costs 
                        for r ∈ odpairs
                            vot = r.financial_status.VoT
                            speed = 30
                            if r.region_type.name == "urban"
                                waiting_time = 20 / 60
                            else
                                waiting_time = 40 / 60
                            end
                            waiting_time = 15
                            los = sum(k.length for k ∈ r.paths) / 30 + waiting_time
                            intangible_costs = vot * los
                            add_to_expression!(
                                total_cost_expr,
                                intangible_costs * sum(
                                    model[:f][y, (r.product.id, r.id, k.id), mv, g] *
                                    k.length for r ∈ odpairs for k ∈ r.paths for
                                    g ∈ g_init:y
                                ),
                            )
                        end
                    end
                end
            end
        end
        for t ∈ technologies
            for e ∈ edge_list
                add_to_expression!(
                    total_cost_expr,
                    model[:q_fuel_infr_plus_e][y, t.id, e.id] *
                    t.fuel.cost_per_kW[y-y_init+1],
                )
            end
            for n ∈ node_list
                add_to_expression!(
                    total_cost_expr,
                    model[:q_fuel_infr_plus_n][y, t.id, n.id] *
                    t.fuel.cost_per_kW[y-y_init+1],
                )
            end
        end
    end

    @objective(model, Min, total_cost_expr)
end