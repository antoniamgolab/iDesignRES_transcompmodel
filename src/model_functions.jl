"""

    This file contains functions relating to the mathematical formulation of the model, i.e., the definition of constraints and the objective function, including also the definition of decision variables.

"""

using YAML, JuMP
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

    data_structures["m_tv_pairs"] = m_tv_pairs
    data_structures["techvehicle_ids"] = techvehicle_ids
    data_structures["t_v_pairs"] = t_v_pairs
    data_structures["p_r_k_pairs"] = p_r_k_pairs
    data_structures["p_r_k_e_pairs"] = p_r_k_e_pairs
    data_structures["p_r_k_n_pairs"] = p_r_k_n_pairs
    data_structures["p_r_k_g_pairs"] = p_r_k_g_pairs
    data_structures["r_k_pairs"] = create_r_k_set(data_structures["odpair_list"])
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
        model,
        n_fueling[y in y_init:Y_end, p_r_k_g_pairs, f_id in [f.id for f ∈ fuel_list]] >= 0
    )
    if data_structures["supplytype_list"] != []
        supplytype_list = data_structures["supplytype_list"]
        @variable(
            model,
            q_supply_infr_plus[
                y in y_init:Y_end,
                s_id in [s.id for s ∈ supplytype_list],
                geo_id in [geo.id for geo ∈ geographic_element_list],
            ] >= 0
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

    # case 2.1 : g < y && g > y
    valid_subset_case2 = filter(t -> t[2] < t[1], all_indices)
    for (y, g, r, tv) ∈ valid_subset_case2
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
        ]) <=
        r.financial_status.monetary_budget_purchase_ub *
        mean(r.F) *
        (data_structures["Y_end"] - data_structures["y_init"] + 1) *
        (1 / r.financial_status.monetary_budget_purchase_time_horizon) + sum(
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
        mean(r.F) *
        (data_structures["Y_end"] - data_structures["y_init"] + 1) *
        (1 / r.financial_status.monetary_budget_purchase_time_horizon) - sum(
            model[:budget_penalty_minus][y, r.id] for
            y ∈ data_structures["y_init"]:data_structures["Y_end"]
        )
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
                model[:h_plus][y, r.id, v.id, g] * v.capital_cost[g-g_init+1] for y ∈ y0 for
                v ∈ techvehicles for g ∈ g_init:y
            ) <=
            r.financial_status.monetary_budget_purchase_ub * mean(
                r.F[(y0[1]-data_structures["y_init"]+1):(y0[1]-data_structures["y_init"]+r.financial_status.monetary_budget_purchase_time_horizon-1)],
            ) + sum(model[:budget_penalty_plus][y, r.id] for y ∈ y0)
        )
        @constraint(
            model,
            [y0 in y_set],
            sum(
                model[:h_plus][y, r.id, v.id, g] * v.capital_cost[g-g_init+1] for y ∈ y0 for
                v ∈ techvehicles for g ∈ g_init:y
            ) >=
            r.financial_status.monetary_budget_purchase_lb * mean(
                r.F[(y0[1]-data_structures["y_init"]+1):(y0[1]-data_structures["y_init"]+r.financial_status.monetary_budget_purchase_time_horizon-1)],
            ) - sum(model[:budget_penalty_minus][y, r.id] for y ∈ y0)
        )
    end
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


function constraint_supply_infrastructure(model::JuMP.Model, data_structures::Dict)
    technologies = data_structures["technology_list"]

    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    techvehicles = data_structures["techvehicle_list"]
    fuel_list = data_structures["fuel_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    initsupplyinfr_list = data_structures["initialsupplyinfr_list"]
    gamma = data_structures["gamma"]
    supplytype_list = data_structures["supplytype_list"]

    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            l in supplytype_list,
            geo in geographic_element_list,
        ],
        initsupplyinfr_list[findfirst(
            i -> i.supply_type.name == l.name && i.allocation.id == geo.id,
            initsupplyinfr_list,
        )].installed_kW +
        sum(model[:q_supply_infr_plus][y0, l.id, geo.id] for y0 ∈ data_structures["y_init"]:y) >=
        sum(
            gamma * model[:s][y, p_r_k_g, tv.id] for p_r_k_g ∈ p_r_k_g_pairs for
            tv ∈ techvehicles for f ∈ fuel_list if p_r_k_g[4] == geo.id &&
            tv.technology.fuel.name == f.name &&
            l.fuel.name == f.name
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
            model[:f][y, p_r_k, m_tv, g] for p_r_k ∈ data_structures["p_r_k_pairs"] for
            m_tv ∈ data_structures["m_tv_pairs"] for g in data_structures["g_init"]:y if
            geo in path_list[findfirst(p -> p.id == p_r_k[3], path_list)].sequence && m.id == m_tv[1]
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
            model[:s][y, (p.id, r_k[1], r_k[2], el.id), v.id] for
            el ∈ paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence
        ) >= sum(
            (
                (v.spec_cons[g-g_init+1]) / v.W[g-g_init+1] *
                paths[findfirst(p0 -> p0.id == r_k[2], paths)].length
            ) * model[:f][y, (p.id, r_k[1], r_k[2]), (v.vehicle_type.mode.id, v.id), g] for
            g ∈ g_init:y
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

    # for y = y_init
    @constraint(
        model,
        [r in odpairs, t in technologies],
        (
            sum(
                model[:h][y_init, r.id, tv.id, g] for g ∈ g_init:y_init for
                tv ∈ techvehicles if tv.technology.id == t.id
            ) - sum(
                model[:h_exist][y_init, r.id, tv.id, g] for g ∈ g_init:y_init for
                tv ∈ techvehicles if tv.technology.id == t.id
            )
        ) <=
        alpha_h * sum(
            model[:h][y_init, r.id, tv.id, g] for g ∈ g_init:(y_init-1) for
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
                model[:h][y_init, r.id, tv.id, g] for g ∈ g_init:y_init for
                tv ∈ techvehicles if g <= y_init && tv.technology.id == t.id
            ) - sum(
                model[:h_exist][y_init, r.id, tv.id, g] for g ∈ g_init:y_init for
                tv ∈ techvehicles if g <= y_init - 1 && tv.technology.id == t.id
            )
        ) <=
        alpha_h * sum(
            model[:h][y_init, r.id, tv.id, g] for g ∈ g_init:(y_init-1) for
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
                tv ∈ techvehicles if g <= y && tv.technology.id == t.id
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:y for
                tv ∈ techvehicles if g <= y - 1 && tv.technology.id == t.id
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv.id, g] for g ∈ g_init:(y-1) for tv ∈ techvehicles) +
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
                tv ∈ techvehicles if g <= y && tv.technology.id == t.id
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:y for
                tv ∈ techvehicles if g <= y - 1 && tv.technology.id == t.id
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv.id, g] for g ∈ g_init:(y-1) for tv ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g]  for g ∈ g_init:(y-1) for
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
    max_mode_share_list = data_structures["max_mode_shares_list"]
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
    min_mode_share_list = data_structures["min_mode_shares_list"]
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
                    10^(-3) for r ∈ odpairs for k ∈ r.paths for g ∈ g_init:y
                ) <= el.emission
            )
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
        discount_factor = 1 / ((1 + discount_rate)^(y - y_init))
        for r ∈ odpairs
            add_to_expression!(
                total_cost_expr,
                model[:budget_penalty_plus][y, r.id] *
                data_structures["budget_penalty_plus"] *
                discount_factor,
            )
            add_to_expression!(
                total_cost_expr,
                model[:budget_penalty_minus][y, r.id] *
                data_structures["budget_penalty_minus"] *
                discount_factor,
            )
        end
        for v ∈ techvehicles
            if findfirst(
                elem -> elem.vehicle_type.id == v.vehicle_type.id && y in elem.years,
                vehicle_subsidy_list,
            ) != nothing
                veh_sub = vehicle_subsidy_list[findfirst(
                    elem ->
                        elem.vehicle_type.id == v.vehicle_type.id && y in elem.years,
                    vehicle_subsidy_list,
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

                for k ∈ r.paths
                    for geo ∈ k.sequence
                        add_to_expression!(
                            total_cost_expr,
                            model[:s][y, (r.product.id, r.id, k.id, geo.id), v.id] *
                            fuel_cost *
                            discount_factor +
                            10^(-3) *
                            model[:s][y, (r.product.id, r.id, k.id, geo.id), v.id] *
                            v.technology.fuel.emission_factor[y-y_init+1] *
                            geo.carbon_price[y-y_init+1] *
                            discount_factor,
                        )
                    end
                end

                for g ∈ g_init:y
                    capital_cost = capital_cost_map[(v.id, g)]

                    add_to_expression!(
                        total_cost_expr,
                        model[:h_plus][y, r.id, v.id, g] *
                        (capital_cost - veh_sub) *
                        discount_factor,
                    )

                    if y - g < v.Lifetime[g-g_init+1]
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] *
                            v.maintenance_cost_annual[g-g_init+1][y-g+1] *
                            discount_factor,
                        )
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] *
                            v.maintenance_cost_distance[g-g_init+1][y-g+1] *
                            route_length *
                            discount_factor,
                        )
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] *
                            regiontypes[findfirst(
                                rt -> rt.name == r.region_type.name,
                                regiontypes,
                            )].costs_fix[y-y+1] *
                            discount_factor,
                        )
                    end


                    # value of time

                    # the detour time reduction needs to go somewhere els
                    for k ∈ r.paths
                        vot = r.financial_status.VoT
                        los_wo_detour =
                            route_length / speed +
                            v.vehicle_type.mode.waiting_time[y-y_init+1] +
                            v.fueling_time[g-g_init+1]
                        intangible_costs = vot * los_wo_detour
                        add_to_expression!(
                            total_cost_expr,
                            discount_factor *
                            intangible_costs *
                            model[:f][
                                y,
                                (r.product.id, r.id, k.id),
                                (v.vehicle_type.mode.id, v.id),
                                g,
                            ],
                        )
                    end
                end
            end
        end
        for m ∈ modes
            for geo ∈ geographic_element_list
                add_to_expression!(
                    total_cost_expr,
                    model[:q_mode_infr_plus][y, m.id, geo.id] *
                    m.infrastructure_expansion_costs[y-y_init+1] *
                    discount_factor,
                )
                for y0 ∈ y_init:y
                    add_to_expression!(
                        total_cost_expr,
                        (
                            initialmodeinfr_list[findfirst(
                                i -> i.mode.id == m.id && i.allocation == geo.id,
                                initialmodeinfr_list,
                            )].installed_ukm + model[:q_mode_infr_plus][y0, m.id, geo.id]
                        ) *
                        m.infrastructure_om_costs[y-y_init+1] *
                        discount_factor,
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
                                        discount_factor *
                                        route_length *
                                        (
                                            m.cost_per_ukm[y-y_init+1] +
                                            m.emission_factor[y-y_init+1] *
                                            10^(-3) *
                                            create_emission_price_along_path(
                                                k,
                                                y - y_init + 1,
                                                data_structures,
                                            )
                                        ),
                                    )
                                    add_to_expression!(
                                        total_cost_expr,
                                        intangible_costs *
                                        discount_factor *
                                        model[:f][y, (r.product.id, r.id, k.id), mv, g],
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
                    f.cost_per_kW[y-y_init+1] *
                    discount_factor,
                )
                for y0 ∈ y_init:y
                    add_to_expression!(
                        total_cost_expr,
                        (
                            initialfuelinfr_list[findfirst(
                                i -> i.fuel.id == f.id && i.allocation == geo.id,
                                initialfuelinfr_list,
                            )].installed_kW + model[:q_fuel_infr_plus][y0, f.id, geo.id]
                        ) *
                        f.fueling_infrastructure_om_costs[y-y_init+1] *
                        discount_factor,
                    )
                end
            end
        end

        if data_structures["initialsupplyinfr_list"] != []
            supplytype_list = data_structures["supplytype_list"]
            initialsupplyinfr_list = data_structures["initialsupplyinfr_list"]
            for st ∈ supplytype_list
                for geo ∈ geographic_element_list
                    add_to_expression!(
                        total_cost_expr,
                        model[:q_supply_infr_plus][y, st.id, geo.id] *
                        st.install_costs[y-y_init+1] *
                        discount_factor,
                    )
                    for y0 ∈ y_init:y
                        add_to_expression!(
                            total_cost_expr,
                            (
                                initialsupplyinfr_list[findfirst(
                                    i -> i.supply_type.id == st.id && i.allocation.id == geo.id,
                                    initialsupplyinfr_list,
                                )].installed_kW +
                                model[:q_supply_infr_plus][y0, st.id, geo.id]
                            ) *
                            st.om_costs[y-y_init+1] *
                            discount_factor,
                        )
                    end
                end
            end

        end
    end
    @objective(model, Min, total_cost_expr)
end
