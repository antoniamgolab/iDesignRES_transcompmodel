"""
Clean figure showing delta from baseline: how demand shifts between border regions
under electricity price vs network fee surcharges at AT33 and ITH1.
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
    "font.size": 14,
})

BASE = Path(__file__).resolve().parent
FIG_DIR = BASE / 'figures'
MANUSCRIPT_IMG = BASE.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'

with open(BASE / 'input_data' / 'fixed_nuts_2' / 'GeographicElement.yaml') as f:
    geo = yaml.safe_load(f)
geoid_to_nuts2 = {int(g['id']): g.get('nuts2_region', '')
                  for g in geo if g.get('type') == 'node' and g.get('nuts2_region')}

BORDER = {'AT33', 'AT34', 'ITC4', 'ITH1', 'ITH2', 'ITH3', 'DE14', 'DE21', 'DE27'}
YEAR = 2040

S_PAT = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*"?([\d.eE+-]+)"?')

def load_border_by_nuts2(s_file, year):
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
    return dict(by_n2)

bl_s = sorted(glob.glob(str(BASE / 'results' / 'uncertainty_scenarios_v2' / 'scenario_000' / '*_s_dict.yaml')))[-1]
bl = load_border_by_nuts2(bl_s, YEAR)

def load_scenarios(rdir):
    data = {}
    for folder in sorted(Path(rdir).iterdir()):
        if not folder.is_dir(): continue
        s_files = sorted(folder.glob('*_s_dict.yaml'))
        if s_files:
            data[folder.name] = load_border_by_nuts2(str(s_files[-1]), YEAR)
    return data

at33_data = load_scenarios(BASE / 'results' / 'at33_surcharge')
ith1_data = load_scenarios(BASE / 'results' / 'ith1_surcharge')

# Regions to show (order: target first, then neighbors)
REGIONS_AT33 = ['AT33', 'AT34', 'DE21', 'ITC4', 'ITH1', 'ITH2', 'ITH3']
REGIONS_ITH1 = ['ITH1', 'ITH2', 'ITH3', 'ITC4', 'AT33', 'AT34', 'DE21']

REGION_COLORS = {
    'DE14': '#9b91c9', 'DE21': '#7268af', 'DE27': '#bdb5dc',
    'AT33': '#d4a017', 'AT34': '#e8cc6e',
    'ITH1': '#e05050', 'ITH2': '#e88a7a', 'ITH3': '#f0b0a0', 'ITC4': '#c93c3c',
}

ELEC_COL = '#e07b54'
NET_COL = '#4a90a4'

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))

def plot_delta_panel(ax, target, prefix, sc_data, regions, title):
    elec_key = f'{prefix}_elec_high'    # +4 ct/kWh
    net_key = f'{prefix}_network_high'  # +10 EUR/kW/yr

    elec = sc_data.get(elec_key, {})
    net = sc_data.get(net_key, {})

    x = np.arange(len(regions))
    bar_w = 0.35

    elec_deltas = [elec.get(r, 0) - bl.get(r, 0) for r in regions]
    net_deltas = [net.get(r, 0) - bl.get(r, 0) for r in regions]

    bars_e = ax.bar(x - bar_w / 2, elec_deltas, bar_w, color=ELEC_COL, edgecolor='black',
                     linewidth=0.5, label='+4 ct/kWh (electricity)')
    bars_n = ax.bar(x + bar_w / 2, net_deltas, bar_w, color=NET_COL, edgecolor='black',
                     linewidth=0.5, label='+10 EUR/kW/yr (network)')

    # Compute y-limits with extra headroom for annotations
    all_vals = elec_deltas + net_deltas
    ymin = min(min(all_vals) * 1.35, -5)
    ymax = max(max(all_vals) * 1.5, 5)
    pad = (ymax - ymin) * 0.05

    # Annotate values
    for i, (de, dn) in enumerate(zip(elec_deltas, net_deltas)):
        if abs(de) > 1:
            offset = pad if de > 0 else -pad
            va = 'bottom' if de > 0 else 'top'
            ax.text(x[i] - bar_w / 2, de + offset, f'{de:+.0f}',
                    ha='center', va=va, fontsize=9, fontweight='bold', color=ELEC_COL)
        if abs(dn) > 1:
            offset = pad if dn > 0 else -pad
            va = 'bottom' if dn > 0 else 'top'
            ax.text(x[i] + bar_w / 2, dn + offset, f'{dn:+.0f}',
                    ha='center', va=va, fontsize=9, fontweight='bold', color=NET_COL)

    ax.axhline(y=0, color='black', linewidth=0.8)

    # Highlight target region
    target_idx = regions.index(target)
    ax.axvspan(target_idx - 0.45, target_idx + 0.45, color=REGION_COLORS[target], alpha=0.1, zorder=0)

    # Region labels with baseline values
    xlabels = [f'{r}\n({bl.get(r, 0):.0f})' for r in regions]
    ax.set_xticks(x)
    ax.set_xticklabels(xlabels, fontsize=11)
    ax.set_title(title, fontsize=15)
    ax.set_ylim(ymin, ymax)
    ax.grid(axis='y', alpha=0.2)

plot_delta_panel(ax1, 'AT33', 'at33', at33_data, REGIONS_AT33,
                 'Surcharge in AT33 (Tirol)')
plot_delta_panel(ax2, 'ITH1', 'ith1', ith1_data, REGIONS_ITH1,
                 'Surcharge in ITH1 (Veneto)')

ax1.set_ylabel(f'Change in charging demand\nvs baseline (GWh, {YEAR})', fontsize=13)

# Shared legend below figure
handles, labels = ax1.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, -0.06),
           ncol=2, fontsize=12, framealpha=0.9)

fig.suptitle('Charging demand reallocation: electricity price vs network fee surcharges',
             fontsize=16, y=1.06)

plt.tight_layout()
plt.savefig(str(FIG_DIR / 'surcharge_reallocation_clean.pdf'), bbox_inches='tight', dpi=300)
plt.savefig(str(FIG_DIR / 'surcharge_reallocation_clean.png'), bbox_inches='tight', dpi=300)
if MANUSCRIPT_IMG.exists():
    plt.savefig(str(MANUSCRIPT_IMG / 'surcharge_reallocation_clean.pdf'), bbox_inches='tight', dpi=300)
print('Saved: surcharge_reallocation_clean.pdf/.png')
plt.close()
