"""
Regenerate Figure 10 (rail_tkm_by_latitude_scenarios_overlap.pdf) and
Figure 11 (bev_energy_by_latitude_GoRES_only.pdf) with:
  - text.usetex=True (Computer Modern Roman font, matching other figures)
  - No bold text in titles/labels
  - Figure 10: bigger legend
  - Figure 11: fix x-axis label overlap
"""

import ast
import yaml
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from scipy.ndimage import gaussian_filter1d
from pathlib import Path

# ── Font settings ────────────────────────────────────────────────────
plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": "mathpazo",
    "font.size": 20,
})

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / 'results'
INPUT_DIR = BASE_DIR / 'input_data'
FIG_DIR = BASE_DIR / 'figures'
MANUSCRIPT_IMG = BASE_DIR.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'

SCENARIOS = {
    'Go RES': {
        'baseline_dir': RESULTS_DIR / 'uncertainty_scenarios_v2' / 'scenario_000',
        'baseline_prefix': 'scenario_000_cs_2026-02-14_18-25-42',
        'rail_dir': RESULTS_DIR / 'rail' / 'scenario_004',
        'rail_prefix': 'scenario_004_cs_2026-02-14_20-52-20',
        'input_baseline': INPUT_DIR / 'uncertainty_scenarios' / 'scenario_000',
        'input_rail': INPUT_DIR / 'uncertainty_scenarios_rail' / 'scenario_000',
    },
    'NECPEssentials': {
        'baseline_dir': RESULTS_DIR / 'uncertainty_scenarios_v2' / 'scenario_001',
        'baseline_prefix': 'scenario_001_cs_2026-02-14_20-00-45',
        'rail_dir': RESULTS_DIR / 'rail' / 'scenario_010',
        'rail_prefix': 'scenario_010_cs_2026-02-14_21-34-41',
        'input_baseline': INPUT_DIR / 'uncertainty_scenarios' / 'scenario_001',
        'input_rail': INPUT_DIR / 'uncertainty_scenarios_rail' / 'scenario_001',
    },
    'REPowerEU++': {
        'baseline_dir': RESULTS_DIR / 'uncertainty_scenarios_v2' / 'scenario_002',
        'baseline_prefix': 'scenario_002_cs_2026-02-14_22-18-02',
        'rail_dir': RESULTS_DIR / 'rail' / 'scenario_016',
        'rail_prefix': 'scenario_016_cs_2026-02-14_22-16-25',
        'input_baseline': INPUT_DIR / 'uncertainty_scenarios' / 'scenario_002',
        'input_rail': INPUT_DIR / 'uncertainty_scenarios_rail' / 'scenario_002',
    },
    'Trinity': {
        'baseline_dir': RESULTS_DIR / 'uncertainty_scenarios_v2' / 'scenario_003',
        'baseline_prefix': 'scenario_003_cs_2026-02-15_00-33-53',
        'rail_dir': RESULTS_DIR / 'rail' / 'scenario_022',
        'rail_prefix': 'scenario_022_cs_2026-02-14_22-49-14',
        'input_baseline': INPUT_DIR / 'uncertainty_scenarios' / 'scenario_003',
        'input_rail': INPUT_DIR / 'uncertainty_scenarios_rail' / 'scenario_003',
    },
}

COUNTRY_LAT_CENTROIDS = {
    'IT': 43.0, 'AT': 47.5, 'DE': 50.5, 'DK': 55.5, 'SE': 59.5, 'NO': 62.0, 'FI': 64.5
}

MODEL_YEARS = list(range(2020, 2061, 4))
COMPARE_YEARS = [2032, 2040, 2048]

RAIL_COLORS = {
    'Go RES':         '#0072B2',
    'NECPEssentials': '#E69F00',
    'REPowerEU++':    '#009E73',
    'Trinity':        '#CC79A7',
}
RAIL_LINESTYLES = {
    'Go RES':         '-',
    'NECPEssentials': '--',
    'REPowerEU++':    '-.',
    'Trinity':        ':',
}
SCENARIO_COLORS = {
    'Go RES':         '#1f77b4',
    'NECPEssentials': '#ff7f0e',
    'REPowerEU++':    '#2ca02c',
    'Trinity':        '#d62728',
}


# ── Data loading functions ───────────────────────────────────────────
def load_yaml(fpath):
    with open(fpath, 'r') as f:
        return yaml.safe_load(f)


def load_f_dict(results_dir, prefix):
    fpath = results_dir / f'{prefix}_f_dict.yaml'
    raw = load_yaml(fpath)
    return {ast.literal_eval(k): v for k, v in raw.items()}


def load_input_data(input_dir):
    geo = load_yaml(input_dir / 'GeographicElement.yaml')
    paths = load_yaml(input_dir / 'Path.yaml')
    geo_by_id = {g['id']: g for g in geo}
    path_by_id = {p['id']: p for p in paths}
    return {'geo_by_id': geo_by_id, 'path_by_id': path_by_id}


# ── Figure 10 helper: rail tkm by node latitude ─────────────────────
def rail_tkm_by_node_latitude(f_dict, input_data, target_year):
    path_by_id = input_data['path_by_id']
    geo_by_id = input_data['geo_by_id']
    result = {}

    for key, tonnes in f_dict.items():
        year = key[0]
        if year != target_year:
            continue
        path_id = key[1][2]
        mode_id = key[2][0]
        if mode_id != 2:  # rail only
            continue
        if tonnes <= 0:
            continue

        path_info = path_by_id.get(path_id)
        if path_info is None:
            continue

        sequence = path_info['sequence']
        dist_from_prev = path_info['distance_from_previous']

        for i, node_id in enumerate(sequence):
            geo = geo_by_id.get(node_id)
            if geo is None:
                continue
            if geo.get('type', 'node') != 'node':
                continue

            segment_km = dist_from_prev[i]
            tkm = tonnes * segment_km

            if node_id not in result:
                result[node_id] = {
                    'rail_tkm': 0.0,
                    'lat': geo['coordinate_lat'],
                }
            result[node_id]['rail_tkm'] += tkm

    return result


# ── Figure 11 helper: energy by node ─────────────────────────────────
def energy_by_node(f_dict, input_data, target_year, spec_cons, w_payload, tv_filter=1):
    path_by_id = input_data['path_by_id']
    geo_by_id = input_data['geo_by_id']
    result = {}

    for key, tonnes_kt in f_dict.items():
        year = key[0]
        if year != target_year:
            continue
        path_id = key[1][2]
        mode_id = key[2][0]
        tv_id = key[2][1]
        gen = key[3]

        if mode_id != 1:
            continue
        if tv_id != tv_filter:
            continue
        if tonnes_kt <= 0:
            continue

        path_info = path_by_id.get(path_id)
        if path_info is None:
            continue

        gen_idx = min(max(gen - 2020, 0), len(spec_cons[tv_id]) - 1)
        sc = spec_cons[tv_id][gen_idx]
        w = w_payload[tv_id][gen_idx]

        sequence = path_info['sequence']
        dist_from_prev = path_info['distance_from_previous']

        for i, node_id in enumerate(sequence):
            geo = geo_by_id.get(node_id)
            if geo is None:
                continue
            segment_km = dist_from_prev[i]
            if segment_km <= 0:
                continue

            energy_kwh = (tonnes_kt * 1000 / w) * sc * segment_km
            energy_mwh = energy_kwh / 1e3

            if node_id not in result:
                result[node_id] = {
                    'energy_mwh': 0.0,
                    'lat': geo['coordinate_lat'],
                    'country': geo.get('country', '??'),
                }
            result[node_id]['energy_mwh'] += energy_mwh

    return result


# ── Load data ────────────────────────────────────────────────────────
print("Loading data...")
data = {}
for scen_name, cfg in SCENARIOS.items():
    print(f"  {scen_name}...")
    data[scen_name] = {}
    for run_type, dir_key, prefix_key, input_key in [
        ('baseline', 'baseline_dir', 'baseline_prefix', 'input_baseline'),
        ('rail', 'rail_dir', 'rail_prefix', 'input_rail'),
    ]:
        data[scen_name][run_type] = {
            'f': load_f_dict(cfg[dir_key], cfg[prefix_key]),
            'input': load_input_data(cfg[input_key]),
        }

# Load TechVehicle parameters
tv_yaml = load_yaml(INPUT_DIR / 'uncertainty_scenarios' / 'scenario_000' / 'TechVehicle.yaml')
SPEC_CONS = {}
W_PAYLOAD = {}
for tv in tv_yaml:
    SPEC_CONS[tv['id']] = tv['spec_cons']
    W_PAYLOAD[tv['id']] = tv['W']
print(f"  BEV spec_cons: {SPEC_CONS[1][0]:.2f} -> {SPEC_CONS[1][-1]:.2f} kWh/km")
print("Data loaded.\n")


# =====================================================================
# Figure 10: rail_tkm_by_latitude_scenarios_overlap
# =====================================================================
print("Generating Figure 10: rail_tkm_by_latitude_scenarios_overlap...")
PLOT_YEARS = [2028, 2032, 2040, 2048]
rail_by_node = {}
for scen_name in SCENARIOS:
    rail_by_node[scen_name] = {}
    for year in PLOT_YEARS:
        rail_by_node[scen_name][year] = rail_tkm_by_node_latitude(
            data[scen_name]['rail']['f'],
            data[scen_name]['rail']['input'],
            year
        )

fig, axes = plt.subplots(1, 4, figsize=(12, 5), sharey=True)

for yi, year in enumerate(PLOT_YEARS):
    ax = axes[yi]

    scenario_curves = {}
    for scen_name in SCENARIOS:
        node_data = rail_by_node[scen_name][year]
        if not node_data:
            continue
        sorted_nodes = sorted(node_data.values(), key=lambda x: x['lat'])
        lats = np.array([n['lat'] for n in sorted_nodes])
        tkm_vals = np.array([n['rail_tkm'] for n in sorted_nodes])
        if len(lats) > 3:
            tkm_smooth = gaussian_filter1d(tkm_vals / 1e3, sigma=1.5)
        else:
            tkm_smooth = tkm_vals / 1e3
        scenario_curves[scen_name] = (lats, tkm_smooth)

    # Envelope
    if scenario_curves:
        all_lat_vals = np.concatenate([c[0] for c in scenario_curves.values()])
        common_lats = np.linspace(all_lat_vals.min(), all_lat_vals.max(), 300)
        interp_smooth = []
        for scen_name, (lats, smooth) in scenario_curves.items():
            interp_vals = np.interp(common_lats, lats, smooth)
            interp_smooth.append(interp_vals)
        smooth_stack = np.array(interp_smooth)
        ax.fill_betweenx(common_lats, smooth_stack.min(axis=0), smooth_stack.max(axis=0),
                         alpha=0.18, color='#888888', label='Scenario range')

    for scen_name in SCENARIOS:
        if scen_name not in scenario_curves:
            continue
        lats, tkm_smooth = scenario_curves[scen_name]
        ax.plot(tkm_smooth, lats,
                color=RAIL_COLORS[scen_name],
                linestyle=RAIL_LINESTYLES[scen_name],
                linewidth=2.5,
                label=scen_name.replace('++', '{++}'),
                alpha=0.95)

    # Country labels — only on rightmost panel
    for country, clat in COUNTRY_LAT_CENTROIDS.items():
        ax.axhline(clat, color='gray', linestyle=':', alpha=0.3, linewidth=0.8)
        if yi == len(PLOT_YEARS) - 1:
            ax.text(1.03, clat, country, transform=ax.get_yaxis_transform(),
                    va='center', fontsize=9, color='gray',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                              edgecolor='#ccc', alpha=0.8))

    ax.set_title(f'{year}', fontsize=14)
    ax.set_xlabel('Rail transport work\n(thousand tkm)', fontsize=11)
    if yi == 0:
        ax.set_ylabel(r'Latitude ($^\circ$N)', fontsize=12)
    ax.grid(True, alpha=0.2, linestyle='--')
    ax.set_xlim(left=0)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=3))
    ax.tick_params(axis='x', labelsize=11)

# Legend
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.02),
           ncol=5, fontsize=13, frameon=True, edgecolor='#ccc')

fig.suptitle('Rail-shifted transport work by latitude', fontsize=14, y=1.01)
plt.tight_layout(rect=[0, 0.06, 1, 1])
for dst in [FIG_DIR, MANUSCRIPT_IMG]:
    fig.savefig(dst / 'rail_tkm_by_latitude_scenarios_overlap.pdf', bbox_inches='tight')
fig.savefig(FIG_DIR / 'rail_tkm_by_latitude_scenarios_overlap.png', bbox_inches='tight', dpi=150)
plt.close(fig)
print("  Saved.\n")


# =====================================================================
# Figure 11: bev_energy_by_latitude_GoRES_only
# =====================================================================
print("Generating Figure 11: bev_energy_by_latitude_GoRES_only...")

# Compute energy data for Go RES only
GORES = 'Go RES'
energy_data = {}
for run_type in ['baseline', 'rail']:
    energy_data[run_type] = {}
    for year in COMPARE_YEARS:
        energy_data[run_type][year] = energy_by_node(
            data[GORES][run_type]['f'],
            data[GORES][run_type]['input'],
            year, SPEC_CONS, W_PAYLOAD
        )
        total = sum(v['energy_mwh'] for v in energy_data[run_type][year].values())
        print(f"  {run_type} {year}: {len(energy_data[run_type][year])} nodes, {total:.0f} MWh")

GORES_COLOR = SCENARIO_COLORS[GORES]

fig, axes = plt.subplots(1, len(COMPARE_YEARS), figsize=(13, 5), sharey=True)

for yi, year in enumerate(COMPARE_YEARS):
    ax = axes[yi]

    # Compute smoothed curves for both run types so we can reuse them for fill
    smooth_curves = {}
    for run_type, ls, lw, alpha, label in [
        ('baseline', '-',  1, 0.9, 'Baseline (road-only)'),
        ('rail',     '--', 1, 0.9, 'With modal shift to rail'),
    ]:
        nd = energy_data[run_type][year]
        if not nd:
            continue
        sorted_nodes = sorted(nd.values(), key=lambda x: x['lat'])
        lats = np.array([n['lat'] for n in sorted_nodes])
        energy_vals = np.array([n['energy_mwh'] for n in sorted_nodes])

        if len(lats) > 3:
            smooth = gaussian_filter1d(energy_vals / 1e3, sigma=1.5)  # GWh
        else:
            smooth = energy_vals / 1e3

        smooth_curves[run_type] = (lats, smooth)
        ax.plot(smooth, lats, color=GORES_COLOR, linewidth=lw, linestyle=ls,
                label=label if yi == 0 else None, alpha=alpha)

    # Fill between baseline and rail using the exact same smoothed data as the lines
    if 'baseline' in smooth_curves and 'rail' in smooth_curves:
        base_lats, base_smooth = smooth_curves['baseline']
        rail_lats, rail_smooth = smooth_curves['rail']
        # Interpolate both onto a common fine latitude grid
        all_lats = np.concatenate([base_lats, rail_lats])
        common_fine = np.linspace(all_lats.min(), all_lats.max(), 500)
        base_interp = np.interp(common_fine, base_lats, base_smooth)
        rail_interp = np.interp(common_fine, rail_lats, rail_smooth)
        ax.fill_betweenx(common_fine, rail_interp, base_interp,
                         where=base_interp >= rail_interp,
                         alpha=0.15, color=GORES_COLOR,
                         label='Reduction from rail' if yi == 0 else None)

    # Country labels — only on rightmost panel
    for country, clat in COUNTRY_LAT_CENTROIDS.items():
        ax.axhline(clat, color='gray', linestyle=':', alpha=0.3, linewidth=0.8)
        if yi == len(COMPARE_YEARS) - 1:
            ax.text(1.03, clat, country, transform=ax.get_yaxis_transform(),
                    va='center', fontsize=10, color='gray',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                              edgecolor='#ccc', alpha=0.8))

    ax.set_title(f'{year}', fontsize=14)
    ax.set_xlabel('Energy charged (GWh)', fontsize=11)
    if yi == 0:
        ax.set_ylabel(r'Latitude ($^\circ$N)', fontsize=12)
    ax.grid(True, alpha=0.2, linestyle='--')
    ax.set_xlim(left=0)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=3))
    ax.tick_params(axis='x', labelsize=11)

# Legend below
fig.legend(loc='lower center', bbox_to_anchor=(0.5, -0.06), ncol=3,
           fontsize=13, frameon=True, edgecolor='#ccc')
plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.subplots_adjust(wspace=0.15)
for dst in [FIG_DIR, MANUSCRIPT_IMG]:
    fig.savefig(dst / 'bev_energy_by_latitude_GoRES_only.pdf', bbox_inches='tight')
fig.savefig(FIG_DIR / 'bev_energy_by_latitude_GoRES_only.png', bbox_inches='tight', dpi=150)
plt.close(fig)
print("  Saved.\n")

print("Done.")
