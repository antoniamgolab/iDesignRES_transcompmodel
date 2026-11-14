"""
AT surcharge sensitivity: BEV adoption slowdown across surcharge scenarios.
Shows BEV fleet share (%) over time for baseline vs all surcharge scenarios.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
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
FIG_DIR = BASE / 'figures'
MANUSCRIPT_IMG = BASE.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'

MODELED_YEARS = list(range(2020, 2064, 4))
TUPLE_PAT = re.compile(r'\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*"?([\d.eE+-]+)"?')

def load_fleet_shares(h_file):
    fleet = defaultdict(lambda: defaultdict(float))
    with open(h_file) as f:
        for line in f:
            m = TUPLE_PAT.match(line.strip())
            if not m:
                continue
            yr, odpair, tv_id, gen = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            val = float(m.group(5))
            if val > 0:
                fleet[yr]['BEV' if tv_id == 1 else 'diesel'] += val
    shares = {}
    for yr in MODELED_YEARS:
        total = fleet[yr]['BEV'] + fleet[yr]['diesel']
        shares[yr] = fleet[yr]['BEV'] / total * 100 if total > 0 else 0
    return shares

# Load baseline
baseline_h = sorted(glob.glob(str(BASE / 'results' / 'uncertainty_scenarios_v2' / 'scenario_000' / '*_h_dict.yaml')))[-1]
bl_shares = load_fleet_shares(baseline_h)
print(f'Baseline: {Path(baseline_h).name}')

# Load surcharge scenarios
surcharge_dir = BASE / 'results' / 'at_surcharge'
ELEC_SCENARIOS = [
    ('at_elec_low', '+1 ct/kWh'),
    ('at_elec_med', '+2 ct/kWh'),
    ('at_elec_high', '+4 ct/kWh'),
    ('at_elec_extreme', '+6 ct/kWh'),
]
NET_SCENARIOS = [
    ('at_network_low', '+2 EUR/kW/yr'),
    ('at_network_med', '+5 EUR/kW/yr'),
    ('at_network_high', '+10 EUR/kW/yr'),
]

sc_shares = {}
for sid, label in ELEC_SCENARIOS + NET_SCENARIOS:
    h_files = sorted((surcharge_dir / sid).glob('*_h_dict.yaml'))
    if h_files:
        sc_shares[sid] = load_fleet_shares(str(h_files[-1]))
        print(f'  {label}: {h_files[-1].name}')

# === Figure: 2 panels (electricity surcharges | network fee surcharges) ===
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

years = np.array(MODELED_YEARS)
bl_vals = np.array([bl_shares[y] for y in MODELED_YEARS])

# Color gradients for electricity surcharges (light to dark)
elec_colors = ['#f4c28a', '#e8994a', '#d4701a', '#a34d0a']
net_colors = ['#a8c4d8', '#6a9bbf', '#3a6d99']

# Panel (a): Electricity surcharges
ax1.plot(years, bl_vals, 'k-o', linewidth=2.5, markersize=6, label='Reference', zorder=5)
for i, (sid, label) in enumerate(ELEC_SCENARIOS):
    if sid in sc_shares:
        vals = np.array([sc_shares[sid][y] for y in MODELED_YEARS])
        ax1.plot(years, vals, '-s', color=elec_colors[i], linewidth=1.8, markersize=5, label=label, alpha=0.9)
        # Shade the gap
        ax1.fill_between(years, bl_vals, vals, alpha=0.08, color=elec_colors[i])

ax1.set_xlabel('Year', fontsize=15)
ax1.set_ylabel('BET fleet share (%)', fontsize=15)
ax1.set_title('Electricity price surcharges', fontsize=16)
ax1.legend(fontsize=12, loc='upper left')
ax1.grid(alpha=0.3)
ax1.set_xlim(2020, 2060)
ax1.set_ylim(-2, 105)

# Panel (b): Network fee surcharges
ax2.plot(years, bl_vals, 'k-o', linewidth=2.5, markersize=6, label='Reference', zorder=5)
for i, (sid, label) in enumerate(NET_SCENARIOS):
    if sid in sc_shares:
        vals = np.array([sc_shares[sid][y] for y in MODELED_YEARS])
        ax2.plot(years, vals, '-D', color=net_colors[i], linewidth=1.8, markersize=5, label=label, alpha=0.9)
        ax2.fill_between(years, bl_vals, vals, alpha=0.08, color=net_colors[i])

ax2.set_xlabel('Year', fontsize=15)
ax2.set_title('Network fee surcharges', fontsize=16)
ax2.legend(fontsize=12, loc='upper left')
ax2.grid(alpha=0.3)
ax2.set_xlim(2020, 2060)

fig.suptitle('BET adoption slowdown under Austrian locational cost premiums\n(Go RES scenario, corridor-wide)',
             fontsize=17, y=1.02)

plt.tight_layout()
plt.savefig(str(FIG_DIR / 'at_surcharge_bev_adoption_slowdown.pdf'), bbox_inches='tight', dpi=300)
plt.savefig(str(FIG_DIR / 'at_surcharge_bev_adoption_slowdown.png'), bbox_inches='tight', dpi=300)
if MANUSCRIPT_IMG.exists():
    plt.savefig(str(MANUSCRIPT_IMG / 'at_surcharge_bev_adoption_slowdown.pdf'), bbox_inches='tight', dpi=300)
print('\nSaved: at_surcharge_bev_adoption_slowdown.pdf/.png')
plt.close()
