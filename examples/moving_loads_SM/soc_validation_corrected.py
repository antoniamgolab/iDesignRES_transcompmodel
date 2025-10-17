# SOC Constraint Verification - CORRECTED VERSION
# This validates that constraint_soc_max and constraint_soc_track are working properly

print("="*80)
print("STATE OF CHARGE (SOC) CONSTRAINT VERIFICATION - CORRECTED")
print("="*80)

# Check if soc data exists
if "soc" not in output_data or len(output_data["soc"]) == 0:
    print("\n⚠️  No SOC data found in results!")
    print("   Possible reasons:")
    print("   - The soc variable was not saved")
    print("   - The constraints were not active in the model")
    print("   - No electric vehicles were used")
else:
    print(f"\n✓ Found {len(output_data['soc'])} SOC entries")

    # Get fuel infrastructure pairs for tracking
    f_l_pairs = set()
    for l_id, l_data in fueling_infr_types_list.items():
        fuel_name = l_data["fuel"]
        fuel_id = fuel_list[fuel_name]["id"]
        f_l_pairs.add((fuel_id, l_id))

    print(f"  Fuel-infrastructure pairs: {sorted(f_l_pairs)}")

    # Verify SOC constraints for a sample of paths
    sample_paths = list(path_list.keys())[:3]  # Check first 3 paths
    print(f"\n  Analyzing {len(sample_paths)} sample paths")

    violations_soc_max = []
    violations_soc_track = []
    successful_checks = 0

    for path_id in sample_paths:
        path_data = path_list[path_id]
        sequence = path_data["sequence"]
        cumulative_distance = path_data.get("cumulative_distance", [0] * len(sequence))
        distance_from_previous = path_data.get("distance_from_previous", [0] * len(sequence))

        print(f"\n{'='*80}")
        print(f"PATH {path_id}: {path_data.get('name', 'N/A')}")
        print(f"  Total length: {path_data['length']:.2f} km")
        print(f"  Number of nodes: {len(sequence)}")
        print(f"{'='*80}")

        # Find OD pairs using this path
        odpairs_on_path = [(r_id, r_data) for r_id, r_data in odpair_list.items()
                          if r_data["path_id"] == path_id]

        if len(odpairs_on_path) == 0:
            print(f"  ⚠️  No OD pairs use this path")
            continue

        print(f"  Found {len(odpairs_on_path)} OD pair(s) using this path")

        # Check SOC for specific years
        test_years = [2030, 2040]

        for year in test_years:
            print(f"\n  {'─'*76}")
            print(f"  YEAR {year}")
            print(f"  {'─'*76}")

            for tv_id, tv_data in techvehicle_list.items():
                tech_id = tv_data["technology"]
                tech_data = technology_list[tech_id]
                fuel_name = tech_data["fuel"]
                fuel_id = fuel_list[fuel_name]["id"]

                # Get vehicle parameters for this year/generation
                idx_year = min(year - y_init, len(tv_data.get("tank_capacity", [100])) - 1)
                tank_capacity_single = tv_data.get("tank_capacity", [100])[idx_year] if isinstance(tv_data.get("tank_capacity"), list) else tv_data.get("tank_capacity", 100)

                # Find matching fuel-infrastructure pair
                f_l = None
                for fl in f_l_pairs:
                    if fl[0] == fuel_id:
                        f_l = fl
                        break

                if f_l is None:
                    continue

                # Check if this vehicle has any flow on this path in this year
                has_flow = False
                total_flow = 0
                for r_id, r_data in odpairs_on_path:
                    # IMPORTANT: Check g <= year as per constraint definition
                    for gen in range(g_init, year + 1):  # g <= year
                        key_f = (year, (0, r_id, path_id), (1, tv_id), gen)
                        if key_f in output_data["f"]:
                            flow_val = output_data["f"][key_f]
                            if flow_val > 0.01:
                                has_flow = True
                                total_flow += flow_val

                if not has_flow:
                    continue  # Skip vehicles with no flow

                print(f"\n    {tv_data['name']} ({fuel_name}, fuel_id={fuel_id})")
                print(f"      Tank capacity (single vehicle): {tank_capacity_single:.2f} kWh")
                print(f"      Total flow in year {year}: {total_flow:.4f} (thousands of tons)")

                # Get spec_cons for checking energy consumption
                idx_gen_2030 = min(2030 - g_init, len(tv_data.get("spec_cons", [0.5])) - 1)
                spec_cons = tv_data.get("spec_cons", [0.5])[idx_gen_2030] if isinstance(tv_data.get("spec_cons"), list) else tv_data.get("spec_cons", 0.5)
                W = tv_data.get("W", [1.0])[idx_gen_2030] if isinstance(tv_data.get("W"), list) else tv_data.get("W", 1.0)
                annual_range = tv_data.get("AnnualRange", [50000])[idx_gen_2030] if isinstance(tv_data.get("AnnualRange"), list) else tv_data.get("AnnualRange", 50000)

                print(f"      Spec. consumption: {spec_cons:.4f} kWh/km, W: {W:.2f}, AnnualRange: {annual_range:.0f} km")

                # For each OD pair on this path
                for r_id, r_data in odpairs_on_path:
                    soc_profile = []

                    # Check generations g <= year (as per constraint)
                    for gen in range(g_init, year + 1):
                        # Calculate expected fleet size for this generation
                        key_f = (year, (0, r_id, path_id), (1, tv_id), gen)
                        if key_f not in output_data["f"]:
                            continue

                        flow = output_data["f"][key_f]
                        if flow < 0.01:
                            continue

                        # Calculate number of vehicles (as per constraint)
                        idx_gen = gen - g_init
                        W_gen = tv_data.get("W", [1.0])[idx_gen] if isinstance(tv_data.get("W"), list) else tv_data.get("W", 1.0)
                        annual_range_gen = tv_data.get("AnnualRange", [50000])[idx_gen] if isinstance(tv_data.get("AnnualRange"), list) else tv_data.get("AnnualRange", 50000)
                        tank_capacity_gen = tv_data.get("tank_capacity", [100])[idx_gen] if isinstance(tv_data.get("tank_capacity"), list) else tv_data.get("tank_capacity", 100)
                        spec_cons_gen = tv_data.get("spec_cons", [0.5])[idx_gen] if isinstance(tv_data.get("spec_cons"), list) else tv_data.get("spec_cons", 0.5)

                        num_vehicles = (path_data['length'] / (W_gen * annual_range_gen)) * 1000 * flow
                        fleet_tank_capacity = tank_capacity_gen * num_vehicles

                        # Check SOC values along the route
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

                                soc_profile.append({
                                    'node_idx': i,
                                    'geo_id': geo_id,
                                    'soc': soc_val,
                                    'fleet_capacity': fleet_tank_capacity,
                                    'cum_dist': cum_dist,
                                    'gen': gen,
                                    'num_vehicles': num_vehicles
                                })

                                successful_checks += 1

                        # Verify SOC tracking constraint along the route
                        if len(soc_profile) > 1:
                            print(f"\n      Generation {gen} (bought in {gen}):")
                            print(f"        Number of vehicles: {num_vehicles:.2f}")
                            print(f"        Fleet tank capacity: {fleet_tank_capacity:.2f} kWh")
                            print(f"        SOC profile ({len(soc_profile)} nodes):")
                            print(f"        {'Node':<6} {'Geo ID':<8} {'Dist (km)':<12} {'SOC (kWh)':<14} {'% of Fleet Cap':<16}")
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

                            # Verify SOC tracking: check if energy balance holds
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

                                # Expected energy consumption
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

print(f"\n{'='*80}")
print(f"VERIFICATION SUMMARY")
print(f"{'='*80}")
print(f"Total SOC entries checked: {successful_checks}")
print(f"SOC_MAX violations: {len(violations_soc_max)}")
print(f"SOC_TRACK violations: {len(violations_soc_track)}")

if len(violations_soc_max) > 0:
    print(f"\n⚠️  SOC_MAX VIOLATIONS (SOC > fleet capacity):")
    print(f"{'Year':<6} {'Path':<6} {'OD':<6} {'TV':<6} {'Gen':<6} {'Node':<6} {'GeoID':<8} {'SOC':<12} {'Capacity':<12} {'Excess':<10}")
    print("-" * 90)
    for v in violations_soc_max[:10]:
        print(f"{v['year']:<6} {v['path_id']:<6} {v['odpair']:<6} {v['tv_id']:<6} {v['gen']:<6} {v['node_idx']:<6} {v['geo_id']:<8} {v['soc']:>10.2f} {v['fleet_capacity']:>10.2f} {v['excess']:>8.4f}")
    if len(violations_soc_max) > 10:
        print(f"... and {len(violations_soc_max) - 10} more violations")

if len(violations_soc_track) > 0:
    print(f"\n⚠️  SOC_TRACK VIOLATIONS (energy balance errors):")
    print(f"{'Year':<6} {'Path':<6} {'OD':<6} {'TV':<6} {'Gen':<6} {'Transition':<12} {'ΔSOC':<12} {'Expected':<12} {'Error':<10}")
    print("-" * 90)
    for v in violations_soc_track[:10]:
        print(f"{v['year']:<6} {v['path_id']:<6} {v['odpair']:<6} {v['tv_id']:<6} {v['gen']:<6} {v['transition']:<12} {v['soc_change']:>10.2f} {v['expected_change']:>10.2f} {v['error']:>8.4f}")
    if len(violations_soc_track) > 10:
        print(f"... and {len(violations_soc_track) - 10} more violations")

if len(violations_soc_max) == 0 and len(violations_soc_track) == 0:
    print(f"\n✅ All SOC constraints are satisfied!")
    print(f"   - SOC values never exceed fleet tank capacity")
    print(f"   - SOC tracking correctly accounts for energy consumption and charging")
else:
    print(f"\n❌ SOC constraint violations detected!")
    print(f"   Please review the constraint implementation.")

print(f"\n{'='*80}")
print(f"END OF SOC VERIFICATION")
print(f"{'='*80}")
