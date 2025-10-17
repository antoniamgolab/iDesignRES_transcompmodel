# FIXED CODE FOR SOC VALIDATION IN results_SM.ipynb
# Replace the code starting around line 2383 (after "For each OD pair on this path")

# This is the CORRECTED version that separates SOC profiles by generation

for r_id, r_data in odpairs_on_path:
    # CHANGED: Create separate SOC profiles for each generation
    # OLD: soc_profile = []
    # NEW: Dictionary that maps generation -> list of SOC entries
    soc_profiles_by_gen = {}

    # Check generations g <= year (as per constraint)
    for gen in range(g_init, year + 1):
        # Initialize empty profile for this generation
        soc_profiles_by_gen[gen] = []

        # Calculate expected fleet size for this generation
        key_f = (year, (0, r_id, path_id), (1, tv_id), gen)
        if key_f not in output_data["f"]:
            continue

        flow = output_data["f"][key_f]
        if flow < 0.01:
            continue

        # Get parameters for THIS generation
        idx_gen = gen - g_init
        W_gen = tv_data.get("W", [1.0])[idx_gen] if isinstance(tv_data.get("W"), list) else tv_data.get("W", 1.0)
        annual_range_gen = tv_data.get("AnnualRange", [50000])[idx_gen] if isinstance(tv_data.get("AnnualRange"), list) else tv_data.get("AnnualRange", 50000)
        tank_capacity_gen = tv_data.get("tank_capacity", [100])[idx_gen] if isinstance(tv_data.get("tank_capacity"), list) else tv_data.get("tank_capacity", 100)
        spec_cons_gen = tv_data.get("spec_cons", [0.5])[idx_gen] if isinstance(tv_data.get("spec_cons"), list) else tv_data.get("spec_cons", 0.5)

        num_vehicles = (path_data['length'] / (W_gen * annual_range_gen)) * 1000 * flow
        fleet_tank_capacity = tank_capacity_gen * num_vehicles

        # Check SOC values along the route FOR THIS GENERATION ONLY
        for i, geo_id in enumerate(sequence):
            key_soc = (year, (0, r_id, path_id, geo_id), tv_id, f_l, gen)

            if key_soc in output_data["soc"]:
                soc_val = output_data["soc"][key_soc]
                cum_dist = cumulative_distance[i] if i < len(cumulative_distance) else 0

                # Check constraint_soc_max: SOC <= fleet_tank_capacity
                if soc_val > fleet_tank_capacity + 1e-3:  # tolerance for numerical errors
                    violations_soc_max.append({
                        'year': year,
                        'path_id': path_id,
                        'odpair': r_id,
                        'tv_id': tv_id,
                        'gen': gen,
                        'node_idx': i,
                        'geo_id': geo_id,
                        'soc': soc_val,
                        'fleet_capacity': fleet_tank_capacity,
                        'excess': soc_val - fleet_tank_capacity,
                        'cum_dist': cum_dist
                    })

                # Add to THIS generation's SOC profile
                soc_profiles_by_gen[gen].append({
                    'node_idx': i,
                    'geo_id': geo_id,
                    'soc': soc_val,
                    'fleet_capacity': fleet_tank_capacity,
                    'cum_dist': cum_dist,
                    'gen': gen,
                    'num_vehicles': num_vehicles
                })

    # NOW PRINT EACH GENERATION'S PROFILE SEPARATELY
    for gen in sorted(soc_profiles_by_gen.keys()):
        soc_profile = soc_profiles_by_gen[gen]

        if len(soc_profile) == 0:
            continue  # Skip generations with no SOC data

        # Get parameters for THIS generation for printing
        idx_gen = gen - g_init
        W_gen = tv_data.get("W", [1.0])[idx_gen] if isinstance(tv_data.get("W"), list) else tv_data.get("W", 1.0)
        annual_range_gen = tv_data.get("AnnualRange", [50000])[idx_gen] if isinstance(tv_data.get("AnnualRange"), list) else tv_data.get("AnnualRange", 50000)
        tank_capacity_gen = tv_data.get("tank_capacity", [100])[idx_gen] if isinstance(tv_data.get("tank_capacity"), list) else tv_data.get("tank_capacity", 100)
        spec_cons_gen = tv_data.get("spec_cons", [0.5])[idx_gen] if isinstance(tv_data.get("spec_cons"), list) else tv_data.get("spec_cons", 0.5)

        key_f = (year, (0, r_id, path_id), (1, tv_id), gen)
        flow = output_data["f"][key_f]
        num_vehicles = (path_data['length'] / (W_gen * annual_range_gen)) * 1000 * flow
        fleet_tank_capacity = tank_capacity_gen * num_vehicles

        print(f"\n      Generation {gen} (bought in {gen}):")
        print(f"        Number of vehicles: {num_vehicles:.2f}")
        print(f"        Fleet tank capacity: {fleet_tank_capacity:.2f} kWh")
        print(f"        SOC profile ({len(soc_profile)} nodes):")
        print(f"        {'Node':<6} {'Geo ID':<8} {'Dist (km)':>10}  {'SOC (kWh)':>12}  {'% of Fleet Cap':>15}")
        print(f"        {'-'*60}")

        # Show first 5 and last 5 nodes
        nodes_to_show = list(range(min(5, len(soc_profile)))) + list(range(max(5, len(soc_profile) - 5), len(soc_profile)))
        nodes_to_show = sorted(set(nodes_to_show))

        for idx in nodes_to_show:
            if idx < len(soc_profile):
                entry = soc_profile[idx]
                pct_full = (entry['soc'] / entry['fleet_capacity'] * 100) if entry['fleet_capacity'] > 0 else 0
                print(f"        {entry['node_idx']:<6} {entry['geo_id']:<8} {entry['cum_dist']:>10.2f}  {entry['soc']:>12.2f}  {pct_full:>14.1f}%")

        if len(soc_profile) > 10:
            print(f"        ... {len(soc_profile) - 10} nodes omitted ...")

        # SOC Tracking Verification (first 5 transitions)
        if len(soc_profile) > 1:
            print(f"\n        SOC Tracking Verification (first 5 transitions):")
            print(f"        {'Transition':<15} {'ΔDistance':<12} {'ΔSOC':<12} {'Expected ΔE':<15} {'Charging':<12} {'Balance':<10}")
            print(f"        {'-'*80}")

            for j in range(1, min(6, len(soc_profile))):
                prev_soc = soc_profile[j-1]['soc']
                curr_soc = soc_profile[j]['soc']
                prev_geo = soc_profile[j-1]['geo_id']
                curr_geo = soc_profile[j]['geo_id']

                dist_increment = soc_profile[j]['cum_dist'] - soc_profile[j-1]['cum_dist']
                soc_change = curr_soc - prev_soc

                # Expected energy consumption FOR THIS GENERATION
                expected_energy_loss = dist_increment * spec_cons_gen * num_vehicles

                # Check if charging occurred at current node
                key_s = (year, (0, r_id, path_id, curr_geo), tv_id, f_l, gen)
                charging = output_data["s"].get(key_s, 0) * 1000  # Convert to kWh

                # SOC balance: SOC_curr = SOC_prev - energy_consumed + charging
                expected_soc_change = -expected_energy_loss + charging
                balance_error = abs(soc_change - expected_soc_change)

                transition_label = f"{j-1}→{j}"
                status = "✓" if balance_error < 1e-2 else "✗"

                print(f"        {transition_label:<15} {dist_increment:>10.2f}  {soc_change:>10.2f}  {-expected_energy_loss:>13.2f}  {charging:>10.2f}  {status} {balance_error:.4f}")

                # Record violations
                if balance_error >= 1e-2:
                    violations_soc_track.append({
                        'year': year,
                        'path_id': path_id,
                        'odpair': r_id,
                        'tv_id': tv_id,
                        'gen': gen,
                        'transition': f"{j-1}→{j}",
                        'prev_geo': prev_geo,
                        'curr_geo': curr_geo,
                        'soc_change': soc_change,
                        'expected_change': expected_soc_change,
                        'error': balance_error
                    })

# KEY CHANGES:
# 1. Changed from single soc_profile = [] to soc_profiles_by_gen = {} dictionary
# 2. Each generation gets its own soc_profile list
# 3. SOC entries are added to the correct generation's list
# 4. Printing loops over each generation separately
# 5. num_vehicles, fleet_tank_capacity, and spec_cons_gen are calculated per generation
#    both when building the profile AND when validating energy balance
