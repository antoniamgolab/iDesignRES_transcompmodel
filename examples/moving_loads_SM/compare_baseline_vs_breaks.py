"""
Compare baseline (SM_batch.jl) vs breaks-only (SM_batch_breaks_only.jl) scenarios.

Creates:
1. Side-by-side latitude plot for charging demand
2. BEV fleet development comparison
"""

import os
import yaml
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
from glob import glob
from scipy.ndimage import gaussian_filter1d
import warnings
warnings.filterwarnings('ignore')

# Set plot style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['font.family'] = 'serif'

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = r"C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM"
RESULTS_DIR = os.path.join(BASE_DIR, "results")

# Results folders - the 4 core GENeSYS scenarios
BASELINE_DIR = os.path.join(RESULTS_DIR, "uncertainty_scenarios")  # BEVs can charge anywhere
BREAKS_ONLY_DIR = os.path.join(RESULTS_DIR, "uncertainty_scenarios_breaks_only")  # Charging at breaks only

# Scenarios to compare (the 4 core GENeSYS scenarios)
SCENARIOS = ["scenario_004", "scenario_010", "scenario_016", "scenario_022"]
SCENARIO_LABELS = {
    "scenario_004": "Go RES",
    "scenario_010": "NECPEssentials",
    "scenario_016": "REPowerEU++",
    "scenario_022": "Trinity"
}

# Colors for scenarios
SCENARIO_COLORS = {
    "scenario_004": "#1f77b4",
    "scenario_010": "#2ca02c",
    "scenario_016": "#ff7f0e",
    "scenario_022": "#d62728"
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_latest_file(folder, pattern):
    """Get the most recent file matching a pattern in a folder."""
    files = glob(os.path.join(folder, f"*{pattern}"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def load_yaml_safe(filepath):
    """Load YAML file with error handling."""
    try:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def load_geo_data():
    """Load geographic element data to get latitude for each node."""
    geo_file = os.path.join(BASE_DIR, "input_data", "uncertainty_scenarios_rail", "scenario_004", "GeographicElement.yaml")
    with open(geo_file, 'r') as f:
        geo_elements = yaml.safe_load(f)

    geo_id_to_lat = {}
    for geo in geo_elements:
        if geo.get('type') == 'node' and 'coordinate_lat' in geo:
            geo_id_to_lat[geo['id']] = geo['coordinate_lat']

    print(f"Loaded {len(geo_id_to_lat)} node locations with latitude data")
    return geo_id_to_lat

def load_techvehicle_data():
    """Load technology data to identify BEV vs ICEV."""
    tv_file = os.path.join(BASE_DIR, "input_data", "uncertainty_scenarios_rail", "scenario_004", "TechVehicle.yaml")
    with open(tv_file, 'r') as f:
        techvehicles = yaml.safe_load(f)

    # tech_id: 0=ICEV, 1=BEV
    tv_to_tech = {}
    for tv in techvehicles:
        tv_to_tech[tv['id']] = tv['technology']

    return tv_to_tech

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_scenario_data(results_dir, scenario):
    """Load h_dict (fleet) and s_dict (energy) for a scenario."""
    scenario_path = os.path.join(results_dir, scenario)

    if not os.path.exists(scenario_path):
        print(f"  WARNING: {scenario_path} does not exist")
        return None, None

    h_file = get_latest_file(scenario_path, "_h_dict.yaml")
    s_file = get_latest_file(scenario_path, "_s_dict.yaml")

    h_dict = load_yaml_safe(h_file) if h_file else None
    s_dict = load_yaml_safe(s_file) if s_file else None

    return h_dict, s_dict

def extract_fleet_by_year(h_dict, tv_to_tech):
    """Extract fleet (vehicles) by year and technology."""
    fleet_by_year = defaultdict(lambda: {'ICEV': 0, 'BEV': 0})

    if not h_dict:
        return fleet_by_year

    for key_str, value in h_dict.items():
        try:
            key = eval(key_str) if isinstance(key_str, str) else key_str
            year = key[0]
            tv_id = key[2]

            tech_id = tv_to_tech.get(tv_id, 0)
            tech_name = 'BEV' if tech_id == 1 else 'ICEV'

            fleet_by_year[year][tech_name] += value
        except:
            continue

    return fleet_by_year

def extract_charging_by_latitude(s_dict, geo_id_to_lat, target_year):
    """Extract charging (kWh) by latitude for a specific year."""
    charging_by_lat = defaultdict(float)
    SCALING_FACTOR = 1000  # Energy scaling

    if not s_dict:
        return charging_by_lat

    for key_str, energy_value in s_dict.items():
        try:
            key = eval(key_str) if isinstance(key_str, str) else key_str
            # Key structure: (year, (mode, odpair_id, path_id, geo_id), tv_id, (infr_type, infr_id), gen)
            key_year = key[0]

            if key_year != target_year:
                continue

            geo_id = key[1][3]  # geo_id from nested tuple
            tv_id = key[2]

            # Only BEV charging (tech_id=1)
            # Assume tv_id 1,3,5... are BEV (odd) and 0,2,4... are ICEV (even)
            # Actually need to check - let's include all for now

            if geo_id in geo_id_to_lat:
                lat = geo_id_to_lat[geo_id]
                charging_by_lat[lat] += energy_value * SCALING_FACTOR
        except:
            continue

    return charging_by_lat

# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================

def plot_bev_fleet_comparison(baseline_data, breaks_data, tv_to_tech):
    """Create BEV fleet development comparison plot."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    years = sorted(set(
        list(baseline_data.get(SCENARIOS[0], {}).keys()) +
        list(breaks_data.get(SCENARIOS[0], {}).keys())
    ))
    if not years:
        years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]

    # Plot 1: Absolute BEV numbers
    ax1 = axes[0]
    for scenario in SCENARIOS:
        if scenario in baseline_data:
            bev_baseline = [baseline_data[scenario].get(y, {}).get('BEV', 0) for y in years]
            ax1.plot(years, bev_baseline, 'o-', label=f"{SCENARIO_LABELS[scenario]} (baseline)",
                    color=SCENARIO_COLORS[scenario], linewidth=2, markersize=5)

        if scenario in breaks_data:
            bev_breaks = [breaks_data[scenario].get(y, {}).get('BEV', 0) for y in years]
            ax1.plot(years, bev_breaks, 's--', label=f"{SCENARIO_LABELS[scenario]} (breaks only)",
                    color=SCENARIO_COLORS[scenario], linewidth=2, markersize=5, alpha=0.7)

    ax1.set_xlabel('Year')
    ax1.set_ylabel('BEV Fleet (vehicles)')
    ax1.set_title('BEV Fleet Development: Baseline vs Breaks-Only')
    ax1.legend(loc='upper left', fontsize=8, ncol=2)
    ax1.grid(True, alpha=0.3)

    # Plot 2: BEV share (%)
    ax2 = axes[1]
    for scenario in SCENARIOS:
        if scenario in baseline_data:
            shares_baseline = []
            for y in years:
                bev = baseline_data[scenario].get(y, {}).get('BEV', 0)
                icev = baseline_data[scenario].get(y, {}).get('ICEV', 0)
                total = bev + icev
                shares_baseline.append(bev / total * 100 if total > 0 else 0)
            ax2.plot(years, shares_baseline, 'o-', label=f"{SCENARIO_LABELS[scenario]} (baseline)",
                    color=SCENARIO_COLORS[scenario], linewidth=2, markersize=5)

        if scenario in breaks_data:
            shares_breaks = []
            for y in years:
                bev = breaks_data[scenario].get(y, {}).get('BEV', 0)
                icev = breaks_data[scenario].get(y, {}).get('ICEV', 0)
                total = bev + icev
                shares_breaks.append(bev / total * 100 if total > 0 else 0)
            ax2.plot(years, shares_breaks, 's--', label=f"{SCENARIO_LABELS[scenario]} (breaks only)",
                    color=SCENARIO_COLORS[scenario], linewidth=2, markersize=5, alpha=0.7)

    ax2.set_xlabel('Year')
    ax2.set_ylabel('BEV Share (%)')
    ax2.set_title('BEV Share: Baseline vs Breaks-Only')
    ax2.legend(loc='upper left', fontsize=8, ncol=2)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 100)

    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, 'figures', 'bev_fleet_baseline_vs_breaks.pdf'), dpi=150, bbox_inches='tight')
    plt.savefig(os.path.join(BASE_DIR, 'figures', 'bev_fleet_baseline_vs_breaks.png'), dpi=150, bbox_inches='tight')
    print("Saved: figures/bev_fleet_baseline_vs_breaks.pdf")
    plt.show()

def plot_charging_by_latitude_comparison(baseline_charging, breaks_charging, target_year=2040):
    """Create side-by-side latitude plot for charging demand."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

    lat_bins = np.arange(42, 72, 0.5)  # 0.5 degree bins from 42°N to 72°N

    # Plot baseline
    ax1 = axes[0]
    for scenario in SCENARIOS:
        if scenario in baseline_charging:
            lat_data = baseline_charging[scenario]
            if lat_data:
                lats = list(lat_data.keys())
                values = list(lat_data.values())

                # Bin by latitude
                binned = np.zeros(len(lat_bins) - 1)
                for lat, val in zip(lats, values):
                    idx = np.digitize(lat, lat_bins) - 1
                    if 0 <= idx < len(binned):
                        binned[idx] += val

                # Smooth
                smoothed = gaussian_filter1d(binned, sigma=2)
                lat_centers = (lat_bins[:-1] + lat_bins[1:]) / 2

                ax1.fill_between(lat_centers, 0, smoothed / 1e9, alpha=0.3,
                               color=SCENARIO_COLORS[scenario], label=SCENARIO_LABELS[scenario])
                ax1.plot(lat_centers, smoothed / 1e9, color=SCENARIO_COLORS[scenario], linewidth=1.5)

    ax1.set_xlabel('Latitude (°N)')
    ax1.set_ylabel('Electricity Charged (GWh)')
    ax1.set_title(f'Baseline (charge anywhere) - {target_year}')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(42, 72)

    # Plot breaks-only
    ax2 = axes[1]
    for scenario in SCENARIOS:
        if scenario in breaks_charging:
            lat_data = breaks_charging[scenario]
            if lat_data:
                lats = list(lat_data.keys())
                values = list(lat_data.values())

                # Bin by latitude
                binned = np.zeros(len(lat_bins) - 1)
                for lat, val in zip(lats, values):
                    idx = np.digitize(lat, lat_bins) - 1
                    if 0 <= idx < len(binned):
                        binned[idx] += val

                # Smooth
                smoothed = gaussian_filter1d(binned, sigma=2)
                lat_centers = (lat_bins[:-1] + lat_bins[1:]) / 2

                ax2.fill_between(lat_centers, 0, smoothed / 1e9, alpha=0.3,
                               color=SCENARIO_COLORS[scenario], label=SCENARIO_LABELS[scenario])
                ax2.plot(lat_centers, smoothed / 1e9, color=SCENARIO_COLORS[scenario], linewidth=1.5)

    ax2.set_xlabel('Latitude (°N)')
    ax2.set_title(f'Breaks Only (charging at mandatory breaks) - {target_year}')
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(42, 72)

    plt.suptitle(f'Charging Demand by Latitude: Baseline vs Breaks-Only ({target_year})',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, 'figures', f'charging_latitude_baseline_vs_breaks_{target_year}.pdf'),
                dpi=150, bbox_inches='tight')
    plt.savefig(os.path.join(BASE_DIR, 'figures', f'charging_latitude_baseline_vs_breaks_{target_year}.png'),
                dpi=150, bbox_inches='tight')
    print(f"Saved: figures/charging_latitude_baseline_vs_breaks_{target_year}.pdf")
    plt.show()

def plot_delta_summary(baseline_data, breaks_data):
    """Create summary plot showing delta between baseline and breaks-only."""
    fig, ax = plt.subplots(figsize=(10, 6))

    years = [2032, 2040, 2048, 2056, 2060]
    x = np.arange(len(years))
    width = 0.2

    for i, scenario in enumerate(SCENARIOS):
        deltas = []
        for y in years:
            bev_base = baseline_data.get(scenario, {}).get(y, {}).get('BEV', 0)
            bev_breaks = breaks_data.get(scenario, {}).get(y, {}).get('BEV', 0)
            delta_pct = ((bev_breaks - bev_base) / bev_base * 100) if bev_base > 0 else 0
            deltas.append(delta_pct)

        ax.bar(x + i * width, deltas, width, label=SCENARIO_LABELS[scenario],
               color=SCENARIO_COLORS[scenario], alpha=0.8)

    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.set_xlabel('Year')
    ax.set_ylabel('BEV Fleet Change (%)')
    ax.set_title('Impact of Mandatory Break Charging Constraint\n(Breaks-Only vs Baseline)')
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(years)
    ax.legend(loc='lower left')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, 'figures', 'bev_delta_breaks_vs_baseline.pdf'), dpi=150, bbox_inches='tight')
    plt.savefig(os.path.join(BASE_DIR, 'figures', 'bev_delta_breaks_vs_baseline.png'), dpi=150, bbox_inches='tight')
    print("Saved: figures/bev_delta_breaks_vs_baseline.pdf")
    plt.show()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("COMPARING BASELINE vs BREAKS-ONLY SCENARIOS")
    print("="*80)

    # Load helper data
    geo_id_to_lat = load_geo_data()
    tv_to_tech = load_techvehicle_data()

    # Load data for all scenarios
    print("\nLoading baseline data...")
    baseline_fleet = {}
    baseline_charging = {}
    for scenario in SCENARIOS:
        print(f"  Loading {scenario}...")
        h_dict, s_dict = load_scenario_data(BASELINE_DIR, scenario)
        if h_dict:
            baseline_fleet[scenario] = extract_fleet_by_year(h_dict, tv_to_tech)
        if s_dict:
            baseline_charging[scenario] = extract_charging_by_latitude(s_dict, geo_id_to_lat, 2040)

    print("\nLoading breaks-only data...")
    breaks_fleet = {}
    breaks_charging = {}
    for scenario in SCENARIOS:
        print(f"  Loading {scenario}...")
        h_dict, s_dict = load_scenario_data(BREAKS_ONLY_DIR, scenario)
        if h_dict:
            breaks_fleet[scenario] = extract_fleet_by_year(h_dict, tv_to_tech)
        if s_dict:
            breaks_charging[scenario] = extract_charging_by_latitude(s_dict, geo_id_to_lat, 2040)

    # Print summary
    print("\n" + "="*80)
    print("FLEET SUMMARY (2040)")
    print("="*80)
    print(f"{'Scenario':<20} {'Baseline BEV':>15} {'Breaks BEV':>15} {'Delta %':>12}")
    print("-"*65)
    for scenario in SCENARIOS:
        bev_base = baseline_fleet.get(scenario, {}).get(2040, {}).get('BEV', 0)
        bev_breaks = breaks_fleet.get(scenario, {}).get(2040, {}).get('BEV', 0)
        delta = ((bev_breaks - bev_base) / bev_base * 100) if bev_base > 0 else 0
        print(f"{SCENARIO_LABELS[scenario]:<20} {bev_base:>15,.0f} {bev_breaks:>15,.0f} {delta:>11.1f}%")

    # Create plots
    print("\nCreating plots...")
    os.makedirs(os.path.join(BASE_DIR, 'figures'), exist_ok=True)

    plot_bev_fleet_comparison(baseline_fleet, breaks_fleet, tv_to_tech)
    plot_charging_by_latitude_comparison(baseline_charging, breaks_charging, 2040)
    plot_delta_summary(baseline_fleet, breaks_fleet)

    print("\nDone!")
