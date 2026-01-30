"""
Detour Function Curve Validation
=================================
Validates the theoretical detour-time curve by:
1. Using current charging infrastructure as baseline
2. Randomly removing chargers to simulate lower capacity states
3. Measuring empirical detour times at each capacity level
4. Comparing empirical points to theoretical curves

This approach reconstructs the curve empirically to validate the model.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
import json
import os
from typing import List, Tuple, Dict
from math import radians, sin, cos, sqrt, atan2

try:
    import geopandas as gpd
    from shapely.geometry import Point
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False

# =============================================================================
# CONFIGURATION
# =============================================================================

TOTAL_AREA_KM2 = 7234  # Basque Country total area (km2)
SPEED_KMH = 30  # Average speed for time calculation (km/h)
CIRCUITY_FACTOR = 1.4  # Aerial to driving distance factor

# Monte Carlo settings
N_CAPACITY_SAMPLES = 20  # Random configurations per capacity level
N_RANDOM_POINTS = 1000  # Random origin points per configuration

# Capacity levels to test (as fraction of total)
CAPACITY_FRACTIONS = [1.0, 0.75, 0.50, 0.25, 0.10]

# OpenChargeMap API
OCM_API_URL = "https://api.openchargemap.io/v3/poi/"
OCM_API_KEY = "cc50de4b-52dc-4b87-a031-ad3b7650c0e0"

# NUTS shapefile path
NUTS_SHAPEFILE = "c:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/iDesignRES_transcompmodel/examples/moving_loads_SM/data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp"
BASQUE_NUTS2 = "ES21"

# Basque Country center and search radius
BASQUE_CENTER = (43.0, -2.5)
SEARCH_RADIUS_KM = 80

# Power threshold for fast vs slow charging (kW)
FAST_CHARGING_THRESHOLD = 22


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great circle distance in km."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))


def load_nuts_boundary(nuts_code: str = BASQUE_NUTS2):
    """Load NUTS boundary from Eurostat shapefile."""
    if not HAS_GEOPANDAS or not os.path.exists(NUTS_SHAPEFILE):
        return None

    try:
        gdf = gpd.read_file(NUTS_SHAPEFILE)
        mask = (gdf['LEVL_CODE'] == 2) & (gdf['NUTS_ID'] == nuts_code)
        region = gdf[mask]
        if len(region) > 0:
            return region.geometry.values[0]
    except Exception as e:
        print(f"Error loading NUTS: {e}")
    return None


class BoundaryHandler:
    """Handles boundary checking."""

    def __init__(self):
        self.geometry = load_nuts_boundary()
        if self.geometry:
            bounds = self.geometry.bounds
            self.bbox = {'min_lon': bounds[0], 'min_lat': bounds[1],
                        'max_lon': bounds[2], 'max_lat': bounds[3]}
            print(f"Using NUTS boundary for ES21")
        else:
            self.bbox = {'min_lat': 42.45, 'max_lat': 43.45,
                        'min_lon': -3.45, 'max_lon': -1.72}
            print("Using fallback boundary")

    def contains(self, lon: float, lat: float) -> bool:
        if self.geometry:
            return self.geometry.contains(Point(lon, lat))
        return True  # Simplified

    def generate_random_point(self) -> Tuple[float, float]:
        for _ in range(100):
            lat = np.random.uniform(self.bbox['min_lat'], self.bbox['max_lat'])
            lon = np.random.uniform(self.bbox['min_lon'], self.bbox['max_lon'])
            if self.contains(lon, lat):
                return (lat, lon)
        return (BASQUE_CENTER[0], BASQUE_CENTER[1])


def fetch_chargers(use_cache: bool = True) -> pd.DataFrame:
    """Fetch charging station data from OpenChargeMap API."""
    cache_file = 'data/ocm_chargers_basque.json'

    if use_cache and os.path.exists(cache_file):
        print("Loading charger data from cache...")
        with open(cache_file, 'r') as f:
            data = json.load(f)
    else:
        print("Fetching charger data from API...")
        params = {
            'output': 'json', 'latitude': BASQUE_CENTER[0], 'longitude': BASQUE_CENTER[1],
            'distance': SEARCH_RADIUS_KM, 'distanceunit': 'KM', 'maxresults': 500,
            'compact': 'false', 'verbose': 'false', 'key': OCM_API_KEY
        }
        response = requests.get(OCM_API_URL, params=params, timeout=30)
        data = response.json()
        os.makedirs('data', exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(data, f)

    chargers = []
    for station in data:
        try:
            lat = station.get('AddressInfo', {}).get('Latitude')
            lon = station.get('AddressInfo', {}).get('Longitude')
            if lat is None or lon is None:
                continue

            connections = station.get('Connections', [])
            max_power = 0
            total_power = 0
            for conn in connections:
                power = conn.get('PowerKW') or 0
                if power > max_power:
                    max_power = power
                total_power += power

            if total_power == 0:
                total_power = 22 * max(1, len(connections))

            chargers.append({
                'id': station.get('ID'), 'lat': lat, 'lon': lon,
                'power_kw': total_power, 'max_power_kw': max_power,
                'is_fast': max_power >= FAST_CHARGING_THRESHOLD
            })
        except Exception:
            continue

    return pd.DataFrame(chargers)


def theoretical_detour(power_kw: float, area_km2: float = TOTAL_AREA_KM2,
                       pts_per_site: int = 10, avg_power: float = 22,
                       alpha: float = CIRCUITY_FACTOR, speed: float = SPEED_KMH) -> float:
    """Calculate theoretical detour time based on spatial model."""
    if power_kw <= 0:
        return float('inf')
    nb_sites = max(1, (power_kw / avg_power) / pts_per_site)
    d_aerial = 0.5 * np.sqrt(area_km2 / nb_sites) * alpha
    return d_aerial * 2 * (60 / speed)  # Round-trip time in minutes


def sample_chargers_by_capacity(chargers: pd.DataFrame, target_capacity_kw: float) -> pd.DataFrame:
    """
    Randomly sample chargers to achieve approximately the target capacity.
    Removes chargers randomly until we're at or below target capacity.
    """
    if chargers.empty:
        return chargers

    current_capacity = chargers['power_kw'].sum()

    if current_capacity <= target_capacity_kw:
        return chargers

    # Shuffle and remove until we reach target
    shuffled = chargers.sample(frac=1).reset_index(drop=True)

    selected = []
    running_capacity = 0

    for _, charger in shuffled.iterrows():
        if running_capacity + charger['power_kw'] <= target_capacity_kw:
            selected.append(charger)
            running_capacity += charger['power_kw']
        elif running_capacity < target_capacity_kw * 0.9:
            # Allow slight overshoot to get closer to target
            selected.append(charger)
            running_capacity += charger['power_kw']
            if running_capacity >= target_capacity_kw * 0.95:
                break

    return pd.DataFrame(selected)


def measure_detour_time(chargers: pd.DataFrame, boundary: BoundaryHandler,
                        n_points: int = N_RANDOM_POINTS) -> float:
    """Measure average detour time for a given charger configuration."""
    if chargers.empty:
        return float('inf')

    charger_coords = [(r['lat'], r['lon']) for _, r in chargers.iterrows()]

    distances = []
    for _ in range(n_points):
        origin = boundary.generate_random_point()

        # Find nearest charger
        min_dist = float('inf')
        for charger in charger_coords:
            d = haversine(origin[0], origin[1], charger[0], charger[1])
            if d < min_dist:
                min_dist = d

        # Apply circuity factor
        driving_dist = min_dist * CIRCUITY_FACTOR
        distances.append(driving_dist)

    # Convert to round-trip time
    mean_dist = np.mean(distances)
    return mean_dist * 2 * (60 / SPEED_KMH)


def run_curve_validation(chargers: pd.DataFrame, boundary: BoundaryHandler,
                         capacity_fractions: List[float] = CAPACITY_FRACTIONS,
                         n_samples: int = N_CAPACITY_SAMPLES,
                         charger_type: str = "all") -> Dict:
    """
    Run Monte Carlo simulation at multiple capacity levels to reconstruct the curve.
    """
    total_capacity = chargers['power_kw'].sum()
    avg_power = total_capacity / len(chargers) if len(chargers) > 0 else 22

    print(f"\n{'='*60}")
    print(f"CURVE VALIDATION: {charger_type.upper()}")
    print(f"{'='*60}")
    print(f"Total chargers: {len(chargers)}")
    print(f"Total capacity: {total_capacity:.0f} kW")
    print(f"Avg power/station: {avg_power:.1f} kW")
    print(f"Capacity levels: {capacity_fractions}")
    print(f"Samples per level: {n_samples}")

    results = {
        'capacity_kw': [],
        'mean_detour': [],
        'std_detour': [],
        'n_chargers': [],
        'theoretical_distributed': [],
        'theoretical_balanced': [],
        'theoretical_concentrated': []
    }

    for frac in capacity_fractions:
        target_capacity = total_capacity * frac
        print(f"\n  Testing {frac*100:.0f}% capacity ({target_capacity:.0f} kW)...")

        detour_times = []
        charger_counts = []

        for sample in range(n_samples):
            # Sample chargers to reach target capacity
            sampled = sample_chargers_by_capacity(chargers, target_capacity)
            actual_capacity = sampled['power_kw'].sum()

            # Measure detour time for this configuration
            detour = measure_detour_time(sampled, boundary)
            detour_times.append(detour)
            charger_counts.append(len(sampled))

            if (sample + 1) % 5 == 0:
                print(f"    Sample {sample + 1}/{n_samples}: {len(sampled)} chargers, {detour:.1f} min")

        # Store results
        actual_capacity = np.mean([chargers['power_kw'].sum() * frac for _ in range(n_samples)])
        actual_capacity = target_capacity  # Use target for consistency

        results['capacity_kw'].append(actual_capacity)
        results['mean_detour'].append(np.mean(detour_times))
        results['std_detour'].append(np.std(detour_times))
        results['n_chargers'].append(np.mean(charger_counts))

        # Theoretical predictions at this capacity
        results['theoretical_distributed'].append(theoretical_detour(actual_capacity, avg_power=avg_power, pts_per_site=2))
        results['theoretical_balanced'].append(theoretical_detour(actual_capacity, avg_power=avg_power, pts_per_site=10))
        results['theoretical_concentrated'].append(theoretical_detour(actual_capacity, avg_power=avg_power, pts_per_site=40))

        print(f"    Mean detour: {np.mean(detour_times):.1f} +/- {np.std(detour_times):.1f} min")

    return results


def plot_curve_validation(results: Dict, charger_type: str, avg_power: float,
                          color: str, filename_suffix: str):
    """Plot the curve validation results."""
    fig, ax = plt.subplots(figsize=(10, 7))

    # Plot theoretical curves
    power_range = np.linspace(500, 40000, 100)

    strategies = {
        'Distributed (2 pts/site)': (2, '#4f6d7a', '--'),
        'Balanced (10 pts/site)': (10, '#840032', '-'),
        'Concentrated (40 pts/site)': (40, '#dd6e42', '--')
    }

    for name, (pts, col, ls) in strategies.items():
        times = [theoretical_detour(p, avg_power=avg_power, pts_per_site=pts) for p in power_range]
        ax.plot(power_range, times, ls, color=col, linewidth=2, label=name, alpha=0.8)

    # Plot empirical points with error bars
    ax.errorbar(results['capacity_kw'], results['mean_detour'],
                yerr=results['std_detour'],
                fmt='o', color=color, markersize=12, capsize=8, capthick=2,
                label=f'Empirical ({charger_type})', zorder=10, linewidth=2)

    # Connect empirical points with a line
    ax.plot(results['capacity_kw'], results['mean_detour'],
            '-', color=color, alpha=0.5, linewidth=1.5)

    # Add annotations for each point
    for i, (cap, det, n) in enumerate(zip(results['capacity_kw'],
                                           results['mean_detour'],
                                           results['n_chargers'])):
        ax.annotate(f'{n:.0f} stations',
                   xy=(cap, det), xytext=(10, 10),
                   textcoords='offset points', fontsize=9,
                   color=color, alpha=0.8)

    ax.axhline(y=5, color='gray', linestyle=':', alpha=0.5)
    ax.text(35000, 6, '5 min threshold', fontsize=9, color='gray')

    ax.set_xlabel('Installed Capacity (kW)', fontsize=12)
    ax.set_ylabel('Average Detour Time (minutes)', fontsize=12)
    ax.set_title(f'Detour Time vs Capacity - {charger_type}\n(Empirical Curve Validation)', fontsize=14)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 40000)
    ax.set_ylim(0, 100)

    plt.tight_layout()

    # Save
    os.makedirs('results', exist_ok=True)
    fig.savefig(f'results/curve_validation_{filename_suffix}.png', dpi=300, bbox_inches='tight')
    fig.savefig(f'results/curve_validation_{filename_suffix}.pdf', bbox_inches='tight')
    print(f"Figure saved: results/curve_validation_{filename_suffix}.png")

    return fig


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("DETOUR FUNCTION CURVE VALIDATION")
    print("Reconstructing the curve by sampling at different capacity levels")
    print("=" * 70)

    # Load boundary and chargers
    boundary = BoundaryHandler()
    chargers = fetch_chargers(use_cache=True)

    # Filter to boundary
    chargers_in_boundary = chargers[chargers.apply(
        lambda r: boundary.contains(r['lon'], r['lat']), axis=1)]
    print(f"Chargers within boundary: {len(chargers_in_boundary)}")

    # Split by type
    fast_chargers = chargers_in_boundary[chargers_in_boundary['is_fast'] == True].copy()
    slow_chargers = chargers_in_boundary[chargers_in_boundary['is_fast'] == False].copy()

    print(f"\nFast chargers: {len(fast_chargers)} ({fast_chargers['power_kw'].sum():.0f} kW)")
    print(f"Slow chargers: {len(slow_chargers)} ({slow_chargers['power_kw'].sum():.0f} kW)")

    # Calculate average power per station
    avg_power_fast = fast_chargers['power_kw'].sum() / len(fast_chargers) if len(fast_chargers) > 0 else 50
    avg_power_slow = slow_chargers['power_kw'].sum() / len(slow_chargers) if len(slow_chargers) > 0 else 11

    # Run validation for FAST chargers
    results_fast = run_curve_validation(fast_chargers, boundary, charger_type="Fast Charging (>22kW)")
    plot_curve_validation(results_fast, "Fast Charging (>22kW)", avg_power_fast, '#e74c3c', 'fast')

    # Run validation for SLOW chargers
    results_slow = run_curve_validation(slow_chargers, boundary, charger_type="Slow Charging (<=22kW)")
    plot_curve_validation(results_slow, "Slow Charging (<=22kW)", avg_power_slow, '#3498db', 'slow')

    # Save results
    results_df = pd.DataFrame({
        'capacity_fraction': CAPACITY_FRACTIONS,
        'fast_capacity_kw': results_fast['capacity_kw'],
        'fast_mean_detour': results_fast['mean_detour'],
        'fast_std_detour': results_fast['std_detour'],
        'fast_n_chargers': results_fast['n_chargers'],
        'slow_capacity_kw': results_slow['capacity_kw'],
        'slow_mean_detour': results_slow['mean_detour'],
        'slow_std_detour': results_slow['std_detour'],
        'slow_n_chargers': results_slow['n_chargers']
    })
    results_df.to_csv('results/curve_validation_results.csv', index=False)
    print("\nResults saved: results/curve_validation_results.csv")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print("\nFAST CHARGING:")
    for i, frac in enumerate(CAPACITY_FRACTIONS):
        print(f"  {frac*100:3.0f}% capacity: {results_fast['mean_detour'][i]:.1f} +/- {results_fast['std_detour'][i]:.1f} min "
              f"({results_fast['n_chargers'][i]:.0f} stations)")

    print("\nSLOW CHARGING:")
    for i, frac in enumerate(CAPACITY_FRACTIONS):
        print(f"  {frac*100:3.0f}% capacity: {results_slow['mean_detour'][i]:.1f} +/- {results_slow['std_detour'][i]:.1f} min "
              f"({results_slow['n_chargers'][i]:.0f} stations)")

    plt.show()

    return results_fast, results_slow


if __name__ == "__main__":
    results_fast, results_slow = main()
