"""
Robustness figure (new Section 5.3): System-optimal vs Heuristic benchmark across the four energy system scenarios and all
sensitivity variants of the Go RES base case. Input: results/final/robustness_table.json (robustness_table_final.py).
(a) share of System-optimal capacity located differently from the Heuristic benchmark
(b) System-optimal vs Heuristic benchmark capacity
(c) AT33+ITH1 share of corridor charging demand, System-optimal minus Heuristic benchmark (pp)
Filled markers: 2040, open markers: 2048.
"""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI', 'sans-serif']
matplotlib.rcParams['font.size'] = 15

d = {r['run']: r for r in json.load(open('results/final/robustness_table.json'))}
GROUPS = [
    ('Energy system scenario', [('base', 'Go RES (base case)'), ('scen_1', 'NECP'), ('scen_2', 'REPowerEU++'), ('scen_3', 'Trinity')]),
    ('Charging infrastructure', [('cx400', 'Grid connection 0 €/kW'), ('cx650', 'Grid connection 250 €/kW'),
                                 ('kappa_pwr_0.3', r'$\kappa^{\mathrm{pwr}}$ = 0.3'), ('kappa_pwr_1.0', r'$\kappa^{\mathrm{pwr}}$ = 1.0'),
                                 ('kspace_cum_0.002', r'$\kappa^{\mathrm{space}}$ = 0.002'), ('kspace_cum_0.008', r'$\kappa^{\mathrm{space}}$ = 0.008'),
                                 ('no_space_cap', 'No space cap'),
                                 ('gamma_m25', r'$\gamma_l$ $-$25 %'), ('gamma_p25', r'$\gamma_l$ +25 %'), ('mcs_only', 'MCS only')]),
    ('Charging costs', [('uniform_prices', 'No time-of-day prices'), ('gc_x2.5', r'Grid charges $\times$2.5'), ('gc_x5', r'Grid charges $\times$5')]),
    ('Fleet and demand', [('bat_low_70pct', r'Battery $-$30 %'), ('bat_high_130pct', 'Battery +30 %'),
                          ('high_start_70_50', 'SOC 70/50 %'), ('low_start_30_50', 'SOC 30/50 %'), ('high_end_50_70', 'SOC 50/70 %'),
                          ('low_end_50_30', 'SOC 50/30 %'), ('loose_70_30', 'SOC 70/30 %'), ('tight_30_70', 'SOC 30/70 %'),
                          ('freight_low', r'Freight growth $-$50 %'), ('freight_high', 'Freight growth +50 %')]),
    ('Shift to rail', [('base_rail', 'With shift to rail'), ('rail_growth_2pp', 'Rail growth 2 pp'),
                       ('rail_growth_5pp', 'Rail growth 5 pp'), ('rail_cap_20', 'Max. rail share 20 %'),
                       ('rail_cost_0.04', 'Rail cost 0.04 EUR/tkm'), ('rail_cost_0.08', 'Rail cost 0.08 EUR/tkm')]),
]
METRICS = [('ld', '(a) Capacity located\ndifferently (%)', None),
           ('dcap', '(b) Difference in total\ncapacity (%)', 0),
           ('br', '(c) Difference in demand\nshare at AT33+ITH1 (pp)', 0)]
val = lambda r, y, k: r[y]['brenner_e'] - r[y]['brenner_h'] if k == 'br' else r[y][k]

rows, ylab, gpos = [], [], []
y = 0
for g, items in GROUPS:
    gpos.append((y, g)); y += 1
    for k, lab in items:
        rows.append((y, k)); ylab.append((y, lab)); y += 1
    y += 0.4
COL = {'2040': '#1a5276', '2048': '#c0392b'}

fig, axes = plt.subplots(1, 3, figsize=(13, 12.5), sharey=True)
for ax, (k, title, zero) in zip(axes, METRICS):
    for yr, mk in [('2040', 'o'), ('2048', 'o')]:
        xs = [val(d[r], yr, k) for _, r in rows]
        ax.scatter(xs, [yy for yy, _ in rows], s=60, marker=mk, zorder=3,
                   facecolors=COL[yr] if yr == '2040' else 'white', edgecolors=COL[yr], linewidths=1.4)
        ax.axvline(val(d['base'], yr, k), color=COL[yr], lw=1, ls='--', alpha=0.5)
    if zero is not None:
        ax.axvline(0, color='black', lw=0.8)
    for yy, _ in gpos[1:]:
        ax.axhline(yy - 0.7, color='gray', lw=0.5, alpha=0.5)
    ax.set_title(title, fontsize=15)
    ax.grid(True, axis='x', alpha=0.2)
axes[0].set_yticks([yy for yy, _ in ylab] + [yy for yy, _ in gpos])
axes[0].set_yticklabels([l for _, l in ylab] + [g for _, g in gpos])
for t, (yy, _) in zip(axes[0].get_yticklabels()[len(ylab):], gpos):
    t.set_fontweight('bold'); t.set_fontstyle('italic')
axes[0].invert_yaxis()
axes[0].tick_params(axis='y', length=0)
fig.legend(handles=[Line2D([], [], marker='o', ls='', color=COL['2040'], label='2040'),
                    Line2D([], [], marker='o', ls='', markerfacecolor='white', markeredgecolor=COL['2048'], markeredgewidth=1.4, label='2048'),
                    Line2D([], [], color='gray', ls='--', label='Go RES base case')],
           loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(0.6, -0.01))
plt.tight_layout(rect=(0, 0.03, 1, 1))
for ext in ('pdf', 'png'):
    plt.savefig(f'figures/robustness_final.{ext}', bbox_inches='tight', dpi=300)
print('Saved: figures/robustness_final.pdf/.png')
