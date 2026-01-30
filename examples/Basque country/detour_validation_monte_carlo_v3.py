"""
Detour Function Monte Carlo Validation (v3)
============================================
Validates the theoretical detour-time function g(q) against
empirical charger data using:
- Real charging infrastructure from OpenChargeMap API
- Official NUTS boundary polygon from Eurostat
- OpenRouteService for road snapping and actual driving distances

Requirements:
    pip install requests numpy pandas matplotlib geopandas shapely openrouteservice

Data sources:
- OpenChargeMap API: Real charging station locations
- NUTS shapefile: Official Eurostat administrative boundaries
- OpenRouteService: Road snapping and driving distances
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
import json
import time
import os
from typing import List, Tuple, Dict, Optional
from math import radians, sin, cos, sqrt, atan2

try:
    import geopandas as gpd
    from shapely.geometry import Point, Polygon
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False
    print("Warning: geopandas not installed. Using simplified boundary.")

# =============================================================================
# CONFIGURATION
# =============================================================================

TOTAL_AREA_KM2 = 7234  # Basque Country total area (km2)
SPEED_KMH = 30  # Average speed for time calculation (km/h)
N_MONTE_CARLO = 10  # Number of Monte Carlo iterations (set to 100 for full run)
N_RANDOM_POINTS = 50  # Random points per iteration

# OpenChargeMap API
OCM_API_URL = "https://api.openchargemap.io/v3/poi/"
OCM_API_KEY = "cc50de4b-52dc-4b87-a031-ad3b7650c0e0"

# OpenRouteService API
# Get your free API key at: https://openrouteservice.org/dev/#/signup
ORS_API_KEY = "5b3ce3597851110001cf6248777243bb45eb4261a5d5f9c15d8ff7e7"
ORS_BASE_URL = "https://api.openrouteservice.org"
USE_ORS = True  # Set to True to use OpenRouteService

# Rate limiting - ORS free tier allows ~40 requests/minute
ORS_RATE_LIMIT_DELAY = 2.0  # Seconds between ORS batch requests (need ~1.5s minimum)
ORS_MATRIX_BATCH_SIZE = 7  # Origins per matrix request (with ~471 destinations)
ORS_MAX_RETRIES = 3  # Max retries on rate limit
ORS_RETRY_BACKOFF = 5.0  # Initial backoff in seconds, doubles each retry

# NUTS shapefile path
NUTS_SHAPEFILE = "c:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/iDesignRES_transcompmodel/examples/moving_loads_SM/data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp"

# Basque Country NUTS codes
BASQUE_NUTS2 = "ES21"  # Pais Vasco

# Basque Country bounding box (for API queries)
BASQUE_CENTER = (43.0, -2.5)
SEARCH_RADIUS_KM = 80

# Power threshold for fast vs slow charging (kW)
FAST_CHARGING_THRESHOLD = 22

# Circuity factor (fallback if ORS fails)
CIRCUITY_FACTOR = 1.4

# =============================================================================
# BOUNDARY FUNCTIONS
# =============================================================================

def load_nuts_boundary(nuts_code: str = BASQUE_NUTS2, level: int = 2) -> Optional[Polygon]:
    """Load NUTS boundary from official Eurostat shapefile."""
    if not HAS_GEOPANDAS:
        print("geopandas not available, using fallback boundary")
        return None

    if not os.path.exists(NUTS_SHAPEFILE):
        print(f"NUTS shapefile not found: {NUTS_SHAPEFILE}")
        return None

    print(f"Loading NUTS boundary from: {NUTS_SHAPEFILE}")

    try:
        gdf = gpd.read_file(NUTS_SHAPEFILE)
        level_col = 'LEVL_CODE'
        id_col = 'NUTS_ID'

        if level_col in gdf.columns and id_col in gdf.columns:
            mask = (gdf[level_col] == level) & (gdf[id_col] == nuts_code)
            region = gdf[mask]

            if len(region) == 0:
                mask = gdf[id_col] == nuts_code
                region = gdf[mask]

            if len(region) > 0:
                geometry = region.geometry.values[0]
                print(f"Loaded NUTS boundary: {nuts_code} ({region['NUTS_NAME'].values[0] if 'NUTS_NAME' in region.columns else 'Unknown'})")
                return geometry
            else:
                print(f"NUTS code {nuts_code} not found in shapefile")
                return None
        else:
            print(f"Required columns not found. Available: {gdf.columns.tolist()}")
            return None

    except Exception as e:
        print(f"Error loading NUTS boundary: {e}")
        return None


def get_fallback_boundary() -> List[Tuple[float, float]]:
    """Simplified fallback boundary for Basque Country."""
    return [
        (-3.411, 43.390), (-3.300, 43.420), (-3.100, 43.380), (-2.900, 43.400),
        (-2.700, 43.450), (-2.500, 43.420), (-2.300, 43.400), (-2.100, 43.380),
        (-1.900, 43.350), (-1.780, 43.320), (-1.720, 43.280), (-1.750, 43.100),
        (-1.800, 42.900), (-1.850, 42.750), (-2.000, 42.600), (-2.200, 42.500),
        (-2.400, 42.450), (-2.600, 42.480), (-2.800, 42.550), (-3.000, 42.650),
        (-3.150, 42.800), (-3.300, 42.950), (-3.400, 43.100), (-3.450, 43.250),
        (-3.411, 43.390)
    ]


def point_in_polygon_simple(lon: float, lat: float, polygon: List[Tuple[float, float]]) -> bool:
    """Check if point is inside polygon using ray casting algorithm."""
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if lat > min(p1y, p2y):
            if lat <= max(p1y, p2y):
                if lon <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (lat - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or lon <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


class BoundaryHandler:
    """Handles boundary checking with NUTS or fallback polygon."""

    def __init__(self):
        self.nuts_geometry = load_nuts_boundary(BASQUE_NUTS2, level=2)
        self.fallback_polygon = get_fallback_boundary()
        self.use_nuts = self.nuts_geometry is not None and HAS_GEOPANDAS

        if self.use_nuts:
            bounds = self.nuts_geometry.bounds
            self.bbox = {
                'min_lon': bounds[0],
                'min_lat': bounds[1],
                'max_lon': bounds[2],
                'max_lat': bounds[3]
            }
            print(f"Using official NUTS boundary (bbox: {self.bbox})")
        else:
            self.bbox = {
                'min_lat': 42.45, 'max_lat': 43.45,
                'min_lon': -3.45, 'max_lon': -1.72
            }
            print("Using fallback boundary polygon")

    def contains(self, lon: float, lat: float) -> bool:
        """Check if point is inside the boundary."""
        if self.use_nuts:
            point = Point(lon, lat)
            return self.nuts_geometry.contains(point)
        else:
            return point_in_polygon_simple(lon, lat, self.fallback_polygon)

    def get_boundary_coords(self) -> List[Tuple[float, float]]:
        """Get boundary coordinates for plotting."""
        if self.use_nuts:
            if hasattr(self.nuts_geometry, 'exterior'):
                coords = list(self.nuts_geometry.exterior.coords)
            else:
                largest = max(self.nuts_geometry.geoms, key=lambda x: x.area)
                coords = list(largest.exterior.coords)
            return [(c[0], c[1]) for c in coords]
        else:
            return self.fallback_polygon

    def generate_random_point(self) -> Tuple[float, float]:
        """Generate a random point inside the boundary."""
        max_attempts = 100
        for _ in range(max_attempts):
            lat = np.random.uniform(self.bbox['min_lat'], self.bbox['max_lat'])
            lon = np.random.uniform(self.bbox['min_lon'], self.bbox['max_lon'])
            if self.contains(lon, lat):
                return (lat, lon)
        return (BASQUE_CENTER[0], BASQUE_CENTER[1])


# =============================================================================
# DATA FETCHING FUNCTIONS
# =============================================================================

def fetch_chargers_from_ocm(use_cache: bool = True) -> pd.DataFrame:
    """Fetch charging station data from OpenChargeMap API."""
    cache_file = 'data/ocm_chargers_basque.json'

    if use_cache and os.path.exists(cache_file):
        print("Loading charger data from cache...")
        with open(cache_file, 'r') as f:
            data = json.load(f)
    else:
        print("Fetching charger data from OpenChargeMap API...")
        params = {
            'output': 'json',
            'latitude': BASQUE_CENTER[0],
            'longitude': BASQUE_CENTER[1],
            'distance': SEARCH_RADIUS_KM,
            'distanceunit': 'KM',
            'maxresults': 500,
            'compact': 'false',
            'verbose': 'false',
            'key': OCM_API_KEY
        }

        try:
            response = requests.get(OCM_API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            os.makedirs('data', exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            print(f"Fetched and cached {len(data)} charging stations")
        except Exception as e:
            print(f"Error fetching from API: {e}")
            return pd.DataFrame()

    # Parse the data
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
            num_points = len(connections)

            for conn in connections:
                power = conn.get('PowerKW') or 0
                if power > max_power:
                    max_power = power
                total_power += power

            if total_power == 0:
                total_power = 22 * max(1, num_points)

            chargers.append({
                'id': station.get('ID'),
                'lat': lat,
                'lon': lon,
                'power_kw': total_power,
                'max_power_kw': max_power,
                'num_points': num_points,
                'is_fast': max_power >= FAST_CHARGING_THRESHOLD,
                'name': station.get('AddressInfo', {}).get('Title', 'Unknown'),
                'town': station.get('AddressInfo', {}).get('Town', 'Unknown')
            })
        except Exception:
            continue

    df = pd.DataFrame(chargers)
    print(f"Parsed {len(df)} valid charging stations")
    return df


# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great circle distance in km."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))


class OpenRouteServiceClient:
    """Client for OpenRouteService API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = ORS_BASE_URL
        self.headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }
        self.snap_success = 0
        self.snap_fallback = 0
        self.matrix_success = 0
        self.matrix_fallback = 0
        self.route_success = 0
        self.route_fallback = 0

    def snap_to_road(self, points: List[Tuple[float, float]], radius: float = 350) -> List[Tuple[float, float]]:
        """
        Snap points to nearest road segment using ORS snap endpoint.

        Args:
            points: List of (lat, lon) tuples
            radius: Maximum snapping radius in meters (max 350m)

        Returns:
            List of snapped (lat, lon) tuples
        """
        if not points:
            return []

        # ORS expects [lon, lat] format
        locations = [[p[1], p[0]] for p in points]

        url = f"{self.base_url}/v2/snap/driving-car"
        body = {
            'locations': locations,
            'radius': min(radius, 350)  # Max 350m
        }

        # Retry logic with exponential backoff
        for retry in range(ORS_MAX_RETRIES + 1):
            try:
                response = requests.post(url, json=body, headers=self.headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    snapped = []
                    locations_result = data.get('locations', [])

                    for i, loc in enumerate(locations_result):
                        if loc is not None and 'location' in loc:
                            # ORS returns [lon, lat], convert to (lat, lon)
                            snapped.append((loc['location'][1], loc['location'][0]))
                            self.snap_success += 1
                        else:
                            # Keep original point if snapping failed
                            snapped.append(points[i])
                            self.snap_fallback += 1

                    return snapped
                elif response.status_code == 429:
                    # Rate limit - retry with backoff
                    if retry < ORS_MAX_RETRIES:
                        wait_time = ORS_RETRY_BACKOFF * (2 ** retry)
                        print(f"  Snap rate limit, waiting {wait_time:.0f}s (retry {retry + 1}/{ORS_MAX_RETRIES})")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.snap_fallback += len(points)
                        return points
                else:
                    print(f"  Snap API error {response.status_code}: {response.text[:200]}")
                    self.snap_fallback += len(points)
                    return points

            except Exception as e:
                print(f"  Snap API exception: {e}")
                self.snap_fallback += len(points)
                return points

        return points

    def get_distance_matrix(self, origins: List[Tuple[float, float]],
                            destinations: List[Tuple[float, float]],
                            metrics: List[str] = ['distance']) -> Optional[Dict]:
        """
        Get distance matrix between origins and destinations.

        Args:
            origins: List of (lat, lon) tuples
            destinations: List of (lat, lon) tuples
            metrics: List of metrics ['distance', 'duration']

        Returns:
            Dictionary with 'distances' and/or 'durations' matrices
        """
        if not origins or not destinations:
            return None

        # ORS expects [lon, lat] format
        # Combine all locations: origins first, then destinations
        all_locations = [[p[1], p[0]] for p in origins] + [[p[1], p[0]] for p in destinations]

        # Source indices (origins)
        sources = list(range(len(origins)))
        # Destination indices
        destinations_idx = list(range(len(origins), len(origins) + len(destinations)))

        url = f"{self.base_url}/v2/matrix/driving-car"
        body = {
            'locations': all_locations,
            'sources': sources,
            'destinations': destinations_idx,
            'metrics': metrics,
            'units': 'km'  # Get distances in km
        }

        # Retry logic with exponential backoff
        for retry in range(ORS_MAX_RETRIES + 1):
            try:
                response = requests.post(url, json=body, headers=self.headers, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    self.matrix_success += len(origins) * len(destinations)
                    return data
                elif response.status_code == 429:
                    # Rate limit exceeded - retry with backoff
                    if retry < ORS_MAX_RETRIES:
                        wait_time = ORS_RETRY_BACKOFF * (2 ** retry)
                        print(f"  Rate limit hit, waiting {wait_time:.0f}s before retry {retry + 1}/{ORS_MAX_RETRIES}")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"  Matrix API rate limit after {ORS_MAX_RETRIES} retries, using fallback")
                        self.matrix_fallback += len(origins) * len(destinations)
                        return None
                else:
                    print(f"  Matrix API error {response.status_code}: {response.text[:200]}")
                    self.matrix_fallback += len(origins) * len(destinations)
                    return None

            except Exception as e:
                print(f"  Matrix API exception: {e}")
                self.matrix_fallback += len(origins) * len(destinations)
                return None

        return None

    def get_route_distance(self, origin: Tuple[float, float],
                           destination: Tuple[float, float]) -> Optional[float]:
        """
        Get driving distance from origin to destination using directions API.

        Args:
            origin: (lat, lon) tuple
            destination: (lat, lon) tuple

        Returns:
            Distance in km, or None if failed
        """
        # ORS expects [lon, lat] format
        url = f"{self.base_url}/v2/directions/driving-car"
        body = {
            'coordinates': [[origin[1], origin[0]], [destination[1], destination[0]]],
            'units': 'km'
        }

        for retry in range(ORS_MAX_RETRIES + 1):
            try:
                response = requests.post(url, json=body, headers=self.headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    if 'routes' in data and len(data['routes']) > 0:
                        distance = data['routes'][0]['summary']['distance']
                        self.route_success += 1
                        return distance
                    return None
                elif response.status_code == 429:
                    if retry < ORS_MAX_RETRIES:
                        wait_time = ORS_RETRY_BACKOFF * (2 ** retry)
                        time.sleep(wait_time)
                        continue
                    else:
                        self.route_fallback += 1
                        return None
                else:
                    self.route_fallback += 1
                    return None

            except Exception as e:
                self.route_fallback += 1
                return None

        return None


def find_nearest_charger_aerial(origin: Tuple[float, float],
                                 charger_coords: List[Tuple[float, float]]) -> Tuple[int, float]:
    """
    Find nearest charger by aerial distance.

    Returns:
        (index of nearest charger, aerial distance in km)
    """
    min_dist = float('inf')
    min_idx = 0
    for i, charger in enumerate(charger_coords):
        d = haversine(origin[0], origin[1], charger[0], charger[1])
        if d < min_dist:
            min_dist = d
            min_idx = i
    return min_idx, min_dist


def get_distances_ors(ors_client: OpenRouteServiceClient,
                      origins: List[Tuple[float, float]],
                      charger_coords: List[Tuple[float, float]],
                      batch_size: int = ORS_MATRIX_BATCH_SIZE) -> List[float]:
    """
    Get distances from origins to nearest charger using ORS directions API.

    New approach (more efficient):
    1. Find nearest charger by aerial distance (no API call)
    2. Get driving route only to that one charger (1 API call per origin)

    Args:
        ors_client: ORS client instance
        origins: List of (lat, lon) origin points
        charger_coords: List of (lat, lon) charger locations
        batch_size: Not used in new approach, kept for compatibility

    Returns:
        List of minimum distances (one per origin)
    """
    min_distances = []

    for origin in origins:
        # Step 1: Find nearest charger by aerial distance (free, local)
        nearest_idx, aerial_dist = find_nearest_charger_aerial(origin, charger_coords)
        nearest_charger = charger_coords[nearest_idx]

        # Step 2: Get driving distance to that charger only
        driving_dist = ors_client.get_route_distance(origin, nearest_charger)

        if driving_dist is not None:
            min_distances.append(driving_dist)
        else:
            # Fallback: use aerial distance with circuity
            min_distances.append(aerial_dist * CIRCUITY_FACTOR)

        # Rate limiting between requests
        time.sleep(ORS_RATE_LIMIT_DELAY)

    return min_distances


def get_distances_aerial(origins: List[Tuple[float, float]],
                         charger_coords: List[Tuple[float, float]]) -> List[float]:
    """Get distances from origins to nearest charger using aerial distance * circuity."""
    min_distances = []

    for origin in origins:
        min_d = float('inf')
        for charger in charger_coords:
            d = haversine(origin[0], origin[1], charger[0], charger[1]) * CIRCUITY_FACTOR
            if d < min_d:
                min_d = d
        min_distances.append(min_d)

    return min_distances


# =============================================================================
# MONTE CARLO SIMULATION
# =============================================================================

def run_monte_carlo_simulation(chargers: pd.DataFrame,
                                boundary: BoundaryHandler,
                                ors_client: Optional[OpenRouteServiceClient] = None,
                                n_iterations: int = N_MONTE_CARLO,
                                n_points: int = N_RANDOM_POINTS) -> Dict:
    """Run Monte Carlo simulation to estimate average detour time."""
    use_ors = ors_client is not None

    print(f"\nRunning Monte Carlo simulation...")
    print(f"  Iterations: {n_iterations}")
    print(f"  Points per iteration: {n_points}")
    print(f"  Routing: {'OpenRouteService (real driving)' if use_ors else 'Aerial x circuity'}")

    fast_chargers = chargers[chargers['is_fast'] == True].copy()
    slow_chargers = chargers[chargers['is_fast'] == False].copy()
    all_chargers = chargers.copy()

    print(f"  All chargers: {len(all_chargers)}")
    print(f"  Fast chargers: {len(fast_chargers)}")
    print(f"  Slow chargers: {len(slow_chargers)}")

    # Pre-compute charger coordinates
    all_coords = [(r['lat'], r['lon']) for _, r in all_chargers.iterrows()]
    fast_coords = [(r['lat'], r['lon']) for _, r in fast_chargers.iterrows()]
    slow_coords = [(r['lat'], r['lon']) for _, r in slow_chargers.iterrows()]

    results = {
        'all': {'distances': [], 'times': []},
        'fast': {'distances': [], 'times': []},
        'slow': {'distances': [], 'times': []}
    }

    for iteration in range(n_iterations):
        if (iteration + 1) % 10 == 0:
            print(f"  Iteration {iteration + 1}/{n_iterations}")

        # Generate random points
        points = [boundary.generate_random_point() for _ in range(n_points)]

        # Snap points to roads if using ORS
        if use_ors:
            points = ors_client.snap_to_road(points)
            time.sleep(ORS_RATE_LIMIT_DELAY)

        # Get distances to chargers
        if use_ors:
            distances_all = get_distances_ors(ors_client, points, all_coords)
            time.sleep(ORS_RATE_LIMIT_DELAY)

            if fast_coords:
                distances_fast = get_distances_ors(ors_client, points, fast_coords)
                time.sleep(ORS_RATE_LIMIT_DELAY)
            else:
                distances_fast = []

            if slow_coords:
                distances_slow = get_distances_ors(ors_client, points, slow_coords)
                time.sleep(ORS_RATE_LIMIT_DELAY)
            else:
                distances_slow = []
        else:
            distances_all = get_distances_aerial(points, all_coords)
            distances_fast = get_distances_aerial(points, fast_coords) if fast_coords else []
            distances_slow = get_distances_aerial(points, slow_coords) if slow_coords else []

        # Calculate iteration means
        if distances_all:
            mean_dist_all = np.mean(distances_all)
            results['all']['distances'].append(mean_dist_all)
            results['all']['times'].append(mean_dist_all * 2 * (60 / SPEED_KMH))

        if distances_fast:
            mean_dist_fast = np.mean(distances_fast)
            results['fast']['distances'].append(mean_dist_fast)
            results['fast']['times'].append(mean_dist_fast * 2 * (60 / SPEED_KMH))

        if distances_slow:
            mean_dist_slow = np.mean(distances_slow)
            results['slow']['distances'].append(mean_dist_slow)
            results['slow']['times'].append(mean_dist_slow * 2 * (60 / SPEED_KMH))

    # Print routing statistics
    if use_ors:
        print(f"\n  ORS routing statistics:")
        print(f"    Snap successful: {ors_client.snap_success}")
        print(f"    Snap fallback: {ors_client.snap_fallback}")
        print(f"    Route successful: {ors_client.route_success}")
        print(f"    Route fallback: {ors_client.route_fallback}")

    return results


def theoretical_detour(power_kw: float, area_km2: float,
                       pts_per_site: int = 10, avg_power: float = 22,
                       alpha: float = 1.4, speed: float = 30) -> float:
    """Calculate theoretical detour time based on spatial model."""
    if power_kw <= 0:
        return float('inf')
    nb_sites = max(1, (power_kw / avg_power) / pts_per_site)
    d_aerial = 0.5 * np.sqrt(area_km2 / nb_sites) * alpha
    return d_aerial * 2 * (60 / speed)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("DETOUR FUNCTION MONTE CARLO VALIDATION (v3)")
    print("Using: Official NUTS boundary + OpenRouteService")
    print("=" * 70)

    # Check ORS API key
    global ORS_API_KEY
    if ORS_API_KEY is None:
        # Try to load from environment variable
        ORS_API_KEY = os.environ.get('ORS_API_KEY')

    if not ORS_API_KEY and USE_ORS:
        print("\n" + "!" * 70)
        print("WARNING: OpenRouteService API key not set!")
        print("Get a free key at: https://openrouteservice.org/dev/#/signup")
        print("Set it by:")
        print("  1. Edit ORS_API_KEY in this script, or")
        print("  2. Set environment variable: export ORS_API_KEY=your_key")
        print("\nFalling back to aerial distance * circuity factor")
        print("!" * 70 + "\n")
        ors_client = None
    elif USE_ORS:
        print(f"\nUsing OpenRouteService with API key: {ORS_API_KEY[:20]}...")
        ors_client = OpenRouteServiceClient(ORS_API_KEY)
    else:
        print("\nOpenRouteService disabled, using aerial distance * circuity")
        ors_client = None

    # Initialize boundary handler
    boundary = BoundaryHandler()

    # Fetch real charger data
    chargers = fetch_chargers_from_ocm(use_cache=True)

    if chargers.empty:
        print("ERROR: No charger data available")
        return

    # Filter chargers to those within boundary
    chargers_in_boundary = []
    for _, charger in chargers.iterrows():
        if boundary.contains(charger['lon'], charger['lat']):
            chargers_in_boundary.append(charger)

    chargers = pd.DataFrame(chargers_in_boundary)
    print(f"Chargers within NUTS boundary: {len(chargers)}")

    # Summary statistics
    fast_chargers = chargers[chargers['is_fast'] == True]
    slow_chargers = chargers[chargers['is_fast'] == False]

    total_power = chargers['power_kw'].sum()
    fast_power = fast_chargers['power_kw'].sum()
    slow_power = slow_chargers['power_kw'].sum()

    print(f"\n{'='*50}")
    print("CHARGING INFRASTRUCTURE SUMMARY")
    print(f"{'='*50}")
    print(f"Total stations:     {len(chargers)}")
    print(f"  - Fast (>{FAST_CHARGING_THRESHOLD}kW): {len(fast_chargers)} ({fast_power:.0f} kW)")
    print(f"  - Slow (<={FAST_CHARGING_THRESHOLD}kW): {len(slow_chargers)} ({slow_power:.0f} kW)")
    print(f"Total power:        {total_power:.0f} kW")

    # Run Monte Carlo simulation
    print(f"\n{'='*50}")
    print("MONTE CARLO SIMULATION")
    print(f"{'='*50}")

    results = run_monte_carlo_simulation(
        chargers,
        boundary,
        ors_client=ors_client,
        n_iterations=N_MONTE_CARLO,
        n_points=N_RANDOM_POINTS
    )

    # Calculate statistics
    print(f"\n{'='*50}")
    print("EMPIRICAL RESULTS")
    print(f"{'='*50}")

    for key, label in [('all', 'All chargers'), ('fast', 'Fast only'), ('slow', 'Slow only')]:
        if results[key]['times']:
            times = results[key]['times']
            print(f"\n{label}:")
            print(f"  Mean detour time:   {np.mean(times):.1f} min")
            print(f"  Std deviation:      {np.std(times):.1f} min")
            print(f"  95% CI:             [{np.percentile(times, 2.5):.1f}, {np.percentile(times, 97.5):.1f}] min")

    # Theoretical predictions
    print(f"\n{'='*50}")
    print("THEORETICAL PREDICTIONS")
    print(f"{'='*50}")

    strategies = {
        'Distributed (2 pts/site)': 2,
        'Balanced (10 pts/site)': 10,
        'Concentrated (40 pts/site)': 40,
    }

    for name, pts in strategies.items():
        theo = theoretical_detour(total_power, TOTAL_AREA_KM2, pts)
        print(f"  {name}: {theo:.1f} min")

    # Generate figures
    print(f"\n{'='*50}")
    print("GENERATING FIGURES")
    print(f"{'='*50}")

    os.makedirs('results', exist_ok=True)
    version_suffix = '_ors' if ors_client else '_aerial'

    # Get boundary coordinates for all plots
    boundary_coords = boundary.get_boundary_coords()
    boundary_lons = [p[0] for p in boundary_coords]
    boundary_lats = [p[1] for p in boundary_coords]

    # Helper function to generate figure for a specific charger type
    def generate_charger_figure(charger_subset, result_times, charger_type, color, power_kw, avg_power_per_station):
        """
        Generate validation figure for a specific charger type.

        Args:
            charger_subset: DataFrame of chargers
            result_times: Monte Carlo result times
            charger_type: Label for this charger type
            color: Color for plotting
            power_kw: Total power of this charger type
            avg_power_per_station: Average power per station (for theoretical curves)
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # Plot 1: Histogram
        ax1 = axes[0]
        if result_times:
            ax1.hist(result_times, bins=20, color=color, alpha=0.7,
                     edgecolor='white', label='Monte Carlo results')
            ax1.axvline(np.mean(result_times), color='red', linestyle='--',
                        linewidth=2, label=f'Mean: {np.mean(result_times):.1f} min')

        theo_balanced = theoretical_detour(power_kw, TOTAL_AREA_KM2, 10, avg_power=avg_power_per_station)
        ax1.axvline(theo_balanced, color='green', linestyle=':', linewidth=2,
                    label=f'Theoretical (Balanced): {theo_balanced:.1f} min')

        ax1.set_xlabel('Detour Time (minutes)')
        ax1.set_ylabel('Frequency')
        ax1.set_title(f'Distribution of Mean Detour Times ({charger_type})')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Charger locations with NUTS boundary
        ax2 = axes[1]
        ax2.scatter(charger_subset['lon'], charger_subset['lat'],
                    c=color, s=charger_subset['power_kw']*2, alpha=0.7,
                    label=f'{charger_type} ({len(charger_subset)})')

        ax2.plot(boundary_lons, boundary_lats, 'k-', linewidth=1.5, alpha=0.7,
                 label='NUTS boundary' if boundary.use_nuts else 'Approx. boundary')

        ax2.set_xlabel('Longitude')
        ax2.set_ylabel('Latitude')
        ax2.set_title(f'{charger_type} Charging Infrastructure')
        ax2.legend(loc='lower right')
        ax2.grid(True, alpha=0.3)

        # Plot 3: Detour vs Infrastructure
        # Use appropriate power range based on charger type
        ax3 = axes[2]
        power_range = np.linspace(500, 50000, 100)

        colors_theo = {'Distributed (2 pts/site)': '#4f6d7a',
                       'Balanced (10 pts/site)': '#840032',
                       'Concentrated (40 pts/site)': '#dd6e42'}

        # Use the specific avg_power for this charger type in theoretical curves
        for name, pts in strategies.items():
            times = [theoretical_detour(p, TOTAL_AREA_KM2, pts, avg_power=avg_power_per_station) for p in power_range]
            ax3.plot(power_range, times, '-', color=colors_theo[name], linewidth=2,
                     label=name, alpha=0.8)

        if result_times:
            emp_mean = np.mean(result_times)
            emp_std = np.std(result_times)
            ax3.errorbar([power_kw], [emp_mean], yerr=[emp_std],
                         fmt='o', color='#2ecc71', markersize=12, capsize=8,
                         label=f'Empirical ({len(charger_subset)} stations)', zorder=10)

        ax3.axhline(y=5, color='gray', linestyle='--', alpha=0.5)
        ax3.text(40000, 6, '5 min threshold', fontsize=9, color='gray')

        ax3.set_xlabel('Installed Power (kW)')
        ax3.set_ylabel('Average Detour Time (minutes)')
        ax3.set_title(f'Detour Time vs Infrastructure ({charger_type})')
        ax3.legend(loc='upper right')
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim(0, 50000)
        ax3.set_ylim(0, 100)

        plt.tight_layout()
        return fig

    # Calculate average power per station for each type
    avg_power_fast = fast_power / len(fast_chargers) if len(fast_chargers) > 0 else 50
    avg_power_slow = slow_power / len(slow_chargers) if len(slow_chargers) > 0 else 11
    avg_power_all = total_power / len(chargers) if len(chargers) > 0 else 22

    print(f"  Average power per station:")
    print(f"    Fast: {avg_power_fast:.1f} kW")
    print(f"    Slow: {avg_power_slow:.1f} kW")
    print(f"    All:  {avg_power_all:.1f} kW")

    # Generate FAST charging figure
    fig_fast = generate_charger_figure(
        fast_chargers,
        results['fast']['times'],
        'Fast Charging (>22kW)',
        '#e74c3c',
        fast_power,
        avg_power_fast
    )
    fig_fast.savefig(f'results/detour_validation_fast{version_suffix}.png', dpi=300, bbox_inches='tight')
    print(f"Figure saved: results/detour_validation_fast{version_suffix}.png")
    fig_fast.savefig(f'results/detour_validation_fast{version_suffix}.pdf', bbox_inches='tight')
    print(f"Figure saved: results/detour_validation_fast{version_suffix}.pdf")

    # Generate SLOW charging figure
    fig_slow = generate_charger_figure(
        slow_chargers,
        results['slow']['times'],
        'Slow Charging (<=22kW)',
        '#3498db',
        slow_power,
        avg_power_slow
    )
    fig_slow.savefig(f'results/detour_validation_slow{version_suffix}.png', dpi=300, bbox_inches='tight')
    print(f"Figure saved: results/detour_validation_slow{version_suffix}.png")
    fig_slow.savefig(f'results/detour_validation_slow{version_suffix}.pdf', bbox_inches='tight')
    print(f"Figure saved: results/detour_validation_slow{version_suffix}.pdf")

    # Also generate combined figure (all chargers)
    fig_all = generate_charger_figure(
        chargers,
        results['all']['times'],
        'All Chargers',
        '#9b59b6',
        total_power,
        avg_power_all
    )
    fig_all.savefig(f'results/detour_validation_all{version_suffix}.png', dpi=300, bbox_inches='tight')
    print(f"Figure saved: results/detour_validation_all{version_suffix}.png")
    fig_all.savefig(f'results/detour_validation_all{version_suffix}.pdf', bbox_inches='tight')
    print(f"Figure saved: results/detour_validation_all{version_suffix}.pdf")

    # Save data
    chargers.to_csv('results/charger_data_basque_v3.csv', index=False)
    print("Charger data saved: results/charger_data_basque_v3.csv")

    results_df = pd.DataFrame({
        'iteration': range(len(results['all']['times'])),
        'mean_detour_all': results['all']['times'],
        'mean_detour_fast': results['fast']['times'] if results['fast']['times'] else [None]*len(results['all']['times']),
        'mean_detour_slow': results['slow']['times'] if results['slow']['times'] else [None]*len(results['all']['times'])
    })
    results_df.to_csv(f'results/monte_carlo_results_v3{version_suffix}.csv', index=False)
    print(f"Monte Carlo results saved: results/monte_carlo_results_v3{version_suffix}.csv")

    plt.show()

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    if results['all']['times']:
        emp_mean = np.mean(results['all']['times'])
        emp_ci = (np.percentile(results['all']['times'], 2.5),
                  np.percentile(results['all']['times'], 97.5))

        routing_method = "OpenRouteService (real driving distances)" if ors_client else "Aerial x circuity factor"
        boundary_method = "Official NUTS (Eurostat)" if boundary.use_nuts else "Simplified polygon"

        print(f"""
Empirical detour time (Monte Carlo, {N_MONTE_CARLO} iterations):
  Mean: {emp_mean:.1f} min
  95% CI: [{emp_ci[0]:.1f}, {emp_ci[1]:.1f}] min

Theoretical predictions:
  Distributed (2 pts/site):   {theoretical_detour(total_power, TOTAL_AREA_KM2, 2):.1f} min
  Balanced (10 pts/site):     {theoretical_detour(total_power, TOTAL_AREA_KM2, 10):.1f} min
  Concentrated (40 pts/site): {theoretical_detour(total_power, TOTAL_AREA_KM2, 40):.1f} min

Data sources:
  - Charger locations: OpenChargeMap API ({len(chargers)} stations)
  - Boundary: {boundary_method}
  - Routing: {routing_method}
  - Random points: {N_RANDOM_POINTS} per iteration
        """)

    return results, chargers


if __name__ == "__main__":
    results, chargers = main()
