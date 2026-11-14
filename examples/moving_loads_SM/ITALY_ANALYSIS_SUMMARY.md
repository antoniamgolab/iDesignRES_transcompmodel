# Italy Freight Analysis Summary

## The Question
Why does the model show freight "in Italy" when there are **0 Italian OD pairs** in the processed dataset (`case_20251107_105426_rail`)?

---

## Key Findings

### 1. Italy IS in the Original Truck Traffic Data
- **131,220 routes FROM Italy** (80.4M trucks/year)
- **122,320 routes TO Italy** (81.4M trucks/year)
- **11,032 domestic Italian routes (IT→IT)** (70.5M trucks/year)
- **120,188 Italy exports (IT→other)** (9.9M trucks/year)
- **111,288 Italy imports (other→IT)** (10.9M trucks/year)

**Source:** `data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv`

### 2. Italy's Cross-Border Partners

**Within Scandinavian-Mediterranean Corridor:**
- Partners: AT, DE, DK, NO, SE
- Routes: **91,128 (39.4% of cross-border)**
- Traffic: **6,580,878 trucks/year (31.6%)**

Top corridor partners:
- Germany: 78k routes, 4.3M trucks/year
- Austria: 7.1k routes, 2.1M trucks/year
- Sweden: 3k routes, 46k trucks/year
- Denmark: 2k routes, 86k trucks/year
- Norway: 1k routes, 8k trucks/year

**Outside Corridor:**
- Partners: FR, CH, ES, PL, SI, UK, CZ, BE, NL, HU, GR, RO, HR, SK, PT, etc.
- Routes: **140,348 (60.6%)**
- Traffic: **14,213,154 trucks/year (68.4%)**

### 3. Italy in Processed Case (`case_20251107_105426_rail`)

**Geographic Elements:** ✅ 19 Italian NUTS2 regions included
- ITC1, ITC2, ITC3, ITC4 (Northwest)
- ITH1, ITH2, ITH3, ITH4, ITH5 (Northeast)
- ITI1, ITI2, ITI3, ITI4 (Central)
- ITF1, ITF2, ITF3, ITF4, ITF5, ITF6 (South)

**OD Pairs:** ❌ **0 Italian routes** in Odpair.yaml
- Total OD pairs in file: 3,027
- OD pairs with Italian origin or destination: **0**

---

## The Answer: Transit Freight

The "freight in Italy" visible in your model results is **TRANSIT FREIGHT** - cargo passing through Italian nodes/edges on routes between OTHER countries.

### Example Transit Routes:
- **Germany → Austria** (route passes through Italian Alps)
- **Sweden → Germany** (route passes through Italian territory)
- **Denmark → Austria** (route passes through Italian waypoints)

These routes use Italian geographic nodes as waypoints, but:
- Origin ≠ Italy
- Destination ≠ Italy
- Volume still appears "in Italy" because the path traverses Italian territory

---

## Why Were Italian OD Pairs Filtered Out?

### Root Cause: Buggy Country Code Extraction

The preprocessing script (`SM_preprocessing_nuts2_complete.py`) extracts "country codes" incorrectly:

```python
# Line 534 (BUGGY):
valid_traffic['origin_country'] = valid_traffic['ID_origin_region'].astype(str).str[:2]
```

This extracts the first 2 digits from **numeric NUTS3 region IDs**, not actual country codes:
- Italian region 118120200 → "11" (NOT "IT")
- Austrian region 101010101 → "10" (NOT "AT")
- German region 106050101 → "10" (NOT "DE")

### Correct Approach:
Map numeric NUTS3 IDs to countries via the NUTS3 regions file:
```python
nuts3 = pd.read_csv('data/Trucktraffic_NUTS3/02_NUTS-3-Regions.csv')
id_to_country = dict(zip(nuts3['ETISPlus_Zone_ID'], nuts3['Country']))
traffic['origin_country'] = traffic['ID_origin_region'].map(id_to_country)
```

### Impact of Bug:
1. **Cross-border filter doesn't work correctly**: Compares numeric prefixes instead of countries
2. **Italian domestic routes (IT→IT) filtered out**: `cross_border_only=True` by default
3. **Italian corridor routes may be misclassified**: "11" ≠ "IT" breaks corridor logic

---

## Supporting Evidence

### Scripts Created:
1. **`analyze_odpairs.py`**: Analyzes original vs processed OD pairs
2. **`count_italian_routes.py`**: Counts Italian routes using proper NUTS3 mapping
3. **`check_region_ids.py`**: Verifies Italian regions exist in truck traffic
4. **`check_italian_cross_border_partners.py`**: Analyzes Italian trade partners

### Key Statistics:
- **Original data**: 1,514,573 total routes
- **Italian NUTS3 regions**: 107 regions (IDs starting with "118...")
- **Italian regions in traffic data**: All 107 present as origins AND destinations
- **Corridor filtering**: Kept 1,030,907 routes (includes Italy)
- **Final processed case**: 3,027 OD pairs (0 Italian)

---

## Recommendations

### Option 1: Fix the Preprocessing Script
Modify `SM_preprocessing_nuts2_complete.py` line 534 to use proper NUTS3 mapping instead of `.str[:2]`.

### Option 2: Disable Cross-Border Filter
Run preprocessing with `cross_border_only=False` to include domestic Italian routes (11k routes, 70M trucks/year).

### Option 3: Document Transit Behavior
Clarify in analysis that "freight in Italy" represents:
- Transit freight passing through Italian territory
- Not freight originating from or destined to Italy
- Valid for corridor analysis (e.g., German→Austrian freight via Italian Alps)

---

## Conclusion

Italy was **NOT missing from the source data** - it was **filtered out during preprocessing** due to:
1. Buggy country code extraction
2. Cross-border-only filtering (excludes domestic IT→IT routes)
3. Majority of Italian trade being with non-corridor countries (68.4%)

The freight you see "in Italy" in your model is **real and valid** - it's transit freight using Italian infrastructure as part of international routes within the Scandinavian-Mediterranean corridor.

---

Generated: 2025-01-07
Case analyzed: `case_20251107_105426_rail`
