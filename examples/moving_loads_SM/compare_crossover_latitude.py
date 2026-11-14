"""
Compare spatial distribution of BEV charging demand by latitude
between original (Crossover=0) and re-run (crossover enabled) results
for scenario_000.

Crossover=0 (original): results/uncertainty_scenarios/scenario_000/
Crossover enabled (v2): results/uncertainty_scenarios_v2/scenario_000/
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from collections import defaultdict
from scipy.ndimage import gaussian_filter1d
from scipy.stats import pearsonr
import pathlib

# ── Configuration ─────────────────────────────────────────────────────
BASE = pathlib.Path(r'C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis'
                    r'\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM')

ORIG_S_DICT = (BASE / 'results/uncertainty_scenarios/scenario_000/'
               'scenario_000_cs_2026-02-11_11-52-48_s_dict.yaml')
V2_S_DICT   = (BASE / 'results/uncertainty_scenarios_v2/scenario_000/'
               'scenario_000_cs_2026-02-14_18-25-42_s_dict.yaml')

GEO_YAML = BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml'
SCENARIO_INPUT = BASE / 'input_data/uncertainty_scenarios/scenario_000'

FIG_DIR = BASE / 'figures'
FIG_DIR.mkdir(exist_ok=True)

# Year indices (1-based): 1=2020, 2=2024, 3=2028, 4=2032, 5=2036, 6=2040, ...
YEAR_MAP = {i+1: 2020 + 4*i for i in range(11)}
YEAR_IDX_MAP = {v: k for k, v in YEAR_MAP.items()}  # year -> index

TARGET_YEARS = [2032, 2040]
BEV_FL_IDXS = {1, 2}   # slow and fast charging (electricity)
SCALING_FACTOR = 1000   # s values are in MWh (scaled), multiply by 1000 -> kWh

# Country latitude bands for annotation
COUNTRY_BANDS = {
    'IT':  (42, 46.5),
    'AT':  (46.5, 48.5),
    'DE':  (48.5, 54.5),
    'DK':  (54.5, 57.5),
    'SE':  (57.5, 66),
    'NO':  (59, 70),
}

# ── 1. Load geographic elements ──────────────────────────────────────
print("Loading geographic element data...")
with open(GEO_YAML) as f:
    geo_data = yaml.safe_load(f)

geo_lat = {}
geo_country = {}
geo_name = {}
for g in geo_data:
    gid = g['id']
    geo_lat[gid] = g['coordinate_lat']
    geo_country[gid] = g.get('country', '')
    geo_name[gid] = g.get('name', f'id_{gid}')

print(f"  Loaded {len(geo_lat)} geographic elements")
print(f"  Latitude range: {min(geo_lat.values()):.2f} to {max(geo_lat.values()):.2f}")

# ── 2. Build p_r_k_g mapping from Odpair/Path data ──────────────────
print("\nBuilding p_r_k_g index mapping...")
with open(SCENARIO_INPUT / 'Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(SCENARIO_INPUT / 'Odpair.yaml') as f:
    odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)

path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}

# Build the same set as Julia's create_p_r_k_g_set
p_r_k_g_set = set()
for od in odpairs:
    od_id = int(od['id'])
    pid = int(od['path_id'])
    prod_id = 0  # single product (all have product 0)
    for geo_id in path_by_id[pid]:
        p_r_k_g_set.add((prod_id, od_id, pid, geo_id))

p_r_k_g_sorted = sorted(p_r_k_g_set)
prkg_idx_map = {i+1: t for i, t in enumerate(p_r_k_g_sorted)}  # 1-based

print(f"  Total p_r_k_g pairs: {len(p_r_k_g_sorted)}")
print(f"  Number of paths: {len(path_by_id)}")
print(f"  Number of OD pairs: {len(odpairs)}")

# ── 3. Parse s_dict files ────────────────────────────────────────────
ci_pat = re.compile(
    r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)'
)

def load_s_dict_by_year_geo(filepath, target_year_idxs, prkg_idx_map):
    """Parse s_dict, return {year_idx: {geo_id: total_bev_kwh}}."""
    result = {yi: defaultdict(float) for yi in target_year_idxs}
    total_lines = 0
    matched = 0
    skipped_prkg = 0

    with open(filepath) as f:
        for line in f:
            total_lines += 1
            m = ci_pat.match(line.strip())
            if not m:
                continue

            y_idx   = int(m.group(1))
            prkg_i  = int(m.group(2))
            # tv_idx = int(m.group(3))  # not needed
            fl_idx  = int(m.group(4))
            # gen_idx = int(m.group(5))  # not needed
            val     = float(m.group(6))

            if y_idx not in target_year_idxs:
                continue
            if fl_idx not in BEV_FL_IDXS:
                continue
            if val < 1e-8:
                continue

            prkg = prkg_idx_map.get(prkg_i)
            if prkg is None:
                skipped_prkg += 1
                continue

            _, _, _, geo_id = prkg
            # val is in model units (MWh scaled); convert to kWh
            result[y_idx][geo_id] += val * SCALING_FACTOR
            matched += 1

    print(f"  Parsed {total_lines} lines, {matched} matched BEV entries, "
          f"{skipped_prkg} skipped (unmapped prkg)")
    return result


target_idxs = {YEAR_IDX_MAP[y] for y in TARGET_YEARS}

print(f"\nLoading ORIGINAL s_dict (Crossover=0)...")
print(f"  File: {ORIG_S_DICT.name}")
orig_data = load_s_dict_by_year_geo(ORIG_S_DICT, target_idxs, prkg_idx_map)

print(f"\nLoading V2 s_dict (Crossover enabled)...")
print(f"  File: {V2_S_DICT.name}")
v2_data = load_s_dict_by_year_geo(V2_S_DICT, target_idxs, prkg_idx_map)

# ── 4. Summary statistics ────────────────────────────────────────────
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

for year in TARGET_YEARS:
    yi = YEAR_IDX_MAP[year]
    orig_by_geo = orig_data[yi]
    v2_by_geo = v2_data[yi]

    total_orig_gwh = sum(orig_by_geo.values()) / 1e6
    total_v2_gwh = sum(v2_by_geo.values()) / 1e6

    print(f"\nYear {year} (index {yi}):")
    print(f"  Original (Crossover=0):  {total_orig_gwh:10.4f} GWh  "
          f"({len(orig_by_geo)} nodes with BEV charging)")
    print(f"  V2 (Crossover enabled):  {total_v2_gwh:10.4f} GWh  "
          f"({len(v2_by_geo)} nodes with BEV charging)")
    print(f"  Delta (V2 - Orig):       {total_v2_gwh - total_orig_gwh:+10.4f} GWh  "
          f"({(total_v2_gwh/total_orig_gwh - 1)*100:+.2f}%)" if total_orig_gwh > 0
          else f"  Delta: N/A")

    # Correlation by latitude
    all_geos = sorted(set(orig_by_geo.keys()) | set(v2_by_geo.keys()))
    if len(all_geos) > 2:
        orig_vals = np.array([orig_by_geo.get(g, 0) for g in all_geos])
        v2_vals   = np.array([v2_by_geo.get(g, 0) for g in all_geos])
        r, p = pearsonr(orig_vals, v2_vals)
        print(f"  Pearson correlation (by node): r = {r:.6f}, p = {p:.2e}")

        # Also compute correlation on latitude-binned values
        lat_bins = np.arange(42, 71, 1)
        orig_lat_binned = np.zeros(len(lat_bins) - 1)
        v2_lat_binned = np.zeros(len(lat_bins) - 1)
        for g in all_geos:
            lat = geo_lat.get(g, None)
            if lat is None:
                continue
            bin_idx = np.searchsorted(lat_bins, lat) - 1
            if 0 <= bin_idx < len(lat_bins) - 1:
                orig_lat_binned[bin_idx] += orig_by_geo.get(g, 0)
                v2_lat_binned[bin_idx] += v2_by_geo.get(g, 0)

        nonzero = (orig_lat_binned > 0) | (v2_lat_binned > 0)
        if nonzero.sum() > 2:
            r_lat, p_lat = pearsonr(orig_lat_binned[nonzero], v2_lat_binned[nonzero])
            print(f"  Pearson correlation (1-deg lat bins): r = {r_lat:.6f}, p = {p_lat:.2e}")

# ── 5. Build latitude profiles ───────────────────────────────────────
def build_latitude_profile(data_by_geo, geo_lat, bin_edges):
    """Aggregate kWh into latitude bins, return (bin_centers, values_gwh)."""
    n = len(bin_edges) - 1
    vals = np.zeros(n)
    for g, kwh in data_by_geo.items():
        lat = geo_lat.get(g, None)
        if lat is None:
            continue
        bi = np.searchsorted(bin_edges, lat) - 1
        if 0 <= bi < n:
            vals[bi] += kwh
    centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    return centers, vals / 1e6  # convert kWh -> GWh


lat_bins = np.arange(41.5, 70.5, 1.0)  # 1-degree bins from 41.5 to 69.5

# ── 6. Create figure ─────────────────────────────────────────────────
print("\nCreating comparison figure...")

fig, axes = plt.subplots(len(TARGET_YEARS), 3,
                         figsize=(14, 4.5 * len(TARGET_YEARS)),
                         gridspec_kw={'width_ratios': [1, 1, 0.8]})

if len(TARGET_YEARS) == 1:
    axes = axes[np.newaxis, :]

COLOR_ORIG = '#2c3e50'    # dark blue-grey
COLOR_V2   = '#c0392b'    # red
COLOR_DELTA = '#27ae60'   # green

for row, year in enumerate(TARGET_YEARS):
    yi = YEAR_IDX_MAP[year]
    orig_by_geo = orig_data[yi]
    v2_by_geo = v2_data[yi]

    centers_orig, gwh_orig = build_latitude_profile(orig_by_geo, geo_lat, lat_bins)
    centers_v2, gwh_v2 = build_latitude_profile(v2_by_geo, geo_lat, lat_bins)

    # Smooth for visual clarity
    sigma = 1.2
    gwh_orig_smooth = gaussian_filter1d(gwh_orig, sigma=sigma)
    gwh_v2_smooth = gaussian_filter1d(gwh_v2, sigma=sigma)
    gwh_delta = gwh_v2 - gwh_orig
    gwh_delta_smooth = gaussian_filter1d(gwh_delta, sigma=sigma)

    # ── Panel 1: Original (Crossover=0) ──
    ax1 = axes[row, 0]
    ax1.fill_betweenx(centers_orig, 0, gwh_orig_smooth,
                       color=COLOR_ORIG, alpha=0.4, zorder=2)
    ax1.plot(gwh_orig_smooth, centers_orig,
             color=COLOR_ORIG, linewidth=2, alpha=0.9, zorder=3)
    ax1.set_title(f'{year} -- Crossover = 0 (original)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('BEV Charging (GWh)', fontsize=11)
    ax1.set_ylabel('Latitude ($\\degree$N)', fontsize=11)

    # ── Panel 2: V2 (Crossover enabled) ──
    ax2 = axes[row, 1]
    ax2.fill_betweenx(centers_v2, 0, gwh_v2_smooth,
                       color=COLOR_V2, alpha=0.4, zorder=2)
    ax2.plot(gwh_v2_smooth, centers_v2,
             color=COLOR_V2, linewidth=2, alpha=0.9, zorder=3)
    ax2.set_title(f'{year} -- Crossover enabled (v2)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('BEV Charging (GWh)', fontsize=11)

    # Share y-axis range and x-axis range for panels 1 & 2
    xmax = max(gwh_orig_smooth.max(), gwh_v2_smooth.max()) * 1.15
    for ax in [ax1, ax2]:
        ax.set_xlim(0, xmax)
        ax.set_ylim(42, 68)
        ax.grid(True, alpha=0.25, linestyle='--')
        ax.tick_params(labelsize=10)

    # ── Panel 3: Delta (V2 - Original) ──
    ax3 = axes[row, 2]
    # Color positive and negative differently
    pos_mask = gwh_delta_smooth >= 0
    neg_mask = gwh_delta_smooth < 0
    ax3.fill_betweenx(centers_orig, 0, gwh_delta_smooth,
                       where=pos_mask,
                       color='#e74c3c', alpha=0.4, label='V2 > Orig', zorder=2)
    ax3.fill_betweenx(centers_orig, 0, gwh_delta_smooth,
                       where=neg_mask,
                       color='#3498db', alpha=0.4, label='Orig > V2', zorder=2)
    ax3.plot(gwh_delta_smooth, centers_orig,
             color='#333', linewidth=1.5, alpha=0.8, zorder=3)
    ax3.axvline(0, color='grey', linewidth=0.8, linestyle='-', alpha=0.5)
    ax3.set_title(f'{year} -- Delta (V2 $-$ Orig)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('$\\Delta$ Charging (GWh)', fontsize=11)
    ax3.set_ylim(42, 68)
    ax3.grid(True, alpha=0.25, linestyle='--')
    ax3.tick_params(labelsize=10)
    ax3.legend(fontsize=8, loc='upper right', framealpha=0.9)

    # ── Add country labels to all panels ──
    country_label_lats = {
        'IT': 44.0,
        'AT': 47.5,
        'DE': 51.0,
        'DK': 56.0,
        'SE': 62.0,
        'NO': 65.0,
    }
    for ax in [ax1, ax2, ax3]:
        for country, lat in country_label_lats.items():
            ax.text(1.02, lat, country,
                    transform=ax.get_yaxis_transform(),
                    fontsize=9, fontweight='bold', va='center', ha='left',
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                              edgecolor='#888', alpha=0.85, linewidth=0.8),
                    zorder=10)
        # Add faint horizontal lines at approximate borders
        for border_lat in [46.5, 48.5, 54.5, 57.5]:
            ax.axhline(border_lat, color='gray', linestyle=':', alpha=0.3, linewidth=0.7)

fig.suptitle('BEV Charging Demand by Latitude: Crossover=0 vs Crossover Enabled\n'
             'Scenario 000 (Go RES), Scandinavian-Mediterranean Corridor',
             fontsize=14, fontweight='bold', y=1.02)

plt.tight_layout()

out_pdf = FIG_DIR / 'crossover_vs_nocrossover_latitude.pdf'
out_png = FIG_DIR / 'crossover_vs_nocrossover_latitude.png'
plt.savefig(str(out_pdf), format='pdf', bbox_inches='tight', dpi=150)
plt.savefig(str(out_png), format='png', bbox_inches='tight', dpi=200)
print(f"\nSaved: {out_pdf}")
print(f"Saved: {out_png}")
plt.close()

# ── 7. Detailed per-latitude-bin comparison table ────────────────────
print("\n" + "=" * 80)
print("DETAILED LATITUDE-BIN COMPARISON")
print("=" * 80)

for year in TARGET_YEARS:
    yi = YEAR_IDX_MAP[year]
    orig_by_geo = orig_data[yi]
    v2_by_geo = v2_data[yi]
    centers, gwh_orig_raw = build_latitude_profile(orig_by_geo, geo_lat, lat_bins)
    _, gwh_v2_raw = build_latitude_profile(v2_by_geo, geo_lat, lat_bins)

    print(f"\n--- Year {year} ---")
    print(f"{'Lat band':>12}  {'Orig (GWh)':>12}  {'V2 (GWh)':>12}  {'Delta (GWh)':>12}  {'Delta %':>10}")
    print("-" * 62)
    for i, c in enumerate(centers):
        o = gwh_orig_raw[i]
        v = gwh_v2_raw[i]
        d = v - o
        pct = (d / o * 100) if o > 1e-8 else float('nan')
        if o > 1e-6 or v > 1e-6:
            pct_str = f"{pct:+.1f}%" if not np.isnan(pct) else "N/A"
            print(f"  {c-0.5:.0f}-{c+0.5:.0f} N  {o:12.4f}  {v:12.4f}  {d:+12.4f}  {pct_str:>10}")

    total_o = gwh_orig_raw.sum()
    total_v = gwh_v2_raw.sum()
    total_d = total_v - total_o
    total_pct = (total_d / total_o * 100) if total_o > 1e-8 else float('nan')
    print("-" * 62)
    pct_str = f"{total_pct:+.1f}%" if not np.isnan(total_pct) else "N/A"
    print(f"  {'TOTAL':>7}  {total_o:12.4f}  {total_v:12.4f}  {total_d:+12.4f}  {pct_str:>10}")

print("\nDone.")
