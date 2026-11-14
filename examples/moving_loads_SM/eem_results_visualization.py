"""
EEM Paper Results Visualization
================================
Generates figures for the three research questions:
  RQ1: CO2 emissions on German highways
  RQ2: Charging demand distribution North vs South Germany
  RQ3: Infrastructure overcapacity from split timing

Uses decision variables:
  - s (charged energy by location)
  - q_fuel_infr_plus (infrastructure capacity added)
  - f (transport volume) and h (fleet stock) for CO2
"""

import yaml
import re
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
from collections import defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
os.chdir(SCRIPT_DIR)

RESULTS_DIR = SCRIPT_DIR / 'results' / 'eem_scenarios'
INPUT_DIR = SCRIPT_DIR / 'input_data' / 'eem_scenarios'
FIGURES_DIR = SCRIPT_DIR / 'figures'
FIGURES_DIR.mkdir(exist_ok=True)

# Zone definitions
DE_NORTH = {'DE30','DE40','DE50','DE60','DE80','DE91','DE92','DE93','DE94',
            'DEF0','DED2','DED4','DED5','DEE0','DEG0'}
DE_SOUTH = {'DE11','DE12','DE13','DE14','DE21','DE22','DE23','DE24','DE25','DE26','DE27',
            'DE71','DE72','DE73','DEA1','DEA2','DEA3','DEA4','DEA5',
            'DEB1','DEB2','DEB3','DEC0'}

MODELED_YEARS = list(range(2020, 2061))
IDX_TO_YEAR = {i+1: y for i, y in enumerate(MODELED_YEARS)}

# Scenario organization
SCENARIOS = {
    'DE_unified': {'label': 'Baseline', 'spread': 0, 'timing': None, 'color': 'black', 'ls': '-'},
    'DE_split_low_from2020':  {'label': 'Low 5%, from 2020',  'spread': 5,  'timing': 2020, 'color': '#2196F3', 'ls': '-'},
    'DE_split_low_from2032':  {'label': 'Low 5%, from 2032',  'spread': 5,  'timing': 2032, 'color': '#2196F3', 'ls': '--'},
    'DE_split_low_from2040':  {'label': 'Low 5%, from 2040',  'spread': 5,  'timing': 2040, 'color': '#2196F3', 'ls': ':'},
    'DE_split_mid_from2020':  {'label': 'Mid 10%, from 2020', 'spread': 10, 'timing': 2020, 'color': '#FF9800', 'ls': '-'},
    'DE_split_mid_from2032':  {'label': 'Mid 10%, from 2032', 'spread': 10, 'timing': 2032, 'color': '#FF9800', 'ls': '--'},
    'DE_split_mid_from2040':  {'label': 'Mid 10%, from 2040', 'spread': 10, 'timing': 2040, 'color': '#FF9800', 'ls': ':'},
    'DE_split_high_from2020': {'label': 'High 20%, from 2020','spread': 20, 'timing': 2020, 'color': '#F44336', 'ls': '-'},
    'DE_split_high_from2032': {'label': 'High 20%, from 2032','spread': 20, 'timing': 2032, 'color': '#F44336', 'ls': '--'},
    'DE_split_high_from2040': {'label': 'High 20%, from 2040','spread': 20, 'timing': 2040, 'color': '#F44336', 'ls': ':'},
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_geo_mapping():
    """Build geo_id -> nuts2 and zone mappings."""
    geos = yaml.safe_load(open(INPUT_DIR / 'DE_unified' / 'GeographicElement.yaml'))
    geo_id_to_nuts2 = {}
    geo_id_to_zone = {}
    for g in geos:
        nuts2 = g.get('nuts2_region', '')
        geo_id_to_nuts2[g['id']] = nuts2
        if nuts2 in DE_NORTH:
            geo_id_to_zone[g['id']] = 'DE-North'
        elif nuts2 in DE_SOUTH:
            geo_id_to_zone[g['id']] = 'DE-South'
        else:
            country = nuts2[:2] if len(nuts2) >= 2 else '??'
            geo_id_to_zone[g['id']] = country
    return geo_id_to_nuts2, geo_id_to_zone


def find_result_file(scenario, varname):
    """Find the result YAML file for a given scenario and variable."""
    sc_dir = RESULTS_DIR / scenario
    pattern = f'*_{varname}_dict.yaml'
    files = list(sc_dir.glob(pattern))
    if not files:
        return None
    return files[0]


def load_s_by_zone(scenario, geo_id_to_zone):
    """Load charging energy (s) aggregated by zone and year."""
    fpath = find_result_file(scenario, 's')
    if fpath is None:
        print(f"  WARNING: No s_dict for {scenario}")
        return {}

    data = yaml.safe_load(open(fpath))
    pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')

    # s[year_idx, odpair, tech, gen, geo_id] = kWh
    zone_year = defaultdict(lambda: defaultdict(float))

    for key, val in data.items():
        m = pat.match(key)
        if not m:
            continue
        y_idx = int(m.group(1))
        tech_id = int(m.group(3))
        geo_id = int(m.group(5))
        year = IDX_TO_YEAR.get(y_idx)
        if year is None:
            continue
        # Only BEV charging (tech_id for BEV)
        zone = geo_id_to_zone.get(geo_id, 'Other')
        zone_year[zone][year] += val

    return zone_year


def load_q_by_zone(scenario, geo_id_to_zone):
    """Load infrastructure additions (q_fuel_infr_plus) aggregated by zone and year."""
    fpath = find_result_file(scenario, 'q_fuel_infr_plus')
    if fpath is None:
        print(f"  WARNING: No q_fuel_infr_plus for {scenario}")
        return {}

    data = yaml.safe_load(open(fpath))
    pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\)')

    # q[year_idx, fueling_type, geo_id] = kW
    zone_year = defaultdict(lambda: defaultdict(float))

    for key, val in data.items():
        m = pat.match(key)
        if not m:
            continue
        y_idx = int(m.group(1))
        geo_id = int(m.group(3))
        year = IDX_TO_YEAR.get(y_idx)
        if year is None:
            continue
        zone = geo_id_to_zone.get(geo_id, 'Other')
        zone_year[zone][year] += val

    return zone_year


def load_h_by_tech(scenario):
    """Load fleet stock (h) aggregated by technology and year."""
    fpath = find_result_file(scenario, 'h')
    if fpath is None:
        return {}

    data = yaml.safe_load(open(fpath))
    # h keys: '(year, odpair_id, tech_id, gen_year)'
    pat = re.compile(r'\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')

    # Load techvehicle to map tv_id -> technology
    tv = yaml.safe_load(open(INPUT_DIR / 'DE_unified' / 'TechVehicle.yaml'))
    tv_id_to_tech = {t['id']: t['technology'] for t in tv}

    tech_year = defaultdict(lambda: defaultdict(float))

    for key, val in data.items():
        m = pat.match(key)
        if not m:
            continue
        year = int(m.group(1))
        tv_id = int(m.group(3))
        tech = tv_id_to_tech.get(tv_id, -1)
        tech_year[tech][year] += val

    return tech_year


# ============================================================================
# LOAD ALL DATA
# ============================================================================

print("Loading geographic mappings...")
geo_id_to_nuts2, geo_id_to_zone = load_geo_mapping()
print(f"  {sum(1 for v in geo_id_to_zone.values() if v=='DE-North')} North nodes, "
      f"{sum(1 for v in geo_id_to_zone.values() if v=='DE-South')} South nodes")

print("\nLoading results for all scenarios...")
all_s = {}
all_q = {}
all_h = {}
for sc in SCENARIOS:
    print(f"  Loading {sc}...")
    all_s[sc] = load_s_by_zone(sc, geo_id_to_zone)
    all_q[sc] = load_q_by_zone(sc, geo_id_to_zone)
    all_h[sc] = load_h_by_tech(sc)

print("\nAll data loaded.")

# ============================================================================
# FIGURE 1: CHARGING DEMAND NORTH vs SOUTH (RQ2)
# ============================================================================

print("\n--- Figure 1: Charging demand N vs S ---")

fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)
spread_groups = [(5, 'Low (5%)'), (10, 'Mid (10%)'), (20, 'High (20%)')]

for ax_idx, (spread, spread_label) in enumerate(spread_groups):
    ax = axes[ax_idx]

    # Baseline
    baseline_n = [all_s['DE_unified'].get('DE-North', {}).get(y, 0) / 1e6 for y in MODELED_YEARS]
    baseline_s = [all_s['DE_unified'].get('DE-South', {}).get(y, 0) / 1e6 for y in MODELED_YEARS]
    ax.plot(MODELED_YEARS, baseline_n, 'k-', lw=2, label='Baseline North')
    ax.plot(MODELED_YEARS, baseline_s, 'k--', lw=2, label='Baseline South')

    # Zone-split scenarios for this spread level
    timing_styles = {2020: '-', 2032: '--', 2040: ':'}
    timing_colors_n = {2020: '#1565C0', 2032: '#42A5F5', 2040: '#90CAF9'}
    timing_colors_s = {2020: '#C62828', 2032: '#EF5350', 2040: '#EF9A9A'}

    for sc, info in SCENARIOS.items():
        if info['spread'] != spread:
            continue
        timing = info['timing']
        ls = timing_styles[timing]

        north = [all_s[sc].get('DE-North', {}).get(y, 0) / 1e6 for y in MODELED_YEARS]
        south = [all_s[sc].get('DE-South', {}).get(y, 0) / 1e6 for y in MODELED_YEARS]

        ax.plot(MODELED_YEARS, north, color=timing_colors_n[timing], ls=ls, lw=1.5,
                label=f'North, from {timing}')
        ax.plot(MODELED_YEARS, south, color=timing_colors_s[timing], ls=ls, lw=1.5,
                label=f'South, from {timing}')

    ax.set_title(spread_label, fontweight='bold')
    ax.set_xlabel('Year')
    if ax_idx == 0:
        ax.set_ylabel('Charging energy [GWh/a]')
    ax.legend(fontsize=6, loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2020, 2060)

fig.suptitle('Charging Demand in German Zones: North vs South', fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(FIGURES_DIR / 'eem_charging_demand_north_south.pdf', bbox_inches='tight', dpi=300)
fig.savefig(FIGURES_DIR / 'eem_charging_demand_north_south.png', bbox_inches='tight', dpi=300)
print("  Saved eem_charging_demand_north_south.pdf/.png")
plt.close()


# ============================================================================
# FIGURE 2: CHARGING DEMAND DELTA (vs baseline) — North and South
# ============================================================================

print("--- Figure 2: Charging demand delta vs baseline ---")

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

for zone_idx, zone in enumerate(['DE-North', 'DE-South']):
    ax = axes[zone_idx]

    baseline = {y: all_s['DE_unified'].get(zone, {}).get(y, 0) for y in MODELED_YEARS}

    for sc, info in SCENARIOS.items():
        if sc == 'DE_unified':
            continue
        delta = [(all_s[sc].get(zone, {}).get(y, 0) - baseline[y]) / 1e6 for y in MODELED_YEARS]
        ax.plot(MODELED_YEARS, delta, color=info['color'], ls=info['ls'], lw=1.5,
                label=info['label'])

    ax.axhline(0, color='black', lw=0.5)
    ax.set_title(zone, fontweight='bold')
    ax.set_xlabel('Year')
    ax.set_ylabel('$\\Delta$ Charging energy vs baseline [GWh/a]')
    ax.legend(fontsize=6)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2020, 2060)

fig.suptitle('Change in Charging Demand Relative to Baseline (Unified Zone)', fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(FIGURES_DIR / 'eem_charging_demand_delta.pdf', bbox_inches='tight', dpi=300)
fig.savefig(FIGURES_DIR / 'eem_charging_demand_delta.png', bbox_inches='tight', dpi=300)
print("  Saved eem_charging_demand_delta.pdf/.png")
plt.close()


# ============================================================================
# FIGURE 3: NORTH SHARE OF GERMAN CHARGING DEMAND
# ============================================================================

print("--- Figure 3: North share of German charging ---")

fig, ax = plt.subplots(figsize=(8, 5))

for sc, info in SCENARIOS.items():
    north = [all_s[sc].get('DE-North', {}).get(y, 0) for y in MODELED_YEARS]
    south = [all_s[sc].get('DE-South', {}).get(y, 0) for y in MODELED_YEARS]
    total = [n + s for n, s in zip(north, south)]
    share = [n / t * 100 if t > 0 else 0 for n, t in zip(north, total)]

    lw = 2.5 if sc == 'DE_unified' else 1.5
    ax.plot(MODELED_YEARS, share, color=info['color'], ls=info['ls'], lw=lw,
            label=info['label'])

ax.axhline(50, color='gray', lw=0.5, ls='--', alpha=0.5)
ax.set_xlabel('Year')
ax.set_ylabel('North share of German charging demand [%]')
ax.set_title('Share of Charging Demand in Northern Germany', fontweight='bold')
ax.legend(fontsize=7, loc='best')
ax.grid(True, alpha=0.3)
ax.set_xlim(2020, 2060)

fig.tight_layout()
fig.savefig(FIGURES_DIR / 'eem_north_share_charging.pdf', bbox_inches='tight', dpi=300)
fig.savefig(FIGURES_DIR / 'eem_north_share_charging.png', bbox_inches='tight', dpi=300)
print("  Saved eem_north_share_charging.pdf/.png")
plt.close()


# ============================================================================
# FIGURE 4: INFRASTRUCTURE — CUMULATIVE CAPACITY BY ZONE (RQ3)
# ============================================================================

print("--- Figure 4: Infrastructure capacity by zone ---")

fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)

for ax_idx, (spread, spread_label) in enumerate(spread_groups):
    ax = axes[ax_idx]

    for sc, info in SCENARIOS.items():
        if info['spread'] != spread and sc != 'DE_unified':
            continue

        # Cumulative infrastructure for South
        cumul_south = []
        cumul = 0
        for y in MODELED_YEARS:
            cumul += all_q[sc].get('DE-South', {}).get(y, 0)
            cumul_south.append(cumul / 1e3)  # kW -> MW

        lw = 2.5 if sc == 'DE_unified' else 1.5
        color = 'black' if sc == 'DE_unified' else info['color']
        ls = '-' if sc == 'DE_unified' else info['ls']
        label = 'Baseline' if sc == 'DE_unified' else f'from {info["timing"]}'

        ax.plot(MODELED_YEARS, cumul_south, color=color, ls=ls, lw=lw, label=label)

    ax.set_title(f'{spread_label} — South DE', fontweight='bold')
    ax.set_xlabel('Year')
    if ax_idx == 0:
        ax.set_ylabel('Cumulative charging capacity [MW]')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2020, 2060)

fig.suptitle('Cumulative Charging Infrastructure in Southern Germany', fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(FIGURES_DIR / 'eem_infrastructure_south_cumulative.pdf', bbox_inches='tight', dpi=300)
fig.savefig(FIGURES_DIR / 'eem_infrastructure_south_cumulative.png', bbox_inches='tight', dpi=300)
print("  Saved eem_infrastructure_south_cumulative.pdf/.png")
plt.close()


# ============================================================================
# FIGURE 5: STRANDED CAPACITY — SOUTH EXCESS vs EARLY SPLIT (RQ3)
# ============================================================================

print("--- Figure 5: Stranded capacity indicator ---")

fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)

for ax_idx, (spread, spread_label) in enumerate(spread_groups):
    ax = axes[ax_idx]

    # Reference: from2020 (early split)
    ref_sc = f'DE_split_{"low" if spread==5 else "mid" if spread==10 else "high"}_from2020'

    for timing in [2032, 2040]:
        sc = f'DE_split_{"low" if spread==5 else "mid" if spread==10 else "high"}_from{timing}'
        info = SCENARIOS[sc]

        # Cumulative South for this scenario vs early split
        cumul_sc = 0
        cumul_ref = 0
        delta_list = []
        for y in MODELED_YEARS:
            cumul_sc += all_q[sc].get('DE-South', {}).get(y, 0)
            cumul_ref += all_q[ref_sc].get('DE-South', {}).get(y, 0)
            delta_list.append((cumul_sc - cumul_ref) / 1e3)  # kW -> MW

        ax.plot(MODELED_YEARS, delta_list, color=info['color'], ls=info['ls'], lw=1.5,
                label=f'from {timing} vs from 2020')

    # Also show baseline vs early split
    cumul_base = 0
    cumul_ref = 0
    delta_base = []
    for y in MODELED_YEARS:
        cumul_base += all_q['DE_unified'].get('DE-South', {}).get(y, 0)
        cumul_ref += all_q[ref_sc].get('DE-South', {}).get(y, 0)
        delta_base.append((cumul_base - cumul_ref) / 1e3)
    ax.plot(MODELED_YEARS, delta_base, 'k-', lw=2, label='Baseline vs from 2020')

    ax.axhline(0, color='gray', lw=0.5, ls='--')
    ax.set_title(f'{spread_label}', fontweight='bold')
    ax.set_xlabel('Year')
    if ax_idx == 0:
        ax.set_ylabel('South DE excess capacity vs early split [MW]')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2020, 2060)

fig.suptitle('Potential Stranded Capacity: South-DE Infrastructure Excess\n(relative to immediate split from 2020)',
             fontweight='bold', y=1.05)
fig.tight_layout()
fig.savefig(FIGURES_DIR / 'eem_stranded_capacity_south.pdf', bbox_inches='tight', dpi=300)
fig.savefig(FIGURES_DIR / 'eem_stranded_capacity_south.png', bbox_inches='tight', dpi=300)
print("  Saved eem_stranded_capacity_south.pdf/.png")
plt.close()


# ============================================================================
# FIGURE 6: BEV FLEET SHARE (RQ1 — electrification speed)
# ============================================================================

print("--- Figure 6: BEV fleet share ---")

fig, ax = plt.subplots(figsize=(8, 5))

for sc, info in SCENARIOS.items():
    h_data = all_h[sc]
    bev_share = []
    for y in MODELED_YEARS:
        icev = h_data.get(0, {}).get(y, 0)
        bev = h_data.get(1, {}).get(y, 0)
        total = icev + bev
        bev_share.append(bev / total * 100 if total > 0 else 0)

    lw = 2.5 if sc == 'DE_unified' else 1.2
    ax.plot(MODELED_YEARS, bev_share, color=info['color'], ls=info['ls'], lw=lw,
            label=info['label'])

ax.set_xlabel('Year')
ax.set_ylabel('BEV share of truck fleet [%]')
ax.set_title('BEV Fleet Share Across Scenarios', fontweight='bold')
ax.legend(fontsize=7, ncol=2)
ax.grid(True, alpha=0.3)
ax.set_xlim(2020, 2060)
ax.set_ylim(0, 100)

fig.tight_layout()
fig.savefig(FIGURES_DIR / 'eem_bev_fleet_share.pdf', bbox_inches='tight', dpi=300)
fig.savefig(FIGURES_DIR / 'eem_bev_fleet_share.png', bbox_inches='tight', dpi=300)
print("  Saved eem_bev_fleet_share.pdf/.png")
plt.close()


# ============================================================================
# FIGURE 7: NORTH SHARE OF INFRASTRUCTURE
# ============================================================================

print("--- Figure 7: North share of infrastructure ---")

fig, ax = plt.subplots(figsize=(8, 5))

for sc, info in SCENARIOS.items():
    cumul_n = 0
    cumul_s = 0
    share_list = []
    for y in MODELED_YEARS:
        cumul_n += all_q[sc].get('DE-North', {}).get(y, 0)
        cumul_s += all_q[sc].get('DE-South', {}).get(y, 0)
        total = cumul_n + cumul_s
        share_list.append(cumul_n / total * 100 if total > 0 else 0)

    lw = 2.5 if sc == 'DE_unified' else 1.5
    ax.plot(MODELED_YEARS, share_list, color=info['color'], ls=info['ls'], lw=lw,
            label=info['label'])

ax.axhline(50, color='gray', lw=0.5, ls='--', alpha=0.5)
ax.set_xlabel('Year')
ax.set_ylabel('North share of German charging infra [%]')
ax.set_title('Share of Charging Infrastructure in Northern Germany', fontweight='bold')
ax.legend(fontsize=7, loc='best')
ax.grid(True, alpha=0.3)
ax.set_xlim(2020, 2060)

fig.tight_layout()
fig.savefig(FIGURES_DIR / 'eem_north_share_infrastructure.pdf', bbox_inches='tight', dpi=300)
fig.savefig(FIGURES_DIR / 'eem_north_share_infrastructure.png', bbox_inches='tight', dpi=300)
print("  Saved eem_north_share_infrastructure.pdf/.png")
plt.close()


# ============================================================================
# SUMMARY TABLE (printed to console)
# ============================================================================

print("\n" + "=" * 100)
print("SUMMARY TABLE: Key metrics by scenario (year 2040)")
print("=" * 100)
header = f"{'Scenario':<35} {'Obj [B EUR]':>12} {'BEV%':>6} {'N charge':>10} {'S charge':>10} {'N share%':>9} {'N infra%':>9}"
print(header)
print("-" * 100)

for sc, info in SCENARIOS.items():
    # Objective from summary_stats
    summary_file = RESULTS_DIR / sc / 'summary_stats.yaml'
    obj_val = 0
    if summary_file.exists():
        summary = yaml.safe_load(open(summary_file))
        obj_val = summary.get('objective_value', 0) / 1e9

    # BEV share
    h_data = all_h[sc]
    icev_40 = h_data.get(0, {}).get(2040, 0)
    bev_40 = h_data.get(1, {}).get(2040, 0)
    total_40 = icev_40 + bev_40
    bev_pct = bev_40 / total_40 * 100 if total_40 > 0 else 0

    # Charging N/S
    n_charge = all_s[sc].get('DE-North', {}).get(2040, 0) / 1e6
    s_charge = all_s[sc].get('DE-South', {}).get(2040, 0) / 1e6
    total_charge = n_charge + s_charge
    n_share = n_charge / total_charge * 100 if total_charge > 0 else 0

    # Infrastructure N share
    cumul_n = sum(all_q[sc].get('DE-North', {}).get(y, 0) for y in range(2020, 2041))
    cumul_s = sum(all_q[sc].get('DE-South', {}).get(y, 0) for y in range(2020, 2041))
    cumul_total = cumul_n + cumul_s
    n_infra = cumul_n / cumul_total * 100 if cumul_total > 0 else 0

    print(f"{info['label']:<35} {obj_val:>12.2f} {bev_pct:>6.1f} {n_charge:>10.1f} {s_charge:>10.1f} {n_share:>8.1f}% {n_infra:>8.1f}%")

print("=" * 100)
print("\nAll figures saved to:", FIGURES_DIR)
