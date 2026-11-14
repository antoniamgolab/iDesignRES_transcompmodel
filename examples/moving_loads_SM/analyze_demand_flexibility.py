"""
Analyze Geographic Flexibility Potential in Demand Allocation

Step 1: Display distribution of edge lengths from Path.yaml (distance_from_previous)
"""
import yaml
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_paths(case_name, input_dir="input_data"):
    """Load Path.yaml for a given case"""
    file_path = Path(input_dir) / case_name / "Path.yaml"

    if not file_path.exists():
        print(f"[ERROR] Path.yaml not found: {file_path}")
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        paths = yaml.safe_load(f)

    return paths


def extract_edge_lengths(paths):
    """Extract all edge lengths (distance_from_previous) from paths"""
    edge_lengths = []

    for path in paths:
        path_id = path.get('id', 'unknown')
        sequence = path.get('sequence', [])
        distances = path.get('distance_from_previous', [])

        # Zip sequence with distances to get node -> distance pairs
        for i, (node_id, distance) in enumerate(zip(sequence, distances)):
            if distance > 0:  # Skip first node (origin with distance=0)
                edge_lengths.append({
                    'path_id': path_id,
                    'distance_km': distance,
                    'node_id': node_id,
                    'edge_index': i
                })

    return pd.DataFrame(edge_lengths)


def plot_edge_length_distribution(df_edges, case_name):
    """Create visualizations of edge length distribution"""

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Edge Length Distribution - {case_name}', fontsize=14, fontweight='bold')

    distances = df_edges['distance_km'].values

    # 1. Histogram
    ax = axes[0, 0]
    ax.hist(distances, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
    ax.set_xlabel('Edge Length (km)')
    ax.set_ylabel('Frequency')
    ax.set_title('Histogram of Edge Lengths')
    ax.grid(True, alpha=0.3)

    # 2. Log-scale histogram
    ax = axes[0, 1]
    ax.hist(distances, bins=50, edgecolor='black', alpha=0.7, color='coral')
    ax.set_xlabel('Edge Length (km)')
    ax.set_ylabel('Frequency')
    ax.set_yscale('log')
    ax.set_title('Histogram (Log Scale)')
    ax.grid(True, alpha=0.3)

    # 3. Box plot
    ax = axes[1, 0]
    ax.boxplot(distances, vert=True, patch_artist=True,
               boxprops=dict(facecolor='lightgreen', alpha=0.7),
               medianprops=dict(color='red', linewidth=2))
    ax.set_ylabel('Edge Length (km)')
    ax.set_title('Box Plot')
    ax.grid(True, alpha=0.3, axis='y')

    # 4. Cumulative distribution
    ax = axes[1, 1]
    sorted_distances = np.sort(distances)
    cumulative = np.arange(1, len(sorted_distances) + 1) / len(sorted_distances) * 100
    ax.plot(sorted_distances, cumulative, linewidth=2, color='purple')
    ax.set_xlabel('Edge Length (km)')
    ax.set_ylabel('Cumulative Percentage (%)')
    ax.set_title('Cumulative Distribution')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save figure
    output_file = f'edge_length_distribution_{case_name}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved plot: {output_file}")

    return fig


def print_statistics(df_edges):
    """Print summary statistics"""
    distances = df_edges['distance_km'].values

    print("\n" + "="*80)
    print("EDGE LENGTH STATISTICS")
    print("="*80)
    print(f"Total edges: {len(distances):,}")
    print(f"\nDescriptive Statistics:")
    print(f"  Min:      {np.min(distances):.2f} km")
    print(f"  Max:      {np.max(distances):.2f} km")
    print(f"  Mean:     {np.mean(distances):.2f} km")
    print(f"  Median:   {np.median(distances):.2f} km")
    print(f"  Std Dev:  {np.std(distances):.2f} km")
    print(f"\nPercentiles:")
    print(f"  10th:     {np.percentile(distances, 10):.2f} km")
    print(f"  25th:     {np.percentile(distances, 25):.2f} km")
    print(f"  50th:     {np.percentile(distances, 50):.2f} km")
    print(f"  75th:     {np.percentile(distances, 75):.2f} km")
    print(f"  90th:     {np.percentile(distances, 90):.2f} km")
    print(f"  95th:     {np.percentile(distances, 95):.2f} km")
    print(f"  99th:     {np.percentile(distances, 99):.2f} km")

    # Length categories
    print(f"\nEdge Length Categories:")
    categories = [
        ("Very short (< 50 km)", distances < 50),
        ("Short (50-100 km)", (distances >= 50) & (distances < 100)),
        ("Medium (100-200 km)", (distances >= 100) & (distances < 200)),
        ("Long (200-500 km)", (distances >= 200) & (distances < 500)),
        ("Very long (>= 500 km)", distances >= 500)
    ]

    for label, mask in categories:
        count = np.sum(mask)
        pct = count / len(distances) * 100
        print(f"  {label:30s}: {count:6,} ({pct:5.1f}%)")

    print("="*80)


def analyze_charging_flexibility(paths, battery_range_km):
    """
    Analyze charging location flexibility given battery range constraints

    For each path, determine:
    - How many edges FORCE charging (edge > range)
    - How many potential charging locations exist
    - Flexibility score (optional stops / total stops)
    """
    print(f"\n" + "="*80)
    print(f"CHARGING LOCATION FLEXIBILITY ANALYSIS")
    print(f"Battery Range: {battery_range_km} km")
    print("="*80)

    flexibility_data = []

    for path in paths:
        path_id = path.get('id')
        distances = path.get('distance_from_previous', [])
        cumulative = path.get('cumulative_distance', [])
        total_length = path.get('length', 0)

        # Skip origin (distance=0)
        edges = distances[1:]

        # Count forced charging stops (edges exceeding range)
        forced_stops = sum(1 for d in edges if d > battery_range_km)

        # Estimate minimum charging stops needed for entire path
        # (simplified: total_length / range)
        min_stops_total = int(np.ceil(total_length / battery_range_km)) - 1
        min_stops_total = max(0, min_stops_total)

        # Count edges that allow charging (have intermediate nodes)
        total_edges = len(edges)

        # Optional stops = places where we could charge but aren't forced to
        # This is approximate: (min stops needed) - (forced by single edge)
        optional_stops = max(0, min_stops_total - forced_stops)

        # Flexibility score: higher = more choice in where to charge
        if min_stops_total > 0:
            flexibility_score = optional_stops / min_stops_total
        else:
            flexibility_score = 1.0  # Path within range, full flexibility

        flexibility_data.append({
            'path_id': path_id,
            'total_length_km': total_length,
            'num_edges': total_edges,
            'forced_charging_edges': forced_stops,
            'min_charging_stops': min_stops_total,
            'optional_stops': optional_stops,
            'flexibility_score': flexibility_score
        })

    df = pd.DataFrame(flexibility_data)

    # Summary statistics
    print(f"\nPath-level statistics (n={len(df):,} paths):")
    print(f"  Paths with forced charging edges: {(df['forced_charging_edges'] > 0).sum():,} ({(df['forced_charging_edges'] > 0).sum()/len(df)*100:.1f}%)")
    print(f"  Paths requiring charging: {(df['min_charging_stops'] > 0).sum():,} ({(df['min_charging_stops'] > 0).sum()/len(df)*100:.1f}%)")
    print(f"\nCharging stop requirements:")
    print(f"  Total forced stops across all paths: {df['forced_charging_edges'].sum():,}")
    print(f"  Total min stops needed: {df['min_charging_stops'].sum():,}")
    print(f"  Total optional stops: {df['optional_stops'].sum():,}")
    print(f"\nFlexibility score distribution:")
    print(f"  Mean: {df['flexibility_score'].mean():.3f}")
    print(f"  Median: {df['flexibility_score'].median():.3f}")
    print(f"  Fully flexible paths (score=1.0): {(df['flexibility_score'] == 1.0).sum():,} ({(df['flexibility_score'] == 1.0).sum()/len(df)*100:.1f}%)")
    print(f"  No flexibility (score=0.0): {(df['flexibility_score'] == 0.0).sum():,} ({(df['flexibility_score'] == 0.0).sum()/len(df)*100:.1f}%)")

    # Worst cases (least flexibility)
    print(f"\nTop 10 paths with LEAST charging flexibility:")
    worst = df.nsmallest(10, 'flexibility_score')[['path_id', 'total_length_km', 'forced_charging_edges', 'min_charging_stops', 'flexibility_score']]
    print(worst.to_string(index=False))

    return df


def main():
    """Main analysis function"""

    # Choose a case to analyze (they should have the same Path.yaml structure)
    case_name = "case_20251107_194948_var_var"

    # Battery ranges to test (typical BEV truck ranges)
    battery_ranges = [300, 400, 500]  # km

    print("="*80)
    print("CHARGING LOCATION FLEXIBILITY ANALYSIS")
    print("="*80)
    print(f"\nAnalyzing case: {case_name}")
    print(f"Question: Can the model choose WHERE to charge based on costs,")
    print(f"          or is it forced to charge at specific locations by range constraints?")
    print("\n")

    # Load paths
    print("Loading Path.yaml...")
    paths = load_paths(case_name)

    if paths is None:
        return

    print(f"[OK] Loaded {len(paths):,} paths")

    # Extract edge lengths
    print("\nExtracting edge lengths...")
    df_edges = extract_edge_lengths(paths)
    print(f"[OK] Extracted {len(df_edges):,} edges")

    # Print statistics
    print_statistics(df_edges)

    # Create visualizations
    print("\nCreating visualizations...")
    plot_edge_length_distribution(df_edges, case_name)

    # Analyze charging flexibility for different battery ranges
    for battery_range in battery_ranges:
        df_flexibility = analyze_charging_flexibility(paths, battery_range)

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nInterpretation:")
    print("  - High forced stops = model MUST charge at specific locations (no cost flexibility)")
    print("  - High optional stops = model CAN choose cheaper charging locations")
    print("  - Flexibility score = fraction of charging decisions driven by costs vs range")
    print("\nIf flexibility is low, cost variations won't affect charging location allocation.")


if __name__ == "__main__":
    main()
