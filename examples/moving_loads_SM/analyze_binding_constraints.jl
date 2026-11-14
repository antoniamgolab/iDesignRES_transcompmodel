# ============================================================================
# POST-SOLVE ANALYSIS: Binding constraints and shadow prices
# ============================================================================
# Run this AFTER optimize!(model) completes.
# Requires named constraints (con_stock_shift_upper, con_stock_shift_lower,
# con_demand_coverage, con_mode_shift_upper, con_mode_shift_lower, con_soc_max).
# Requires Crossover=1 for clean dual values.
# ============================================================================

using JuMP, Printf, Statistics

println("\n" * "="^80)
println("BINDING CONSTRAINT ANALYSIS (Shadow Prices / Dual Values)")
println("="^80)

technologies = data_structures["technology_list"]
modeled_years = data_structures["modeled_years"]
y_init = data_structures["y_init"]

# Helper: map technology id to name
tech_name = Dict(t.id => t.name for t in technologies)

# ============================================================================
# 1. VEHICLE STOCK SHIFT CONSTRAINTS (h growth/decline limits)
# ============================================================================
println("\n--- Vehicle Stock Shift Constraints ---")
println("Upper bound (growth limit): h_change ≤ α_h·total + β_h·prev_tech")
println("Lower bound (decline limit): -h_change ≤ α_h·total + β_h·prev_tech")
println()

if haskey(model, :con_stock_shift_upper)
    println("  Year  | Tech  | Upper dual    | Lower dual    | Binding?")
    println("  " * "-"^65)
    for y in filter(y -> y > y_init, modeled_years)
        for t in technologies
            d_upper = dual(model[:con_stock_shift_upper][y, t])
            d_lower = dual(model[:con_stock_shift_lower][y, t])

            binding_upper = abs(d_upper) > 1e-6
            binding_lower = abs(d_lower) > 1e-6

            status = if binding_upper && binding_lower
                "BOTH"
            elseif binding_upper
                "UPPER (growth limited)"
            elseif binding_lower
                "LOWER (decline limited)"
            else
                "-"
            end

            if binding_upper || binding_lower
                @printf("  %4d  | %-5s | %+12.4f  | %+12.4f  | %s\n",
                    y, tech_name[t.id], d_upper, d_lower, status)
            end
        end
    end
else
    println("  ⚠ con_stock_shift_upper not found in model")
end

# ============================================================================
# 2. MODE SHIFT CONSTRAINTS (rail growth rate)
# ============================================================================
println("\n--- Mode Shift Constraints (Rail) ---")
println("Upper bound: rail_growth ≤ α_f·total + β_f·prev_rail")
println("Lower bound: -rail_growth ≤ α_f·total + β_f·prev_rail")
println()

if haskey(model, :con_mode_shift_upper)
    modes = data_structures["mode_list"]
    rail_modes = filter(m -> m.id == 2, modes)
    rail_start_year = 2026

    println("  Year  | Upper dual    | Lower dual    | Binding?")
    println("  " * "-"^55)
    for y in filter(y -> y >= rail_start_year, modeled_years)
        for m in rail_modes
            d_upper = dual(model[:con_mode_shift_upper][y, m])
            d_lower = dual(model[:con_mode_shift_lower][y, m])

            binding_upper = abs(d_upper) > 1e-6
            binding_lower = abs(d_lower) > 1e-6

            status = if binding_upper
                "UPPER (rail growth limited)"
            elseif binding_lower
                "LOWER (rail decline limited)"
            else
                "-"
            end

            @printf("  %4d  | %+12.4f  | %+12.4f  | %s\n",
                y, d_upper, d_lower, status)
        end
    end
else
    println("  ⚠ con_mode_shift_upper not found in model")
end

# ============================================================================
# 3. DEMAND COVERAGE CONSTRAINTS (shadow price of demand)
# ============================================================================
println("\n--- Demand Coverage Constraints (top 10 by |dual|) ---")
println("Shadow price = marginal cost of serving one more unit of demand on that OD pair")
println()

if haskey(model, :con_demand_coverage)
    odpairs = data_structures["odpair_list"]
    dual_list = []
    for y in modeled_years
        for r in odpairs
            d = dual(model[:con_demand_coverage][y, r])
            if abs(d) > 1e-6
                push!(dual_list, (year=y, odpair_id=r.id, dual=d))
            end
        end
    end

    # Sort by absolute dual value (most constrained demand first)
    sort!(dual_list, by=x -> abs(x.dual), rev=true)
    println("  Year  | OD pair | Shadow price")
    println("  " * "-"^40)
    for (i, entry) in enumerate(dual_list[1:min(20, length(dual_list))])
        @printf("  %4d  | %7d | %+12.4f\n", entry.year, entry.odpair_id, entry.dual)
    end
    println("  ... ($(length(dual_list)) non-zero duals total)")

    # Summary statistics by year
    println("\n  Shadow price statistics by year:")
    println("  Year  | Mean       | Min        | Max        | Count")
    println("  " * "-"^55)
    for y in modeled_years
        duals_y = [x.dual for x in dual_list if x.year == y]
        if !isempty(duals_y)
            @printf("  %4d  | %+10.2f | %+10.2f | %+10.2f | %d\n",
                y, mean(duals_y), minimum(duals_y), maximum(duals_y), length(duals_y))
        end
    end
else
    println("  ⚠ con_demand_coverage not found in model")
end

# ============================================================================
# 4. SOC MAX CONSTRAINTS (battery capacity limit)
# ============================================================================
println("\n--- SOC Max Constraints (top binding by |dual|) ---")
println("Shadow price = value of additional battery capacity on that segment")
println()

if haskey(model, :con_soc_max)
    soc_duals = []
    for key in keys(model[:con_soc_max])
        d = dual(model[:con_soc_max][key...])
        if abs(d) > 1e-4
            push!(soc_duals, (key=key, dual=d))
        end
    end

    sort!(soc_duals, by=x -> abs(x.dual), rev=true)
    n_binding = length(soc_duals)
    println("  $n_binding SOC max constraints have non-zero duals")
    if n_binding > 0
        println("  Top 10:")
        for (i, entry) in enumerate(soc_duals[1:min(10, n_binding)])
            @printf("    %s : dual = %+.6f\n", string(entry.key), entry.dual)
        end
    end
else
    println("  ⚠ con_soc_max not found in model")
end

# ============================================================================
# 5. BEV SHARE INIT CONSTRAINT
# ============================================================================
println("\n--- BEV Share Init Constraint ---")
if haskey(model, :constraint_bev_share_init)
    d = dual(model[:constraint_bev_share_init])
    @printf("  Dual value: %+.6f  (binding: %s)\n", d, abs(d) > 1e-6 ? "YES" : "no")
else
    println("  ⚠ constraint_bev_share_init not found")
end

# ============================================================================
# SUMMARY
# ============================================================================
println("\n" * "="^80)
println("SUMMARY: Key binding constraints that shape the transition")
println("="^80)

# Count binding stock shift constraints
if haskey(model, :con_stock_shift_upper)
    n_upper_binding = 0
    n_lower_binding = 0
    for y in filter(y -> y > y_init, modeled_years)
        for t in technologies
            if abs(dual(model[:con_stock_shift_upper][y, t])) > 1e-6
                n_upper_binding += 1
            end
            if abs(dual(model[:con_stock_shift_lower][y, t])) > 1e-6
                n_lower_binding += 1
            end
        end
    end
    total_stock = length(filter(y -> y > y_init, modeled_years)) * length(technologies)
    println("  Vehicle stock shift: $n_upper_binding/$total_stock upper + $n_lower_binding/$total_stock lower binding")
end

if haskey(model, :con_mode_shift_upper)
    n_mode_upper = 0
    n_mode_lower = 0
    for y in filter(y -> y >= 2026, modeled_years)
        for m in filter(m -> m.id == 2, data_structures["mode_list"])
            if abs(dual(model[:con_mode_shift_upper][y, m])) > 1e-6
                n_mode_upper += 1
            end
            if abs(dual(model[:con_mode_shift_lower][y, m])) > 1e-6
                n_mode_lower += 1
            end
        end
    end
    total_mode = length(filter(y -> y >= 2026, modeled_years))
    println("  Mode shift (rail):   $n_mode_upper/$total_mode upper + $n_mode_lower/$total_mode lower binding")
end

println("="^80)
println("Done.")
