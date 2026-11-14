"""
AT surcharge sensitivity: BET charging reallocation in DE-AT-IT border regions.
Stacked bars showing charged energy (GWh) by country for baseline + 7 surcharge scenarios.
Based on Go RES (scenario_000) baseline with corrected constraints (Apr 2026 runs).
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import yaml
import re
import glob
from collections import defaultdict
from pathlib import Path

plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "sans-serif"],
    "font.size": 16,
})

BASE = Path(__file__).resolve().parent
INPUT = BASE / 'input_data' / 'fixed_nuts_2'
FIG_DIR = BASE / 'figures'
MANUSCRIPT_IMG = BASE.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'

# Load geo mapping
with open(INPUT / 'GeographicElement.yaml') as f:
    geo = yaml.safe_load(f)
geoid_to_nuts2 = {}
for g in geo:
    if g.get('type') == 'node':
        n2 = g.get('nuts2_region', '')
        if n2:
            geoid_to_nuts2[int(g['id'])] = n2

BORDER = {'AT33', 'AT34', 'ITC4', 'ITH1', 'ITH2', 'ITH3', 'DE14', 'DE21', 'DE27'}
node_to_border = {nid: n2 for nid, n2 in geoid_to_nuts2.items() if n2 in BORDER}

# Tuple regex (handles quoted values from new runs)
TUPLE_PAT = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*"?([\d.eE+-]+)"?')

def load_border_energy(s_file, year):
    by_country = defaultdict(float)
    with open(s_file) as f:
        for line in f:
            m = TUPLE_PAT.match(line.strip())
            if not m:
                continue
            yr = int(m.group(1))
            if yr != year:
                continue
            geo_id = int(m.group(5))
            tv_id = int(m.group(6))
            fuel_id = int(m.group(7))
            val = float(m.group(10))
            if tv_id != 1 or fuel_id != 0 or val <= 0:
                continue
            n2 = node_to_border.get(geo_id)
            if n2:
                by_country[n2[:2]] += val / 1000  # MWh -> GWh
    return dict(by_country)

# Load baseline (Go RES scenario_000)
baseline_files = sorted(glob.glob(str(BASE / 'results' / 'uncertainty_scenarios_v2' / 'scenario_000' / '*_s_dict.yaml')))
baseline_s = baseline_files[-1]
print(f'Baseline: {Path(baseline_s).name}')

# Load surcharge scenarios
surcharge_dir = BASE / 'results' / 'at_surcharge'
surcharge_files = {}
for folder in sorted(surcharge_dir.iterdir()):
    if folder.is_dir():
        s_files = sorted(folder.glob('*_s_dict.yaml'))
        if s_files:
            surcharge_files[folder.name] = str(s_files[-1])

# Scenario order and labels
SCENARIOS = [
    ('baseline', baseline_s, 'Reference'),
    ('at_elec_low', surcharge_files.get('at_elec_low'), '+1 ct/kWh'),
    ('at_elec_med', surcharge_files.get('at_elec_med'), '+2 ct/kWh'),
    ('at_elec_high', surcharge_files.get('at_elec_high'), '+4 ct/kWh'),
    ('at_elec_extreme', surcharge_files.get('at_elec_extreme'), '+6 ct/kWh'),
    ('at_network_low', surcharge_files.get('at_network_low'), '+2 EUR/kW/yr'),
    ('at_network_med', surcharge_files.get('at_network_med'), '+5 EUR/kW/yr'),
    ('at_network_high', surcharge_files.get('at_network_high'), '+10 EUR/kW/yr'),
]

COUNTRY_COLORS = {'AT': '#c9a96e', 'DE': '#8a84b8', 'IT': '#d9908a'}
COUNTRY_LABELS = {'AT': 'Austria', 'DE': 'Germany', 'IT': 'Italy'}
country_order = ['AT', 'DE', 'IT']

# === Generate figure for 2040 ===
YEAR = 2040
print(f'\nLoading data for {YEAR}...')

data = {}
for sid, path, label in SCENARIOS:
    if path is None:
        continue
    d = load_border_energy(path, YEAR)
    data[sid] = d
    total = sum(d.values())
    print(f'  {label:>15s}: AT={d.get("AT",0):>7.1f}  DE={d.get("DE",0):>7.1f}  IT={d.get("IT",0):>7.1f}  Total={total:>7.1f}')

available = [(sid, label) for sid, path, label in SCENARIOS if sid in data]

fig, ax = plt.subplots(figsize=(14, 5))

x = np.arange(len(available))
width = 0.6
bottom = np.zeros(len(available))

for c in country_order:
    vals = np.array([data[sid].get(c, 0) for sid, _ in available])
    bars = ax.bar(x, vals, width, bottom=bottom, label=COUNTRY_LABELS[c],
                  color=COUNTRY_COLORS[c], edgecolor='black', linewidth=0.5)
    # Annotate values inside bars
    for i, (v, b) in enumerate(zip(vals, bottom)):
        if v > 5:
            ax.text(x[i], b + v / 2, f'{v:.0f}', ha='center', va='center',
                    fontsize=12, fontweight='bold', color='white')
    bottom += vals

# Annotate totals on top
for i, (sid, label) in enumerate(available):
    total = sum(data[sid].values())
    ax.text(x[i], bottom[i] + 5, f'{total:.0f}', ha='center', va='bottom',
            fontsize=13, fontweight='bold', color='#333')

# Separators
# After Reference (index 0), before network surcharges
ax.axvline(x=0.5, color='gray', ls='--', alpha=0.5, lw=1)
n_elec = sum(1 for sid, _ in available if 'elec' in sid)
ax.axvline(x=0.5 + n_elec, color='gray', ls=':', alpha=0.4, lw=1)

# Group labels above the bars
ylim_top = max(bottom) * 1.12
elec_center = 0.5 + n_elec / 2
ax.text(elec_center, ylim_top * 0.97, 'Electricity surcharges', ha='center', fontsize=14,
        color='#666', fontstyle='italic')
net_start = 1 + n_elec
n_net = sum(1 for sid, _ in available if 'network' in sid)
net_center = net_start + n_net / 2 - 0.5
ax.text(net_center, ylim_top * 0.97, 'Network fee surcharges', ha='center', fontsize=14,
        color='#666', fontstyle='italic')

ax.set_xticks(x)
ax.set_xticklabels([label for _, label in available], fontsize=14, rotation=30, ha='right')
ax.set_ylabel('BET charging in\nborder regions (GWh)', fontsize=16)
ax.set_title(f'BET charging reallocation in DE-AT-IT border regions -- {YEAR}\n(Go RES scenario, road-only)',
             fontsize=18)
ax.grid(axis='y', alpha=0.3)
ax.set_ylim(0, max(bottom) * 1.12)

ax.legend(fontsize=14, loc='upper right', framealpha=0.9)

plt.tight_layout()
plt.savefig(str(FIG_DIR / 'at_surcharge_border_charging_reallocation.pdf'), bbox_inches='tight', dpi=300)
plt.savefig(str(FIG_DIR / 'at_surcharge_border_charging_reallocation.png'), bbox_inches='tight', dpi=300)
if MANUSCRIPT_IMG.exists():
    plt.savefig(str(MANUSCRIPT_IMG / 'at_surcharge_border_charging_reallocation.pdf'), bbox_inches='tight', dpi=300)
print(f'\nSaved: at_surcharge_border_charging_reallocation.pdf/.png')
plt.close()
