"""
Visual Diagram: NUTS-3 Route Sequence Creation
===============================================

Creates a simple visualization showing how route sequences are
created through NUTS-3 aggregation.

Author: Claude Code
Date: 2025-10-15
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np


def create_aggregation_diagram():
    """Create diagram showing Method A: Path aggregation."""

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
    fig.suptitle('Method A: NUTS-3 Path Aggregation (Preserves Distances)',
                 fontsize=14, fontweight='bold')

    # ============================================================================
    # TOP: Original detailed network
    # ============================================================================
    ax1.set_xlim(0, 14)
    ax1.set_ylim(0, 3)
    ax1.axis('off')
    ax1.set_title('BEFORE: Original Detailed Network', fontsize=12, fontweight='bold')

    # Original nodes
    nodes_orig = [
        (1, 1.5, 'A1', 'NUTS_A', '#FFB6C1'),
        (3, 1.5, 'A2', 'NUTS_A', '#FFB6C1'),
        (5, 1.5, 'A3', 'NUTS_A', '#FFB6C1'),
        (7, 1.5, 'B1', 'NUTS_B', '#87CEEB'),
        (9, 1.5, 'B2', 'NUTS_B', '#87CEEB'),
        (11, 1.5, 'C1', 'NUTS_C', '#90EE90'),
    ]

    # Draw nodes
    for x, y, name, region, color in nodes_orig:
        circle = plt.Circle((x, y), 0.35, color=color, ec='black', linewidth=2, zorder=3)
        ax1.add_patch(circle)
        ax1.text(x, y, name, ha='center', va='center', fontweight='bold', fontsize=10)
        ax1.text(x, y - 0.7, region, ha='center', va='top', fontsize=8, style='italic')

    # Draw edges with distances
    edges = [
        (1, 3, '15 km'),
        (3, 5, '12 km'),
        (5, 7, '45 km'),
        (7, 9, '23 km'),
        (9, 11, '38 km'),
    ]

    for x1, x2, dist in edges:
        arrow = FancyArrowPatch((x1 + 0.35, 1.5), (x2 - 0.35, 1.5),
                               arrowstyle='->', mutation_scale=20, linewidth=2,
                               color='black', zorder=2)
        ax1.add_patch(arrow)
        mid_x = (x1 + x2) / 2
        ax1.text(mid_x, 2.1, dist, ha='center', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black'))

    # Add region boundaries
    ax1.axvspan(0, 5.7, alpha=0.1, color='red', zorder=0)
    ax1.text(2.8, 2.7, 'Region A', fontsize=10, fontweight='bold', ha='center')
    ax1.axvspan(5.7, 9.7, alpha=0.1, color='blue', zorder=0)
    ax1.text(7.7, 2.7, 'Region B', fontsize=10, fontweight='bold', ha='center')
    ax1.axvspan(9.7, 14, alpha=0.1, color='green', zorder=0)
    ax1.text(11.5, 2.7, 'Region C', fontsize=10, fontweight='bold', ha='center')

    # Total distance
    ax1.text(6, 0.3, 'Total distance: 15 + 12 + 45 + 23 + 38 = 133 km',
            ha='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))

    # ============================================================================
    # BOTTOM: Aggregated NUTS-3 network
    # ============================================================================
    ax2.set_xlim(0, 14)
    ax2.set_ylim(0, 3)
    ax2.axis('off')
    ax2.set_title('AFTER: NUTS-3 Aggregated Network', fontsize=12, fontweight='bold')

    # Aggregated nodes
    nodes_agg = [
        (3, 1.5, 'NUTS_A', 'Node 0', '#FFB6C1'),
        (7, 1.5, 'NUTS_B', 'Node 5', '#87CEEB'),
        (11, 1.5, 'NUTS_C', 'Node 12', '#90EE90'),
    ]

    # Draw aggregated nodes (larger)
    for x, y, name, node_id, color in nodes_agg:
        circle = plt.Circle((x, y), 0.5, color=color, ec='black', linewidth=3, zorder=3)
        ax2.add_patch(circle)
        ax2.text(x, y + 0.15, name, ha='center', va='center', fontweight='bold', fontsize=11)
        ax2.text(x, y - 0.15, node_id, ha='center', va='center', fontsize=8, style='italic')

    # Draw aggregated edges
    agg_edges = [
        (3, 7, '72 km', 'Within A: 15+12\n+ Transition A→B: 45'),
        (7, 11, '61 km', 'Within B: 23\n+ Transition B→C: 38'),
    ]

    for x1, x2, dist, details in agg_edges:
        arrow = FancyArrowPatch((x1 + 0.5, 1.5), (x2 - 0.5, 1.5),
                               arrowstyle='->', mutation_scale=25, linewidth=3,
                               color='darkgreen', zorder=2)
        ax2.add_patch(arrow)
        mid_x = (x1 + x2) / 2
        ax2.text(mid_x, 2.3, dist, ha='center', fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen',
                         edgecolor='darkgreen', linewidth=2))
        ax2.text(mid_x, 0.9, details, ha='center', fontsize=7, style='italic',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # Total distance
    ax2.text(7, 0.2, 'Total distance: 72 + 61 = 133 km ✓ (PRESERVED!)',
            ha='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen',
                     edgecolor='darkgreen', linewidth=2))

    plt.tight_layout()
    plt.savefig('nuts3_method_a_aggregation.png', dpi=300, bbox_inches='tight')
    print("[OK] Saved: nuts3_method_a_aggregation.png")


def create_traffic_based_diagram():
    """Create diagram showing Method B: Traffic-based path creation."""

    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    fig.suptitle('Method B: Traffic-Based Path Creation (Distance Accuracy Varies)',
                 fontsize=14, fontweight='bold')

    # ============================================================================
    # TOP: Traffic data
    # ============================================================================
    ax = axes[0]
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 3)
    ax.axis('off')
    ax.set_title('Input: Traffic Data (NUTS-3 Level)', fontsize=12, fontweight='bold')

    # Traffic data box
    traffic_box = FancyBboxPatch((1, 0.5), 12, 2,
                                 boxstyle="round,pad=0.1",
                                 facecolor='lightyellow',
                                 edgecolor='orange', linewidth=3)
    ax.add_patch(traffic_box)

    traffic_text = """
    Origin Region: NUTS_1234 (Region A)
    Destination Region: NUTS_5678 (Region C)
    Total Distance: 347.5 km
    Traffic Flow: 1,523 trucks/year
    """
    ax.text(7, 1.5, traffic_text, ha='center', va='center', fontsize=10,
           family='monospace', fontweight='bold')

    # ============================================================================
    # MIDDLE: Scenario 1 - Direct edge exists
    # ============================================================================
    ax = axes[1]
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 3.5)
    ax.axis('off')
    ax.set_title('Scenario 1: Direct Edge Exists in NUTS-3 Network',
                fontsize=12, fontweight='bold')

    # Nodes
    nodes = [
        (3, 1.5, 'NUTS_A\n(Node 42)', '#FFB6C1'),
        (11, 1.5, 'NUTS_C\n(Node 89)', '#90EE90'),
    ]

    for x, y, name, color in nodes:
        circle = plt.Circle((x, y), 0.6, color=color, ec='black', linewidth=2, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, name, ha='center', va='center', fontweight='bold', fontsize=10)

    # Direct edge (too short!)
    arrow = FancyArrowPatch((3.6, 1.5), (10.4, 1.5),
                           arrowstyle='->', mutation_scale=25, linewidth=3,
                           color='red', zorder=2)
    ax.add_patch(arrow)
    ax.text(7, 2.3, '28 km', ha='center', fontsize=12, fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffcccc',
                    edgecolor='red', linewidth=2))

    # Error annotation
    ax.text(7, 0.5, '❌ ERROR: 28 km ≠ 347.5 km\n(81% underestimate!)',
           ha='center', fontsize=10, fontweight='bold', color='red',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                    edgecolor='red', linewidth=2))

    # ============================================================================
    # BOTTOM: Scenario 2 - Multi-hop path OR Scenario 3 - Fallback
    # ============================================================================
    ax = axes[2]
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 4)
    ax.axis('off')

    # Split into two sub-scenarios
    # Left: Multi-hop
    ax.text(3.5, 3.7, 'Scenario 2: Multi-hop Path', ha='center', fontsize=11,
           fontweight='bold', bbox=dict(boxstyle='round', facecolor='lightblue'))

    nodes_multi = [
        (1, 2, 'A', '#FFB6C1'),
        (2.5, 2, 'B', '#87CEEB'),
        (4, 2, 'D', '#FFCC99'),
        (5.5, 2, 'C', '#90EE90'),
    ]

    for x, y, name, color in nodes_multi:
        circle = plt.Circle((x, y), 0.3, color=color, ec='black', linewidth=2, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, name, ha='center', va='center', fontweight='bold', fontsize=9)

    # Multi-hop edges
    multi_edges = [
        (1, 2.5, '45'),
        (2.5, 4, '67'),
        (4, 5.5, '102'),
    ]

    for x1, x2, dist in multi_edges:
        arrow = FancyArrowPatch((x1 + 0.3, 2), (x2 - 0.3, 2),
                               arrowstyle='->', mutation_scale=15, linewidth=2,
                               color='blue', zorder=2)
        ax.add_patch(arrow)
        mid_x = (x1 + x2) / 2
        ax.text(mid_x, 2.5, dist, ha='center', fontsize=8, fontweight='bold')

    ax.text(3.25, 1.2, 'Total: 214 km\n(38% error)', ha='center', fontsize=9,
           bbox=dict(boxstyle='round', facecolor='lightyellow'))

    # Right: Fallback to traffic distance
    ax.text(10.5, 3.7, 'Scenario 3: No Path → Use Traffic Distance',
           ha='center', fontsize=11, fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='lightgreen'))

    nodes_fallback = [
        (8.5, 2, 'NUTS_A', '#FFB6C1'),
        (12.5, 2, 'NUTS_C', '#90EE90'),
    ]

    for x, y, name, color in nodes_fallback:
        circle = plt.Circle((x, y), 0.4, color=color, ec='black', linewidth=2, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, name, ha='center', va='center', fontweight='bold', fontsize=9)

    # Dashed line (no actual edge)
    ax.plot([8.9, 12.1], [2, 2], 'g--', linewidth=3, zorder=2)
    ax.text(10.5, 2.6, '347.5 km', ha='center', fontsize=10, fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='lightgreen',
                    edgecolor='darkgreen', linewidth=2))

    ax.text(10.5, 1.2, '✓ Uses traffic distance\n(accurate)', ha='center', fontsize=9,
           fontweight='bold', color='darkgreen',
           bbox=dict(boxstyle='round', facecolor='white',
                    edgecolor='darkgreen', linewidth=2))

    plt.tight_layout()
    plt.savefig('nuts3_method_b_traffic_based.png', dpi=300, bbox_inches='tight')
    print("[OK] Saved: nuts3_method_b_traffic_based.png")


def create_comparison_summary():
    """Create a summary comparison chart."""

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')

    # Title
    fig.suptitle('NUTS-3 Route Sequence Methods: Comparison',
                fontsize=16, fontweight='bold')

    # Create comparison table
    rows = [
        ['Aspect', 'Method A:\nPath Aggregation', 'Method B:\nTraffic-Based'],
        ['Input Source', 'Existing detailed paths', 'NUTS-3 traffic data'],
        ['Node Sequence', 'Collapsed from\ndetailed path', 'Created from\nnetwork topology'],
        ['Distance Source', 'Accumulated\noriginal distances', 'Network edges\nOR traffic data'],
        ['Distance Accuracy', '100% preserved\n✓✓✓', 'Varies\n(0-81% error)'],
        ['Direct Edge Case', 'N/A\n(uses aggregated)', 'Uses network edge\n(often too short)'],
        ['No Direct Edge', 'N/A\n(always has path)', 'BFS pathfinding\nor fallback'],
        ['Best Used For', 'Simplifying existing\nhigh-res model', 'Building new model\nfrom traffic data'],
    ]

    # Draw table
    table = ax.table(cellText=rows, cellLoc='center', loc='center',
                    colWidths=[0.25, 0.35, 0.35])

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 3)

    # Style header row
    for i in range(3):
        cell = table[(0, i)]
        cell.set_facecolor('#4472C4')
        cell.set_text_props(weight='bold', color='white', fontsize=11)

    # Style Method A column
    for i in range(1, len(rows)):
        cell = table[(i, 1)]
        cell.set_facecolor('#E7E6F7')
        cell.set_text_props(fontsize=9)

    # Style Method B column
    for i in range(1, len(rows)):
        cell = table[(i, 2)]
        cell.set_facecolor('#FFF4E6')
        cell.set_text_props(fontsize=9)

    # Style row labels
    for i in range(1, len(rows)):
        cell = table[(i, 0)]
        cell.set_facecolor('#F2F2F2')
        cell.set_text_props(weight='bold', fontsize=9)

    # Add key insight box
    insight_text = """
    KEY INSIGHT:

    Method A preserves exact distances by accumulating original edge distances.

    Method B relies on network topology - if network edges don't match real routes,
    significant errors occur (up to 81% for direct edges in your data!).

    RECOMMENDATION: For traffic-based models, always use traffic-reported
    distances, treating network edges as topology indicators only.
    """

    ax.text(0.5, 0.05, insight_text, transform=ax.transAxes,
           ha='center', va='bottom', fontsize=10,
           bbox=dict(boxstyle='round,pad=1', facecolor='#FFFACD',
                    edgecolor='#FF8C00', linewidth=3))

    plt.tight_layout()
    plt.savefig('nuts3_methods_comparison.png', dpi=300, bbox_inches='tight')
    print("[OK] Saved: nuts3_methods_comparison.png")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Creating NUTS-3 Route Sequence Visualizations")
    print("="*80 + "\n")

    print("Creating Method A diagram...")
    create_aggregation_diagram()

    print("\nCreating Method B diagram...")
    create_traffic_based_diagram()

    print("\nCreating comparison summary...")
    create_comparison_summary()

    print("\n" + "="*80)
    print("Done! Created 3 visualization files:")
    print("  1. nuts3_method_a_aggregation.png")
    print("  2. nuts3_method_b_traffic_based.png")
    print("  3. nuts3_methods_comparison.png")
    print("="*80 + "\n")
