import json

with open('charging_constraint_comparison.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Create cells for EUR/1000TKM analysis
tkm_cell1 = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": """# =====================================================
# COST PER TRANSPORT PERFORMANCE: EUR/1000 TKM
# =====================================================

# Load path distances and demand data
import yaml

# Load from scenario_000 (same structure for all scenarios)
input_path = os.path.join(BASE_DIR, 'input_data', 'uncertainty_scenarios', 'scenario_000')

with open(os.path.join(input_path, 'Path.yaml'), 'r') as f:
    paths_data = yaml.safe_load(f)

with open(os.path.join(input_path, 'Odpair.yaml'), 'r') as f:
    odpair_data = yaml.safe_load(f)

# Create mappings
path_distances = {p['id']: p['length'] for p in paths_data}  # km
odpair_demand = {}  # {odpair_id: [F values by year]}
odpair_path = {}  # {odpair_id: path_id}

for od in odpair_data:
    odpair_demand[od['id']] = od['F']  # tonnes per year
    odpair_path[od['id']] = od['path_id']

print(f'Loaded {len(path_distances)} paths')
print(f'Loaded {len(odpair_demand)} OD pairs')
print(f'Years in optimization: {len(odpair_demand[list(odpair_demand.keys())[0]])} years')
""".split('\n')
}
# Fix source format
tkm_cell1['source'] = [line + '\n' for line in tkm_cell1['source'][:-1]] + [tkm_cell1['source'][-1]]

tkm_cell2 = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": """# Calculate total TKM across all years
# TKM = sum over all OD pairs and years of (F[od,year] * distance[path])

years = list(range(2020, 2061, 4))  # Model years: 2020, 2024, ..., 2060
print(f'Model years: {years}')

total_tkm = 0
tkm_by_year = {}

for od_id, demand_list in odpair_demand.items():
    path_id = odpair_path.get(od_id)
    if path_id is None:
        continue
    distance = path_distances.get(path_id, 0)  # km

    for year_idx, year in enumerate(years):
        if year_idx < len(demand_list):
            tonnes = demand_list[year_idx]
            tkm = tonnes * distance  # tonne-km
            total_tkm += tkm
            tkm_by_year[year] = tkm_by_year.get(year, 0) + tkm

print(f'\\nTotal TKM over optimization horizon: {total_tkm/1e9:.2f} billion TKM')
print(f'\\nTKM by year (billion):')
for year in sorted(tkm_by_year.keys()):
    print(f'  {year}: {tkm_by_year[year]/1e9:.2f}')
""".split('\n')
}
tkm_cell2['source'] = [line + '\n' for line in tkm_cell2['source'][:-1]] + [tkm_cell2['source'][-1]]

tkm_cell3 = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": """# Calculate EUR/1000 TKM for each scenario
# Using objective value / (total_tkm / 1000)

eur_per_1000tkm = []

for scenario in scenarios:
    base_data = baseline_summary.get(scenario, {})
    const_data = constrained_summary.get(scenario, {})

    base_obj = float(base_data.get('objective_value', 0))
    const_obj = float(const_data.get('objective_value', 0))

    if base_obj > 0 and const_obj > 0:
        # EUR per 1000 TKM
        base_eur_1000tkm = base_obj / (total_tkm / 1000)
        const_eur_1000tkm = const_obj / (total_tkm / 1000)
        delta_eur_1000tkm = const_eur_1000tkm - base_eur_1000tkm

        # Get scenario metadata
        case_idx = int(scenario.split('_')[1])
        case_info = cases_config['cases'][case_idx]

        eur_per_1000tkm.append({
            'scenario': scenario,
            'genesys': case_info['genesys_scenario'].replace(' v1.2', ''),
            'charging_markup': case_info['charging_markup'],
            'tech_cost': case_info['tech_cost_multiplier'],
            'baseline_eur_1000tkm': base_eur_1000tkm,
            'constrained_eur_1000tkm': const_eur_1000tkm,
            'delta_eur_1000tkm': delta_eur_1000tkm,
            'pct_change': (delta_eur_1000tkm / base_eur_1000tkm) * 100
        })

tkm_df = pd.DataFrame(eur_per_1000tkm)
print(f'Calculated EUR/1000 TKM for {len(tkm_df)} scenarios')
print(f'\\nTotal transport performance: {total_tkm/1e9:.2f} billion TKM')
print(f'\\nSummary Statistics (EUR/1000 TKM):')
print(tkm_df[['baseline_eur_1000tkm', 'constrained_eur_1000tkm', 'delta_eur_1000tkm']].describe())
""".split('\n')
}
tkm_cell3['source'] = [line + '\n' for line in tkm_cell3['source'][:-1]] + [tkm_cell3['source'][-1]]

tkm_cell4_source = """# Visualize EUR/1000 TKM comparison
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# 1. Baseline vs Constrained scatter
ax = axes[0]
colors_map = {'Go RES': '#2ecc71', 'NECPEssentials': '#3498db', 'REPowerEU++': '#9b59b6', 'Trinity': '#e74c3c'}
scatter_colors = [colors_map.get(g, 'gray') for g in tkm_df['genesys']]
ax.scatter(tkm_df['baseline_eur_1000tkm'], tkm_df['constrained_eur_1000tkm'],
           c=scatter_colors, s=100, alpha=0.7, edgecolors='black')
# Diagonal line (no change)
min_val = min(tkm_df['baseline_eur_1000tkm'].min(), tkm_df['constrained_eur_1000tkm'].min())
max_val = max(tkm_df['baseline_eur_1000tkm'].max(), tkm_df['constrained_eur_1000tkm'].max())
ax.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=1, label='No change')
ax.set_xlabel('Baseline (EUR/1000 TKM)')
ax.set_ylabel('Constrained (EUR/1000 TKM)')
ax.set_title('EUR/1000 TKM: Baseline vs Constrained')
ax.legend()

# 2. Delta distribution
ax = axes[1]
ax.hist(tkm_df['delta_eur_1000tkm'], bins=15, edgecolor='black', alpha=0.7, color='steelblue')
ax.axvline(0, color='red', linestyle='--', linewidth=2)
mean_delta = tkm_df['delta_eur_1000tkm'].mean()
ax.axvline(mean_delta, color='orange', linestyle='-', linewidth=2, label=f'Mean: {mean_delta:.2f}')
ax.set_xlabel('Change in EUR/1000 TKM')
ax.set_ylabel('Count')
ax.set_title('Distribution of Cost Change')
ax.legend()

# 3. By GENeSYS scenario
ax = axes[2]
genesys_means = tkm_df.groupby('genesys').agg({
    'baseline_eur_1000tkm': 'mean',
    'constrained_eur_1000tkm': 'mean'
}).sort_values('baseline_eur_1000tkm')

x = np.arange(len(genesys_means))
width = 0.35
ax.bar(x - width/2, genesys_means['baseline_eur_1000tkm'], width, label='Baseline', color='#3498db', edgecolor='black')
ax.bar(x + width/2, genesys_means['constrained_eur_1000tkm'], width, label='Constrained', color='#e74c3c', edgecolor='black')
ax.set_xticks(x)
ax.set_xticklabels(genesys_means.index, rotation=45, ha='right')
ax.set_ylabel('EUR/1000 TKM')
ax.set_title('Cost per TKM by GENeSYS Scenario')
ax.legend()

plt.tight_layout()
plt.savefig('figures/eur_per_1000tkm_comparison.pdf', bbox_inches='tight', dpi=150)
plt.show()

# Summary
print('\\n=== EUR/1000 TKM Summary ===')
print(f'Mean Baseline: {tkm_df["baseline_eur_1000tkm"].mean():.2f} EUR/1000 TKM')
print(f'Mean Constrained: {tkm_df["constrained_eur_1000tkm"].mean():.2f} EUR/1000 TKM')
print(f'Mean Change: {tkm_df["delta_eur_1000tkm"].mean():.2f} EUR/1000 TKM ({tkm_df["pct_change"].mean():.4f}%)')
"""

tkm_cell4 = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [line + '\n' for line in tkm_cell4_source.split('\n')[:-1]] + [tkm_cell4_source.split('\n')[-1]]
}

tkm_cell5_source = """# Detailed comparison table
tkm_display = tkm_df[['scenario', 'genesys', 'charging_markup', 'tech_cost',
                       'baseline_eur_1000tkm', 'constrained_eur_1000tkm',
                       'delta_eur_1000tkm', 'pct_change']].copy()
tkm_display = tkm_display.round(2)
tkm_display.columns = ['Scenario', 'GENeSYS', 'Markup', 'Tech Cost',
                        'Baseline', 'Constrained', 'Delta', '% Change']

print('EUR/1000 TKM Comparison by Scenario:')
print(tkm_display.to_string(index=False))
"""

tkm_cell5 = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [line + '\n' for line in tkm_cell5_source.split('\n')[:-1]] + [tkm_cell5_source.split('\n')[-1]]
}

# Add cells at the end
for cell in [tkm_cell1, tkm_cell2, tkm_cell3, tkm_cell4, tkm_cell5]:
    nb['cells'].append(cell)

with open('charging_constraint_comparison.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print(f"Added 5 EUR/1000 TKM analysis cells to the notebook")
