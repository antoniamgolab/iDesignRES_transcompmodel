"""
Build highway_km_per_nuts2.csv from Eurostat tran_r_net data.

Source: Eurostat table tran_r_net (transport regional network, motorways in km).

Strategy:
  1. For most countries, Eurostat provides NUTS-2 level data directly.
  2. For Germany, Eurostat only provides NUTS-1 level data. For Bundeslaender
     with a single NUTS-2 child (e.g. DE3->DE30), the 4-char code is already
     present. For multi-child Bundeslaender (DE1, DE2, DE7, DE9, DEA, DEB, DED),
     we split the NUTS-1 total proportionally by NUTS-2 area.
  3. For a few other countries (IT, NO, PL, PT), some NUTS-2 children are missing.
     If the NUTS-1 parent has a total and some siblings are present, we compute
     the missing child(ren) as the residual. If ALL children are missing, we
     split by area.

Area is computed from the NUTS 2021 shapefile projected to EPSG:3035.

Author: auto-generated
Date: 2026-02-11
"""

import pandas as pd
import geopandas as gpd
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────────
EUROSTAT_CSV = (
    r"D:\AntoniaMariaG\other data"
    r"\tran_r_net$defaultview_linear.csv"
    r"\tran_r_net$defaultview_linear.csv"
)
SHAPEFILE = (
    r"C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis"
    r"\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM"
    r"\data\NUTS_RG_20M_2021_4326.shp\NUTS_RG_20M_2021_4326.shp"
)
OUTPUT_CSV = (
    r"C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis"
    r"\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM"
    r"\highway_km_per_nuts2.csv"
)

# ── 1. Read old CSV for comparison later (before overwriting) ─────────────────
try:
    old_df = pd.read_csv(OUTPUT_CSV)
    old_values = dict(zip(old_df["NUTS2_CODE"], old_df["highway_km"]))
except Exception:
    old_values = {}

# ── 2. Read Eurostat CSV ──────────────────────────────────────────────────────
df = pd.read_csv(EUROSTAT_CSV)

# Filter to motorways only
df = df[df["tra_infr"] == "MWAY:Motorways"].copy()

# Extract the NUTS code (part before the colon) from the geo column
df["nuts_code"] = df["geo"].str.split(":").str[0]

# Parse OBS_VALUE as numeric (some might be empty or have flags)
df["OBS_VALUE"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")

# Parse TIME_PERIOD as int year
df["year"] = pd.to_numeric(df["TIME_PERIOD"], errors="coerce").astype("Int64")

# Drop rows without a valid value
df = df.dropna(subset=["OBS_VALUE", "year"])

# ── 3. For each nuts_code, pick the latest available year ─────────────────────
df = df.sort_values("year", ascending=False)
latest = df.groupby("nuts_code").first().reset_index()
latest = latest[["nuts_code", "year", "OBS_VALUE"]].rename(
    columns={"OBS_VALUE": "highway_km"}
)
latest_lookup = latest.set_index("nuts_code")["highway_km"].to_dict()

# ── 4. Load shapefile for NUTS-2 areas (needed before filtering Eurostat) ─────
print("Loading NUTS shapefile...")
gdf = gpd.read_file(SHAPEFILE)
nuts2_shapes = gdf[gdf["LEVL_CODE"] == 2].copy()
nuts2_shapes = nuts2_shapes.to_crs(epsg=3035)
nuts2_shapes["area_km2"] = nuts2_shapes.geometry.area / 1e6
nuts2_area = nuts2_shapes.set_index("NUTS_ID")["area_km2"].to_dict()

# All NUTS-2 codes from the 2021 NUTS shapefile
all_nuts2_from_shp = set(nuts2_shapes["NUTS_ID"])

# ── 5. Collect NUTS-2 codes (4-char) available directly in Eurostat ──────────
# IMPORTANT: Only keep codes that exist in the 2021 NUTS classification (shapefile)
# to avoid double-counting from old NUTS versions (e.g. Norway NO01-NO05 vs NO02-NO0B)
nuts2_direct = latest[latest["nuts_code"].str.len() == 4].copy()
nuts2_direct = nuts2_direct.set_index("nuts_code")

# Filter to only codes in the 2021 shapefile
old_codes = set(nuts2_direct.index) - all_nuts2_from_shp
if old_codes:
    print(f"  Dropping {len(old_codes)} codes not in 2021 NUTS shapefile: "
          f"{sorted(old_codes)}")
    nuts2_direct = nuts2_direct.loc[nuts2_direct.index.isin(all_nuts2_from_shp)]
nuts2_set = set(nuts2_direct.index)

# ── 6. Identify NUTS-1 codes that have missing NUTS-2 children ────────────────
nuts1_codes = set(latest.loc[latest["nuts_code"].str.len() == 3, "nuts_code"])

# Build the gap-fill rows
gapfill_rows = {}

for n1_code in sorted(nuts1_codes):
    # Find children from shapefile (4-char codes with matching prefix)
    children_shp = sorted(
        [c for c in all_nuts2_from_shp if c[:3] == n1_code and len(c) == 4]
    )
    if len(children_shp) <= 1:
        # No sub-division to worry about (or single child that should already be
        # in Eurostat as a 4-char code)
        continue

    children_in_eurostat = [c for c in children_shp if c in nuts2_set]
    children_missing = [c for c in children_shp if c not in nuts2_set]

    if not children_missing:
        continue  # all children present, nothing to do

    # We need the NUTS-1 total
    if n1_code not in latest_lookup:
        print(f"  WARNING: {n1_code} has missing children {children_missing} "
              f"but no NUTS-1 total available -- skipping")
        continue

    n1_km = latest_lookup[n1_code]

    if not children_in_eurostat:
        # --- Case A: ALL children missing -> split by area ---
        total_area = sum(nuts2_area.get(c, 0) for c in children_shp)
        if total_area == 0:
            print(f"  WARNING: {n1_code} -- zero total area for {children_shp}")
            continue
        print(f"  {n1_code} ({n1_km:.0f} km): ALL {len(children_shp)} children "
              f"missing -> area split")
        for c in children_shp:
            area_c = nuts2_area.get(c, 0)
            frac = area_c / total_area
            km_alloc = round(n1_km * frac, 3)
            gapfill_rows[c] = km_alloc
            print(f"    {c}: area={area_c:.1f} km², frac={frac:.4f}, "
                  f"highway_km={km_alloc:.3f}")
    else:
        # --- Case B: SOME children present -> residual for the missing ones ---
        sum_present = sum(latest_lookup.get(c, 0) for c in children_in_eurostat)
        residual = max(0, n1_km - sum_present)

        if len(children_missing) == 1:
            # Only one missing child: assign all the residual
            c = children_missing[0]
            gapfill_rows[c] = round(residual, 3)
            print(f"  {n1_code} ({n1_km:.0f} km): 1 child missing ({c}) -> "
                  f"residual = {n1_km:.0f} - {sum_present:.0f} = {residual:.0f} km")
        else:
            # Multiple missing children: split residual by area
            total_missing_area = sum(
                nuts2_area.get(c, 0) for c in children_missing
            )
            if total_missing_area == 0:
                print(f"  WARNING: {n1_code} -- zero area for missing children "
                      f"{children_missing}")
                continue
            print(f"  {n1_code} ({n1_km:.0f} km): {len(children_missing)} children "
                  f"missing -> residual {residual:.0f} km split by area")
            for c in children_missing:
                area_c = nuts2_area.get(c, 0)
                frac = area_c / total_missing_area
                km_alloc = round(residual * frac, 3)
                gapfill_rows[c] = km_alloc
                print(f"    {c}: area={area_c:.1f} km², frac={frac:.4f}, "
                      f"highway_km={km_alloc:.3f}")

print(f"\nGap-filled {len(gapfill_rows)} NUTS-2 regions")

# ── 7. Combine everything ────────────────────────────────────────────────────
# Start with the direct NUTS-2 data
result_dict = dict(zip(nuts2_direct.index, nuts2_direct["highway_km"]))

# Add/override with gap-filled data
result_dict.update(gapfill_rows)

# Build the result DataFrame
result = pd.DataFrame(
    {"highway_km": result_dict.values()},
    index=pd.Index(result_dict.keys(), name="NUTS2_CODE"),
)
result = result.sort_index()
result["highway_km"] = result["highway_km"].round(3)

print(f"\nTotal NUTS-2 regions in output: {len(result)}")
print(f"  of which German: {sum(1 for c in result.index if c.startswith('DE'))}")

# ── 8. Save ──────────────────────────────────────────────────────────────────
result.to_csv(OUTPUT_CSV)
print(f"\nSaved to: {OUTPUT_CSV}")

# ── 9. Sanity checks ────────────────────────────────────────────────────────
print("\n-- SANITY CHECKS --")
for country in ["DE", "IT", "AT", "SE", "DK", "NO", "FI"]:
    c_total_eurostat = latest_lookup.get(country, None)
    c_total_output = result.loc[result.index.str.startswith(country), "highway_km"].sum()
    if c_total_eurostat is not None:
        diff = c_total_output - c_total_eurostat
        print(f"  {country}: Eurostat country total = {c_total_eurostat:.0f} km, "
              f"sum of NUTS-2 = {c_total_output:.1f} km, diff = {diff:+.1f} km")

# ── 10. Comparison table for key border regions ─────────────────────────────
border_regions = [
    "AT33", "AT34", "DE14", "DE21", "DE27", "ITC4", "ITH1", "ITH2", "ITH3",
]

old_known = {
    "AT33": 68.6, "AT34": 47.3, "DE14": 76.6, "DE21": 310.0, "DE27": 129.4,
    "ITC4": 252.5, "ITH1": 29.2, "ITH2": 60.4, "ITH3": 374.7,
}

print("\n" + "=" * 80)
print("COMPARISON: Old vs New highway_km for key border regions")
print("=" * 80)
header = (
    f"{'NUTS2':<8} {'Old (file)':<14} {'Old (known)':<14} "
    f"{'New (Eurostat)':<16} {'Delta (new-known)':<18}"
)
print(header)
print("-" * 80)

for code in border_regions:
    old_file_val = old_values.get(code, None)
    old_known_val = old_known.get(code, None)
    new_val = result.loc[code, "highway_km"] if code in result.index else None

    old_file_str = f"{old_file_val:.3f}" if old_file_val is not None else "N/A"
    old_known_str = f"{old_known_val:.1f}" if old_known_val is not None else "N/A"
    new_str = f"{new_val:.3f}" if new_val is not None else "N/A"

    if new_val is not None and old_known_val is not None:
        delta = new_val - old_known_val
        delta_str = f"{delta:+.3f}"
    else:
        delta_str = "N/A"

    print(f"{code:<8} {old_file_str:<14} {old_known_str:<14} "
          f"{new_str:<16} {delta_str:<18}")

print("=" * 80)

# Print the year used for key regions
print("\n-- Year used for each border region --")
for code in border_regions:
    yr = latest.loc[latest["nuts_code"] == code, "year"]
    if len(yr) > 0:
        print(f"  {code}: {yr.values[0]} (direct from Eurostat)")
    elif code in gapfill_rows:
        parent = code[:3]
        yr_parent = latest.loc[latest["nuts_code"] == parent, "year"]
        if len(yr_parent) > 0:
            print(f"  {code}: derived from {parent} (year {yr_parent.values[0]})")
        else:
            print(f"  {code}: gap-filled (parent year unknown)")
    else:
        print(f"  {code}: NOT FOUND")
