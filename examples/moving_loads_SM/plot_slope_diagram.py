"""
Slope diagram: BEV adoption by OD country pair — Go RES vs REPowerEU++
"""
import yaml, re, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Times New Roman', 'serif']
matplotlib.rcParams['font.size'] = 14

BASE = Path(__file__).resolve().parent
RESULTS = BASE / 'results' / 'uncertainty_scenarios_v2'
FIG_DIR = BASE / 'figures'

COUNTRY_ORDER = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']
CI_RE = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')
YEAR_MAPPING = {i: 2020 + (i-1)*4 for i in range(1, 15)}

with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geoid2country = {g['id']: g.get('country', '??') for g in geo_data if g.get('type') == 'node'}

with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/Odpair.yaml') as f:
    odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
odpair_map = {od['id']: (od['from'], od['to']) for od in odpairs}

def load_bev_share_by_od(sc_id, target_year):
    h_files = sorted(glob.glob(str(RESULTS / sc_id / '*_h_dict.yaml')))
    with open(h_files[-1]) as f:
        h_dict = yaml.safe_load(f)

    bev_by_pair = defaultdict(float)
    icev_by_pair = defaultdict(float)

    for key, value in h_dict.items():
        if isinstance(value, str): value = float(value)
        if value < 0.01: continue
        m = CI_RE.match(str(key))
        if m:
            yi, oid, tid = int(m.group(1)), int(m.group(2)), int(m.group(3))
            year = YEAR_MAPPING.get(yi, yi)
            if year != target_year: continue
        else:
            try:
                parts = str(key).strip('()').split(',')
                year = int(parts[0].strip()); oid = int(parts[1].strip()); tid = int(parts[2].strip())
                if year != target_year: continue
            except: continue
        if oid not in odpair_map: continue
        og, dg = odpair_map[oid]
        oc = geoid2country.get(og); dc = geoid2country.get(dg)
        if not oc or not dc: continue
        pair = tuple(sorted([oc, dc], key=lambda c: COUNTRY_ORDER.index(c)))
        if tid == 1: bev_by_pair[pair] += value
        elif tid == 0: icev_by_pair[pair] += value

    result = {}
    for pair in set(list(bev_by_pair.keys()) + list(icev_by_pair.keys())):
        b = bev_by_pair[pair]; i = icev_by_pair[pair]; t = b + i
        if t > 10:
            result[pair] = b / t * 100
    return result

# Load data
for target_year in [2040, 2048]:
    print(f"Loading {target_year}...")
    go_res = load_bev_share_by_od('scenario_000', target_year)
    repower = load_bev_share_by_od('scenario_002', target_year)

    # Get all pairs present in both
    common_pairs = sorted(
        set(go_res.keys()) & set(repower.keys()),
        key=lambda p: max(go_res.get(p, 0), repower.get(p, 0)),
        reverse=True
    )[:15]  # top 15 by max adoption

    # ── SLOPE DIAGRAM ──
    fig, ax = plt.subplots(figsize=(8, 10))

    x_left = 0.2
    x_right = 0.8
    y_positions = np.linspace(0.95, 0.05, len(common_pairs))

    for i, pair in enumerate(common_pairs):
        v_left = go_res.get(pair, 0)
        v_right = repower.get(pair, 0)
        y = y_positions[i]

        # Color by direction of change
        if v_right > v_left + 1:
            color = '#2ECC71'  # green — REPower higher
            alpha = 0.8
        elif v_right < v_left - 1:
            color = '#E74C3C'  # red — REPower lower
            alpha = 0.8
        else:
            color = '#95A5A6'  # gray — similar
            alpha = 0.5

        # Draw slope line
        ax.plot([x_left, x_right], [v_left, v_right],
                color=color, linewidth=2, alpha=alpha, zorder=2)

        # Left dot and label
        ax.scatter(x_left, v_left, color='#2C3E50', s=50, zorder=3)
        pair_label = f"{pair[0]}-{pair[1]}"
        ax.annotate(f"{pair_label}  {v_left:.0f}%",
                   xy=(x_left - 0.02, v_left), ha='right', va='center', fontsize=10)

        # Right dot and label
        ax.scatter(x_right, v_right, color='#0D47A1', s=50, zorder=3)
        delta = v_right - v_left
        delta_str = f"{delta:+.0f} pp" if abs(delta) > 0.5 else ""
        ax.annotate(f"{v_right:.0f}%  {delta_str}",
                   xy=(x_right + 0.02, v_right), ha='left', va='center', fontsize=10,
                   color=color if abs(delta) > 1 else 'gray')

    # Headers
    ax.text(x_left, max(go_res.values()) * 1.05 + 2, 'Go RES',
            ha='center', va='bottom', fontsize=14, fontweight='bold', color='#2C3E50')
    ax.text(x_right, max(go_res.values()) * 1.05 + 2, 'REPowerEU++',
            ha='center', va='bottom', fontsize=14, fontweight='bold', color='#0D47A1')

    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-5, max(max(go_res.values()), max(repower.values())) + 10)
    ax.set_ylabel('BEV share (%)', fontsize=13)
    ax.set_title(f'BEV adoption by OD country pair - {target_year}\nGo RES vs REPowerEU++',
                fontsize=15, fontweight='bold')

    # Remove x-axis ticks
    ax.set_xticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.grid(axis='y', alpha=0.2)

    plt.tight_layout()
    outfile = FIG_DIR / f'slope_bev_gores_vs_repower_{target_year}.pdf'
    plt.savefig(outfile, bbox_inches='tight', dpi=300)
    plt.savefig(str(outfile).replace('.pdf', '.png'), bbox_inches='tight', dpi=200)
    print(f"  Saved: {outfile.name}")
    plt.close()

print("Done!")
