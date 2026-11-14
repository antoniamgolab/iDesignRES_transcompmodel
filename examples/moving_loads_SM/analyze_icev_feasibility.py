"""
Analyze if first 20 routes can be completed with ICEVs only (no charging time needed).
This checks if the infeasibility is due to BEV charging requirements vs fundamental issue.
"""

import yaml

print("="*80)
print("ICEV FEASIBILITY ANALYSIS - First 20 Routes")
print("="*80)

# Load input data from the active case
folder = "case_20251106_102427"  # From SM.jl line 20
input_path = f"input_data/{folder}"

print(f"Loading input from: {input_path}")
print()

# Load individual YAML files
with open(f'{input_path}/TechVehicle.yaml', 'r') as f:
    techvehicles = yaml.safe_load(f)

with open(f'{input_path}/Path.yaml', 'r') as f:
    paths = yaml.safe_load(f)

with open(f'{input_path}/Fuel.yaml', 'r') as f:
    fuels = yaml.safe_load(f)

with open(f'{input_path}/Technology.yaml', 'r') as f:
    technologies = yaml.safe_load(f)

with open(f'{input_path}/MandatoryBreaks.yaml', 'r') as f:
    mandatory_breaks = yaml.safe_load(f)

# Create lookups
tv_dict = {tv['id']: tv for tv in techvehicles}
path_dict = {path['id']: path for path in paths}
fuel_dict = {fuel['id']: fuel for fuel in fuels}
tech_dict = {tech['id']: tech for tech in technologies}

# Debug: Show available fuels
print(f"Available fuels:")
for fuel in fuels:
    print(f"  Fuel ID {fuel['id']}: {fuel['name']}")
print()

# Classify vehicles by fuel type
icev_tv_ids = []
bev_tv_ids = []
print(f"Loaded {len(techvehicles)} tech vehicles from file")
print(f"TV dict has {len(tv_dict)} entries")
print()

print(f"Classifying {len(techvehicles)} vehicles...")
for tv in techvehicles:
    tv_id = tv.get('id')
    tech_id = tv.get('technology')
    tech = tech_dict.get(tech_id)

    if tech:
        fuel_name = tech.get('fuel', '').lower()
        print(f"  TV{tv_id} ({tv.get('name')}): technology={tech_id}, fuel='{fuel_name}'")

        if 'diesel' in fuel_name or 'petrol' in fuel_name or 'gasoline' in fuel_name:
            icev_tv_ids.append(tv_id)
            print(f"    -> Classified as ICEV")
        elif 'electric' in fuel_name or 'battery' in fuel_name:
            bev_tv_ids.append(tv_id)
            print(f"    -> Classified as BEV")
        else:
            print(f"    -> Not classified (fuel: {fuel_name})")
    else:
        print(f"  TV{tv_id}: No technology found for tech_id={tech_id}")
print()

print(f"Vehicle Classification:")
print(f"  ICEVs (diesel/petrol): {len(icev_tv_ids)} vehicles")
print(f"  BEVs (electric): {len(bev_tv_ids)} vehicles")
print()

# Get first 20 unique paths with breaks
paths_with_breaks = {}
for mb in mandatory_breaks:
    path_id = mb['path_id']
    if path_id not in paths_with_breaks:
        paths_with_breaks[path_id] = []
    paths_with_breaks[path_id].append(mb)

first_20_paths = list(paths_with_breaks.keys())[:20]

print(f"Analyzing first {len(first_20_paths)} routes with mandatory breaks:")
print("="*80)
print()

# Check each route
summary = {
    'total_routes': len(first_20_paths),
    'icev_can_complete': 0,
    'icev_need_refuel': 0,
    'bev_need_multiple_charges': 0
}

for idx, path_id in enumerate(first_20_paths, 1):
    path = path_dict.get(path_id)
    if not path:
        print(f"{idx}. Path {path_id}: NOT FOUND in input data")
        continue

    breaks = paths_with_breaks[path_id]
    first_break = [mb for mb in breaks if mb.get('break_number') == 1 and mb.get('num_drivers') == 1]

    if not first_break:
        print(f"{idx}. Path {path_id}: No first break found")
        continue

    mb = first_break[0]

    print(f"{idx}. Path {path_id}")
    print(f"   Length: {path['length']:.0f} km")
    print(f"   Route: Node {path['sequence'][0]} -> Node {path['sequence'][-1]}")
    print(f"   First break at: {mb['cumulative_driving_time']:.2f}h driving")
    print(f"   Mandatory break: {mb['time_with_breaks'] - mb['cumulative_driving_time']:.2f}h (45 min)")
    print()

    # Check ICEV feasibility
    icev_feasible = False
    if icev_tv_ids:
        print(f"   ICEV Analysis (sample):")
        for tv_id in icev_tv_ids[:2]:  # Check first 2 ICEVs
            tv = tv_dict[tv_id]
            tech = tech_dict[tv['technology']]

            # Use first generation (index 0)
            battery_cap = tv['W'][0]  # kWh (fuel tank capacity for ICEV)
            efficiency = tv['AnnualRange'][0]  # km per kWh
            total_range = battery_cap * efficiency  # km

            print(f"     TV{tv_id} ({tech['fuel']}): Range={total_range:.0f}km, ", end="")

            if path['length'] <= total_range * 0.9:  # 90% safety margin
                print(f"[OK] CAN COMPLETE (no refuel)")
                icev_feasible = True
            else:
                refuels_needed = path['length'] / total_range
                print(f"[!] Needs {refuels_needed:.1f} refuels")
                if refuels_needed <= 2:
                    print(f"       -> Refueling time: ~10 min (fast, during mandatory break)")
                    icev_feasible = True

        if icev_feasible:
            summary['icev_can_complete'] += 1
        else:
            summary['icev_need_refuel'] += 1

    # Check BEV challenge
    if bev_tv_ids:
        print(f"   BEV Analysis (sample):")
        for tv_id in bev_tv_ids[:2]:  # Check first 2 BEVs
            tv = tv_dict[tv_id]
            tech = tech_dict[tv['technology']]

            # Use first generation
            battery_cap = tv['W'][0]  # kWh
            efficiency = tv['AnnualRange'][0]  # km per kWh
            total_range = battery_cap * efficiency  # km
            peak_charging = tv['peak_fueling'][0]  # kW

            print(f"     TV{tv_id} ({tech['fuel']}): Range={total_range:.0f}km, Charge={peak_charging:.0f}kW")

            if path['length'] <= total_range * 0.8:  # 80% safety for BEV
                print(f"       [OK] Can complete, but may need partial charge")
            else:
                charges_needed = path['length'] / (total_range * 0.8)
                energy_per_charge = battery_cap * 0.5  # Assume 50% recharge each stop
                charging_time = energy_per_charge / peak_charging  # hours

                print(f"       [!] Needs {charges_needed:.1f} charges")
                print(f"       -> Charging time per stop: {charging_time:.2f}h ({charging_time*60:.0f} min)")
                print(f"       -> REQUIRES MORE THAN 0.75h mandatory break!")

                if charges_needed > 1:
                    summary['bev_need_multiple_charges'] += 1

    print()

print("="*80)
print("SUMMARY")
print("="*80)
print(f"\nRoutes analyzed: {summary['total_routes']}")
print(f"  ICEVs can complete: {summary['icev_can_complete']}/{summary['total_routes']}")
print(f"  BEVs need extra charging time: {summary['bev_need_multiple_charges']}")
print()

print("="*80)
print("ROOT CAUSE OF INFEASIBILITY")
print("="*80)
print()
print("Current constraint: travel_time[break_location] == min_fleet_travel_time")
print()
print("Problem:")
print("  1. This forces travel_time to EXACTLY equal mandatory break time (0.75h)")
print("  2. BEVs need: 0.75h break + charging_time")
print("  3. With ==, there's no time for charging -> INFEASIBLE for BEVs")
print()
print("Why ICEVs would work:")
print("  - Refueling time: ~5-10 minutes (fast)")
print("  - Can refuel DURING the 45-minute mandatory break")
print("  - No extra time needed beyond mandatory break")
print()

print("="*80)
print("SOLUTIONS")
print("="*80)
print()
print("Option 1: CHANGE BACK TO >= (RECOMMENDED)")
print("  - Allows: travel_time >= min_fleet_travel_time")
print("  - BEVs can add charging time on top of mandatory break")
print("  - The 'long stops' you see are NECESSARY for BEV charging, not waste")
print()
print("Option 2: FORCE ICEV-ONLY SCENARIO")
print("  - Add constraint excluding BEVs from solution")
print("  - Only diesel/petrol vehicles allowed")
print("  - Model will be feasible with == constraint")
print()
print("Option 3: SEPARATE CHARGING CONSTRAINT")
print("  - Keep == for break time")
print("  - Add separate variable for charging time")
print("  - More complex model structure")
print()

print("RECOMMENDATION:")
print("Use '>=' constraint. Run the analysis in break_times.ipynb to verify that")
print("long stops are CHARGING-driven (necessary) not SLACK-driven (wasteful).")
print()
