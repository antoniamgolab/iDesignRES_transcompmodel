"""
Combined Section 5.1 figure:
  Row 1: Delta matrices (NECP, REPowerEU++, Trinity vs Go RES) — BET share by OD pair at 2040
  Row 2: (a) Energy by latitude 2040 — filled area, all 4 scenarios
         (b) Normalized spatial distribution by latitude 2040
         (c) Country-level CCS+MCS stacked bars: Go RES vs NECP at 2040
"""
import yaml, re, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Patch
from pathlib import Path
from collections import defaultdict
from scipy.ndimage import gaussian_filter1d

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI', 'sans-serif']
matplotlib.rcParams['font.size'] = 13

BASE = Path(__file__).resolve().parent
RESULTS_PATH = BASE / 'results' / 'uncertainty_scenarios_v2'  # old
RES_DIR = {'scenario_000': BASE / 'results/final/uncertainty_scenarios/scenario_000',
           'scenario_001': BASE / 'results/final/uncertainty_scenarios/scenario_001',
           'scenario_002': BASE / 'results/final/uncertainty_scenarios/scenario_002',
           'scenario_003': BASE / 'results/final/uncertainty_scenarios/scenario_003'}
FIG_DIR = BASE / 'figures'
FIG_DIR.mkdir(exist_ok=True)

COUNTRY_ORDER = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']
TARGET_YEAR = 2040
MODELED_YEARS = list(range(2020, 2064, 4))
y_idx_to_year = {i+1: y for i, y in enumerate(MODELED_YEARS)}

# Colors
SC_COLORS = {
    'scenario_000': '#2c6e99',  # medium navy
    'scenario_001': '#9b59b6',  # medium purple
    'scenario_002': '#45a0cc',  # medium blue
    'scenario_003': '#d97a3e',  # warm orange
}
SC_NAMES = {
    'scenario_000': 'Go RES',
    'scenario_001': 'NECP',
    'scenario_002': 'REPowerEU++',
    'scenario_003': 'Trinity',
}

# ── Load input data ──
print("Loading input data...")
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geoid2country = {g['id']: g.get('country', '??') for g in geo_data if g.get('type') == 'node'}
geoid2lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}
all_geo_ids = [g['id'] for g in geo_data if g.get('type') == 'node']

with open(BASE / 'input_data/uncertainty_scenarios_v2_night/scenario_000/Odpair.yaml') as f:
    odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
odpair_map = {od['id']: (od['from'], od['to']) for od in odpairs}

# ══════════════════════════════════════════════════════════════════════
# ROW 1: Delta matrices
# ══════════════════════════════════════════════════════════════════════
CI_RE = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')

def load_bev_by_od(sc_id, target_year):
    h_files = sorted(glob.glob(str(RES_DIR[sc_id] / '*_h_dict.yaml')))
    with open(h_files[-1]) as f:
        h_dict = yaml.safe_load(f)
    bev = defaultdict(float)
    icev = defaultdict(float)
    for key, value in h_dict.items():
        if isinstance(value, str): value = float(value)
        if value < 0.01: continue
        try:
            parts = str(key).strip('()').split(',')
            year = int(parts[0].strip()); oid = int(parts[1].strip()); tid = int(parts[2].strip())
            if year != target_year: continue
        except:
            continue
        if oid not in odpair_map: continue
        og, dg = odpair_map[oid]
        oc = geoid2country.get(og); dc = geoid2country.get(dg)
        if not oc or not dc: continue
        pair = tuple(sorted([oc, dc], key=lambda c: COUNTRY_ORDER.index(c)))
        if tid == 1: bev[pair] += value
        elif tid == 0: icev[pair] += value
    result = {}
    for pair in set(list(bev.keys()) + list(icev.keys())):
        b = bev[pair]; i = icev[pair]; t = b + i
        if t > 10: result[pair] = b / t * 100
    return result

print("Loading BEV adoption by OD pair...")
ref_od = load_bev_by_od('scenario_000', TARGET_YEAR)
comp_od = {}
for sc in ['scenario_001', 'scenario_002', 'scenario_003']:
    comp_od[sc] = load_bev_by_od(sc, TARGET_YEAR)

# Load BEV fleet share at TARGET_YEAR for each scenario
bev_pct_at_year = {}
for sc in ['scenario_000', 'scenario_001', 'scenario_002', 'scenario_003']:
    with open(RES_DIR[sc] / 'summary_stats.yaml') as f:
        s = yaml.safe_load(f)
    fl = s.get('fleet_by_year', {}).get(TARGET_YEAR, {})
    i = fl.get('ICEV', 0); b = fl.get('BEV', 0); t = i + b
    bev_pct_at_year[sc] = b / t * 100 if t > 0 else 0

# ══════════════════════════════════════════════════════════════════════
# ROW 2a/2b: Energy by latitude
# ══════════════════════════════════════════════════════════════════════
tuple_re = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')

print("Loading energy data...")
PLOT_YEARS = [2036, 2040, 2048]
energy_by_sc_year = {}  # {(sc, year): {geo: MWh}}
for sc in ['scenario_000', 'scenario_001', 'scenario_002', 'scenario_003']:
    s_files = sorted(glob.glob(str(RES_DIR[sc] / '*_s_dict.yaml')))
    energy_by_year_geo = defaultdict(lambda: defaultdict(float))
    with open(s_files[-1]) as f:
        for line in f:
            m = tuple_re.match(line.strip())
            if not m: continue
            yr = int(m.group(1))
            if yr not in PLOT_YEARS: continue
            gid = int(m.group(5))
            fu = int(m.group(7)); inf = int(m.group(8))
            val = float(m.group(10))
            if val < 1e-6 or fu != 0 or inf not in {1, 2}: continue
            energy_by_year_geo[yr][gid] += val
    for yr in PLOT_YEARS:
        energy_by_sc_year[(sc, yr)] = dict(energy_by_year_geo[yr])

# ══════════════════════════════════════════════════════════════════════
# ROW 2c: CCS vs MCS by country (Go RES vs NECP)
# ══════════════════════════════════════════════════════════════════════
ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

print("Loading infrastructure data...")
infra_by_sc_year = {}  # {(sc, year): {'ccs': {country: MW}, 'mcs': {country: MW}}}
for sc in ['scenario_000', 'scenario_002']:
    q_files = sorted(glob.glob(str(RES_DIR[sc] / '*_q_fuel_infr_plus_dict.yaml')))
    for target_yr in PLOT_YEARS:
        ccs_country = defaultdict(float)
        mcs_country = defaultdict(float)
        with open(q_files[-1]) as f:
            for line in f:
                m = ci3_pat.match(line.strip())
                if not m: continue
                yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
                val = float(m.group(4))
                if val < 1e-3 or fi == 3: continue
                geo_id = pos - 1  # CartesianIndex is 1-based
                yr = y_idx_to_year.get(yi)
                if yr and yr <= target_yr:
                    c = geoid2country.get(geo_id, '??')
                    # CORRECTED: fi=1=MCS, fi=2=CCS
                    if fi == 2: ccs_country[c] += val / 1000  # MW
                    elif fi == 1: mcs_country[c] += val / 1000
        infra_by_sc_year[(sc, target_yr)] = {'ccs': dict(ccs_country), 'mcs': dict(mcs_country)}

# ══════════════════════════════════════════════════════════════════════
# BUILD FIGURE
# ══════════════════════════════════════════════════════════════════════
print("Building figure...")
fig = plt.figure(figsize=(16, 10))

# GridSpec: 2 rows
gs = fig.add_gridspec(2, 3, height_ratios=[1, 1], hspace=0.75, wspace=0.3)

# ── ROW 1: Delta matrices ──
countries = COUNTRY_ORDER
nc = len(countries)
delta_scenarios = [
    ('scenario_001', 'NECP'),
    ('scenario_002', 'REPowerEU++'),
    ('scenario_003', 'Trinity'),
]

    # Trimmed matrix: remove NO row (first) and IT column (last)
    # x-axis (columns) = origins: NO, FI, SE, DK, DE, AT (drop IT)
    # y-axis (rows) = destinations: FI, SE, DK, DE, AT, IT (drop NO)
x_countries = COUNTRY_ORDER[:-1]  # NO, FI, SE, DK, DE, AT
y_countries = COUNTRY_ORDER[1:]   # FI, SE, DK, DE, AT, IT
nx = len(x_countries)
ny = len(y_countries)

for idx, (sc_id, sc_label) in enumerate(delta_scenarios):
    ax = fig.add_subplot(gs[1, idx])
    comp = comp_od[sc_id]

    matrix = np.full((ny, nx), np.nan)
    text_matrix = [['' for _ in range(nx)] for _ in range(ny)]

    for i in range(ny):
        for j in range(nx):
            c_row = y_countries[i]  # destination
            c_col = x_countries[j]  # origin
            # Only lower triangle: row country must be south of column country
            row_idx = COUNTRY_ORDER.index(c_row)
            col_idx = COUNTRY_ORDER.index(c_col)
            if row_idx <= col_idx:
                continue  # upper triangle or diagonal
            pair = tuple(sorted([c_col, c_row], key=lambda c: COUNTRY_ORDER.index(c)))
            ref_val = ref_od.get(pair)
            comp_val = comp.get(pair)
            if ref_val is None and comp_val is None:
                text_matrix[i][j] = 'n.a.'
            elif ref_val is None or comp_val is None:
                if ref_val is not None:
                    matrix[i, j] = -ref_val
                    text_matrix[i][j] = f'{-ref_val:+.0f}'
                elif comp_val is not None:
                    matrix[i, j] = comp_val
                    text_matrix[i][j] = f'{comp_val:+.0f}'
            else:
                delta = comp_val - ref_val
                matrix[i, j] = delta
                text_matrix[i][j] = f'{delta:+.0f}' if abs(delta) >= 0.5 else '0'

    norm = TwoSlopeNorm(vmin=-60, vcenter=0, vmax=60)
    im = ax.imshow(matrix, cmap='PuOr_r', norm=norm, aspect='auto')

    ax.set_xticks(range(nx))
    ax.set_xticklabels(x_countries, fontsize=13)
    ax.set_yticks(range(ny))
    ax.set_yticklabels(y_countries, fontsize=13)

    for i in range(ny):
        for j in range(nx):
            c_row = y_countries[i]
            c_col = x_countries[j]
            row_idx = COUNTRY_ORDER.index(c_row)
            col_idx = COUNTRY_ORDER.index(c_col)
            if row_idx <= col_idx:
                # Upper triangle / diagonal — white out
                ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1,
                            fill=True, facecolor='white', edgecolor='white', linewidth=0))
            elif text_matrix[i][j] == 'n.a.':
                ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1,
                            fill=True, facecolor='white', edgecolor='lightgray', linewidth=0.5))
                ax.text(j, i, 'n.a.', ha='center', va='center', fontsize=9, color='#bbb', style='italic')
            else:
                val = matrix[i, j]
                if not np.isnan(val):
                    color = 'white' if abs(val) > 25 else 'black'
                    ax.text(j, i, text_matrix[i][j], ha='center', va='center',
                           fontsize=10, color=color, fontweight='bold' if abs(val) > 10 else 'normal')

    bev_sc = bev_pct_at_year[sc_id]
    ax.set_title(f'{sc_label} $-$ Go RES\n(BET share: {bev_sc:.0f}%)', fontsize=12)
    for spine in ax.spines.values(): spine.set_visible(False)

# Reference annotation — placed above the delta matrices row (bottom row only)
bev_ref = bev_pct_at_year['scenario_000']
fig.text(0.12, 0.44, f'Reference: Go RES (BET share {bev_ref:.0f}% in {TARGET_YEAR})',
         fontsize=12, fontstyle='italic', va='bottom', ha='left')

# Colorbar for row 1 — positioned between the two rows
cbar_ax = fig.add_axes([0.15, 0.03, 0.7, 0.015])
cbar = fig.colorbar(im, cax=cbar_ax, orientation='horizontal')
cbar.set_label('$\\Delta$ BET share (pp)', fontsize=13)
cbar.ax.tick_params(labelsize=11)

# ── ROW 2: Three latitude panels (2036, 2040, 2048 absolute) ──
sigma = 1.2
# Plot largest first (background), smallest last (foreground) so small scenarios are visible
scenario_order = ['scenario_000', 'scenario_002', 'scenario_001', 'scenario_003']
country_lats = {'IT': 42.5, 'AT': 47.5, 'DE': 51.0, 'DK': 56.0, 'SE': 62.0, 'NO': 64.0}

lat_panels = [
    (2036, 'abs', '(a) Charging demand in 2036'),
    (2040, 'abs', '(b) Charging demand in 2040'),
    (2048, 'abs', '(c) Charging demand in 2048'),
]

lat_axes = []
for panel_idx, (yr, mode, title) in enumerate(lat_panels):
    ax = fig.add_subplot(gs[0, panel_idx])
    lat_axes.append(ax)

    for sc in scenario_order:
        e_by_lat = defaultdict(float)
        for gid, mwh in energy_by_sc_year.get((sc, yr), {}).items():
            lat = geoid2lat.get(gid)
            if lat is not None:
                e_by_lat[lat] += mwh

        lats = np.array(sorted(e_by_lat.keys()))
        vals = np.array([e_by_lat[l] for l in lats])
        vals = vals / 1000  # GWh
        xlabel = 'Charging demand (GWh)'

        vals_smooth = gaussian_filter1d(vals, sigma)
        ax.fill_betweenx(lats, 0, vals_smooth, alpha=0.25, color=SC_COLORS[sc])
        ax.plot(vals_smooth, lats, color=SC_COLORS[sc], linewidth=1.5, alpha=0.9, label=SC_NAMES[sc])

    ax.set_ylabel('Latitude')
    ax.set_xlabel(xlabel)
    ax.set_title(title, fontsize=13)
    if panel_idx == 0:
        ax.legend(fontsize=11, loc='upper center')
    ax.grid(True, alpha=0.2)

# Set same x-axis scale across all three panels
max_xlim = max(ax.get_xlim()[1] for ax in lat_axes)
for ax in lat_axes:
    ax.set_xlim(0, max_xlim)

# Add country labels after setting xlim
for ax in lat_axes:
    for c, lat in country_lats.items():
        ax.axhline(y=lat, color='gray', linestyle=':', alpha=0.3, linewidth=0.5)
        ax.text(max_xlim * 0.95, lat, c, fontsize=9, ha='right', va='center', color='gray')

# ── Save ──
plt.savefig(str(FIG_DIR / 'combined_section5_1_final.pdf'), bbox_inches='tight', dpi=300)
plt.savefig(str(FIG_DIR / 'combined_section5_1_final.png'), bbox_inches='tight', dpi=300)
print("Saved: figures/combined_section5_1_final.pdf/.png")
plt.close()
