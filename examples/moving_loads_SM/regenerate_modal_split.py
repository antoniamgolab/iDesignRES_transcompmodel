"""
Regenerate modal_split_GoRES_tkm.pdf and modal_split_4scenarios_tkm.pdf
with consistent font settings matching analytical_even_charging.py.
"""

import yaml
import matplotlib.pyplot as plt
from pathlib import Path

# ── Font settings (matching visualize_4_scenarios.ipynb) ─────────────
plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    'font.serif': 'mathpazo',
    'font.size': 20,
})

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / 'results'
INPUT_DIR = BASE_DIR / 'input_data'
FIG_DIR = BASE_DIR / 'figures'
MANUSCRIPT_IMG = BASE_DIR.parent.parent / 'manuscript' / 'images'

SCENARIOS = {
    'Go RES': {
        'rail_dir': RESULTS_DIR / 'rail' / 'scenario_004',
        'rail_prefix': 'scenario_004_cs_2026-02-14_20-52-20',
        'input_rail': INPUT_DIR / 'uncertainty_scenarios_rail' / 'scenario_000',
    },
    'NECPEssentials': {
        'rail_dir': RESULTS_DIR / 'rail' / 'scenario_010',
        'rail_prefix': 'scenario_010_cs_2026-02-14_21-34-41',
        'input_rail': INPUT_DIR / 'uncertainty_scenarios_rail' / 'scenario_001',
    },
    'REPowerEU++': {
        'rail_dir': RESULTS_DIR / 'rail' / 'scenario_016',
        'rail_prefix': 'scenario_016_cs_2026-02-14_22-16-25',
        'input_rail': INPUT_DIR / 'uncertainty_scenarios_rail' / 'scenario_002',
    },
    'Trinity': {
        'rail_dir': RESULTS_DIR / 'rail' / 'scenario_022',
        'rail_prefix': 'scenario_022_cs_2026-02-14_22-49-14',
        'input_rail': INPUT_DIR / 'uncertainty_scenarios_rail' / 'scenario_003',
    },
}

COLOR_RAIL = '#3498DB'
COLOR_ICEV = '#E74C3C'
COLOR_BEV  = '#2ECC71'
MODEL_YEARS = list(range(2020, 2061, 4))


# ── Data loading ─────────────────────────────────────────────────────
def load_yaml(fpath):
    with open(fpath, 'r') as f:
        return yaml.safe_load(f)


def parse_f_dict_key(key_str):
    """Parse f_dict key string -> tuple."""
    import ast
    return ast.literal_eval(key_str)


def load_f_dict(results_dir, prefix):
    fpath = results_dir / f'{prefix}_f_dict.yaml'
    raw = load_yaml(fpath)
    return {parse_f_dict_key(k): v for k, v in raw.items()}


def load_input_data(input_dir):
    path_yaml = load_yaml(input_dir / 'Path.yaml')
    path_by_id = {}
    for p in path_yaml:
        pid = p['id']
        length = p.get('length', 0)
        path_by_id[pid] = {'length': length, 'sequence': p.get('sequence', [])}
    return {'path_by_id': path_by_id}


def calculate_tkm_by_mode_tech(f_dict, input_data):
    path_by_id = input_data['path_by_id']
    result = {}
    for key, tonnes in f_dict.items():
        year = key[0]
        path_id = key[1][2]
        mode_id = key[2][0]
        tv_id = key[2][1]

        if year not in result:
            result[year] = {'road_icev': 0.0, 'road_bev': 0.0, 'rail': 0.0}

        path_info = path_by_id.get(path_id)
        if path_info is None:
            continue
        length_km = path_info['length']
        tkm = tonnes * length_km

        if mode_id == 2:
            result[year]['rail'] += tkm
        elif mode_id == 1:
            if tv_id == 1:
                result[year]['road_bev'] += tkm
            else:
                result[year]['road_icev'] += tkm
    return result


# ── Load data ────────────────────────────────────────────────────────
print("Loading data...")
tkm_data = {}
for scen_name, cfg in SCENARIOS.items():
    print(f"  {scen_name}...")
    f_dict = load_f_dict(cfg['rail_dir'], cfg['rail_prefix'])
    inp = load_input_data(cfg['input_rail'])
    tkm_data[scen_name] = calculate_tkm_by_mode_tech(f_dict, inp)

print("Data loaded.\n")


# ── Figure 1: modal_split_GoRES_tkm ─────────────────────────────────
print("Generating modal_split_GoRES_tkm...")
scen_name = 'Go RES'
vol = tkm_data[scen_name]
years = sorted([y for y in vol.keys() if y in MODEL_YEARS and y <= 2048])

rail_vals = [vol[y]['rail'] / 1e9 for y in years]
icev_vals = [vol[y]['road_icev'] / 1e9 for y in years]
bev_vals  = [vol[y]['road_bev'] / 1e9 for y in years]

fig, ax = plt.subplots(figsize=(10, 6))
bar_width = 2.8

ax.bar(years, icev_vals, width=bar_width, color=COLOR_ICEV, alpha=0.85,
       label='Road ICEV', edgecolor='white', linewidth=0.5)
ax.bar(years, bev_vals, width=bar_width, bottom=icev_vals, color=COLOR_BEV, alpha=0.85,
       label='Road BEV', edgecolor='white', linewidth=0.5)
bottom_rail = [i + b for i, b in zip(icev_vals, bev_vals)]
ax.bar(years, rail_vals, width=bar_width, bottom=bottom_rail, color=COLOR_RAIL, alpha=0.85,
       label='Rail', edgecolor='white', linewidth=0.5)

# Rail percentage labels
for yi, y in enumerate(years):
    total = icev_vals[yi] + bev_vals[yi] + rail_vals[yi]
    if total > 0 and rail_vals[yi] / total > 0.02:
        rail_pct = rail_vals[yi] / total * 100
        ax.text(y, bottom_rail[yi] + rail_vals[yi] / 2, f'{rail_pct:.0f}\\%',
                ha='center', va='center', fontsize=14, fontweight='bold', color='white')

ax.set_xlabel('Year')
ax.set_ylabel('Transport volume (billion tkm)')
ax.set_title(f'Modal split: {scen_name} scenario', fontweight='bold')
ax.set_xticks(years)
ax.tick_params(axis='x', rotation=45)
ax.grid(True, alpha=0.3, linestyle='--', axis='y')
ax.legend(fontsize=16, loc='upper left')

plt.tight_layout()
for dst in [FIG_DIR, MANUSCRIPT_IMG]:
    fig.savefig(dst / 'modal_split_GoRES_tkm.pdf', bbox_inches='tight')
fig.savefig(FIG_DIR / 'modal_split_GoRES_tkm.png', bbox_inches='tight', dpi=150)
plt.close(fig)
print("  Saved: modal_split_GoRES_tkm.pdf\n")


# ── Figure 2: modal_split_4scenarios_tkm ─────────────────────────────
print("Generating modal_split_4scenarios_tkm...")
fig, axes = plt.subplots(2, 2, figsize=(16, 12), sharey=True)
axes_flat = axes.flatten()

for idx, (scen_name, ax) in enumerate(zip(SCENARIOS.keys(), axes_flat)):
    vol = tkm_data[scen_name]
    years = sorted([y for y in vol.keys() if y in MODEL_YEARS and y <= 2048])

    rail_vals = [vol[y]['rail'] / 1e9 for y in years]
    icev_vals = [vol[y]['road_icev'] / 1e9 for y in years]
    bev_vals  = [vol[y]['road_bev'] / 1e9 for y in years]

    bar_width = 2.5

    ax.bar(years, icev_vals, width=bar_width, color=COLOR_ICEV, alpha=0.8,
           label='Road ICEV', edgecolor='white', linewidth=0.5)
    ax.bar(years, bev_vals, width=bar_width, bottom=icev_vals, color=COLOR_BEV, alpha=0.8,
           label='Road BEV', edgecolor='white', linewidth=0.5)
    bottom_rail = [i + b for i, b in zip(icev_vals, bev_vals)]
    ax.bar(years, rail_vals, width=bar_width, bottom=bottom_rail, color=COLOR_RAIL, alpha=0.8,
           label='Rail', edgecolor='white', linewidth=0.5)

    for yi, y in enumerate(years):
        total = icev_vals[yi] + bev_vals[yi] + rail_vals[yi]
        if total > 0 and rail_vals[yi] / total > 0.02:
            rail_pct = rail_vals[yi] / total * 100
            ax.text(y, bottom_rail[yi] + rail_vals[yi] / 2, f'{rail_pct:.0f}\\%',
                    ha='center', va='center', fontsize=12, fontweight='bold', color='white')

    ax.set_title(scen_name.replace('++', '{++}'), fontweight='bold')
    ax.set_xlabel('Year')
    if idx % 2 == 0:
        ax.set_ylabel('Transport volume (billion tkm)')
    ax.set_xticks(years[::2])
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    if idx == 0:
        ax.legend(loc='upper left', fontsize=14)

fig.suptitle('Modal split: road (ICEV + BEV) vs rail --- 4 GENeSYS-MOD scenarios',
             fontweight='bold', y=1.01)
plt.tight_layout()
for dst in [FIG_DIR, MANUSCRIPT_IMG]:
    fig.savefig(dst / 'modal_split_4scenarios_tkm.pdf', bbox_inches='tight')
fig.savefig(FIG_DIR / 'modal_split_4scenarios_tkm.png', bbox_inches='tight', dpi=150)
plt.close(fig)
print("  Saved: modal_split_4scenarios_tkm.pdf\n")

print("Done.")
