"""
Surcharge sensitivity: AT33 (Tirol) and ITH1 (Veneto) targeted locational cost premiums.
Row 1: Charging energy reallocation (GWh) with target node highlighted
Row 2: MCS + CCS infrastructure (MW) at target node
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import yaml, re, glob
from collections import defaultdict
from pathlib import Path

plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "sans-serif"],
    "font.size": 15,
})

BASE = Path(__file__).resolve().parent
FIG_DIR = BASE / 'figures'
MANUSCRIPT_IMG = BASE.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'

# Load geo mapping
with open(BASE / 'input_data' / 'fixed_nuts_2' / 'GeographicElement.yaml') as f:
    geo = yaml.safe_load(f)
geoid_to_nuts2 = {int(g['id']): g.get('nuts2_region', '')
                  for g in geo if g.get('type') == 'node' and g.get('nuts2_region')}

BORDER = {'AT33', 'AT34', 'ITC4', 'ITH1', 'ITH2', 'ITH3', 'DE14', 'DE21', 'DE27'}
MODELED_YEARS = list(range(2020, 2064, 4))
year_idx = {i + 1: y for i, y in enumerate(MODELED_YEARS)}

# Regex patterns
S_PAT = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*"?([\d.eE+-]+)"?')
CI_PAT = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*"?([\d.eE+-]+)"?')
TUPLE_Q_PAT = re.compile(r'\((\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*"?([\d.eE+-]+)"?')

YEAR = 2040

def load_border_data(s_file, year):
    by_n2 = defaultdict(float)
    with open(s_file) as f:
        for line in f:
            m = S_PAT.match(line.strip())
            if not m: continue
            if int(m.group(1)) != year: continue
            geo_id = int(m.group(5))
            if int(m.group(6)) != 1 or int(m.group(7)) != 0: continue
            val = float(m.group(10))
            if val <= 0: continue
            n2 = geoid_to_nuts2.get(geo_id, '')
            if n2 in BORDER:
                by_n2[n2] += val / 1000
    by_c = defaultdict(float)
    for n2, v in by_n2.items():
        by_c[n2[:2]] += v
    return dict(by_n2), dict(by_c)

def load_infra(q_file, max_year=2040):
    mcs_by_n2 = defaultdict(float)
    ccs_by_n2 = defaultdict(float)
    with open(q_file) as f:
        for line in f:
            line = line.strip()
            m = CI_PAT.match(line)
            if m:
                yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
                val = float(m.group(4))
                yr = year_idx.get(yi)
                geo_id = pos - 1
            else:
                m = TUPLE_Q_PAT.match(line)
                if not m: continue
                yr = int(m.group(1))
                fuel_id, fi = int(m.group(2)), int(m.group(3))
                geo_id = int(m.group(4))
                val = float(m.group(5))
                if fuel_id != 0: continue
            if val < 1e-3 or yr is None or yr > max_year: continue
            n2 = geoid_to_nuts2.get(geo_id, '')
            if n2 in BORDER:
                if fi == 1: mcs_by_n2[n2] += val / 1000
                elif fi == 2: ccs_by_n2[n2] += val / 1000
    return dict(mcs_by_n2), dict(ccs_by_n2)

# Load baseline
bl_s = sorted(glob.glob(str(BASE / 'results' / 'uncertainty_scenarios_v2' / 'scenario_000' / '*_s_dict.yaml')))[-1]
bl_q = sorted(glob.glob(str(BASE / 'results' / 'uncertainty_scenarios_v2' / 'scenario_000' / '*_q_fuel_infr_plus_dict.yaml')))[-1]
bl_n2, bl_c = load_border_data(bl_s, YEAR)
bl_mcs, bl_ccs = load_infra(bl_q)

# Scenario definitions
ELEC_SCENARIOS = [
    ('elec_low', '+1 ct/kWh'),
    ('elec_med', '+2 ct/kWh'),
    ('elec_high', '+4 ct/kWh'),
    ('elec_extreme', '+6 ct/kWh'),
    ('elec_8ct', '+8 ct/kWh'),
    ('elec_10ct', '+10 ct/kWh'),
    ('elec_15ct', '+15 ct/kWh'),
]
NET_SCENARIOS = [
    ('network_low', '+2 EUR/kW/yr'),
    ('network_med', '+5 EUR/kW/yr'),
    ('network_high', '+10 EUR/kW/yr'),
    ('network_20', '+20 EUR/kW/yr'),
    ('network_50', '+50 EUR/kW/yr'),
]

# Colors
MCS_COL = '#5b7fb8'   # steel blue
CCS_COL = '#c47a3e'   # warm amber
TARGET_COL = {
    'AT33': '#8B6914',  # dark gold
    'ITH1': '#a0282a',  # dark red
}
OTHER_COUNTRY_COL = {
    'AT33': '#c9a96e',  # light gold
    'ITH1': '#d9908a',  # light red
}

def load_all_scenarios(results_dir, prefix):
    s_data = {}
    q_data = {}
    for folder in sorted(Path(results_dir).iterdir()):
        if not folder.is_dir(): continue
        s_files = sorted(folder.glob('*_s_dict.yaml'))
        q_files = sorted(folder.glob('*_q_fuel_infr_plus_dict.yaml'))
        if s_files:
            s_data[folder.name] = load_border_data(str(s_files[-1]), YEAR)
        if q_files:
            q_data[folder.name] = load_infra(q_files[-1])
    return s_data, q_data

at33_s, at33_q = load_all_scenarios(BASE / 'results' / 'at33_surcharge', 'at33')
ith1_s, ith1_q = load_all_scenarios(BASE / 'results' / 'ith1_surcharge', 'ith1')

# === Figure: 2x2 grid ===
fig, axes = plt.subplots(2, 2, figsize=(18, 11))

def build_scenario_list(prefix, sc_data):
    scenarios = [('Reference', None)]
    for suffix, label in ELEC_SCENARIOS:
        key = f'{prefix}_{suffix}'
        if key in sc_data:
            scenarios.append((label, key))
    for suffix, label in NET_SCENARIOS:
        key = f'{prefix}_{suffix}'
        if key in sc_data:
            scenarios.append((label, key))
    return scenarios

def plot_energy_panel(ax, target_nuts2, target_country, prefix, sc_s_data, title):
    scenarios = build_scenario_list(prefix, sc_s_data)
    if target_country == 'AT':
        other_countries = ['DE', 'IT']
    else:
        other_countries = ['AT', 'DE']

    other_colors = {'AT': '#c9a96e', 'DE': '#8a84b8', 'IT': '#d9908a'}
    other_labels = {'AT': 'Austria', 'DE': 'Germany', 'IT': 'Italy'}

    x = np.arange(len(scenarios))
    width = 0.6
    bottom = np.zeros(len(scenarios))

    # Target node
    target_vals = []
    for label, key in scenarios:
        if key is None:
            target_vals.append(bl_n2.get(target_nuts2, 0))
        else:
            target_vals.append(sc_s_data[key][0].get(target_nuts2, 0))
    target_vals = np.array(target_vals)

    ax.bar(x, target_vals, width, bottom=bottom, color=TARGET_COL[target_nuts2],
           edgecolor='black', linewidth=0.5, label=target_nuts2)
    for i, v in enumerate(target_vals):
        if v > 5:
            ax.text(x[i], bottom[i] + v / 2, f'{v:.0f}', ha='center', va='center',
                    fontsize=9, fontweight='bold', color='white')
    bottom += target_vals

    # Rest of target country
    rest_vals = []
    for label, key in scenarios:
        if key is None:
            rest_vals.append(bl_c.get(target_country, 0) - bl_n2.get(target_nuts2, 0))
        else:
            rest_vals.append(sc_s_data[key][1].get(target_country, 0) - sc_s_data[key][0].get(target_nuts2, 0))
    rest_vals = np.maximum(rest_vals, 0)

    ax.bar(x, rest_vals, width, bottom=bottom, color=OTHER_COUNTRY_COL[target_nuts2],
           edgecolor='black', linewidth=0.5, label=f'{target_country} (other)')
    for i, v in enumerate(rest_vals):
        if v > 5:
            ax.text(x[i], bottom[i] + v / 2, f'{v:.0f}', ha='center', va='center',
                    fontsize=9, fontweight='bold', color='white')
    bottom += rest_vals

    # Other countries
    for oc in other_countries:
        vals = []
        for label, key in scenarios:
            if key is None:
                vals.append(bl_c.get(oc, 0))
            else:
                vals.append(sc_s_data[key][1].get(oc, 0))
        vals = np.array(vals)
        ax.bar(x, vals, width, bottom=bottom, color=other_colors[oc],
               edgecolor='black', linewidth=0.5, label=other_labels[oc])
        for i, v in enumerate(vals):
            if v > 8:
                ax.text(x[i], bottom[i] + v / 2, f'{v:.0f}', ha='center', va='center',
                        fontsize=9, fontweight='bold', color='white')
        bottom += vals

    # Separators
    ax.axvline(x=0.5, color='gray', ls='--', alpha=0.5, lw=1)
    n_elec = sum(1 for s, _ in ELEC_SCENARIOS if f'{prefix}_{s}' in sc_s_data)
    if n_elec > 0:
        ax.axvline(x=0.5 + n_elec, color='gray', ls=':', alpha=0.4, lw=1)

    ylim_top = max(bottom) * 1.15
    if n_elec > 0:
        ax.text(0.5 + n_elec / 2, ylim_top * 0.97, 'Electricity', ha='center', fontsize=10,
                color='#666', fontstyle='italic')
    n_net = sum(1 for s, _ in NET_SCENARIOS if f'{prefix}_{s}' in sc_s_data)
    if n_net > 0:
        ax.text(1 + n_elec + n_net / 2 - 0.5, ylim_top * 0.97, 'Network fee', ha='center', fontsize=10,
                color='#666', fontstyle='italic')

    ax.set_xticks(x)
    ax.set_xticklabels([s[0] for s in scenarios], fontsize=10, rotation=40, ha='right')
    ax.set_title(title, fontsize=15)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, ylim_top)


def plot_infra_panel(ax, target_nuts2, prefix, sc_q_data, title):
    scenarios = build_scenario_list(prefix, sc_q_data)
    n_sc = len(scenarios)
    x = np.arange(n_sc)
    bar_w = 0.35  # width per sub-bar

    # Collect target node and neighbor data
    t_mcs, t_ccs, n_mcs, n_ccs = [], [], [], []
    for label, key in scenarios:
        if key is None:
            t_mcs.append(bl_mcs.get(target_nuts2, 0))
            t_ccs.append(bl_ccs.get(target_nuts2, 0))
            n_mcs.append(sum(v for k, v in bl_mcs.items() if k != target_nuts2))
            n_ccs.append(sum(v for k, v in bl_ccs.items() if k != target_nuts2))
        else:
            mcs_d, ccs_d = sc_q_data[key]
            t_mcs.append(mcs_d.get(target_nuts2, 0))
            t_ccs.append(ccs_d.get(target_nuts2, 0))
            n_mcs.append(sum(v for k, v in mcs_d.items() if k != target_nuts2))
            n_ccs.append(sum(v for k, v in ccs_d.items() if k != target_nuts2))

    t_mcs, t_ccs = np.array(t_mcs), np.array(t_ccs)
    n_mcs, n_ccs = np.array(n_mcs), np.array(n_ccs)

    # Left sub-bar: target node
    ax.bar(x - bar_w / 2, t_mcs, bar_w, color=MCS_COL, edgecolor='black', linewidth=0.5, label=f'{target_nuts2} MCS')
    ax.bar(x - bar_w / 2, t_ccs, bar_w, bottom=t_mcs, color=CCS_COL, edgecolor='black', linewidth=0.5, label=f'{target_nuts2} CCS')

    # Right sub-bar: neighbors (lighter)
    ax.bar(x + bar_w / 2, n_mcs, bar_w, color=MCS_COL, edgecolor='black', linewidth=0.5, alpha=0.4, label='Neighbors MCS')
    ax.bar(x + bar_w / 2, n_ccs, bar_w, bottom=n_mcs, color=CCS_COL, edgecolor='black', linewidth=0.5, alpha=0.4, label='Neighbors CCS')

    # Annotate target node totals
    for i in range(n_sc):
        t_tot = t_mcs[i] + t_ccs[i]
        if t_tot > 0.3:
            ax.text(x[i] - bar_w / 2, t_tot + 0.5, f'{t_tot:.0f}', ha='center', va='bottom',
                    fontsize=8, fontweight='bold', color=TARGET_COL[target_nuts2])
        n_tot = n_mcs[i] + n_ccs[i]
        if n_tot > 0.3:
            ax.text(x[i] + bar_w / 2, n_tot + 0.5, f'{n_tot:.0f}', ha='center', va='bottom',
                    fontsize=8, color='#555')

    # Separators
    ax.axvline(x=0.5, color='gray', ls='--', alpha=0.5, lw=1)
    n_elec = sum(1 for s, _ in ELEC_SCENARIOS if f'{prefix}_{s}' in sc_q_data)
    if n_elec > 0:
        ax.axvline(x=0.5 + n_elec, color='gray', ls=':', alpha=0.4, lw=1)

    all_tops = np.maximum(t_mcs + t_ccs, n_mcs + n_ccs)
    ylim_top = max(all_tops) * 1.18
    if n_elec > 0:
        ax.text(0.5 + n_elec / 2, ylim_top * 0.97, 'Electricity', ha='center', fontsize=10,
                color='#666', fontstyle='italic')
    n_net = sum(1 for s, _ in NET_SCENARIOS if f'{prefix}_{s}' in sc_q_data)
    if n_net > 0:
        ax.text(1 + n_elec + n_net / 2 - 0.5, ylim_top * 0.97, 'Network fee', ha='center', fontsize=10,
                color='#666', fontstyle='italic')

    ax.set_xticks(x)
    ax.set_xticklabels([s[0] for s in scenarios], fontsize=10, rotation=40, ha='right')
    ax.set_title(title, fontsize=15)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, ylim_top)


# Plot panels
plot_energy_panel(axes[0, 0], 'AT33', 'AT', 'at33', at33_s,
                  '(a) Charging energy — AT33 (Tirol)')
plot_energy_panel(axes[0, 1], 'ITH1', 'IT', 'ith1', ith1_s,
                  '(b) Charging energy — ITH1 (Veneto)')
plot_infra_panel(axes[1, 0], 'AT33', 'at33', at33_q,
                 '(c) Infrastructure at AT33 (cumul. MW)')
plot_infra_panel(axes[1, 1], 'ITH1', 'ith1', ith1_q,
                 '(d) Infrastructure at ITH1 (cumul. MW)')

axes[0, 0].set_ylabel(f'BET charging in\nborder regions (GWh)', fontsize=14)
axes[1, 0].set_ylabel(f'Installed capacity at\ntarget node (MW)', fontsize=14)

# Legends
# Top row: country legend
h1, l1 = axes[0, 0].get_legend_handles_labels()
h2, l2 = axes[0, 1].get_legend_handles_labels()
all_h, all_l = [], []
seen = set()
for h, l in zip(h1 + h2, l1 + l2):
    if l not in seen:
        all_h.append(h)
        all_l.append(l)
        seen.add(l)
fig.legend(all_h, all_l, loc='upper center', bbox_to_anchor=(0.5, 1.03),
           ncol=len(all_l), fontsize=12, framealpha=0.9)

# Bottom row: MCS/CCS legend (shared, below bottom panels)
h_infra, l_infra = axes[1, 0].get_legend_handles_labels()
fig.legend(h_infra, l_infra, loc='lower center', bbox_to_anchor=(0.5, -0.02),
           ncol=4, fontsize=11, framealpha=0.9)

fig.suptitle(f'Locational cost premium sensitivity — border region charging and infrastructure ({YEAR})',
             fontsize=17, y=1.06)

plt.tight_layout()
plt.savefig(str(FIG_DIR / 'surcharge_sensitivity_at33_ith1.pdf'), bbox_inches='tight', dpi=300)
plt.savefig(str(FIG_DIR / 'surcharge_sensitivity_at33_ith1.png'), bbox_inches='tight', dpi=300)
if MANUSCRIPT_IMG.exists():
    plt.savefig(str(MANUSCRIPT_IMG / 'surcharge_sensitivity_at33_ith1.pdf'), bbox_inches='tight', dpi=300)
print('Saved: surcharge_sensitivity_at33_ith1.pdf/.png')
plt.close()
