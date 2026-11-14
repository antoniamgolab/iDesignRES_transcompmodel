"""
4-panel figure: Optimized vs. Breaks-only vs. Analytical even at breaks
Shows BEV charged energy by latitude for all 4 GENeSYS scenarios at 2032.
"""
import yaml, pathlib, re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from collections import defaultdict
from scipy.ndimage import gaussian_filter1d

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'
RESULTS_UNC = BASE / 'results/uncertainty_scenarios_v2'
RESULTS_BRK = BASE / 'results/uncertainty_scenarios_breaks_only'
FIG_DIR = BASE / 'figures'

# Font settings (match manuscript figures)
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    'font.serif': 'mathpazo',
    'font.size': 20,
    'axes.labelsize': 20,
})

# Scenario config
SCENARIOS = {
    'scenario_000': {'name': 'Go RES', 'color': '#1B5E20'},
    'scenario_001': {'name': 'NECPEssentials', 'color': '#E65100'},
    'scenario_002': {'name': 'REPowerEU++', 'color': '#0D47A1'},
    'scenario_003': {'name': 'Trinity', 'color': '#6A1B9A'},
}

# Latest s_dict files (v2 = re-run with Crossover=-1)
S_FILES_UNC = {
    'scenario_000': 'scenario_000_cs_2026-02-14_18-25-42_s_dict.yaml',
    'scenario_001': 'scenario_001_cs_2026-02-14_20-00-45_s_dict.yaml',
    'scenario_002': 'scenario_002_cs_2026-02-14_22-18-02_s_dict.yaml',
    'scenario_003': 'scenario_003_cs_2026-02-15_00-33-53_s_dict.yaml',
}
S_FILES_BRK = {
    'scenario_000': 'scenario_000_cs_2026-02-14_20-51-10_s_dict.yaml',
    'scenario_001': 'scenario_001_cs_2026-02-14_22-29-10_s_dict.yaml',
    'scenario_002': 'scenario_002_cs_2026-02-14_23-47-28_s_dict.yaml',
    'scenario_003': 'scenario_003_cs_2026-02-15_01-16-54_s_dict.yaml',
}

TARGET_YEAR_IDX = 4   # period 4 → 2032
BEV_FL_IDXS = {1, 2}  # fl_idx 1=slow, 2=fast

# ── 1. Load geographic elements ───────────────────────────────────────
print("Loading geographic data...")
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_lat = {g['id']: g['coordinate_lat'] for g in geo_data}
geo_country = {g['id']: g['country'] for g in geo_data}

# ── Load Julia's actual prkg ordering ────────────────────────────────
_ordering_file = BASE / 'prkg_ordering_elsevier.txt'
_PRKG_FROM_FILE = None
if _ordering_file.exists():
    _PRKG_FROM_FILE = {}
    with open(_ordering_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line:
                continue
            _parts = _line.split('\t')
            _idx = int(_parts[0])
            _t = _parts[1].strip('()')
            _vals = [int(x.strip()) for x in _t.split(',')]
            _PRKG_FROM_FILE[_idx] = tuple(_vals)
    print(f"Loaded prkg ordering from Julia: {len(_PRKG_FROM_FILE)} entries")
else:
    print("WARNING: prkg_ordering_elsevier.txt not found, using Python sorted")


# ── 2. Per-scenario: load paths, odpairs, breaks, build p_r_k_g ──────
def load_scenario_structural(scenario_id):
    """Load paths, odpairs, breaks and build p_r_k_g mapping for one scenario."""
    inp = INPUT_BASE / scenario_id
    with open(inp / 'Path.yaml') as f:
        paths = yaml.load(f, Loader=yaml.UnsafeLoader)
    with open(inp / 'Odpair.yaml') as f:
        odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
    with open(inp / 'MandatoryBreaks.yaml') as f:
        breaks_data = yaml.safe_load(f)

    path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
    # Also store distance_from_previous for SOC simulation
    path_dist_by_id = {}
    for p in paths:
        pid = int(p['id'])
        dist = p.get('distance_from_previous', [])
        path_dist_by_id[pid] = [float(d) for d in dist]

    # Build p_r_k_g index — use Julia's ordering if available
    if _PRKG_FROM_FILE is not None:
        prkg_idx_map = dict(_PRKG_FROM_FILE)
    else:
        p_r_k_g_set = set()
        for od in odpairs:
            od_id = int(od['id'])
            pid = int(od['path_id'])
            for geo_id in path_by_id[pid]:
                p_r_k_g_set.add((0, od_id, pid, geo_id))
        p_r_k_g_sorted = sorted(p_r_k_g_set)
        prkg_idx_map = {i+1: t for i, t in enumerate(p_r_k_g_sorted)}

    # Breaks by path
    breaks_by_path = defaultdict(list)
    for brk in breaks_data:
        breaks_by_path[int(brk['path_id'])].append(int(brk['latest_geo_id']))

    return path_by_id, path_dist_by_id, prkg_idx_map, breaks_by_path


def load_s_dict(filepath, prkg_idx_map):
    """Parse CartesianIndex s_dict. Returns BEV by node, BEV by (od,path),
    BEV by (node, fl_idx), and diesel by node."""
    ci_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

    by_node = defaultdict(float)          # geo_id → BEV kWh
    by_od_path = defaultdict(float)       # (od_id, path_id) → BEV kWh
    by_node_fl = defaultdict(float)       # (geo_id, fl_idx) → BEV kWh
    diesel_by_node = defaultdict(float)   # geo_id → diesel kWh

    DIESEL_FL_IDX = 3

    with open(filepath) as f:
        for line in f:
            m = ci_pat.match(line.strip())
            if not m:
                continue
            y_idx = int(m.group(1))
            prkg_idx = int(m.group(2))
            fl_idx = int(m.group(4))
            val = float(m.group(6))

            if y_idx != TARGET_YEAR_IDX or val < 1e-6:
                continue

            prkg = prkg_idx_map.get(prkg_idx)
            if prkg is None:
                continue

            prod, od_id, path_id, geo_id = prkg

            if fl_idx in BEV_FL_IDXS:
                by_node[geo_id] += val
                by_od_path[(od_id, path_id)] += val
                by_node_fl[(geo_id, fl_idx)] += val
            elif fl_idx == DIESEL_FL_IDX:
                diesel_by_node[geo_id] += val

    return by_node, by_od_path, by_node_fl, diesel_by_node


def compute_analytical_even(by_od_path, breaks_by_path, path_by_id):
    """Distribute each OD pair's total energy evenly across its break nodes."""
    even = defaultdict(float)
    for (od_id, path_id), total_energy in by_od_path.items():
        break_nodes = breaks_by_path.get(path_id, [])
        if not break_nodes:
            seq = path_by_id.get(path_id, [])
            if len(seq) >= 2:
                even[seq[0]] += total_energy / 2
                even[seq[-1]] += total_energy / 2
            continue
        per_break = total_energy / len(break_nodes)
        for geo_id in break_nodes:
            even[geo_id] += per_break
    return even


BATTERY_CAP = 1187.0   # kWh
SPEC_CONS_2032 = 1.6   # kWh/km at year index 12 (2032)


def compute_soc_aware_distribution(by_od_path, breaks_by_path, path_by_id,
                                   path_dist_by_id, battery_cap=BATTERY_CAP,
                                   spec_cons=SPEC_CONS_2032,
                                   initial_soc_frac=0.5):
    """Distribute energy across break nodes using SOC-aware 'lazy charging' rule.

    For each OD pair's path:
      1. Start at initial_soc_frac of battery capacity (default 50%, matching
         the optimization model's SOC^{init} = 0.5 assumption)
      2. Consume energy per km along the route
      3. At each mandatory break, check if SOC suffices to reach the next break
         (or destination). If yes, skip. If no, charge to full.
      4. Scale proportions to match the model's actual total for this OD pair
    """
    soc_dist = defaultdict(float)
    n_skipped = 0
    n_charged = 0
    n_total_routes = 0

    for (od_id, path_id), total_energy in by_od_path.items():
        if total_energy < 1e-6:
            continue
        n_total_routes += 1

        seq = path_by_id.get(path_id, [])
        dist = path_dist_by_id.get(path_id, [])
        break_set = set(breaks_by_path.get(path_id, []))

        if not seq or not dist or len(seq) != len(dist):
            breaks = breaks_by_path.get(path_id, [])
            if breaks:
                per = total_energy / len(breaks)
                for g in breaks:
                    soc_dist[g] += per
            continue

        # Pre-compute: for each node index, distance to the next break or end
        # This lets us decide at each break whether we can skip it
        break_indices = [i for i, n in enumerate(seq) if n in break_set]

        # Simulate SOC with lazy charging
        initial_soc = battery_cap * initial_soc_frac
        soc = initial_soc
        charges = {}

        for bi_pos, bi in enumerate(break_indices):
            # Consume energy from previous position to this break
            # (We track SOC cumulatively)
            pass

        # Simpler approach: walk through the entire sequence
        soc = initial_soc
        charges = {}

        for i, node in enumerate(seq):
            if i > 0:
                soc -= spec_cons * dist[i]

            if node in break_set:
                # Calculate distance from here to the NEXT break (or destination)
                # Find next break index after current position
                remaining_to_next = 0.0
                found_next_break = False
                for j in range(i + 1, len(seq)):
                    remaining_to_next += dist[j]
                    if seq[j] in break_set:
                        found_next_break = True
                        break
                if not found_next_break:
                    # No more breaks — need to reach destination
                    remaining_to_next = sum(dist[j] for j in range(i + 1, len(seq)))

                energy_to_next = remaining_to_next * spec_cons

                if soc < energy_to_next:
                    # Must charge — charge to full
                    charge = battery_cap - soc
                    charges[node] = charges.get(node, 0) + charge
                    soc = battery_cap
                    n_charged += 1
                else:
                    # Can skip this break
                    n_skipped += 1

        # Scale simulation charges to match model's actual total
        sim_total = sum(charges.values())
        if sim_total > 0:
            for node, sim_kWh in charges.items():
                soc_dist[node] += total_energy * (sim_kWh / sim_total)
        else:
            # Route completable on initial SOC — distribute to last break
            breaks = breaks_by_path.get(path_id, [])
            if breaks:
                # Put all at the last break (closest to where battery runs low)
                soc_dist[breaks[-1]] += total_energy

    print(f"    SOC-aware (lazy): {n_skipped} breaks skipped, "
          f"{n_charged} charged, across {n_total_routes} routes")
    return soc_dist


def node_dict_to_lat_curve(node_dict, sigma=1.5, normalize=False):
    """Convert {geo_id: value} to smoothed (lat_array, val_array).
    If normalize=True, values sum to 100 (percent of total)."""
    lat_vals = []
    for geo_id, val in node_dict.items():
        lat = geo_lat.get(geo_id)
        if lat is not None and val > 0:
            lat_vals.append((lat, val))
    if len(lat_vals) < 2:
        return np.array([]), np.array([])
    lat_vals.sort()
    lats = np.array([x[0] for x in lat_vals])
    vals = np.array([x[1] for x in lat_vals])
    if normalize:
        total = vals.sum()
        if total > 0:
            vals = vals / total * 100  # percent
    else:
        vals = vals / 1000  # kWh → MWh
    vals_smooth = gaussian_filter1d(vals, sigma=sigma)
    return lats, vals_smooth


# ── 3. Load and process all scenarios ─────────────────────────────────
all_data = {}
for scen_id in SCENARIOS:
    print(f"Processing {scen_id} ({SCENARIOS[scen_id]['name']})...")
    path_by_id, path_dist_by_id, prkg_idx_map, breaks_by_path = load_scenario_structural(scen_id)

    # Unconstrained
    unc_file = RESULTS_UNC / scen_id / S_FILES_UNC[scen_id]
    unc_by_node, unc_by_od, unc_by_node_fl, unc_diesel = load_s_dict(unc_file, prkg_idx_map)

    # Breaks-only
    brk_file = RESULTS_BRK / scen_id / S_FILES_BRK[scen_id]
    brk_by_node, brk_by_od, brk_by_node_fl, brk_diesel = load_s_dict(brk_file, prkg_idx_map)

    # Analytical even (based on unconstrained total energy per OD pair)
    even_by_node = compute_analytical_even(unc_by_od, breaks_by_path, path_by_id)
    even_by_node_fl = {(geo_id, 1): val for geo_id, val in even_by_node.items()}

    # SOC-aware distribution (charge-to-full at breaks)
    soc_by_node = compute_soc_aware_distribution(
        unc_by_od, breaks_by_path, path_by_id, path_dist_by_id)
    soc_by_node_fl = {(geo_id, 1): val for geo_id, val in soc_by_node.items()}

    all_data[scen_id] = {
        'unc': unc_by_node,
        'brk': brk_by_node,
        'even': even_by_node,
        'soc': soc_by_node,
        'unc_fl': unc_by_node_fl,
        'brk_fl': brk_by_node_fl,
        'even_fl': even_by_node_fl,
        'soc_fl': soc_by_node_fl,
        'unc_diesel': unc_diesel,
        'brk_diesel': brk_diesel,
        'path_by_id': path_by_id,
        'path_dist_by_id': path_dist_by_id,
        'prkg_idx_map': prkg_idx_map,
        'breaks_by_path': breaks_by_path,
    }
    print(f"  Unc: {sum(unc_by_node.values()):.0f} kWh | "
          f"Brk: {sum(brk_by_node.values()):.0f} kWh | "
          f"Even: {sum(even_by_node.values()):.0f} kWh | "
          f"SOC: {sum(soc_by_node.values()):.0f} kWh | "
          f"Diesel(unc): {sum(unc_diesel.values()):.0f} kWh | "
          f"Diesel(brk): {sum(brk_diesel.values()):.0f} kWh")

# ── 4. Plot 4-panel figure ────────────────────────────────────────────
print("\nPlotting...")
country_lats = {'IT': 42.5, 'AT': 47.5, 'DE': 51.0, 'DK': 56.0, 'SE': 62.0, 'NO': 64.0}
scenario_order = ['scenario_000', 'scenario_001', 'scenario_002', 'scenario_003']

fig, axes = plt.subplots(1, 4, figsize=(16, 7), sharey=True)

curve_styles = [
    ('unc', '-',  1.5, 0.20, 'Reference'),
    ('soc', ':', 1.5, 0.05, 'Deterministic benchmark'),
]

for i, scen_id in enumerate(scenario_order):
    ax = axes[i]
    cfg = SCENARIOS[scen_id]
    data = all_data[scen_id]

    for key, ls, lw, alpha_fill, label in curve_styles:
        lats, vals = node_dict_to_lat_curve(data[key], normalize=True)
        if len(lats) == 0:
            continue

        show_label = label if i == 0 else None
        ax.fill_betweenx(lats, 0, vals, color=cfg['color'], alpha=alpha_fill)
        ax.plot(vals, lats, color=cfg['color'], linewidth=lw, linestyle=ls, label=show_label)

    ax.set_title(cfg['name'], fontweight='bold')
    ax.set_xlabel('Share of total charging (\\%)')
    ax.set_ylim(40, 68)
    ax.grid(True, alpha=0.3, axis='x')

axes[0].set_ylabel('Latitude ($^\\circ$N)')

# Country labels on right
for country, lat in country_lats.items():
    axes[-1].text(1.02, lat, country, transform=axes[-1].get_yaxis_transform(),
                  fontsize=14, fontweight='bold', va='center', ha='left',
                  bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                           edgecolor='#888', alpha=0.9))

# Legend
legend_elements = [
    Line2D([0], [0], color='#555', linewidth=1.5, linestyle='-', label='Reference'),
    Line2D([0], [0], color='#555', linewidth=1.5, linestyle=':', label='Deterministic benchmark'),
]
plt.suptitle('Normalized charging distribution by latitude (2032)', fontweight='bold', y=1.01)
plt.tight_layout()
plt.subplots_adjust(bottom=0.22, wspace=0.08)

fig.legend(handles=legend_elements, loc='lower center', ncol=2, fontsize=16,
           bbox_to_anchor=(0.5, -0.01), frameon=True)

manuscript_img = BASE.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'
for ext in ['pdf', 'svg']:
    fig.savefig(FIG_DIR / f'analytical_even_charging_at_breaks.{ext}',
                bbox_inches='tight', dpi=300)
    manuscript_img.mkdir(parents=True, exist_ok=True)
    fig.savefig(manuscript_img / f'analytical_even_charging_at_breaks.{ext}',
                bbox_inches='tight', dpi=300)
print(f"Saved to {FIG_DIR / 'analytical_even_charging_at_breaks.pdf'}")
plt.close()

# ── 5. Quantify demand shift ─────────────────────────────────────────

# (1) Country-level share shift: SOC-aware benchmark vs optimized vs breaks-only
def aggregate_by_country(node_dict):
    """Sum energy by country from {geo_id: kWh}."""
    by_country = defaultdict(float)
    for geo_id, val in node_dict.items():
        c = geo_country.get(geo_id, '??')
        by_country[c] += val
    return dict(by_country)

# (2) Total relocated volume = sum|opt(node) - even(node)| / 2
def total_relocated_pct(opt_dict, even_dict):
    all_nodes = set(opt_dict.keys()) | set(even_dict.keys())
    abs_diff = sum(abs(opt_dict.get(n, 0) - even_dict.get(n, 0)) for n in all_nodes)
    total = sum(opt_dict.values())
    if total == 0:
        return 0.0
    return (abs_diff / 2) / total * 100

print("\n" + "=" * 80)
print("DEMAND SHIFT QUANTIFICATION (2032)")
print("=" * 80)

country_order = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']

for scen_id in scenario_order:
    cfg = SCENARIOS[scen_id]
    data = all_data[scen_id]

    soc_c = aggregate_by_country(data['soc'])
    unc_c = aggregate_by_country(data['unc'])
    brk_c = aggregate_by_country(data['brk'])

    total_soc = sum(soc_c.values())
    total_unc = sum(unc_c.values())
    total_brk = sum(brk_c.values())

    reloc_unc = total_relocated_pct(data['unc'], data['soc'])
    reloc_brk = total_relocated_pct(data['brk'], data['soc'])

    print(f"\n--- {cfg['name']} ---")
    print(f"{'Country':>4s}  {'SOC-aware (%)':>13s}  {'Optim (%)':>10s}  {'Delta (pp)':>11s}  {'Breaks (%)':>11s}  {'Delta (pp)':>11s}")
    for c in country_order:
        s_pct = soc_c.get(c, 0) / total_soc * 100 if total_soc else 0
        u_pct = unc_c.get(c, 0) / total_unc * 100 if total_unc else 0
        b_pct = brk_c.get(c, 0) / total_brk * 100 if total_brk else 0
        print(f"  {c:>4s}  {s_pct:13.1f}  {u_pct:10.1f}  {u_pct - s_pct:+10.1f}  {b_pct:10.1f}  {b_pct - s_pct:+10.1f}")

    print(f"\n  Total relocated (optimized vs SOC-aware): {reloc_unc:.1f}%")
    print(f"  Total relocated (breaks vs SOC-aware):    {reloc_brk:.1f}%")

# ── 6. Export summary table as CSV ────────────────────────────────────
import csv
rows = []
for scen_id in scenario_order:
    cfg = SCENARIOS[scen_id]
    data = all_data[scen_id]
    soc_c = aggregate_by_country(data['soc'])
    unc_c = aggregate_by_country(data['unc'])
    total_soc = sum(soc_c.values())
    total_unc = sum(unc_c.values())
    reloc = total_relocated_pct(data['unc'], data['soc'])
    for c in country_order:
        s_pct = soc_c.get(c, 0) / total_soc * 100 if total_soc else 0
        u_pct = unc_c.get(c, 0) / total_unc * 100 if total_unc else 0
        rows.append({
            'scenario': cfg['name'],
            'country': c,
            'soc_aware_share_pct': round(s_pct, 2),
            'optimized_share_pct': round(u_pct, 2),
            'delta_pp': round(u_pct - s_pct, 2),
        })
    rows.append({
        'scenario': cfg['name'],
        'country': 'TOTAL_RELOCATED',
        'soc_aware_share_pct': '',
        'optimized_share_pct': '',
        'delta_pp': round(reloc, 2),
    })

csv_path = FIG_DIR / 'charging_demand_shift_quantification.csv'
with open(csv_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['scenario', 'country', 'soc_aware_share_pct', 'optimized_share_pct', 'delta_pp'])
    w.writeheader()
    w.writerows(rows)
print(f"\nCSV saved to {csv_path}")

# ══════════════════════════════════════════════════════════════════════
# ── 7. RAIL SCENARIOS — same analysis ────────────────────────────────
# ══════════════════════════════════════════════════════════════════════

RAIL_INPUT_BASE = BASE / 'input_data/uncertainty_scenarios_rail'
RAIL_RESULTS = BASE / 'results/rail'

RAIL_SCENARIOS = {
    'scenario_004': {'name': 'Go RES', 'color': '#1B5E20', 'road_id': 'scenario_000'},
    'scenario_010': {'name': 'NECPEssentials', 'color': '#E65100', 'road_id': 'scenario_001'},
    'scenario_016': {'name': 'REPowerEU++', 'color': '#0D47A1', 'road_id': 'scenario_002'},
    'scenario_022': {'name': 'Trinity', 'color': '#6A1B9A', 'road_id': 'scenario_003'},
}

RAIL_S_FILES = {
    'scenario_004': 'scenario_004_cs_2026-02-14_20-52-20_s_dict.yaml',
    'scenario_010': 'scenario_010_cs_2026-02-14_21-34-41_s_dict.yaml',
    'scenario_016': 'scenario_016_cs_2026-02-14_22-16-25_s_dict.yaml',
    'scenario_022': 'scenario_022_cs_2026-02-14_22-49-14_s_dict.yaml',
}

rail_scenario_order = ['scenario_004', 'scenario_010', 'scenario_016', 'scenario_022']

# Load rail structural data (different paths/odpairs than road)
def load_rail_scenario_structural(scenario_id):
    inp = RAIL_INPUT_BASE / scenario_id
    with open(inp / 'Path.yaml') as f:
        paths = yaml.load(f, Loader=yaml.UnsafeLoader)
    with open(inp / 'Odpair.yaml') as f:
        odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
    with open(inp / 'MandatoryBreaks.yaml') as f:
        breaks_data = yaml.safe_load(f)

    path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
    path_dist_by_id = {}
    for p in paths:
        pid = int(p['id'])
        dist = p.get('distance_from_previous', [])
        path_dist_by_id[pid] = [float(d) for d in dist]

    p_r_k_g_set = set()
    for od in odpairs:
        od_id = int(od['id'])
        pid = int(od['path_id'])
        for geo_id in path_by_id[pid]:
            p_r_k_g_set.add((0, od_id, pid, geo_id))
    p_r_k_g_sorted = sorted(p_r_k_g_set)
    prkg_idx_map = {i+1: t for i, t in enumerate(p_r_k_g_sorted)}

    breaks_by_path = defaultdict(list)
    for brk in breaks_data:
        breaks_by_path[int(brk['path_id'])].append(int(brk['latest_geo_id']))

    return path_by_id, path_dist_by_id, prkg_idx_map, breaks_by_path

# Process rail scenarios
print("\n" + "=" * 80)
print("RAIL SCENARIOS")
print("=" * 80)

rail_data = {}
for scen_id in rail_scenario_order:
    cfg = RAIL_SCENARIOS[scen_id]
    print(f"Processing {scen_id} ({cfg['name']} + rail)...")
    path_by_id, path_dist_by_id, prkg_idx_map, breaks_by_path = load_rail_scenario_structural(scen_id)

    s_file = RAIL_RESULTS / scen_id / RAIL_S_FILES[scen_id]
    rail_by_node, rail_by_od, rail_by_node_fl, rail_diesel = load_s_dict(s_file, prkg_idx_map)
    even_by_node = compute_analytical_even(rail_by_od, breaks_by_path, path_by_id)
    even_by_node_fl = {(geo_id, 1): val for geo_id, val in even_by_node.items()}

    # SOC-aware distribution for rail
    soc_by_node = compute_soc_aware_distribution(
        rail_by_od, breaks_by_path, path_by_id, path_dist_by_id)
    soc_by_node_fl = {(geo_id, 1): val for geo_id, val in soc_by_node.items()}

    rail_data[scen_id] = {
        'unc': rail_by_node,
        'even': even_by_node,
        'soc': soc_by_node,
        'unc_fl': rail_by_node_fl,
        'even_fl': even_by_node_fl,
        'soc_fl': soc_by_node_fl,
        'unc_diesel': rail_diesel,
    }
    print(f"  Rail optimized: {sum(rail_by_node.values()):.0f} kWh | "
          f"Even: {sum(even_by_node.values()):.0f} kWh | "
          f"SOC: {sum(soc_by_node.values()):.0f} kWh | "
          f"Diesel: {sum(rail_diesel.values()):.0f} kWh")

# ── 8. Plot 4-panel figure for rail ──────────────────────────────────
print("\nPlotting rail figure...")

fig, axes = plt.subplots(1, 4, figsize=(16, 7), sharey=True)

rail_curve_styles = [
    ('unc', '-',  1.5, 0.20, 'Optimized (road + rail)'),
    ('soc', '-.', 1.2, 0.05, 'SOC-aware at breaks'),
]

for i, scen_id in enumerate(rail_scenario_order):
    ax = axes[i]
    cfg = RAIL_SCENARIOS[scen_id]
    data = rail_data[scen_id]

    # Also plot road-only optimized for reference
    road_id = cfg['road_id']
    road_node = all_data[road_id]['unc']
    lats_road, vals_road = node_dict_to_lat_curve(road_node, normalize=True)
    if len(lats_road) > 0:
        label_road = 'Optimized (road only)' if i == 0 else None
        ax.fill_betweenx(lats_road, 0, vals_road, color=cfg['color'], alpha=0.08)
        ax.plot(vals_road, lats_road, color=cfg['color'], linewidth=1.2,
                linestyle='--', label=label_road)

    for key, ls, lw, alpha_fill, label in rail_curve_styles:
        lats, vals = node_dict_to_lat_curve(data[key], normalize=True)
        if len(lats) == 0:
            continue
        show_label = label if i == 0 else None
        ax.fill_betweenx(lats, 0, vals, color=cfg['color'], alpha=alpha_fill)
        ax.plot(vals, lats, color=cfg['color'], linewidth=lw, linestyle=ls, label=show_label)

    for country, lat in country_lats.items():
        ax.axhline(lat, color='gray', linestyle=':', alpha=0.3, linewidth=0.8)

    ax.set_title(cfg['name'], fontweight='bold')
    ax.set_xlabel('Share of total charging (\\%)')
    ax.set_ylim(40, 68)
    ax.grid(False)

axes[0].set_ylabel('Latitude ($^\\circ$N)')

for country, lat in country_lats.items():
    axes[-1].text(1.02, lat, country, transform=axes[-1].get_yaxis_transform(),
                  fontsize=14, fontweight='bold', va='center', ha='left',
                  bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                           edgecolor='#888', alpha=0.9))

legend_elements = [
    Line2D([0], [0], color='#555', linewidth=1.5, linestyle='-', label='Optimized (road + rail)'),
    Line2D([0], [0], color='#555', linewidth=1.2, linestyle='--', label='Optimized (road only)'),
    Line2D([0], [0], color='#555', linewidth=1.2, linestyle='-.', label='SOC-aware at breaks'),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=3, fontsize=16,
           bbox_to_anchor=(0.5, -0.02), frameon=True)

plt.suptitle('Normalized BEV charging distribution with modal shift to rail (2032)',
             fontweight='bold', y=1.01)
plt.tight_layout()
plt.subplots_adjust(bottom=0.10, wspace=0.08)

for ext in ['pdf', 'svg']:
    fig.savefig(FIG_DIR / f'analytical_even_charging_rail.{ext}',
                bbox_inches='tight', dpi=300)
    if manuscript_img.exists():
        fig.savefig(manuscript_img / f'analytical_even_charging_rail.{ext}',
                    bbox_inches='tight', dpi=300)
print(f"Saved to {FIG_DIR / 'analytical_even_charging_rail.pdf'}")
plt.close()

# ── 9. Quantify demand shift for rail ─────────────────────────────────
print("\n" + "=" * 80)
print("DEMAND SHIFT QUANTIFICATION — RAIL (2032)")
print("=" * 80)

for scen_id in rail_scenario_order:
    cfg = RAIL_SCENARIOS[scen_id]
    data = rail_data[scen_id]
    road_id = cfg['road_id']

    soc_c = aggregate_by_country(data['soc'])
    rail_c = aggregate_by_country(data['unc'])
    road_c = aggregate_by_country(all_data[road_id]['unc'])

    total_soc = sum(soc_c.values())
    total_rail = sum(rail_c.values())
    total_road = sum(road_c.values())

    reloc_rail = total_relocated_pct(data['unc'], data['soc'])
    reloc_road = total_relocated_pct(all_data[road_id]['unc'], all_data[road_id]['soc'])

    print(f"\n--- {cfg['name']} ---")
    print(f"{'Country':>4s}  {'SOC-aware (%)':>13s}  {'Rail opt (%)':>13s}  {'Delta (pp)':>11s}  {'Road opt (%)':>13s}  {'Delta (pp)':>11s}")
    for c in country_order:
        s_pct = soc_c.get(c, 0) / total_soc * 100 if total_soc else 0
        r_pct = rail_c.get(c, 0) / total_rail * 100 if total_rail else 0
        u_pct = road_c.get(c, 0) / total_road * 100 if total_road else 0
        print(f"  {c:>4s}  {s_pct:13.1f}  {r_pct:13.1f}  {r_pct - s_pct:+10.1f}  {u_pct:13.1f}  {u_pct - s_pct:+10.1f}")

    print(f"\n  Total relocated (rail opt vs SOC-aware):  {reloc_rail:.1f}%")
    print(f"  Total relocated (road opt vs SOC-aware):  {reloc_road:.1f}%")
    print(f"  Total BEV energy — road: {total_road:.0f} kWh, rail: {total_rail:.0f} kWh "
          f"(delta: {(total_rail - total_road) / total_road * 100:+.1f}%)")

# ── 10. Export combined CSV ───────────────────────────────────────────
rows_combined = []
for scen_id in rail_scenario_order:
    cfg = RAIL_SCENARIOS[scen_id]
    data = rail_data[scen_id]
    road_id = cfg['road_id']

    soc_c = aggregate_by_country(data['soc'])
    rail_c = aggregate_by_country(data['unc'])
    road_c = aggregate_by_country(all_data[road_id]['unc'])
    road_soc_c = aggregate_by_country(all_data[road_id]['soc'])

    total_soc = sum(soc_c.values())
    total_rail = sum(rail_c.values())
    total_road = sum(road_c.values())
    total_road_soc = sum(road_soc_c.values())

    reloc_rail = total_relocated_pct(data['unc'], data['soc'])
    reloc_road = total_relocated_pct(all_data[road_id]['unc'], all_data[road_id]['soc'])

    for c in country_order:
        rs_pct = road_soc_c.get(c, 0) / total_road_soc * 100 if total_road_soc else 0
        ro_pct = road_c.get(c, 0) / total_road * 100 if total_road else 0
        s_pct = soc_c.get(c, 0) / total_soc * 100 if total_soc else 0
        r_pct = rail_c.get(c, 0) / total_rail * 100 if total_rail else 0
        rows_combined.append({
            'scenario': cfg['name'],
            'country': c,
            'road_soc_pct': round(rs_pct, 2),
            'road_opt_pct': round(ro_pct, 2),
            'road_delta_pp': round(ro_pct - rs_pct, 2),
            'rail_soc_pct': round(s_pct, 2),
            'rail_opt_pct': round(r_pct, 2),
            'rail_delta_pp': round(r_pct - s_pct, 2),
        })
    rows_combined.append({
        'scenario': cfg['name'],
        'country': 'TOTAL_RELOCATED',
        'road_soc_pct': '', 'road_opt_pct': '', 'road_delta_pp': round(reloc_road, 2),
        'rail_soc_pct': '', 'rail_opt_pct': '', 'rail_delta_pp': round(reloc_rail, 2),
    })

csv_path2 = FIG_DIR / 'charging_demand_shift_road_vs_rail.csv'
with open(csv_path2, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=[
        'scenario', 'country',
        'road_soc_pct', 'road_opt_pct', 'road_delta_pp',
        'rail_soc_pct', 'rail_opt_pct', 'rail_delta_pp',
    ])
    w.writeheader()
    w.writerows(rows_combined)
print(f"\nCombined CSV saved to {csv_path2}")

# ══════════════════════════════════════════════════════════════════════
# ── 11. FUELING COST COMPARISON ──────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════

YEAR_ARRAY_IDX = 12  # 2032 - 2020 = index 12 in the 41-element arrays

def load_fuel_prices(scenario_id, input_base):
    """Load electricity and diesel prices per (location, fueling_infr_type) at 2032."""
    inp = input_base / scenario_id
    with open(inp / 'FuelCost.yaml') as f:
        fc = yaml.safe_load(f)
    with open(inp / 'GeographicElement.yaml') as f:
        geo = yaml.safe_load(f)

    # Electricity price: (location, fit_id) → EUR/kWh
    elec_price = {}
    for entry in fc:
        if entry['fuel'] == 'electricity':
            loc = entry['location']
            fit_id = entry['fueling_infr_type_id']
            price = entry['cost_per_kWh'][YEAR_ARRAY_IDX]
            elec_price[(loc, fit_id)] = price

    # Diesel base price: location → EUR/kWh
    diesel_base = {}
    for entry in fc:
        if entry['fuel'] == 'diesel':
            diesel_base[entry['location']] = entry['cost_per_kWh'][YEAR_ARRAY_IDX]

    # Carbon price: location → EUR/tCO2
    carbon_price = {}
    for g in geo:
        carbon_price[g['id']] = g['carbon_price'][YEAR_ARRAY_IDX]

    # Diesel emission factor = 266 gCO2/kWh = 0.000266 tCO2/kWh
    EMISSION_FACTOR = 266.0 / 1e6  # tCO2/kWh

    # Effective diesel: base + carbon_price * emission_factor
    diesel_effective = {}
    for loc in diesel_base:
        cp = carbon_price.get(loc, 0)
        diesel_effective[loc] = diesel_base[loc] + cp * EMISSION_FACTOR

    return elec_price, diesel_effective


def compute_weighted_elec_cost(by_node_fl, elec_price):
    """Weighted average electricity price (EUR/kWh) from {(geo_id, fl_idx): kWh}."""
    # fl_idx in s_dict: 1=slow(FIT1), 2=fast(FIT2)
    total_cost = 0.0
    total_kwh = 0.0
    for (geo_id, fl_idx), kwh in by_node_fl.items():
        if kwh <= 0:
            continue
        # Map fl_idx to fueling_infr_type_id: 1→1 (slow), 2→2 (fast)
        price = elec_price.get((geo_id, fl_idx), 0)
        total_cost += kwh * price
        total_kwh += kwh
    avg_price = total_cost / total_kwh if total_kwh > 0 else 0
    return total_cost, total_kwh, avg_price


def compute_diesel_cost(diesel_by_node, diesel_effective):
    """Total diesel cost from {geo_id: kWh}."""
    total_cost = 0.0
    total_kwh = 0.0
    for geo_id, kwh in diesel_by_node.items():
        if kwh <= 0:
            continue
        price = diesel_effective.get(geo_id, 0)
        total_cost += kwh * price
        total_kwh += kwh
    avg_price = total_cost / total_kwh if total_kwh > 0 else 0
    return total_cost, total_kwh, avg_price


print("\n" + "=" * 80)
print("FUELING COST COMPARISON (2032)")
print("=" * 80)

cost_rows = []
for scen_id in scenario_order:
    cfg = SCENARIOS[scen_id]
    data = all_data[scen_id]

    elec_price, diesel_eff = load_fuel_prices(scen_id, INPUT_BASE)

    # Electricity costs for 3 strategies
    unc_cost, unc_kwh, unc_avg = compute_weighted_elec_cost(data['unc_fl'], elec_price)
    brk_cost, brk_kwh, brk_avg = compute_weighted_elec_cost(data['brk_fl'], elec_price)
    soc_cost, soc_kwh, soc_avg = compute_weighted_elec_cost(data['soc_fl'], elec_price)

    # Diesel costs (only differs between unc and brk due to fleet changes)
    unc_d_cost, unc_d_kwh, unc_d_avg = compute_diesel_cost(data['unc_diesel'], diesel_eff)
    brk_d_cost, brk_d_kwh, brk_d_avg = compute_diesel_cost(data['brk_diesel'], diesel_eff)

    print(f"\n--- {cfg['name']} ---")
    print(f"  {'Strategy':<25s}  {'Elec kWh':>10s}  {'Avg EUR/kWh':>12s}  {'Elec cost':>12s}  "
          f"{'Diesel kWh':>11s}  {'Diesel cost':>12s}  {'Total fuel':>12s}")
    for label, e_cost, e_kwh, e_avg, d_cost, d_kwh in [
        ('Optimized', unc_cost, unc_kwh, unc_avg, unc_d_cost, unc_d_kwh),
        ('Breaks only', brk_cost, brk_kwh, brk_avg, brk_d_cost, brk_d_kwh),
        ('SOC-aware at breaks', soc_cost, soc_kwh, soc_avg, unc_d_cost, unc_d_kwh),
    ]:
        total_fuel = e_cost + d_cost
        print(f"  {label:<25s}  {e_kwh:10.0f}  {e_avg:12.4f}  {e_cost:12.2f}  "
              f"{d_kwh:10.0f}  {d_cost:12.2f}  {total_fuel:12.2f}")

    # Savings comparisons
    print(f"\n  Avg elec price comparison:")
    print(f"    Optimized:        {unc_avg:.4f} EUR/kWh")
    print(f"    SOC-aware:        {soc_avg:.4f} EUR/kWh  (delta: {(soc_avg-unc_avg)/unc_avg*100:+.1f}%)")
    print(f"    Breaks only:      {brk_avg:.4f} EUR/kWh  (delta: {(brk_avg-unc_avg)/unc_avg*100:+.1f}%)")

    cost_rows.append({
        'scenario': cfg['name'],
        'unc_avg_eur_kwh': round(unc_avg, 4),
        'soc_avg_eur_kwh': round(soc_avg, 4),
        'brk_avg_eur_kwh': round(brk_avg, 4),
        'delta_soc_pct': round((soc_avg-unc_avg)/unc_avg*100, 2),
        'delta_brk_pct': round((brk_avg-unc_avg)/unc_avg*100, 2),
    })

csv_path3 = FIG_DIR / 'fueling_cost_comparison_2032.csv'
with open(csv_path3, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(cost_rows[0].keys()))
    w.writeheader()
    w.writerows(cost_rows)
print(f"\nCSV saved to {csv_path3}")
