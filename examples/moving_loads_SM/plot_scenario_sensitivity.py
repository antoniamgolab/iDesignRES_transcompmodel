"""
Scenario sensitivity analysis figures for the paper.

Generates 3 figure sets:
  (A) BEV adoption by OD country pair across 4 scenarios
  (B) Spatial charging demand distribution (by latitude) across 4 scenarios
  (C) Optimal vs heuristic charging comparison for 2 selected years

Reads results from results/uncertainty_scenarios_v2/scenario_000-003
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
import yaml, re, glob, pathlib
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
RESULTS_BASE = BASE / 'results' / 'uncertainty_scenarios_v2'

SCENARIOS = ['scenario_000', 'scenario_001', 'scenario_002', 'scenario_003']
LABELS = {
    'scenario_000': 'Go RES',
    'scenario_001': 'NECPEssentials',
    'scenario_002': 'REPowerEU++',
    'scenario_003': 'Trinity',
}
COLORS = {
    'scenario_000': '#E74C3C',
    'scenario_001': '#3498DB',
    'scenario_002': '#2ECC71',
    'scenario_003': '#F39C12',
}

# Load geographic data
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}
geo_country = {g['id']: g.get('country', '??') for g in geo_data}

# Load paths and OD pairs (same across scenarios)
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/Odpair.yaml') as f:
    odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/MandatoryBreaks.yaml') as f:
    breaks_data = yaml.load(f, Loader=yaml.UnsafeLoader)

path_seq = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist = {int(p['id']): [float(d) for d in p.get('distance_from_previous', [])] for p in paths}
od_path = {int(od['id']): int(od['path_id']) for od in odpairs}

breaks_by_path = defaultdict(list)
for brk in breaks_data:
    breaks_by_path[int(brk['path_id'])].append(int(brk['latest_geo_id']))

# Regex patterns
tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')
f_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')

MODELED_YEARS = list(range(2020, 2064, 4))
PAYLOAD = 13.6


def load_scenario_data(scenario):
    """Load f (flow) and s (charging) data for a scenario."""
    run_dir = RESULTS_BASE / scenario

    # Find latest result files
    s_files = sorted(glob.glob(str(run_dir / '*_s_dict.yaml')))
    f_files = sorted(glob.glob(str(run_dir / '*_f_dict.yaml')))

    if not s_files or not f_files:
        print(f"  WARNING: Missing files for {scenario}")
        return None, None

    # Parse s (charging by geo and year)
    charging = defaultdict(lambda: defaultdict(float))
    route_charging = defaultdict(lambda: defaultdict(float))
    with open(s_files[-1]) as f:
        for line in f:
            m = tuple_pat.match(line.strip())
            if not m: continue
            year = int(m.group(1))
            od_id, path_id, geo_id = int(m.group(3)), int(m.group(4)), int(m.group(5))
            fuel, infr = int(m.group(7)), int(m.group(8))
            val = float(m.group(10))
            if val < 1e-6 or fuel != 0 or infr not in {1, 2}: continue
            charging[geo_id][year] += val
            route_charging[(od_id, path_id)][year] += val

    # Parse f (flow by tech, OD, year)
    flows = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    with open(f_files[-1]) as f:
        for line in f:
            m = f_pat.match(line.strip())
            if not m: continue
            year = int(m.group(1))
            od_id = int(m.group(3))
            tech_id = int(m.group(6))  # 0=ICEV, 1=BEV
            val = float(m.group(8))
            if val < 1e-6: continue
            # Get origin-destination countries
            pid = od_path.get(od_id)
            if pid is None: continue
            seq = path_seq.get(pid, [])
            if len(seq) < 2: continue
            oc = geo_country.get(seq[0], '??')
            dc = geo_country.get(seq[-1], '??')
            flows[(oc, dc)][year][tech_id] += val * 1000  # to tonnes

    return {'charging': charging, 'route_charging': route_charging}, {'flows': flows}


# ============================================================================
# Load all scenarios
# ============================================================================
print("Loading scenario data...")
scenario_data = {}
available = []
for sc in SCENARIOS:
    print(f"  {sc} ({LABELS[sc]})...", end="", flush=True)
    s_data, f_data = load_scenario_data(sc)
    if s_data is not None:
        scenario_data[sc] = {'s': s_data, 'f': f_data}
        available.append(sc)
        print(" OK")
    else:
        print(" MISSING")

if not available:
    print("No scenario data found! Run SM_batch.jl first.")
    exit(1)

print(f"\nAvailable scenarios: {len(available)}/{len(SCENARIOS)}")


# ============================================================================
# (A) BEV ADOPTION BY OD COUNTRY PAIR
# ============================================================================
print("\n" + "="*80)
print("(A) BEV ADOPTION BY OD COUNTRY PAIR")
print("="*80)

# Get top country pairs by volume
all_country_pairs = set()
for sc in available:
    all_country_pairs.update(scenario_data[sc]['f']['flows'].keys())

# Filter to significant pairs
pair_volumes = defaultdict(float)
for sc in available:
    for cp, year_tech in scenario_data[sc]['f']['flows'].items():
        for year, tech_vals in year_tech.items():
            pair_volumes[cp] += sum(tech_vals.values())

top_pairs = sorted(pair_volumes.keys(), key=lambda x: pair_volumes[x], reverse=True)[:12]

for target_year in [2040, 2048]:
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(top_pairs))
    width = 0.8 / len(available)

    for i, sc in enumerate(available):
        bev_pcts = []
        for cp in top_pairs:
            techs = scenario_data[sc]['f']['flows'].get(cp, {}).get(target_year, {})
            bev = techs.get(1, 0)
            icev = techs.get(0, 0)
            total = bev + icev
            pct = bev / total * 100 if total > 0 else 0
            bev_pcts.append(pct)

        ax.bar(x + i * width, bev_pcts, width, label=LABELS[sc], color=COLORS[sc], alpha=0.8)

    ax.set_xlabel('Origin-Destination Country Pair', fontsize=11)
    ax.set_ylabel('BEV Share (%)', fontsize=11)
    ax.set_title(f'BEV Adoption by OD Country Pair - {target_year}', fontsize=13, fontweight='bold')
    ax.set_xticks(x + width * (len(available) - 1) / 2)
    pair_labels = [f'{cp[0]}->{cp[1]}' for cp in top_pairs]
    ax.set_xticklabels(pair_labels, rotation=45, ha='right', fontsize=9)
    ax.legend(fontsize=9)
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    outfile = BASE / f'scenario_bev_by_od_pair_{target_year}.png'
    plt.savefig(outfile, dpi=200, bbox_inches='tight')
    plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
    print(f"  Saved: {outfile.name}")
    plt.close()


# ============================================================================
# (B) SPATIAL CHARGING DEMAND BY LATITUDE
# ============================================================================
print("\n" + "="*80)
print("(B) SPATIAL CHARGING DEMAND BY LATITUDE")
print("="*80)

BORDERS = {'IT-AT': 46.5, 'AT-DE': 47.5, 'DE-DK': 54.5, 'DK-SE': 55.5}

for target_year in [2040, 2048]:
    # Side-by-side panels
    fig, axes = plt.subplots(1, len(available), figsize=(3.5 * len(available), 8), sharey=True, sharex=True)
    if len(available) == 1:
        axes = [axes]
    fig.suptitle(f'Charging demand by latitude - {target_year}', fontsize=14, fontweight='bold', y=0.98)

    global_max = 0
    all_lat_data = {}

    for sc in available:
        lat_gwh = []
        for geo_id, year_dict in scenario_data[sc]['s']['charging'].items():
            mwh = year_dict.get(target_year, 0)
            lat = geo_lat.get(geo_id, 0)
            if lat > 0 and mwh > 0:
                lat_gwh.append((lat, mwh / 1000))
        lat_gwh.sort()
        all_lat_data[sc] = lat_gwh
        if lat_gwh:
            global_max = max(global_max, max(g for _, g in lat_gwh))

    for idx, sc in enumerate(available):
        ax = axes[idx]
        data = all_lat_data[sc]
        color = COLORS[sc]

        if not data: continue
        lats = np.array([x[0] for x in data])
        gwhs = np.array([x[1] for x in data])
        sort_idx = np.argsort(lats)
        lat_s = lats[sort_idx]
        gwh_s = gwhs[sort_idx]
        gwh_smooth = gaussian_filter1d(gwh_s, sigma=1.2) if len(lat_s) > 3 else gwh_s

        ax.fill_betweenx(lat_s, 0, gwh_smooth, alpha=0.3, color=color)
        ax.plot(gwh_smooth, lat_s, color=color, linewidth=1.5)
        ax.scatter(gwh_s, lat_s, color=color, s=12, zorder=5, alpha=0.6)

        for bname, blat in BORDERS.items():
            ax.axhline(y=blat, color='gray', linestyle='--', alpha=0.3, linewidth=0.7)

        total = sum(gwhs)
        ax.set_title(f'{LABELS[sc]}\n({total:.0f} GWh)', fontsize=10)
        ax.set_xlim(0, global_max * 1.15)
        ax.set_ylim(38, 72)
        ax.set_xlabel('GWh/yr', fontsize=9)
        if idx == 0:
            ax.set_ylabel('Latitude (°N)', fontsize=10)
        ax.grid(axis='y', alpha=0.2)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    outfile = BASE / f'scenario_charging_latitude_{target_year}.png'
    plt.savefig(outfile, dpi=200, bbox_inches='tight')
    plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
    print(f"  Saved: {outfile.name}")
    plt.close()

    # Overlay
    fig, ax = plt.subplots(figsize=(6, 8))
    for sc in available:
        data = all_lat_data[sc]
        if not data: continue
        lats = np.array([x[0] for x in data])
        gwhs = np.array([x[1] for x in data])
        sort_idx = np.argsort(lats)
        gwh_smooth = gaussian_filter1d(gwhs[sort_idx], sigma=1.2) if len(lats) > 3 else gwhs[sort_idx]
        ax.plot(gwh_smooth, lats[sort_idx], color=COLORS[sc], linewidth=2, label=LABELS[sc])

    for bname, blat in BORDERS.items():
        ax.axhline(y=blat, color='gray', linestyle=':', alpha=0.4, linewidth=0.8)

    ax.set_ylabel('Latitude (°N)', fontsize=11)
    ax.set_xlabel('Charging demand (GWh/year)', fontsize=11)
    ax.set_title(f'Charging demand by latitude - {target_year}', fontsize=12)
    ax.set_ylim(38, 72)
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(axis='y', alpha=0.2)
    plt.tight_layout()
    outfile = BASE / f'scenario_charging_overlay_{target_year}.png'
    plt.savefig(outfile, dpi=200, bbox_inches='tight')
    plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
    print(f"  Saved: {outfile.name}")
    plt.close()


# ============================================================================
# (C) OPTIMAL vs HEURISTIC COMPARISON
# ============================================================================
print("\n" + "="*80)
print("(C) OPTIMAL vs HEURISTIC COMPARISON")
print("="*80)

# Load BEV battery data for SOC-aware heuristic
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/TechVehicle.yaml') as f:
    tv_data = yaml.safe_load(f)
bev_tv = next(t for t in tv_data if t['technology'] == 1)
GEN_YEARS = list(range(2008, 2008 + len(bev_tv['tank_capacity'])))
BATTERY_BY_GEN = dict(zip(GEN_YEARS, bev_tv['tank_capacity']))
SPEC_CONS_BY_GEN = dict(zip(GEN_YEARS, bev_tv['spec_cons']))

def battery_cap_for_year(year):
    return BATTERY_BY_GEN.get(year, BATTERY_BY_GEN[max(y for y in BATTERY_BY_GEN if y <= year)])

def spec_cons_for_year(year):
    return SPEC_CONS_BY_GEN.get(year, SPEC_CONS_BY_GEN[max(y for y in SPEC_CONS_BY_GEN if y <= year)])

def compute_soc_charging(od_id, path_id, total_energy_mwh, year):
    """SOC-aware lazy charging at break stops."""
    pid = od_path.get(od_id, path_id)
    seq = path_seq.get(pid, [])
    dist = path_dist.get(pid, [])
    break_set = set(breaks_by_path.get(pid, []))
    if not seq or not dist or len(seq) != len(dist): return {}

    break_indices = [i for i, g in enumerate(seq) if g in break_set]
    if not break_indices:
        n = len(seq)
        return {seq[i]: total_energy_mwh / n for i in range(n)} if n > 0 else {}

    cum_dist = np.cumsum(dist)
    total_dist = cum_dist[-1] if len(cum_dist) > 0 else 0
    if total_dist < 1e-3: return {}

    bat_cap = battery_cap_for_year(year)
    sc = spec_cons_for_year(year)
    soc = bat_cap * 0.5
    charges = {}

    for i, bi in enumerate(break_indices):
        prev_dist = cum_dist[break_indices[i-1]] if i > 0 else 0
        energy_consumed = sc * (cum_dist[bi] - prev_dist)
        soc -= energy_consumed

        if i < len(break_indices) - 1:
            dist_to_next = cum_dist[break_indices[i+1]] - cum_dist[bi]
        else:
            dist_to_next = total_dist - cum_dist[bi]

        energy_to_next = sc * dist_to_next
        if soc < energy_to_next + bat_cap * 0.1:
            charge = min(bat_cap - soc, energy_to_next - soc + bat_cap * 0.1)
            charge = max(0, min(charge, bat_cap - soc))
            if charge > 0:
                charges[seq[bi]] = charges.get(seq[bi], 0) + charge
                soc += charge

    if not charges:
        for bi in break_indices:
            charges[seq[bi]] = 1.0

    total_raw = sum(charges.values())
    if total_raw < 1e-9: return {}
    scale = total_energy_mwh / total_raw
    return {geo_id: kwh * scale for geo_id, kwh in charges.items()}


for target_year in [2040, 2048]:
    print(f"\n--- Year {target_year} ---")

    fig, axes = plt.subplots(1, len(available), figsize=(3.5 * len(available), 8), sharey=True, sharex=True)
    if len(available) == 1:
        axes = [axes]
    fig.suptitle(f'Optimal vs Heuristic charging - {target_year}', fontsize=14, fontweight='bold', y=0.98)

    global_max = 0

    for idx, sc in enumerate(available):
        ax = axes[idx]
        color = COLORS[sc]

        # Optimal: from s_dict
        opt_geo = defaultdict(float)
        route_year = scenario_data[sc]['s']['route_charging']
        for geo_id, year_dict in scenario_data[sc]['s']['charging'].items():
            opt_geo[geo_id] = year_dict.get(target_year, 0)

        # Heuristic: SOC-aware
        heur_geo = defaultdict(float)
        for (od_id, path_id), year_dict in route_year.items():
            total_e = year_dict.get(target_year, 0)
            if total_e < 1e-6: continue
            geo_charges = compute_soc_charging(od_id, path_id, total_e, target_year)
            for geo_id, mwh in geo_charges.items():
                heur_geo[geo_id] += mwh

        # Convert to lat-GWh
        all_geos = set(list(opt_geo.keys()) + list(heur_geo.keys()))
        opt_lat = sorted([(geo_lat.get(g, 0), opt_geo.get(g, 0)/1000) for g in all_geos if geo_lat.get(g, 0) > 0])
        heur_lat = sorted([(geo_lat.get(g, 0), heur_geo.get(g, 0)/1000) for g in all_geos if geo_lat.get(g, 0) > 0])

        # Relocation metric
        total_energy = sum(opt_geo.values())
        relocated = sum(abs(opt_geo.get(g, 0) - heur_geo.get(g, 0)) for g in all_geos) / 2
        reloc_pct = relocated / total_energy * 100 if total_energy > 0 else 0

        # Plot
        if opt_lat:
            lats_o = np.array([x[0] for x in opt_lat])
            gwh_o = np.array([x[1] for x in opt_lat])
            si = np.argsort(lats_o)
            gwh_os = gaussian_filter1d(gwh_o[si], sigma=1.2) if len(lats_o) > 3 else gwh_o[si]
            ax.fill_betweenx(lats_o[si], 0, gwh_os, alpha=0.2, color=color)
            ax.plot(gwh_os, lats_o[si], color=color, linewidth=2, label='Optimal')
            global_max = max(global_max, max(gwh_o))

        if heur_lat:
            lats_h = np.array([x[0] for x in heur_lat])
            gwh_h = np.array([x[1] for x in heur_lat])
            si = np.argsort(lats_h)
            gwh_hs = gaussian_filter1d(gwh_h[si], sigma=1.2) if len(lats_h) > 3 else gwh_h[si]
            ax.plot(gwh_hs, lats_h[si], color='gray', linewidth=1.5, linestyle='--', label='Heuristic')

        for bname, blat in BORDERS.items():
            ax.axhline(y=blat, color='gray', linestyle=':', alpha=0.3, linewidth=0.7)

        opt_total = sum(opt_geo.values()) / 1000
        ax.set_title(f'{LABELS[sc]}\nRelocation: {reloc_pct:.1f}%', fontsize=10)
        ax.set_ylim(38, 72)
        ax.set_xlabel('GWh/yr', fontsize=9)
        if idx == 0:
            ax.set_ylabel('Latitude (°N)', fontsize=10)
            ax.legend(fontsize=8, loc='upper right')
        ax.grid(axis='y', alpha=0.2)

        print(f"  {LABELS[sc]}: relocation = {reloc_pct:.1f}%, total = {opt_total:.0f} GWh")

    # Set shared x-axis
    for ax in axes:
        ax.set_xlim(0, global_max * 1.15)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    outfile = BASE / f'scenario_opt_vs_heuristic_{target_year}.png'
    plt.savefig(outfile, dpi=200, bbox_inches='tight')
    plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
    print(f"  Saved: {outfile.name}")
    plt.close()

print("\nAll figures generated!")
