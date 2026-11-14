"""
Normalized charging distribution by latitude: Optimal vs Heuristic benchmark.
Generates plots for 2032 and 2048 using v2 scenario results.
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.ndimage import gaussian_filter1d
import yaml, re, glob, pathlib
from collections import defaultdict
from heuristic_charging import compute_heuristic_charging

BASE = pathlib.Path(__file__).resolve().parent
RESULTS_BASE = BASE / 'results' / 'uncertainty_scenarios_v2'
FIG_DIR = BASE / 'figures'
FIG_DIR.mkdir(exist_ok=True)

# Font
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Times New Roman', 'serif']
try:
    matplotlib.rcParams['text.usetex'] = True
    matplotlib.rcParams['font.serif'] = 'Times New Roman'
except Exception:
    pass
matplotlib.rcParams['font.size'] = 20
matplotlib.rcParams['axes.labelsize'] = 20

# Geo data
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}
all_geo_ids = [g['id'] for g in geo_data if g.get('type') == 'node']

# Paths, OD pairs, breaks, battery
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/Odpair.yaml') as f:
    odpairs_raw = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/MandatoryBreaks.yaml') as f:
    breaks_data = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/TechVehicle.yaml') as f:
    tv_data = yaml.safe_load(f)

path_seq = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist = {int(p['id']): [float(d) for d in p.get('distance_from_previous', [])] for p in paths}
od_path = {int(od['id']): int(od['path_id']) for od in odpairs_raw}

breaks_by_path = defaultdict(list)
for brk in breaks_data:
    breaks_by_path[int(brk['path_id'])].append(int(brk['latest_geo_id']))

bev_tv = next(t for t in tv_data if t['technology'] == 1)
GEN_YEARS = list(range(2008, 2008 + len(bev_tv['tank_capacity'])))
BATTERY_BY_GEN = dict(zip(GEN_YEARS, bev_tv['tank_capacity']))
SPEC_CONS_BY_GEN = dict(zip(GEN_YEARS, bev_tv['spec_cons']))

tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')

SCENARIOS = {
    'scenario_000': {'name': 'Go RES', 'color': '#1B5E20'},
    'scenario_001': {'name': 'NECPEssentials', 'color': '#E65100'},
    'scenario_002': {'name': 'REPowerEU++', 'color': '#0D47A1'},
    'scenario_003': {'name': 'Trinity', 'color': '#6A1B9A'},
}
scenario_order = ['scenario_000', 'scenario_001', 'scenario_002', 'scenario_003']
country_lats = {'IT': 42.5, 'AT': 47.5, 'DE': 51.0, 'DK': 56.0, 'SE': 62.0, 'NO': 64.0}


def battery_cap_for_year(year):
    return BATTERY_BY_GEN.get(year, BATTERY_BY_GEN[max(y for y in BATTERY_BY_GEN if y <= year)])

def spec_cons_for_year(year):
    return SPEC_CONS_BY_GEN.get(year, SPEC_CONS_BY_GEN[max(y for y in SPEC_CONS_BY_GEN if y <= year)])

def compute_soc_charging(od_id, path_id, total_energy_mwh, year):
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
        soc -= sc * (cum_dist[bi] - prev_dist)
        dist_to_next = (cum_dist[break_indices[i+1]] if i < len(break_indices)-1 else total_dist) - cum_dist[bi]
        energy_to_next = sc * dist_to_next
        if soc < energy_to_next + bat_cap * 0.1:
            charge = max(0, min(bat_cap - soc, energy_to_next - soc + bat_cap * 0.1))
            if charge > 0:
                charges[seq[bi]] = charges.get(seq[bi], 0) + charge
                soc += charge
    if not charges:
        for bi in break_indices:
            charges[seq[bi]] = 1.0
    total_raw = sum(charges.values())
    if total_raw < 1e-9: return {}
    scale = total_energy_mwh / total_raw
    return {g: v * scale for g, v in charges.items()}


def node_dict_to_normalized_curve(node_dict, sigma=1.5):
    """Convert {geo_id: value} to normalized (%) latitude curve, including zero nodes."""
    total = sum(node_dict.values())
    if total <= 0:
        return np.array([]), np.array([])
    # Include all nodes (with zeros)
    lat_val = [(geo_lat[g], node_dict.get(g, 0) / total * 100) for g in all_geo_ids if g in geo_lat]
    lat_val.sort()
    lats = np.array([x[0] for x in lat_val])
    vals = np.array([x[1] for x in lat_val])
    vals_smooth = gaussian_filter1d(vals, sigma=sigma)
    return lats, vals_smooth


# ── Load and process ──
for target_year in [2032, 2048]:
    print(f"\n{'='*80}")
    print(f"YEAR {target_year}")
    print(f"{'='*80}")

    all_data = {}
    for scen_id in scenario_order:
        s_files = sorted(glob.glob(str(RESULTS_BASE / scen_id / '*_s_dict.yaml')))
        if not s_files:
            print(f"  {scen_id}: MISSING")
            continue

        # Parse optimal charging by geo and by route
        opt_geo = defaultdict(float)
        route_energy = defaultdict(float)
        with open(s_files[-1]) as f:
            for line in f:
                m = tuple_pat.match(line.strip())
                if not m: continue
                year = int(m.group(1))
                if year != target_year: continue
                od_id, path_id, geo_id = int(m.group(3)), int(m.group(4)), int(m.group(5))
                fuel, infr = int(m.group(7)), int(m.group(8))
                val = float(m.group(10))
                if val < 1e-6 or fuel != 0 or infr not in {1, 2}: continue
                opt_geo[geo_id] += val
                route_energy[(od_id, path_id)] += val

        # Compute heuristic
        heur_geo = defaultdict(float)
        for (od_id, path_id), total_e in route_energy.items():
            if total_e < 1e-6: continue
            for g, mwh in compute_heuristic_charging(od_id, path_id, total_e, od_path, path_seq, path_dist, breaks_by_path).items():
                heur_geo[g] += mwh

        all_data[scen_id] = {'opt': dict(opt_geo), 'heur': dict(heur_geo)}
        print(f"  {scen_id} ({SCENARIOS[scen_id]['name']}): opt={sum(opt_geo.values())/1000:.0f} GWh, "
              f"heur={sum(heur_geo.values())/1000:.0f} GWh")

    # ── Plot ──
    fig, axes = plt.subplots(1, 4, figsize=(16, 7), sharey=True)

    for i, scen_id in enumerate(scenario_order):
        ax = axes[i]
        cfg = SCENARIOS[scen_id]
        data = all_data.get(scen_id)
        if data is None: continue

        # Optimal (solid, filled)
        lats, vals = node_dict_to_normalized_curve(data['opt'])
        if len(lats) > 0:
            ax.fill_betweenx(lats, 0, vals, color=cfg['color'], alpha=0.20)
            ax.plot(vals, lats, color=cfg['color'], linewidth=1.5, linestyle='-',
                    label='Optimal' if i == 0 else None)

        # Heuristic (dotted)
        lats_h, vals_h = node_dict_to_normalized_curve(data['heur'])
        if len(lats_h) > 0:
            ax.plot(vals_h, lats_h, color=cfg['color'], linewidth=1.5, linestyle=':',
                    label='Heuristic' if i == 0 else None)

        ax.set_title(cfg['name'], fontweight='bold')
        ax.set_xlabel('Share of total (\\%)')
        ax.set_ylim(40, 68)
        ax.grid(True, alpha=0.3, axis='x')

    axes[0].set_ylabel('Latitude ($^\\circ$N)')

    for country, lat in country_lats.items():
        axes[-1].text(1.02, lat, country, transform=axes[-1].get_yaxis_transform(),
                      fontsize=14, fontweight='bold', va='center', ha='left',
                      bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                               edgecolor='#888', alpha=0.9))

    legend_elements = [
        Line2D([0], [0], color='#555', linewidth=1.5, linestyle='-', label='Optimal'),
        Line2D([0], [0], color='#555', linewidth=1.5, linestyle=':', label='Heuristic benchmark'),
    ]
    plt.suptitle(f'Normalized charging distribution by latitude ({target_year})',
                 fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.22, wspace=0.08)
    fig.legend(handles=legend_elements, loc='lower center', ncol=2, fontsize=16,
               bbox_to_anchor=(0.5, -0.01), frameon=True)

    for ext in ['pdf', 'png']:
        fig.savefig(FIG_DIR / f'normalized_charging_opt_vs_heuristic_{target_year}.{ext}',
                    bbox_inches='tight', dpi=300)

    manuscript_img = BASE.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'
    if manuscript_img.exists():
        if target_year == 2032:
            fig.savefig(manuscript_img / 'analytical_even_charging_at_breaks.pdf', bbox_inches='tight')
        fig.savefig(manuscript_img / f'normalized_charging_{target_year}.pdf', bbox_inches='tight')

    print(f"  Saved: normalized_charging_opt_vs_heuristic_{target_year}.pdf")
    plt.close()

print("\nDone!")
