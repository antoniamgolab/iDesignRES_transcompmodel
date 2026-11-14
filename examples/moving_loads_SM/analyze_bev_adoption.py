"""
Analyze BEV adoption from model results
"""
import yaml
import ast
from collections import defaultdict

prefix = 'results/comparison_charging_constraint/comparison_WITHOUT_constraint_2025-12-12_17-54-51'

print('Loading results...')
with open(f'{prefix}_f_dict.yaml', 'r') as f:
    f_dict = yaml.safe_load(f)

# Load OD pairs to get origin/destination info
with open('input_data/case_20251212_164653/Odpair.yaml', 'r') as f:
    odpairs = yaml.safe_load(f)

# Create mapping od_id -> (origin, dest)
od_map = {}
for od in odpairs:
    od_map[od['id']] = (od['from'], od['to'])

# Get geographic elements to map IDs to names
with open('input_data/case_20251212_164653/GeographicElement.yaml', 'r') as f:
    geo_elements = yaml.safe_load(f)

geo_name = {}
for ge in geo_elements:
    geo_name[ge['id']] = ge.get('name', f"GE_{ge['id']}")

# ============================================================================
# ANALYSIS 1: BEV Share by Year
# ============================================================================
flows_by_year_tech = defaultdict(float)

for key_str, val_str in f_dict.items():
    key = ast.literal_eval(key_str)
    year = key[0]
    tv_id = key[2][1]  # key[2] is (mode_id, tv_id)
    f_val = float(val_str)
    flows_by_year_tech[(year, tv_id)] += f_val

print('='*80)
print('BEV ADOPTION ANALYSIS - MODEL WITH SOC CONSTRAINT (FIXED)')
print('='*80)

print()
print('1. TRANSPORT ACTIVITY (tkm) BY VEHICLE TECHNOLOGY')
print('-'*80)
print(f'{"Year":>6} | {"ICEV tkm":>14} | {"BEV tkm":>14} | {"Total tkm":>14} | {"BEV Share":>10}')
print('-'*80)

years = sorted(set(k[0] for k in flows_by_year_tech.keys()))
total_icev = 0
total_bev = 0
for year in years:
    icev = flows_by_year_tech.get((year, 0), 0)
    bev = flows_by_year_tech.get((year, 1), 0)
    total = icev + bev
    bev_share = (bev / total * 100) if total > 0 else 0
    total_icev += icev
    total_bev += bev

    print(f'{year:>6} | {icev:>14,.0f} | {bev:>14,.0f} | {total:>14,.0f} | {bev_share:>9.2f}%')

print('-'*80)
total_all = total_icev + total_bev
print(f'{"TOTAL":>6} | {total_icev:>14,.0f} | {total_bev:>14,.0f} | {total_all:>14,.0f} | {total_bev/total_all*100:>9.2f}%')

# ============================================================================
# ANALYSIS 2: BEV Adoption by OD Pair for 2040
# ============================================================================
year = 2040
flows_by_od_tech = defaultdict(lambda: defaultdict(float))

for key_str, val_str in f_dict.items():
    key = ast.literal_eval(key_str)
    y = key[0]
    if y != year:
        continue
    od_id = key[1][0]  # key[1] is (od_id, r_id, path_id)
    tv_id = key[2][1]  # key[2] is (mode_id, tv_id)
    f_val = float(val_str)
    flows_by_od_tech[od_id][tv_id] += f_val

print()
print(f'2. BEV ADOPTION BY OD PAIR (Year {year})')
print('='*90)
print(f'{"OD Pair":>50} | {"ICEV":>10} | {"BEV":>10} | {"BEV Share":>10}')
print('-'*90)

# Sort by BEV share
results = []
for od_id, tech_flows in flows_by_od_tech.items():
    icev = tech_flows.get(0, 0)
    bev = tech_flows.get(1, 0)
    total = icev + bev
    bev_share = (bev / total * 100) if total > 0 else 0

    if od_id in od_map:
        orig, dest = od_map[od_id]
        orig_name = geo_name.get(orig, str(orig))
        dest_name = geo_name.get(dest, str(dest))
        od_label = f'{orig_name} -> {dest_name}'
    else:
        od_label = f'OD {od_id}'

    results.append((od_label, icev, bev, bev_share))

# Sort by BEV share descending
results.sort(key=lambda x: x[3], reverse=True)

for od_label, icev, bev, bev_share in results[:15]:  # Show top 15
    print(f'{od_label:>50} | {icev:>10,.0f} | {bev:>10,.0f} | {bev_share:>9.2f}%')

print('-'*90)
print('...')
print('-'*90)

# Show bottom 5
for od_label, icev, bev, bev_share in results[-5:]:
    print(f'{od_label:>50} | {icev:>10,.0f} | {bev:>10,.0f} | {bev_share:>9.2f}%')

print('='*90)

# ============================================================================
# ANALYSIS 3: Key observations
# ============================================================================
print()
print('3. KEY OBSERVATIONS')
print('='*80)

# Count OD pairs with 100% BEV
bev_100 = sum(1 for _, _, _, share in results if share >= 99.9)
bev_50_plus = sum(1 for _, _, _, share in results if share >= 50)
bev_any = sum(1 for _, _, _, share in results if share > 0)

print(f'OD pairs with 100% BEV: {bev_100}')
print(f'OD pairs with 50%+ BEV: {bev_50_plus}')
print(f'OD pairs with any BEV: {bev_any}')
print(f'Total OD pairs: {len(results)}')

# Calculate average BEV share weighted by total flow
total_flow = sum(icev + bev for _, icev, bev, _ in results)
weighted_bev_share = sum(bev / total_flow * 100 for _, icev, bev, _ in results if (icev + bev) > 0)
print(f'Overall weighted BEV share (2040): {weighted_bev_share:.2f}%')
