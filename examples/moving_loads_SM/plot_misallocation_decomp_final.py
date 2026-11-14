"""
Extended Figure 5 (final base case): infrastructure effects vs spatial cost differences.
(a) Heuristic vs system-optimal charging capacity for two runs, each compared with the heuristic built from its own BET flows:
    'Uniform costs'  - electricity prices and grid charges spatially uniform (mean of the 7 countries) -> infrastructure effects only
    'Full model'     - base case with country-specific prices and grid charges
    Bottom (solid): capacity at the same locations as the heuristic; top (hatched): differently allocated.
(b) Latitudinal distribution of charging demand: heuristic, system-optimal with uniform costs, system-optimal (full).
"""
import re, yaml, glob, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from collections import defaultdict
from scipy.ndimage import gaussian_filter1d
from heuristic_charging import compute_heuristic_charging

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI', 'sans-serif']
matplotlib.rcParams['font.size'] = 15

TARGET_YEAR = int(os.environ.get('YEAR', '2040'))
RUN_FULL = 'results/final/uncertainty_scenarios/scenario_000'
RUN_UNI = 'results/final/sensitivity/uniform_spatial_costs'
RUN_MCS = 'results/final/sensitivity/mcs_only'

geo_data = yaml.safe_load(open('input_data/fixed_nuts_2/GeographicElement.yaml'))
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}
all_geo_ids = [g['id'] for g in geo_data if g.get('type') == 'node']
inp = 'input_data/uncertainty_scenarios_v2_night/scenario_000/'
paths = yaml.load(open(inp + 'Path.yaml'), Loader=yaml.UnsafeLoader)
odpairs_raw = yaml.load(open(inp + 'Odpair.yaml'), Loader=yaml.UnsafeLoader)
breaks_data = yaml.load(open(inp + 'MandatoryBreaks.yaml'), Loader=yaml.UnsafeLoader)
path_seq = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist = {int(p['id']): [float(d) for d in p.get('distance_from_previous', [])] for p in paths}
od_path = {int(od['id']): int(od['path_id']) for od in odpairs_raw}
breaks_by_path = defaultdict(list)
is_rest = {}
for b in breaks_data:
    breaks_by_path[int(b['path_id'])].append(int(b['latest_geo_id']))
    is_rest[(int(b['path_id']), int(b['latest_geo_id']))] = b['break_duration'] >= 8.0

gamma_ccs, gamma_mcs = 0.75, 0.23
MODELED_YEARS = list(range(2020, 2064, 4))
y_idx_to_year = {i + 1: y for i, y in enumerate(MODELED_YEARS)}
tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')
ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')


def load(run, mcs_only=False):
    """optimal energy/capacity per node and the heuristic built from the run's own BET route energy"""
    opt_energy, route_energy = defaultdict(float), defaultdict(float)
    for line in open(sorted(glob.glob(run + '/*_s_dict.yaml'))[-1]):
        m = tuple_pat.match(line.strip())
        if not m or int(m.group(1)) != TARGET_YEAR: continue
        val = float(m.group(10))
        if val < 1e-6 or int(m.group(7)) != 0 or int(m.group(8)) not in {1, 2}: continue
        opt_energy[int(m.group(5))] += val
        route_energy[(int(m.group(3)), int(m.group(4)))] += val
    heur_energy, h_ccs, h_mcs = defaultdict(float), defaultdict(float), defaultdict(float)
    for (oid, pid), te in route_energy.items():
        actual_pid = od_path.get(oid, pid)
        for g, mwh in compute_heuristic_charging(oid, pid, te, od_path, path_seq, path_dist, breaks_by_path).items():
            heur_energy[g] += mwh
            if is_rest.get((actual_pid, g), False) and not mcs_only: h_ccs[g] += mwh / (gamma_ccs * 8760)
            else: h_mcs[g] += mwh / (gamma_mcs * 8760)
    o_ccs, o_mcs = defaultdict(float), defaultdict(float)
    for line in open(sorted(glob.glob(run + '/*_q_fuel_infr_plus_dict.yaml'))[-1]):
        m = ci3_pat.match(line.strip())
        if not m: continue
        yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
        val = float(m.group(4))
        if val < 1e-3 or fi == 3: continue
        yr = y_idx_to_year.get(yi)
        if yr and yr <= TARGET_YEAR:
            # fi=2 -> CCS, fi=1 -> MCS (see memory: q-fuel-infr-plus-yaml-parsing)
            if fi == 2: o_ccs[pos - 1] += val / 1000
            elif fi == 1: o_mcs[pos - 1] += val / 1000
    cons_ccs = sum(min(o_ccs.get(g, 0), h_ccs.get(g, 0)) for g in all_geo_ids)
    cons_mcs = sum(min(o_mcs.get(g, 0), h_mcs.get(g, 0)) for g in all_geo_ids)
    r = dict(opt_energy=opt_energy, heur_energy=heur_energy,
             h_ccs=sum(h_ccs.values()), h_mcs=sum(h_mcs.values()),
             cons_ccs=cons_ccs, cons_mcs=cons_mcs,
             diff_ccs=sum(o_ccs.values()) - cons_ccs, diff_mcs=sum(o_mcs.values()) - cons_mcs)
    r['h_tot'] = r['h_ccs'] + r['h_mcs']
    r['o_tot'] = sum(o_ccs.values()) + sum(o_mcs.values())
    print(f"{run}: heuristic {r['h_tot']:.0f} MW | optimal {r['o_tot']:.0f} MW ({(r['o_tot']/r['h_tot']-1)*100:+.0f}%) "
          f"| differently allocated {r['diff_ccs']+r['diff_mcs']:.0f} MW ({(r['diff_ccs']+r['diff_mcs'])/r['o_tot']*100:.0f}%)")
    return r


mcs, full = load(RUN_MCS, mcs_only=True), load(RUN_FULL)

fig, axes = plt.subplots(1, 2, figsize=(14, 6.8), gridspec_kw={'width_ratios': [1.35, 1]})
CCS_COL, MCS_COL = '#d4a017', '#5b4fa8'
COL_OPT, COL_HEUR, COL_UNI = '#1a5276', '#c4956a', '#5dade2'

# ── Panel (a) ──
ax = axes[0]
bar_w = 0.7
xs = {'mcs': (0, 0.9), 'full': (2.3, 3.2)}
top = max(r[k] for r in (mcs, full) for k in ('h_tot', 'o_tot'))
for key, r in [('mcs', mcs), ('full', full)]:
    xh, xo = xs[key]
    ax.bar(xh, r['h_ccs'], bar_w, color=CCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.bar(xh, r['h_mcs'], bar_w, bottom=r['h_ccs'], color=MCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.bar(xo, r['cons_ccs'], bar_w, color=CCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.bar(xo, r['cons_mcs'], bar_w, bottom=r['cons_ccs'], color=MCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)
    b = r['cons_ccs'] + r['cons_mcs']
    ax.bar(xo, r['diff_ccs'], bar_w, bottom=b, color=CCS_COL, alpha=0.3, edgecolor=CCS_COL, linewidth=1.0, hatch='///')
    ax.bar(xo, r['diff_mcs'], bar_w, bottom=b + r['diff_ccs'], color=MCS_COL, alpha=0.3, edgecolor=MCS_COL, linewidth=1.0, hatch='///')
    ax.text(xh, r['h_tot'] + top * 0.01, f"{r['h_tot']:.0f} MW", ha='center', va='bottom', fontsize=13, fontweight='bold')
    ax.text(xo, r['o_tot'] + top * 0.01, f"{r['o_tot']:.0f} MW\n({(r['o_tot']/r['h_tot']-1)*100:+.0f}%)",
            ha='center', va='bottom', fontsize=13, fontweight='bold')
    d = r['diff_ccs'] + r['diff_mcs']
    ax.text(xo, r['o_tot'] - d / 2, f"{d:.0f} MW\n({d/r['o_tot']*100:.0f}%)", ha='center', va='center', fontsize=11,
            color='#333', fontweight='bold')
ax.set_xticks([*xs['mcs'], *xs['full']])
ax.set_xticklabels(['Heuristic', 'System-\noptimal'] * 2, fontsize=12)
for key, txt in [('mcs', 'One charger type\n(MCS only)'), ('full', 'Two charger types\n(MCS and CCS, full model)')]:
    ax.text(np.mean(xs[key]), -top * 0.2, txt, ha='center', va='top', fontsize=12, fontstyle='italic')
ax.axvline(1.6, color='gray', lw=0.8, ls=':')
ax.set_ylabel('Cumulative charging infrastructure (MW)', fontsize=14)
ax.set_title(f'(a) Charging infrastructure allocation\n(Go RES, {TARGET_YEAR})', fontsize=16)
ax.set_ylim(0, top * 1.18)
ax.grid(True, alpha=0.15, axis='y')
ax.legend(handles=[
    Patch(facecolor=CCS_COL, alpha=0.85, label='CCS (overnight)'),
    Patch(facecolor=MCS_COL, alpha=0.85, label='MCS (megawatt)'),
    Patch(facecolor=CCS_COL, alpha=0.3, hatch='///', edgecolor=CCS_COL, label='CCS differently allocated'),
    Patch(facecolor=MCS_COL, alpha=0.3, hatch='///', edgecolor=MCS_COL, label='MCS differently allocated'),
], fontsize=10, loc='upper center', bbox_to_anchor=(0.5, -0.27), ncol=2, framealpha=0.9)

# ── Panel (b) ──
ax = axes[1]
country_lats = {'IT': 42.5, 'AT': 47.5, 'DE': 51.0, 'DK': 56.0, 'SE': 62.0, 'NO': 64.0}
for label, geo_dict, color, ls, lw in [
    ('System-optimal (full model)', full['opt_energy'], COL_OPT, '-', 2.0),
    ('System-optimal (MCS only)', mcs['opt_energy'], '#7d3c98', ':', 2.0),
    ('Heuristic', full['heur_energy'], COL_HEUR, '--', 1.8),
]:
    e_by_lat = defaultdict(float)
    for gid, mwh in geo_dict.items():
        if geo_lat.get(gid) is not None: e_by_lat[geo_lat[gid]] += mwh
    lats = np.array(sorted(e_by_lat))
    vals = np.array([e_by_lat[l] for l in lats])
    vals_smooth = gaussian_filter1d(vals / vals.sum() * 100, 1.2)
    ax.fill_betweenx(lats, 0, vals_smooth, alpha=0.12, color=color)
    ax.plot(vals_smooth, lats, color=color, linewidth=lw, linestyle=ls, label=label)
ax.set_ylabel('Latitude')
ax.set_xlabel('Share of total charging demand (%)')
ax.set_title(f'(b) Latitudinal distribution of charging\n(Go RES, {TARGET_YEAR})', fontsize=14)
ax.legend(fontsize=10, loc='upper center')
ax.grid(True, alpha=0.2)
for c, lat in country_lats.items():
    ax.axhline(y=lat, color='gray', linestyle=':', alpha=0.3, linewidth=0.5)
    ax.text(ax.get_xlim()[1] * 0.95, lat, c, fontsize=10, ha='right', va='center', color='gray')

plt.tight_layout()
for ext in ('pdf', 'png'):
    plt.savefig(f'figures/misallocation_decomp_final.{ext}', bbox_inches='tight', dpi=300)
print('Saved: figures/misallocation_decomp_final.pdf/.png')
