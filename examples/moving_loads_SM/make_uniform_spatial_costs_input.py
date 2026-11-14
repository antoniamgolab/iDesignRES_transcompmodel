"""
Counterfactual input for the decomposition in Figure 5: spatially uniform charging costs (2026-10-15).

Base case v4_gridconn150/scenario_000, but electricity prices (FuelCost, per charger type and year) and grid charges
(NetworkConnectionCosts, per year) are replaced at every node by the unweighted mean over the seven corridor countries.
The CCS/MCS difference (time-of-day factor) is kept on average; only the differences between locations are removed.
"""
import os, shutil
from collections import defaultdict
import numpy as np
import yaml

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input_data'))
SRC, DST = 'v4_gridconn150/scenario_000', 'uniform_spatial_costs_final/scenario_000'
assert not os.path.exists(DST), DST
shutil.copytree(SRC, DST)
country = {g['id']: g['country'] for g in yaml.safe_load(open(os.path.join(SRC, 'GeographicElement.yaml')))}

p = os.path.join(DST, 'FuelCost.yaml')
fc = yaml.safe_load(open(p))
by_type = defaultdict(dict)  # type -> country -> price trajectory
for c in fc:
    if c.get('fuel') == 'electricity':
        by_type[c['fueling_infr_type_id']].setdefault(country[c['location']], c['cost_per_kWh'])
mean_price = {t: np.mean(list(d.values()), axis=0).tolist() for t, d in by_type.items()}
for c in fc:
    if c.get('fuel') == 'electricity':
        c['cost_per_kWh'] = [float(x) for x in mean_price[c['fueling_infr_type_id']]]
yaml.safe_dump(fc, open(p, 'w'), sort_keys=False)

p = os.path.join(DST, 'NetworkConnectionCosts.yaml')
nc = yaml.safe_load(open(p))
by_c = {}
for n in nc:
    by_c.setdefault(country[n['location']], n['network_cost_per_kW'])
mean_net = np.mean(list(by_c.values()), axis=0).tolist()
for n in nc:
    n['network_cost_per_kW'] = [float(x) for x in mean_net]
yaml.safe_dump(nc, open(p, 'w'), sort_keys=False)

print('countries', sorted(by_c), '| price 2040 CCS %.3f MCS %.3f EUR/kWh | grid charge %.2f EUR/kW/yr'
      % (mean_price[1][20], mean_price[2][20], mean_net[20]))
