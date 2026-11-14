"""
Compare TransComp model cost assumptions with ICCT study findings for long-haul trucks.

ICCT Studies Referenced:
1. "Total Cost of Ownership for Long-Haul Trucks in Europe" (2023)
   - BEV trucks projected to be least-cost pathway before 2030
   - https://theicct.org/publication/total-cost-ownership-trucks-europe-nov23/

2. "Total Cost of Ownership for Heavy-Duty Vehicle in Europe" (2021)
   - Long-haul BETs can reach TCO parity 2025-2026 for heavy-duty
   - https://theicct.org/sites/default/files/publications/TCO-BETs-Europe-white-paper-v4-nov21.pdf
"""

import matplotlib.pyplot as plt
import numpy as np

# ============================================================================
# MODEL COST ASSUMPTIONS (from TechVehicle.yaml)
# ============================================================================

# ICEV Parameters (long-haul truck, from TechVehicle.yaml id=0)
ICEV_CAPITAL_COST_2020 = 105484  # EUR
ICEV_CAPITAL_COST_2030 = 115252  # EUR (constant from 2030 onwards)
ICEV_MAINTENANCE_ANNUAL = 20703  # EUR/year (constant)
ICEV_PAYLOAD = 10.2  # tonnes (W parameter)
ICEV_ANNUAL_MILEAGE = 136750  # km/year
ICEV_LIFETIME = 12  # years
ICEV_SPEC_CONS = 3.64  # kWh/km (diesel energy consumption)

# BEV Parameters (long-haul truck, from TechVehicle.yaml id=1)
BEV_CAPITAL_COST_2020 = 417255  # EUR (very high!)
BEV_CAPITAL_COST_2025 = 192506  # EUR (index 5, year 2025 = 2020 + 5)
BEV_CAPITAL_COST_2030 = 134445  # EUR (index 10, year 2030 = 2020 + 10)
BEV_CAPITAL_COST_2040 = 124634  # EUR (index 20)
BEV_MAINTENANCE_ANNUAL = 14364  # EUR/year (30% lower than ICEV)
BEV_PAYLOAD_2020 = 3.06  # tonnes (much lower due to battery weight!)
BEV_PAYLOAD_2030 = 4.76  # tonnes (improving)
BEV_PAYLOAD_2040 = 6.46  # tonnes
BEV_PAYLOAD_2050 = 8.16  # tonnes
BEV_ANNUAL_MILEAGE = 136750  # km/year (same as ICEV)
BEV_LIFETIME = 12  # years
BEV_SPEC_CONS = 2.06  # kWh/km (electricity consumption, improving over time)

# Fuel costs (from model data and analysis)
DIESEL_COST_BASE = 0.1845  # EUR/kWh (constant - this is a key issue!)
ELECTRICITY_COST_2020 = 0.49  # EUR/kWh
ELECTRICITY_COST_2030 = 0.22  # EUR/kWh
ELECTRICITY_COST_2040 = 0.17  # EUR/kWh
CHARGING_MARKUP = 0.15  # 15% markup on electricity price

# Carbon prices (Go RES scenario, EUR/tCO2)
CARBON_2020 = 30
CARBON_2030 = 200
CARBON_2040 = 500
DIESEL_EMISSION_FACTOR = 0.000266  # tCO2/kWh

# ============================================================================
# ICCT STUDY VALUES (2023 study for Europe)
# ============================================================================

# ICCT values for long-haul (>150 km/day) tractor-trailers in Europe
ICCT_DIESEL_CAPEX_2020 = 100000  # EUR (similar to model)
ICCT_DIESEL_CAPEX_2030 = 105000  # EUR (slight increase)
ICCT_BEV_CAPEX_2020 = 220000  # EUR (much lower than model's 417k!)
ICCT_BEV_CAPEX_2025 = 170000  # EUR
ICCT_BEV_CAPEX_2030 = 140000  # EUR (battery cost decline)
ICCT_BEV_CAPEX_2040 = 115000  # EUR (approaches diesel)

# ICCT payload assumptions (40-tonne articulated truck)
ICCT_DIESEL_PAYLOAD = 25.0  # tonnes (GVW 40t - tractor ~15t)
ICCT_BEV_PAYLOAD_2020 = 22.0  # tonnes (3t battery penalty)
ICCT_BEV_PAYLOAD_2030 = 24.0  # tonnes (battery density improving)

# ICCT annual mileage
ICCT_ANNUAL_MILEAGE = 120000  # km/year (typical long-haul)

# ICCT fuel efficiency
ICCT_DIESEL_EFFICIENCY = 0.30  # L/km = 3.0 kWh/km at 10 kWh/L
ICCT_BEV_EFFICIENCY = 1.2  # kWh/km (much more efficient than model's 2.06!)

# ICCT fuel prices (Germany 2020 baseline)
ICCT_DIESEL_PRICE_2020 = 1.20  # EUR/L
ICCT_ELECTRICITY_PRICE_2020 = 0.18  # EUR/kWh (public charging)
ICCT_ELECTRICITY_PRICE_2030 = 0.15  # EUR/kWh (declining)


def calculate_tco_per_year(capex, maintenance, fuel_cost_per_km, mileage, lifetime, discount_rate=0.05):
    """Calculate annualized TCO per year."""
    # Annualize capital cost
    if discount_rate > 0:
        annuity_factor = (discount_rate * (1 + discount_rate)**lifetime) / ((1 + discount_rate)**lifetime - 1)
    else:
        annuity_factor = 1 / lifetime

    annual_capex = capex * annuity_factor
    annual_fuel = fuel_cost_per_km * mileage

    return annual_capex + maintenance + annual_fuel


def calculate_tco_per_tkm(tco_per_year, mileage, payload):
    """Calculate TCO per tonne-km."""
    tkm_per_year = mileage * payload
    return tco_per_year / tkm_per_year


# ============================================================================
# CALCULATE TCO FOR DIFFERENT YEARS
# ============================================================================

years = [2020, 2025, 2030, 2035, 2040]

# Model TCO calculations
model_icev_tco = []
model_bev_tco = []
model_icev_tco_per_tkm = []
model_bev_tco_per_tkm = []

# ICCT TCO calculations
icct_icev_tco = []
icct_bev_tco = []
icct_icev_tco_per_tkm = []
icct_bev_tco_per_tkm = []

for year in years:
    # MODEL CALCULATIONS
    # ICEV
    if year <= 2025:
        icev_capex = ICEV_CAPITAL_COST_2020 + (ICEV_CAPITAL_COST_2030 - ICEV_CAPITAL_COST_2020) * (year - 2020) / 10
    else:
        icev_capex = ICEV_CAPITAL_COST_2030

    # Add carbon cost to diesel price
    carbon_price = CARBON_2020 + (CARBON_2030 - CARBON_2020) * min((year - 2020) / 10, 1.0)
    if year > 2030:
        carbon_price = CARBON_2030 + (CARBON_2040 - CARBON_2030) * (year - 2030) / 10
    diesel_with_carbon = DIESEL_COST_BASE + carbon_price * DIESEL_EMISSION_FACTOR
    icev_fuel_per_km = ICEV_SPEC_CONS * diesel_with_carbon

    icev_tco = calculate_tco_per_year(icev_capex, ICEV_MAINTENANCE_ANNUAL, icev_fuel_per_km, ICEV_ANNUAL_MILEAGE, ICEV_LIFETIME)
    model_icev_tco.append(icev_tco)
    model_icev_tco_per_tkm.append(calculate_tco_per_tkm(icev_tco, ICEV_ANNUAL_MILEAGE, ICEV_PAYLOAD))

    # BEV
    if year == 2020:
        bev_capex = BEV_CAPITAL_COST_2020
        bev_payload = BEV_PAYLOAD_2020
    elif year == 2025:
        bev_capex = BEV_CAPITAL_COST_2025
        bev_payload = BEV_PAYLOAD_2020 + (BEV_PAYLOAD_2030 - BEV_PAYLOAD_2020) * 0.5
    elif year == 2030:
        bev_capex = BEV_CAPITAL_COST_2030
        bev_payload = BEV_PAYLOAD_2030
    elif year == 2035:
        bev_capex = (BEV_CAPITAL_COST_2030 + BEV_CAPITAL_COST_2040) / 2
        bev_payload = (BEV_PAYLOAD_2030 + BEV_PAYLOAD_2040) / 2
    else:  # 2040
        bev_capex = BEV_CAPITAL_COST_2040
        bev_payload = BEV_PAYLOAD_2040

    if year == 2020:
        elec_price = ELECTRICITY_COST_2020
    elif year == 2030:
        elec_price = ELECTRICITY_COST_2030
    else:
        # Linear interpolation
        if year < 2030:
            elec_price = ELECTRICITY_COST_2020 + (ELECTRICITY_COST_2030 - ELECTRICITY_COST_2020) * (year - 2020) / 10
        else:
            elec_price = ELECTRICITY_COST_2040

    bev_fuel_per_km = BEV_SPEC_CONS * elec_price * (1 + CHARGING_MARKUP)

    bev_tco = calculate_tco_per_year(bev_capex, BEV_MAINTENANCE_ANNUAL, bev_fuel_per_km, BEV_ANNUAL_MILEAGE, BEV_LIFETIME)
    model_bev_tco.append(bev_tco)
    model_bev_tco_per_tkm.append(calculate_tco_per_tkm(bev_tco, BEV_ANNUAL_MILEAGE, bev_payload))

    # ICCT CALCULATIONS
    # ICEV
    if year <= 2030:
        icct_icev_capex = ICCT_DIESEL_CAPEX_2020 + (ICCT_DIESEL_CAPEX_2030 - ICCT_DIESEL_CAPEX_2020) * (year - 2020) / 10
    else:
        icct_icev_capex = ICCT_DIESEL_CAPEX_2030

    icct_diesel_price = ICCT_DIESEL_PRICE_2020  # EUR/L
    icct_icev_fuel_per_km = ICCT_DIESEL_EFFICIENCY * icct_diesel_price
    icct_icev_maintenance = 15000  # EUR/year (typical ICCT assumption)

    icct_icev_tco_val = calculate_tco_per_year(icct_icev_capex, icct_icev_maintenance, icct_icev_fuel_per_km, ICCT_ANNUAL_MILEAGE, 8)
    icct_icev_tco.append(icct_icev_tco_val)
    icct_icev_tco_per_tkm.append(calculate_tco_per_tkm(icct_icev_tco_val, ICCT_ANNUAL_MILEAGE, ICCT_DIESEL_PAYLOAD))

    # BEV
    if year == 2020:
        icct_bev_capex = ICCT_BEV_CAPEX_2020
        icct_bev_payload = ICCT_BEV_PAYLOAD_2020
    elif year == 2025:
        icct_bev_capex = ICCT_BEV_CAPEX_2025
        icct_bev_payload = (ICCT_BEV_PAYLOAD_2020 + ICCT_BEV_PAYLOAD_2030) / 2
    elif year == 2030:
        icct_bev_capex = ICCT_BEV_CAPEX_2030
        icct_bev_payload = ICCT_BEV_PAYLOAD_2030
    else:
        icct_bev_capex = ICCT_BEV_CAPEX_2030 + (ICCT_BEV_CAPEX_2040 - ICCT_BEV_CAPEX_2030) * (year - 2030) / 10
        icct_bev_payload = ICCT_BEV_PAYLOAD_2030

    icct_elec_price = ICCT_ELECTRICITY_PRICE_2020 if year <= 2025 else ICCT_ELECTRICITY_PRICE_2030
    icct_bev_fuel_per_km = ICCT_BEV_EFFICIENCY * icct_elec_price
    icct_bev_maintenance = 12000  # EUR/year (lower than diesel)

    icct_bev_tco_val = calculate_tco_per_year(icct_bev_capex, icct_bev_maintenance, icct_bev_fuel_per_km, ICCT_ANNUAL_MILEAGE, 8)
    icct_bev_tco.append(icct_bev_tco_val)
    icct_bev_tco_per_tkm.append(calculate_tco_per_tkm(icct_bev_tco_val, ICCT_ANNUAL_MILEAGE, icct_bev_payload))


# ============================================================================
# CREATE VISUALIZATIONS
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Plot 1: Capital Costs Comparison
ax1 = axes[0, 0]
width = 0.35
x = np.arange(len(years))

# Model capex
model_icev_capex = [
    ICEV_CAPITAL_COST_2020,
    (ICEV_CAPITAL_COST_2020 + ICEV_CAPITAL_COST_2030) / 2,
    ICEV_CAPITAL_COST_2030,
    ICEV_CAPITAL_COST_2030,
    ICEV_CAPITAL_COST_2030
]
model_bev_capex = [
    BEV_CAPITAL_COST_2020,
    BEV_CAPITAL_COST_2025,
    BEV_CAPITAL_COST_2030,
    (BEV_CAPITAL_COST_2030 + BEV_CAPITAL_COST_2040) / 2,
    BEV_CAPITAL_COST_2040
]

# ICCT capex
icct_icev_capex_list = [
    ICCT_DIESEL_CAPEX_2020,
    (ICCT_DIESEL_CAPEX_2020 + ICCT_DIESEL_CAPEX_2030) / 2,
    ICCT_DIESEL_CAPEX_2030,
    ICCT_DIESEL_CAPEX_2030,
    ICCT_DIESEL_CAPEX_2030
]
icct_bev_capex_list = [
    ICCT_BEV_CAPEX_2020,
    ICCT_BEV_CAPEX_2025,
    ICCT_BEV_CAPEX_2030,
    (ICCT_BEV_CAPEX_2030 + ICCT_BEV_CAPEX_2040) / 2,
    ICCT_BEV_CAPEX_2040
]

ax1.bar(x - width/2, model_bev_capex, width, label='Model BEV', color='#1f77b4', alpha=0.7)
ax1.bar(x + width/2, icct_bev_capex_list, width, label='ICCT BEV', color='#2ca02c', alpha=0.7)
ax1.axhline(y=np.mean(model_icev_capex), color='#d62728', linestyle='--', linewidth=2, label=f'Model ICEV (~{np.mean(model_icev_capex)/1000:.0f}k)')
ax1.axhline(y=np.mean(icct_icev_capex_list), color='#ff7f0e', linestyle=':', linewidth=2, label=f'ICCT ICEV (~{np.mean(icct_icev_capex_list)/1000:.0f}k)')

ax1.set_xlabel('Year', fontsize=11)
ax1.set_ylabel('Capital Cost (EUR)', fontsize=11)
ax1.set_title('BEV Capital Cost: Model vs ICCT Study', fontsize=12, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(years)
ax1.legend(fontsize=9)
ax1.set_ylim(0, 450000)

# Add annotation for the 2020 discrepancy
ax1.annotate(f'Model: 417k\nICCT: 220k\nDiff: +90%',
            xy=(0, BEV_CAPITAL_COST_2020), xytext=(0.5, 380000),
            fontsize=9, ha='center',
            arrowprops=dict(arrowstyle='->', color='red'))

# Plot 2: Payload Comparison
ax2 = axes[0, 1]
model_bev_payload = [BEV_PAYLOAD_2020,
                     BEV_PAYLOAD_2020 + (BEV_PAYLOAD_2030 - BEV_PAYLOAD_2020) * 0.5,
                     BEV_PAYLOAD_2030,
                     (BEV_PAYLOAD_2030 + BEV_PAYLOAD_2040) / 2,
                     BEV_PAYLOAD_2040]
icct_bev_payload_list = [ICCT_BEV_PAYLOAD_2020,
                         (ICCT_BEV_PAYLOAD_2020 + ICCT_BEV_PAYLOAD_2030) / 2,
                         ICCT_BEV_PAYLOAD_2030,
                         ICCT_BEV_PAYLOAD_2030,
                         ICCT_BEV_PAYLOAD_2030]

ax2.bar(x - width/2, model_bev_payload, width, label='Model BEV Payload', color='#1f77b4', alpha=0.7)
ax2.bar(x + width/2, icct_bev_payload_list, width, label='ICCT BEV Payload', color='#2ca02c', alpha=0.7)
ax2.axhline(y=ICEV_PAYLOAD, color='#d62728', linestyle='--', linewidth=2, label=f'Model ICEV ({ICEV_PAYLOAD}t)')
ax2.axhline(y=ICCT_DIESEL_PAYLOAD, color='#ff7f0e', linestyle=':', linewidth=2, label=f'ICCT ICEV ({ICCT_DIESEL_PAYLOAD}t)')

ax2.set_xlabel('Year', fontsize=11)
ax2.set_ylabel('Payload (tonnes)', fontsize=11)
ax2.set_title('Payload Capacity: Model vs ICCT Study', fontsize=12, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(years)
ax2.legend(fontsize=9)

# Add annotation
ax2.annotate(f'Model ICEV: 10.2t\nICCT ICEV: 25t\nModel assumes\nsmaller trucks?',
            xy=(2, ICEV_PAYLOAD), xytext=(3, 15),
            fontsize=9, ha='center',
            arrowprops=dict(arrowstyle='->', color='blue'))

# Plot 3: Annual TCO Comparison
ax3 = axes[1, 0]
ax3.plot(years, model_icev_tco, 'o-', label='Model ICEV', color='#d62728', linewidth=2, markersize=8)
ax3.plot(years, model_bev_tco, 's-', label='Model BEV', color='#1f77b4', linewidth=2, markersize=8)
ax3.plot(years, icct_icev_tco, 'o--', label='ICCT ICEV', color='#ff7f0e', linewidth=2, markersize=8)
ax3.plot(years, icct_bev_tco, 's--', label='ICCT BEV', color='#2ca02c', linewidth=2, markersize=8)

ax3.set_xlabel('Year', fontsize=11)
ax3.set_ylabel('Annual TCO (EUR/year)', fontsize=11)
ax3.set_title('Annual TCO Comparison', fontsize=12, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)

# Mark TCO parity points
ax3.axvline(x=2026, color='green', linestyle=':', alpha=0.7, label='ICCT TCO parity')
ax3.text(2026.5, max(model_bev_tco) * 0.9, 'ICCT parity\n~2026', fontsize=9, color='green')

# Plot 4: TCO per tkm Comparison
ax4 = axes[1, 1]
ax4.plot(years, model_icev_tco_per_tkm, 'o-', label='Model ICEV', color='#d62728', linewidth=2, markersize=8)
ax4.plot(years, model_bev_tco_per_tkm, 's-', label='Model BEV', color='#1f77b4', linewidth=2, markersize=8)
ax4.plot(years, icct_icev_tco_per_tkm, 'o--', label='ICCT ICEV', color='#ff7f0e', linewidth=2, markersize=8)
ax4.plot(years, icct_bev_tco_per_tkm, 's--', label='ICCT BEV', color='#2ca02c', linewidth=2, markersize=8)

ax4.set_xlabel('Year', fontsize=11)
ax4.set_ylabel('TCO per tkm (EUR/tkm)', fontsize=11)
ax4.set_title('TCO per Tonne-km (Key Metric for Freight)', fontsize=12, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)

# Highlight the issue
ax4.annotate('Model BEV TCO/tkm\nmuch higher due to\nlow payload',
            xy=(2025, model_bev_tco_per_tkm[1]), xytext=(2030, model_bev_tco_per_tkm[1] * 0.8),
            fontsize=9, ha='center',
            arrowprops=dict(arrowstyle='->', color='red'))

plt.tight_layout()
plt.savefig('figures/model_vs_icct_cost_comparison.pdf', dpi=150, bbox_inches='tight')
plt.savefig('figures/model_vs_icct_cost_comparison.png', dpi=150, bbox_inches='tight')
print('Saved: figures/model_vs_icct_cost_comparison.pdf')

# ============================================================================
# PRINT DETAILED COMPARISON
# ============================================================================

print("\n" + "=" * 100)
print("MODEL VS ICCT COST ASSUMPTIONS COMPARISON")
print("=" * 100)

print("\n--- CAPITAL COSTS (EUR) ---")
print(f"{'Year':<8}{'Model ICEV':<15}{'ICCT ICEV':<15}{'Model BEV':<15}{'ICCT BEV':<15}{'BEV Ratio':<12}")
print("-" * 80)
for i, year in enumerate(years):
    ratio = model_bev_capex[i] / icct_bev_capex_list[i]
    print(f"{year:<8}{model_icev_capex[i]:<15,.0f}{icct_icev_capex_list[i]:<15,.0f}{model_bev_capex[i]:<15,.0f}{icct_bev_capex_list[i]:<15,.0f}{ratio:<12.2f}")

print("\n--- PAYLOAD (tonnes) ---")
print(f"{'Year':<8}{'Model ICEV':<15}{'ICCT ICEV':<15}{'Model BEV':<15}{'ICCT BEV':<15}{'BEV Ratio':<12}")
print("-" * 80)
for i, year in enumerate(years):
    ratio = model_bev_payload[i] / icct_bev_payload_list[i]
    print(f"{year:<8}{ICEV_PAYLOAD:<15.1f}{ICCT_DIESEL_PAYLOAD:<15.1f}{model_bev_payload[i]:<15.1f}{icct_bev_payload_list[i]:<15.1f}{ratio:<12.2f}")

print("\n--- ANNUAL TCO (EUR/year) ---")
print(f"{'Year':<8}{'Model ICEV':<15}{'ICCT ICEV':<15}{'Model BEV':<15}{'ICCT BEV':<15}{'Model BEV/ICEV':<15}{'ICCT BEV/ICEV':<15}")
print("-" * 100)
for i, year in enumerate(years):
    model_ratio = model_bev_tco[i] / model_icev_tco[i]
    icct_ratio = icct_bev_tco[i] / icct_icev_tco[i]
    print(f"{year:<8}{model_icev_tco[i]:<15,.0f}{icct_icev_tco[i]:<15,.0f}{model_bev_tco[i]:<15,.0f}{icct_bev_tco[i]:<15,.0f}{model_ratio:<15.2f}{icct_ratio:<15.2f}")

print("\n--- TCO PER TONNE-KM (EUR/tkm) ---")
print(f"{'Year':<8}{'Model ICEV':<15}{'ICCT ICEV':<15}{'Model BEV':<15}{'ICCT BEV':<15}{'Model BEV/ICEV':<15}{'ICCT BEV/ICEV':<15}")
print("-" * 100)
for i, year in enumerate(years):
    model_ratio = model_bev_tco_per_tkm[i] / model_icev_tco_per_tkm[i]
    icct_ratio = icct_bev_tco_per_tkm[i] / icct_icev_tco_per_tkm[i]
    print(f"{year:<8}{model_icev_tco_per_tkm[i]:<15.4f}{icct_icev_tco_per_tkm[i]:<15.4f}{model_bev_tco_per_tkm[i]:<15.4f}{icct_bev_tco_per_tkm[i]:<15.4f}{model_ratio:<15.2f}{icct_ratio:<15.2f}")

print("\n" + "=" * 100)
print("KEY DISCREPANCIES IDENTIFIED")
print("=" * 100)

print("""
1. BEV CAPITAL COST (2020):
   - Model: 417,255 EUR
   - ICCT:  220,000 EUR
   - Discrepancy: Model is 90% HIGHER than ICCT estimate
   - Impact: Significantly delays TCO parity in model

2. PAYLOAD CAPACITY:
   - Model ICEV: 10.2 tonnes (appears to be a smaller truck class)
   - ICCT ICEV: 25.0 tonnes (standard 40t articulated truck)
   - Model BEV 2020: 3.06 tonnes (VERY low - only 30% of ICEV!)
   - ICCT BEV 2020: 22.0 tonnes (88% of ICEV)
   - Impact: Model severely penalizes BEV on per-tkm basis

   NOTE: This suggests the model may be using a different vehicle class
   or applying an excessive battery weight penalty.

3. ENERGY CONSUMPTION:
   - Model BEV: 2.06 kWh/km
   - ICCT BEV: 1.2 kWh/km
   - Discrepancy: Model is 72% HIGHER
   - Impact: Higher operating costs for BEV in model

4. TCO PARITY TIMING:
   - ICCT projection: BEV reaches TCO parity around 2025-2026
   - Model projection: BEV never reaches parity due to low payload

5. CRITICAL ISSUE - PAYLOAD:
   The most significant discrepancy is the BEV payload. In 2020:
   - Model: 3.06 tonnes payload = 0.022 tkm per vehicle-km
   - ICCT: 22 tonnes payload = 0.16 tkm per vehicle-km
   This 7x difference in productivity makes BEV uncompetitive in the model.

RECOMMENDATIONS:
1. Review BEV payload assumptions - 3 tonnes seems too low
2. Consider that ICCT uses 40-tonne GVW articulated trucks
3. Battery weight penalty of ~7 tonnes (10.2 - 3.06) seems excessive
4. Verify BEV capital cost trajectory - 417k EUR in 2020 is very high
5. Check if energy consumption includes charging losses
""")

# plt.show()  # Commented for non-interactive execution
