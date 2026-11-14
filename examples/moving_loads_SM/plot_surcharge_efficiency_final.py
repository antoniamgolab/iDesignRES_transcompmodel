"""
Surcharge efficiency (v4 runs: v3 + BET sales-share cap): demand reduction and infrastructure response at the
surcharged target node vs levelized cost increase, read directly from model results.

v3 = corrected objective + time-of-day prices, 30 % charging markup, Go RES baseline
     (results/uncertainty_scenarios_v2_night/scenario_000).
Surcharge runs: results/v4/surcharge/<target>_<case>  (inputs input_data/surcharge_v3/<case>)

Levelization (same method as plot_surcharge_efficiency.py):
  electricity surcharge  : +s ct/kWh  -> +s ct/kWh
  grid-charge surcharge  : +s EUR/kW/yr -> s / (gamma_MCS * 8760) * 100 ct/kWh
  (gamma_MCS only; with gamma_CCS the same surcharge levelizes ~3x lower)

q_fuel_infr_plus CartesianIndex(yi, fi, pos): fi=1 MCS, fi=2 CCS, fi=3 diesel (skip),
pos-1 = geo id, yi 1..11 -> 2020..2060 step 4; values are kW additions (cumulative = sum yrs <= YEAR).

A target node is plotted only once all its runs are complete (q + s + summary_stats present),
so ITH1 is added automatically when results/v4/surcharge/ith1_* finish.

Usage: python plot_surcharge_efficiency_v4.py [--old]   (--old also prints the pre-v3 AT33 runs)
"""
import re, sys, glob, json
from pathlib import Path
from collections import defaultdict
import yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({"font.family": "sans-serif",
                     "font.sans-serif": ["Segoe UI", "sans-serif"], "font.size": 15})

BASE = Path(__file__).resolve().parent
FIG_DIR = BASE / 'figures'
CACHE = FIG_DIR / 'surcharge_efficiency_final_data.json'
YEAR = 2040
YEARS = list(range(2020, 2064, 4))

BASELINE_DIR = BASE / 'results' / 'final' / 'uncertainty_scenarios' / 'scenario_000'
RUN_DIR = BASE / 'results' / 'final' / 'surcharge'
INPUT_DIR = BASE / 'input_data' / 'surcharge_final'

TARGETS = {'AT33': 2, 'ITH1': 58}    # NUTS-2 -> geo id
ELEC_CASES = [('elec_low', 1), ('elec_med', 2), ('elec_high', 4), ('elec_extreme', 6),
              ('elec_8ct', 8), ('elec_10ct', 10), ('elec_15ct', 15)]           # ct/kWh
NET_CASES = [('network_low', 2), ('network_med', 5), ('network_high', 10),
             ('network_20', 20), ('network_50', 50)]                          # EUR/kW/yr
BORDER = ['AT33', 'AT34', 'DE14', 'DE21', 'DE27', 'ITC4', 'ITH1', 'ITH2', 'ITH3']

ELEC_COL = '#e07b54'
NET_COL = '#4a90a4'

S_PAT = re.compile(r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*'
                   r'\((\d+),\s*(\d+)\),\s*(\d+)\):\s*"?([\d.eE+-]+)"?')
Q_PAT = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*"?([\d.eE+-]+)"?')
# pre-v3 surcharge runs write (year, (fuel, infr_id), geo_id): real FuelingInfrTypes ids (1=CCS, 2=MCS)
Q_OLD_PAT = re.compile(r'\((\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*"?([\d.eE+-]+)"?')

with open(BASE / 'input_data' / 'fixed_nuts_2' / 'GeographicElement.yaml') as f:
    _geo = yaml.safe_load(f)
GEO_N2 = {int(g['id']): g.get('nuts2_region', '') for g in _geo if g.get('type') == 'node'}


def gamma(infr_id, case_dir):
    with open(case_dir / 'FuelingInfrTypes.yaml') as f:
        for e in yaml.load(f, Loader=yaml.CSafeLoader):
            if e['id'] == infr_id:
                return float(e['gamma'][YEAR - 2020])


def newest(folder, suffix):
    files = sorted(Path(folder).glob(f'*{suffix}'))
    return files[-1] if files else None


def complete(folder):
    return all(newest(folder, s) for s in ('_s_dict.yaml', '_q_fuel_infr_plus_dict.yaml')) \
        and (Path(folder) / 'summary_stats.yaml').exists()


def load_run(folder, target_geo):
    """Energy (GWh) per border NUTS-2 in YEAR, target-node energy by type, MW at target, BEV share."""
    e_n2 = defaultdict(float)
    e_tgt = {'CCS': 0.0, 'MCS': 0.0}
    with open(newest(folder, '_s_dict.yaml')) as f:
        for line in f:
            m = S_PAT.match(line.strip())
            if not m or int(m.group(1)) != YEAR:
                continue
            fuel, infr, val = int(m.group(7)), int(m.group(8)), float(m.group(10))
            if fuel != 0 or infr not in (1, 2) or val <= 0:
                continue
            gid = int(m.group(5))
            n2 = GEO_N2.get(gid, '')
            if n2 in BORDER:
                e_n2[n2] += val / 1000            # MWh -> GWh
            if gid == target_geo:
                e_tgt['CCS' if infr == 1 else 'MCS'] += val / 1000   # s-dict uses real infr ids
    mw = {'MCS': 0.0, 'CCS': 0.0}
    with open(newest(folder, '_q_fuel_infr_plus_dict.yaml')) as f:
        for line in f:
            m = Q_PAT.match(line.strip())
            if not m:
                mo = Q_OLD_PAT.match(line.strip())
                if mo and int(mo.group(2)) == 0 and int(mo.group(4)) == target_geo and int(mo.group(1)) <= YEAR:
                    mw['CCS' if int(mo.group(3)) == 1 else 'MCS'] += float(mo.group(5)) / 1000
                continue
            yi, fi, pos, val = int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4))
            if fi == 3 or pos - 1 != target_geo or YEARS[yi - 1] > YEAR:
                continue
            mw['MCS' if fi == 1 else 'CCS'] += val / 1000      # kW -> MW
    bev_share = None
    ss = Path(folder) / 'summary_stats.yaml'
    if ss.exists():
        with open(ss) as f:
            t = (yaml.safe_load(f) or {}).get('tonnes_by_year', {}).get(YEAR)
    if t:
        bev, icev = float(t['BEV']), float(t['ICEV'])
        bev_share = bev / (bev + icev) * 100
    return {'gwh_n2': dict(e_n2), 'gwh_tgt': e_tgt, 'gwh': sum(e_tgt.values()),
            'mcs': mw['MCS'], 'ccs': mw['CCS'], 'bev_share': bev_share}


def collect():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    data = {}
    for node, gid in TARGETS.items():
        folders = {c: RUN_DIR / f'{node.lower()}_{c}' for c, _ in ELEC_CASES + NET_CASES}
        if not all(complete(p) for p in folders.values()):
            print(f'{node}: runs incomplete -> skipped')
            continue
        d = {}
        for key, folder in [('baseline', BASELINE_DIR)] + list(folders.items()):
            ck = f'{node}|{key}|{newest(folder, "_s_dict.yaml").name}'
            if ck not in cache:
                cache[ck] = load_run(folder, gid)
            d[key] = cache[ck]
        data[node] = d
    CACHE.write_text(json.dumps(cache, indent=1))
    return data


def levelized(data_node, node):
    g_mcs = gamma(2, INPUT_DIR / f'{node.lower()}_network_50')
    g_ccs = gamma(1, INPUT_DIR / f'{node.lower()}_network_50')
    net_ct = lambda s: s / (g_mcs * 8760) * 100
    return g_mcs, g_ccs, net_ct


def report(data):
    for node, d in data.items():
        g_mcs, g_ccs, net_ct = levelized(d, node)
        bl = d['baseline']
        print(f'\n=== {node} ({YEAR}) gamma_MCS={g_mcs} gamma_CCS={g_ccs}; '
              f'+50 EUR/kW/yr = {net_ct(50):.2f} ct/kWh (MCS) / {50/(g_ccs*8760)*100:.2f} (CCS)')
        print(f'baseline: {bl["gwh"]:.1f} GWh (CCS {bl["gwh_tgt"]["CCS"]:.1f}, MCS {bl["gwh_tgt"]["MCS"]:.1f}), '
              f'MCS {bl["mcs"]:.1f} MW, CCS {bl["ccs"]:.1f} MW, BEV {bl["bev_share"]:.2f} %')
        print(f'{"case":14s}{"lev ct":>7s}{"GWh":>7s}{"red%":>7s}{"MCS MW":>8s}{"CCS MW":>8s}{"BEV%":>7s}  '
              + ' '.join(f'{r:>6s}' for r in BORDER))
        for cases, conv in ((ELEC_CASES, lambda s: s), (NET_CASES, net_ct)):
            for c, s in cases:
                r = d[c]
                red = (bl['gwh'] - r['gwh']) / bl['gwh'] * 100
                print(f'{c:14s}{conv(s):7.2f}{r["gwh"]:7.1f}{red:7.1f}{r["mcs"]:8.1f}{r["ccs"]:8.1f}'
                      f'{r["bev_share"]:7.2f}  ' + ' '.join(f'{r["gwh_n2"].get(n, 0):6.1f}' for n in BORDER))
        print(f'{"baseline":14s}{"":7s}{"":7s}{"":7s}{"":8s}{"":8s}{"":7s}  '
              + ' '.join(f'{bl["gwh_n2"].get(n, 0):6.1f}' for n in BORDER))


def plot(data):
    nodes = list(data)
    fig, axes = plt.subplots(3, len(nodes), figsize=(7.5 * len(nodes), 10), sharex='col', squeeze=False,
                             gridspec_kw={'hspace': 0.25, 'height_ratios': [1.2, 1, 1]})
    for col, node in enumerate(nodes):
        d = data[node]
        bl = d['baseline']
        _, _, net_ct = levelized(d, node)
        series = [('Surcharge to electricity price', ELEC_COL, 'o', ELEC_CASES, lambda s: s),
                  ('Surcharge to grid charge', NET_COL, 's', NET_CASES, net_ct)]
        ax_top, ax_mcs, ax_ccs = axes[:, col]
        for lab, colr, mk, cases, conv in series:
            x = [0] + [conv(s) for _, s in cases]
            red = [0] + [(bl['gwh'] - d[c]['gwh']) / bl['gwh'] * 100 for c, _ in cases]
            mcs = [bl['mcs']] + [d[c]['mcs'] for c, _ in cases]
            ccs = [bl['ccs']] + [d[c]['ccs'] for c, _ in cases]
            ax_top.plot(x, red, mk + '-', color=colr, ms=7, lw=2, label=lab, zorder=4)
            ax_mcs.plot(x, mcs, mk + '-', color=colr, ms=7, lw=2, label=lab, zorder=4)
            ax_ccs.plot(x, ccs, mk + '-', color=colr, ms=7, lw=2, label=lab, zorder=4)
            unit = 'ct/kWh' if cases is ELEC_CASES else 'EUR/kW/yr'
            show = (1, 2, 4) if cases is ELEC_CASES else (20, 50)
            off = (7, -12) if cases is ELEC_CASES else (-40, 10)
            for (c, s), xi, yi in zip(cases, x[1:], red[1:]):
                if s in show:
                    ax_top.annotate(f'+{s} {unit}', (xi, yi), textcoords='offset points',
                                    xytext=(-70, -14) if (cases is ELEC_CASES and s == 4) else off, fontsize=9, color=colr)
        for ax, key, name in ((ax_mcs, 'mcs', 'MCS'), (ax_ccs, 'ccs', 'CCS')):
            ax.plot(0, bl[key], 'X', color='#333', ms=11, mew=2, zorder=6,
                    label=f'Baseline ({bl[key]:.1f} MW)')
            ax.set_ylim(bottom=-0.5)
            ax.grid(alpha=0.3)
            ax.legend(fontsize=9, loc='upper right')
        ax_top.set_title(f'Surcharge in {node}  (baseline {bl["gwh"]:.1f} GWh)', fontsize=16, fontweight='bold')
        ax_top.set_ylim(-3, 103)
        ax_top.grid(alpha=0.3)
        ax_top.legend(fontsize=10, loc='lower right')
        ax_ccs.set_xlabel('Levelized cost increase (ct/kWh)', fontsize=14)
        ax_ccs.set_xlim(-0.12, 4.4)
    axes[0, 0].set_ylabel('Charging demand\nreduction (%)', fontsize=14)
    axes[1, 0].set_ylabel('MCS capacity at\ntarget node (MW)', fontsize=14)
    axes[2, 0].set_ylabel('CCS capacity at\ntarget node (MW)', fontsize=14)
    fig.suptitle(f'Impact of locational electricity-price surcharges and higher grid charges on the\n'
                 f'charging demand allocation at a target NUTS-2 node ({YEAR})', fontsize=16, y=1.02)
    plt.tight_layout()
    for ext in ('png', 'pdf'):
        plt.savefig(str(FIG_DIR / f'surcharge_efficiency_comparison_final.{ext}'), bbox_inches='tight', dpi=300)
    print('Saved: figures/surcharge_efficiency_comparison_final.png/.pdf')
    plt.close()


def report_old():
    """Pre-v3 AT33 runs (results/at33_surcharge, baseline uncertainty_scenarios_v2) for comparison."""
    old = {'baseline': load_run(BASE / 'results' / 'uncertainty_scenarios_v2' / 'scenario_000', 2)}
    for c, _ in ELEC_CASES + NET_CASES:
        old[c] = load_run(BASE / 'results' / 'at33_surcharge' / f'at33_{c}', 2)
    print('\n=== OLD AT33 runs (correct fi mapping) ===')
    for k, r in old.items():
        print(f'{k:14s}{r["gwh"]:7.1f} GWh  MCS {r["mcs"]:5.1f}  CCS {r["ccs"]:5.1f}  '
              + ' '.join(f'{n}:{r["gwh_n2"].get(n, 0):.1f}' for n in ('AT33', 'ITC4', 'DE21', 'ITH1')))


if __name__ == '__main__':
    FIG_DIR.mkdir(exist_ok=True)
    data = collect()
    report(data)
    if '--old' in sys.argv:
        report_old()
    if data:
        plot(data)
