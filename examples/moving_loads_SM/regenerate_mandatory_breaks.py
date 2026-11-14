"""
Regenerate MandatoryBreaks.yaml using corrected Path.yaml distances.

This script reads the updated Path.yaml (with corrected segment distances)
and regenerates MandatoryBreaks.yaml following EU Regulation 561/2006.
"""

import yaml
from pathlib import Path
from collections import defaultdict


def create_mandatory_breaks(
    path_list: list,
    geo_elements: list,
    driver_limit_hours: float = 4.5,
    avg_speed_kmh: float = 80.0,
    mode: str = 'road',
    daily_driving_limit: float = 9.0,
    short_break_duration: float = 0.75,
    daily_rest_duration: float = 9.0,
    team_driving_threshold: float = 54.0
) -> list:
    """
    Create mandatory break constraints following EU Regulation 561/2006.

    Based on Speth et al. (2022):
    - Break (B): 45 minutes after 4.5h driving
    - Rest (R): 9 hours after 9h driving
    - Team driving: Paths > 54h use 2 drivers
    """
    print("=" * 80)
    print("REGENERATING MANDATORY BREAKS")
    print("=" * 80)
    print(f"  Mode: {mode}")
    print(f"  Single driver: 45 min break after {driver_limit_hours}h driving")
    print(f"  Rest period:   {daily_rest_duration:.1f}h after {daily_driving_limit}h driving")
    print(f"  Team driving:  Paths > {team_driving_threshold}h use 2 drivers")

    # Build node info lookup
    node_info = {}
    for g in geo_elements:
        if g.get('type') == 'node':
            node_info[g['id']] = {
                'nuts2': g.get('nuts2_region'),
                'country': g.get('country'),
            }

    max_distance_short = driver_limit_hours * avg_speed_kmh
    break_id = 0
    mandatory_breaks = []

    # Statistics
    total_short_breaks = 0
    total_rests = 0
    paths_single_driver = 0
    paths_team_driver = 0

    for path in path_list:
        path_id = path['id']
        path_length = path['length']
        sequence = path['sequence']
        distances = path['distance_from_previous']
        cumulative = path['cumulative_distance']

        # Determine number of drivers based on total path driving time
        total_path_driving_time = path_length / avg_speed_kmh
        if total_path_driving_time > team_driving_threshold:
            num_drivers = 2
            paths_team_driver += 1
        else:
            num_drivers = 1
            paths_single_driver += 1

        distance_since_break = 0
        driving_time_today = 0
        break_number = 0
        total_break_time = 0.0

        for i in range(1, len(sequence)):
            geo_id = sequence[i]
            segment_distance = distances[i] if i < len(distances) else 0
            cumulative_dist = cumulative[i] if i < len(cumulative) else 0

            segment_time = segment_distance / avg_speed_kmh
            distance_since_break += segment_distance
            driving_time_today += segment_time

            # Check for SHORT BREAK (single driver only)
            if num_drivers == 1 and distance_since_break >= max_distance_short:
                break_number += 1
                total_short_breaks += 1

                driving_time_at_break = cumulative_dist / avg_speed_kmh

                mandatory_breaks.append({
                    'id': break_id,
                    'path_id': path_id,
                    'break_type': 'short',
                    'latest_geo_id': geo_id,
                    'break_number': break_number,
                    'distance_at_break': round(cumulative_dist, 2),
                    'driving_time_at_break': round(driving_time_at_break, 2),
                    'cumulative_break_time': round(total_break_time + short_break_duration, 2),
                    'break_duration': short_break_duration,
                    'num_drivers': int(num_drivers),
                })
                break_id += 1
                total_break_time += short_break_duration
                distance_since_break = 0

            # Check for DAILY REST
            if driving_time_today >= daily_driving_limit:
                break_number += 1
                total_rests += 1

                driving_time_at_break = cumulative_dist / avg_speed_kmh

                mandatory_breaks.append({
                    'id': break_id,
                    'path_id': path_id,
                    'break_type': 'rest',
                    'latest_geo_id': geo_id,
                    'break_number': break_number,
                    'distance_at_break': round(cumulative_dist, 2),
                    'driving_time_at_break': round(driving_time_at_break, 2),
                    'cumulative_break_time': round(total_break_time + daily_rest_duration, 2),
                    'break_duration': daily_rest_duration,
                    'num_drivers': int(num_drivers),
                })
                break_id += 1
                total_break_time += daily_rest_duration
                driving_time_today = 0
                distance_since_break = 0

    # Print statistics
    print(f"\n[DONE] Generated {len(mandatory_breaks)} mandatory breaks:")
    print(f"  Short breaks (45 min): {total_short_breaks}")
    print(f"  Rest periods (9h):     {total_rests}")
    print(f"  Single driver paths:   {paths_single_driver}")
    print(f"  Team driver paths:     {paths_team_driver}")

    return mandatory_breaks


def main():
    base_dir = Path(__file__).parent / 'input_data' / 'fixed_nuts_2'

    # Load updated Path.yaml
    print("Loading data...")
    with open(base_dir / 'Path.yaml', 'r') as f:
        path_list = yaml.safe_load(f)
    print(f"  Loaded {len(path_list)} paths")

    # Load GeographicElement.yaml
    with open(base_dir / 'GeographicElement.yaml', 'r') as f:
        geo_elements = yaml.safe_load(f)
    print(f"  Loaded {len(geo_elements)} geographic elements")

    # Regenerate mandatory breaks
    mandatory_breaks = create_mandatory_breaks(path_list, geo_elements)

    # Backup original
    backup_path = base_dir / 'MandatoryBreaks.yaml.backup'
    if not backup_path.exists():
        import shutil
        shutil.copy(base_dir / 'MandatoryBreaks.yaml', backup_path)
        print(f"\n[OK] Backed up original to {backup_path}")

    # Save updated breaks
    with open(base_dir / 'MandatoryBreaks.yaml', 'w') as f:
        yaml.dump(mandatory_breaks, f, default_flow_style=False, allow_unicode=True)
    print(f"[OK] Saved updated MandatoryBreaks.yaml")

    # Analyze break distribution by region
    print("\n" + "=" * 80)
    print("BREAK DISTRIBUTION BY REGION")
    print("=" * 80)

    # Build node to region mapping
    node_to_region = {}
    for g in geo_elements:
        if g.get('type') == 'node':
            node_to_region[g['id']] = g.get('nuts2_region')

    breaks_by_region = defaultdict(int)
    for brk in mandatory_breaks:
        geo_id = brk.get('latest_geo_id')
        region = node_to_region.get(geo_id, 'Unknown')
        breaks_by_region[region] += 1

    # Sort by count
    sorted_regions = sorted(breaks_by_region.items(), key=lambda x: -x[1])
    print(f"Top 10 regions by break count:")
    for region, count in sorted_regions[:10]:
        pct = count / len(mandatory_breaks) * 100
        print(f"  {region}: {count} breaks ({pct:.1f}%)")


if __name__ == "__main__":
    main()
