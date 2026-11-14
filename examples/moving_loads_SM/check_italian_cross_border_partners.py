"""
Check which countries Italy's cross-border routes connect to
"""
import pandas as pd

print("="*80)
print("ITALIAN CROSS-BORDER ROUTE PARTNERS")
print("="*80)

# Load NUTS3 regions mapping
nuts3 = pd.read_csv("data/Trucktraffic_NUTS3/02_NUTS-3-Regions.csv")
id_to_country = dict(zip(nuts3['ETISPlus_Zone_ID'], nuts3['Country']))

# Load truck traffic
traffic = pd.read_csv("data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv")
traffic['origin_country'] = traffic['ID_origin_region'].map(id_to_country)
traffic['dest_country'] = traffic['ID_destination_region'].map(id_to_country)

# Italian exports (IT -> other)
italy_exports = traffic[(traffic['origin_country'] == 'IT') & (traffic['dest_country'] != 'IT')]

export_partners = italy_exports.groupby('dest_country').agg({
    'Traffic_flow_trucks_2030': 'sum'
}).sort_values('Traffic_flow_trucks_2030', ascending=False)

print("\nITALIAN EXPORT DESTINATIONS (IT -> other):")
print(f"{'Country':<10} {'Routes':<10} {'Total Traffic (trucks/year)':<30}")
print("-"*55)

for country in export_partners.index:
    routes = len(italy_exports[italy_exports['dest_country'] == country])
    traffic_vol = export_partners.loc[country, 'Traffic_flow_trucks_2030']
    print(f"{country:<10} {routes:>8,}   {traffic_vol:>26,.0f}")

# Italian imports (other -> IT)
italy_imports = traffic[(traffic['origin_country'] != 'IT') & (traffic['dest_country'] == 'IT')]

import_partners = italy_imports.groupby('origin_country').agg({
    'Traffic_flow_trucks_2030': 'sum'
}).sort_values('Traffic_flow_trucks_2030', ascending=False)

print("\n\nITALIAN IMPORT ORIGINS (other -> IT):")
print(f"{'Country':<10} {'Routes':<10} {'Total Traffic (trucks/year)':<30}")
print("-"*55)

for country in import_partners.index:
    routes = len(italy_imports[italy_imports['origin_country'] == country])
    traffic_vol = import_partners.loc[country, 'Traffic_flow_trucks_2030']
    print(f"{country:<10} {routes:>8,}   {traffic_vol:>26,.0f}")

# Check if partners are in Scandinavian-Mediterranean corridor
print("\n" + "="*80)
print("CORRIDOR COUNTRY ANALYSIS")
print("="*80)

# Corridor countries (from preprocessing script)
corridor_nuts0 = ["DE", "DK", "SE"]
corridor_countries = corridor_nuts0 + ["AT", "IT", "NO", "FI"]  # These have NUTS1/2 in corridor

all_export_countries = set(export_partners.index)
all_import_countries = set(import_partners.index)
all_partner_countries = all_export_countries | all_import_countries

print(f"\nAll Italian cross-border partner countries: {sorted(all_partner_countries)}")
print(f"Corridor countries (full or partial): {sorted(corridor_countries)}")

partners_in_corridor = all_partner_countries & set(corridor_countries)
partners_outside_corridor = all_partner_countries - set(corridor_countries)

print(f"\nPartner countries IN corridor: {sorted(partners_in_corridor)}")
print(f"Partner countries OUTSIDE corridor: {sorted(partners_outside_corridor)}")

# Calculate traffic with corridor vs non-corridor countries
italy_cross_border = pd.concat([italy_exports, italy_imports])
italy_cross_border['partner_country'] = italy_cross_border.apply(
    lambda row: row['dest_country'] if row['origin_country'] == 'IT' else row['origin_country'],
    axis=1
)
italy_cross_border['in_corridor'] = italy_cross_border['partner_country'].isin(corridor_countries)

traffic_in_corridor = italy_cross_border[italy_cross_border['in_corridor']]['Traffic_flow_trucks_2030'].sum()
traffic_outside_corridor = italy_cross_border[~italy_cross_border['in_corridor']]['Traffic_flow_trucks_2030'].sum()
total_cross_border = italy_cross_border['Traffic_flow_trucks_2030'].sum()

routes_in_corridor = len(italy_cross_border[italy_cross_border['in_corridor']])
routes_outside_corridor = len(italy_cross_border[~italy_cross_border['in_corridor']])

print(f"\n" + "-"*80)
print("TRAFFIC BREAKDOWN")
print("-"*80)
print(f"\nItaly <-> Corridor countries:")
print(f"  Routes: {routes_in_corridor:,} ({routes_in_corridor/len(italy_cross_border)*100:.1f}%)")
print(f"  Traffic: {traffic_in_corridor:,.0f} trucks/year ({traffic_in_corridor/total_cross_border*100:.1f}%)")

print(f"\nItaly <-> Non-corridor countries:")
print(f"  Routes: {routes_outside_corridor:,} ({routes_outside_corridor/len(italy_cross_border)*100:.1f}%)")
print(f"  Traffic: {traffic_outside_corridor:,.0f} trucks/year ({traffic_outside_corridor/total_cross_border*100:.1f}%)")

print("\n" + "="*80)
print("[FINDING] This shows why Italy has 0 OD pairs in processed data!")
print("="*80)
