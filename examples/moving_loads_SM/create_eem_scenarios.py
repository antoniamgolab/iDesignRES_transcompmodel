"""
Create EEM Paper Scenarios: German Electricity Market Zone Splitting
====================================================================

This script generates input data for the EEM conference paper analyzing
the impact of German electricity market zone splitting on the spatial
distribution of charging demand for long-haul battery-electric trucks.

Scenarios:
  1. Baseline (DE_unified): Single German electricity price zone (= existing Go RES)
  2. Zone split (DE_split): North/South German zone with differentiated prices

Zone definition (based on TSO boundaries, following Trepper et al. 2015,
Fraunholz et al. 2021, Zinke 2023):
  - SOUTH (Amprion + TransnetBW + Bavaria): Higher prices (demand centers)
  - NORTH (50Hertz + TenneT-North): Lower prices (wind-rich)

Price differentials based on literature:
  - Average differential: 2-3 EUR/MWh (Trepper et al. 2015, Knörr et al. 2025)
  - Applied symmetrically: North gets -delta/2, South gets +delta/2
    relative to the uniform German price

Usage:
  python create_eem_scenarios.py

Requires: Existing Go RES scenario in input_data/genesys_scenarios/go_res/

Author: Claude Code + Antonia Golab
Date: 2025-03-06
"""

import sys
import yaml
import os
import shutil
from pathlib import Path
from copy import deepcopy
import numpy as np

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from SM_preprocessing import SMParameterGenerator

# ============================================================================
# CONFIGURATION
# ============================================================================

# Source data for preprocessing (NUTS-2 level, includes domestic routes)
DATA_SOURCE = "input_data/fixed_nuts_2"

# Output directory for EEM scenarios
EEM_OUTPUT_DIR = SCRIPT_DIR / "input_data" / "eem_scenarios"

# Baseline dir (generated in Step 1 below)
BASELINE_DIR = EEM_OUTPUT_DIR / "DE_unified"

# Relative price differential (percentage of wholesale price, applied symmetrically)
#
# Literature basis for RELATIVE differentials:
#   - Fraunholz et al. (2021): Δp = -2% to -5% (North) / +5% to +16% (South)
#     → total N-S spread: ~5-18% of uniform price, time-varying
#   - Knörr et al. (2025): avg 4.77 EUR/MWh on ~47 EUR/MWh wholesale = ~10%
#   - BZR study (ENTSO-E 2024): ~7 EUR/MWh on ~47 EUR/MWh = ~15%
#   - Trepper et al. (2015): 1.55-3.56 EUR/MWh (smaller because earlier, less RES)
#   - Aurora (2023): 5-9 EUR/MWh over 2030-2045
#   - Diers et al. (2023, EWI+THEMA): 10-15 EUR/MWh (2024-2033)
#
# We apply the differential as a percentage of the wholesale electricity price.
# This ensures the absolute spread scales with the price level over time
# (larger when prices are high, smaller when prices fall with RES expansion).
#
# Applied symmetrically: North gets -pct/2, South gets +pct/2 of their
# wholesale price component. The CPO markup chain then amplifies this.
RELATIVE_DIFFERENTIALS_PCT = {
    "low":   5.0,   # Conservative (~Trepper et al. 2015 range)
    "mid":  10.0,   # Central estimate (Knörr et al. 2025, Fraunholz et al. 2021)
    "high": 20.0,   # Upper bound (Fraunholz et al. 2021 early-period spread)
}

# German NUTS-2 region to zone mapping
# Based on TSO boundaries: Trepper et al. (2015), Fraunholz et al. (2021)
DE_SOUTH_NUTS2 = {
    # Baden-Württemberg (TransnetBW)
    'DE11', 'DE12', 'DE13', 'DE14',
    # Bavaria (geographically South, though partly TenneT)
    'DE21', 'DE22', 'DE23', 'DE24', 'DE25', 'DE26', 'DE27',
    # Hesse (Amprion)
    'DE71', 'DE72', 'DE73',
    # Nordrhein-Westfalen (Amprion)
    'DEA1', 'DEA2', 'DEA3', 'DEA4', 'DEA5',
    # Rhineland-Palatinate (Amprion)
    'DEB1', 'DEB2', 'DEB3',
    # Saarland (Amprion)
    'DEC0',
}

DE_NORTH_NUTS2 = {
    # Berlin (50Hertz)
    'DE30',
    # Brandenburg (50Hertz)
    'DE40',
    # Bremen (TenneT)
    'DE50',
    # Hamburg (TenneT)
    'DE60',
    # Mecklenburg-Vorpommern (50Hertz)
    'DE80',
    # Lower Saxony (TenneT-North)
    'DE91', 'DE92', 'DE93', 'DE94',
    # Schleswig-Holstein (TenneT)
    'DEF0',
    # Saxony (50Hertz)
    'DED2', 'DED4', 'DED5',
    # Saxony-Anhalt (50Hertz)
    'DEE0',
    # Thuringia (50Hertz)
    'DEG0',
}

# CPO markup chain (must match SM_preprocessing.py):
# base price * 1.5 (base multiplier) * 0.97 (fast charging discount) for fast charging
# base price * 1.5 (base multiplier) * 1.075 (slow charging markup) for slow charging
# The zone-split delta is applied to the BASE wholesale price before markups.

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_yaml(filepath):
    """Load a YAML file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)


def save_yaml(data, filepath):
    """Save data to a YAML file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def copy_baseline(baseline_dir, output_dir):
    """Copy all baseline YAML files to output directory."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for f in Path(baseline_dir).glob("*.yaml"):
        shutil.copy2(f, output_dir / f.name)


def get_nuts2_for_geo(geo_element):
    """Extract NUTS-2 code from a geographic element."""
    return geo_element.get('nuts2_region', '')


def get_zone(nuts2_code):
    """Return 'north', 'south', or None for a NUTS-2 code."""
    if nuts2_code in DE_NORTH_NUTS2:
        return 'north'
    elif nuts2_code in DE_SOUTH_NUTS2:
        return 'south'
    return None


# ============================================================================
# MAIN SCENARIO GENERATION
# ============================================================================

def create_zone_split_scenario(baseline_dir, output_dir, differential_pct,
                                scenario_label="mid", split_from_year=2020):
    """
    Create a zone-split scenario by modifying electricity prices for German regions.

    The differential is applied as a RELATIVE change (percentage of the price):
      - North Germany: price * (1 - pct/200)   (cheaper, wind-rich)
      - South Germany: price * (1 + pct/200)   (more expensive, demand centers)

    split_from_year: year from which the zone split takes effect.
      Before this year, prices remain at baseline (unified zone).

    This means the absolute spread scales with the price level over time,
    which is consistent with Fraunholz et al. (2021) who report relative Δp.
    """
    print(f"\n{'='*70}")
    print(f"Creating zone-split scenario: {scenario_label}")
    print(f"  Relative differential: {differential_pct}% of price")
    print(f"  (North: -{differential_pct/2}%, South: +{differential_pct/2}%)")
    print(f"  Split effective from: {split_from_year}")
    print(f"  Output: {output_dir}")
    print(f"{'='*70}")

    # Step 1: Copy all baseline files
    copy_baseline(baseline_dir, output_dir)
    print(f"  Copied baseline files from {baseline_dir}")

    # Step 2: Load geographic elements to build geo_id -> zone mapping
    geo_elements = load_yaml(baseline_dir / "GeographicElement.yaml")
    geo_id_to_zone = {}
    geo_id_to_nuts2 = {}
    north_count = 0
    south_count = 0

    for geo in geo_elements:
        nuts2 = get_nuts2_for_geo(geo)
        zone = get_zone(nuts2)
        geo_id = geo['id']
        geo_id_to_nuts2[geo_id] = nuts2
        if zone:
            geo_id_to_zone[geo_id] = zone
            if zone == 'north':
                north_count += 1
            else:
                south_count += 1

    print(f"  German zones: {north_count} North nodes, {south_count} South nodes")
    print(f"  Non-German nodes (unchanged): "
          f"{len(geo_elements) - north_count - south_count}")

    # Step 3: Modify FuelCost.yaml with RELATIVE price changes
    fuel_costs = load_yaml(baseline_dir / "FuelCost.yaml")
    half_pct = differential_pct / 200.0  # e.g., 10% → 0.05 (±5%)

    # Index in the price array where the split takes effect
    # MODEL_YEARS = 2020..2060, so index = split_from_year - 2020
    split_idx = max(0, split_from_year - 2020)

    modified_count = 0
    sample_north_prices = None
    sample_south_prices = None
    sample_baseline_prices = None

    for fc in fuel_costs:
        location_id = fc['location']
        fuel_type = fc['fuel']

        # Only modify electricity prices for German zones
        if fuel_type != 'electricity':
            continue
        if location_id not in geo_id_to_zone:
            continue

        zone = geo_id_to_zone[location_id]

        # Apply relative differential only from split_from_year onwards.
        # Before that year, prices stay at baseline (unified zone).
        original_prices = fc['cost_per_kWh']

        if zone == 'north':
            fc['cost_per_kWh'] = [
                p * (1.0 - half_pct) if i >= split_idx else p
                for i, p in enumerate(original_prices)
            ]
            if sample_north_prices is None:
                sample_north_prices = fc['cost_per_kWh']
                sample_baseline_prices = original_prices
        else:  # south
            fc['cost_per_kWh'] = [
                p * (1.0 + half_pct) if i >= split_idx else p
                for i, p in enumerate(original_prices)
            ]
            if sample_south_prices is None:
                sample_south_prices = fc['cost_per_kWh']

        modified_count += 1

    print(f"  Modified {modified_count} FuelCost entries")

    # Save modified FuelCost
    save_yaml(fuel_costs, output_dir / "FuelCost.yaml")

    # Step 4: Save scenario metadata
    metadata = {
        'scenario_type': 'eem_zone_split',
        'scenario_label': scenario_label,
        'base_scenario': 'Go RES v1.2',
        'zone_split': {
            'differential_type': 'relative (percentage of price)',
            'differential_pct': differential_pct,
            'split_from_year': split_from_year,
            'north_adjustment': f'-{differential_pct/2}%',
            'south_adjustment': f'+{differential_pct/2}%',
            'north_zones': sorted(list(DE_NORTH_NUTS2)),
            'south_zones': sorted(list(DE_SOUTH_NUTS2)),
            'north_delta_direction': 'cheaper (wind-rich)',
            'south_delta_direction': 'more expensive (demand centers)',
            'application': f'relative: North × {1-half_pct:.3f}, South × {1+half_pct:.3f}, from {split_from_year}',
        },
        'literature_basis': [
            'Fraunholz et al. (2021) Energy Policy 149:111833 - relative delta_p of 5-18%',
            'Knorr et al. (2025) arXiv:2403.09265v6 - avg 4.77 EUR/MWh on ~47 EUR/MWh ~10%',
            'Trepper et al. (2015) Energy Policy 87:199-215 - 1.55-3.56 EUR/MWh',
            'Zinke (2023) EWI Working Paper 23/07',
        ],
    }
    save_yaml(metadata, output_dir / "eem_scenario_metadata.yaml")

    # Print summary of price changes
    print(f"\n  Price impact summary (relative +/-{differential_pct/2}%):")
    if sample_baseline_prices and sample_north_prices and sample_south_prices:
        for idx, label in [(0, "2020 (early)"), (15, "~2035 (mid)"), (-1, "2060 (late)")]:
            bp = sample_baseline_prices[idx] * 1000  # EUR/MWh
            np_ = sample_north_prices[idx] * 1000
            sp = sample_south_prices[idx] * 1000
            print(f"    {label}: baseline={bp:.1f}, North={np_:.1f} ({np_-bp:+.1f}), "
                  f"South={sp:.1f} ({sp-bp:+.1f}) EUR/MWh")
            print(f"      N-S spread: {sp-np_:.1f} EUR/MWh "
                  f"({(sp-np_)/bp*100:.1f}% of baseline)")

    return output_dir


def _sanitize_numpy_in_yamls(directory):
    """
    Re-save YAML files that may contain numpy scalar/array types,
    converting them to plain Python types so Julia's YAML parser can read them.
    """
    directory = Path(directory)
    files_to_check = ['Path.yaml', 'MandatoryBreaks.yaml']

    def _convert(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_convert(i) for i in obj]
        return obj

    for fname in files_to_check:
        fpath = directory / fname
        if not fpath.exists():
            continue
        with open(fpath, 'r') as f:
            data = yaml.unsafe_load(f)
        data = _convert(data)
        with open(fpath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        print(f"  Sanitized numpy types in {fname}")


def generate_baseline_with_preprocessing(output_dir):
    """
    Generate the baseline (unified zone) scenario using SM_preprocessing
    with keep_de_cross_zone=True to include German N-S domestic routes.
    """
    print(f"\n{'='*70}")
    print(f"GENERATING BASELINE with DE cross-zone domestic routes")
    print(f"  Source: {DATA_SOURCE}")
    print(f"  Output: {output_dir}")
    print(f"{'='*70}")

    generator = SMParameterGenerator(
        nuts3_data_dir=DATA_SOURCE,
        output_dir=str(output_dir),
        case_name="eem_baseline",
        electricity_prices_variable=True,
        network_costs_variable=True,
        cross_border_only=True,
        keep_de_cross_zone=True,
        require_through_country='DE',
        filter_low_volume=True,
        min_freight_threshold=500.0,
        filter_short_paths=True,
        min_path_length=360.0,
        genesys_scenario='Go RES v1.2',
    )

    generator.load_nuts3_data()
    generator.save_all_parameters()

    # Sanitize numpy types in generated YAML files (Julia's YAML parser can't read them)
    _sanitize_numpy_in_yamls(output_dir)

    # Add scenario metadata
    metadata = {
        'scenario_type': 'eem_baseline',
        'scenario_label': 'DE_unified',
        'base_scenario': 'Go RES v1.2',
        'zone_split': None,
        'description': 'Single German electricity market zone (status quo)',
        'route_scope': 'international + German domestic N-S cross-zone (>= 360 km, >= 500 t)',
    }
    save_yaml(metadata, output_dir / "eem_scenario_metadata.yaml")

    print(f"  Baseline generated with cross-zone domestic routes")
    return output_dir


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("EEM PAPER: GERMAN ELECTRICITY MARKET ZONE SPLITTING SCENARIOS")
    print("=" * 70)

    # Create output directory
    EEM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    created = []

    # Timing dimension: when does the zone split take effect?
    SPLIT_TIMINGS = {
        "2020": 2020,  # from the beginning
        "2032": 2032,  # delayed to 2032
        "2040": 2040,  # delayed to 2040
    }

    # 1. Generate baseline using preprocessing (includes DE cross-zone routes)
    baseline_out = generate_baseline_with_preprocessing(
        EEM_OUTPUT_DIR / "DE_unified"
    )
    created.append(("DE_unified", "Baseline (single zone, incl. DE N-S routes)"))

    # 2. Zone split scenarios: 3 spread levels × 3 timing variants = 9 scenarios
    for level, pct in RELATIVE_DIFFERENTIALS_PCT.items():
        for timing_label, timing_year in SPLIT_TIMINGS.items():
            folder_name = f"DE_split_{level}_from{timing_label}"
            out = create_zone_split_scenario(
                BASELINE_DIR,
                EEM_OUTPUT_DIR / folder_name,
                differential_pct=pct,
                scenario_label=folder_name,
                split_from_year=timing_year,
            )
            created.append((folder_name, f"Zone split ±{pct/2}%, from {timing_year}"))

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Output directory: {EEM_OUTPUT_DIR}")
    print(f"\nCreated {len(created)} scenarios:")
    for name, desc in created:
        print(f"  {name:20s} - {desc}")
    print(f"\nNext steps:")
    print(f"  1. Run: julia SM_batch_eem.jl")
    print(f"{'='*70}")
