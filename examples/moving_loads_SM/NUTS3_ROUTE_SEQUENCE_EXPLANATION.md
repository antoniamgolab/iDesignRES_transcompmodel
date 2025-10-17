# How NUTS-3 Route Sequences Are Created

## Overview

There are **TWO different ways** route sequences are created when working with NUTS-3 aggregated data:

1. **Method A: Aggregating existing paths** (using `aggregate_to_nuts3.py`)
2. **Method B: Creating paths from traffic data** (using `create_nuts3_paths_from_traffic()`)

---

## Method A: Aggregating Existing Paths

**Used when:** You already have detailed paths from a high-resolution model and want to simplify them to NUTS-3 level.

### Step-by-Step Process

#### Step 1: Map each node to its NUTS-3 region

**Example original path:**
```
Original sequence: [node_42, node_43, node_44, node_67, node_68, node_91]
                      ↓        ↓        ↓        ↓        ↓        ↓
NUTS-3 regions:    [NUTS_A, NUTS_A, NUTS_A, NUTS_B, NUTS_B, NUTS_C]
```

Each node in the network belongs to a NUTS-3 region (stored in node metadata).

#### Step 2: Collapse consecutive nodes in the same region

**Logic (lines 198-211 in `aggregate_to_nuts3.py`):**
```python
# Keep first node
simplified_nuts3 = [nuts3_sequence[0]]  # → [NUTS_A]

# Walk through sequence
for i in range(1, len(nuts3_sequence)):
    # If entering a NEW region, keep this transition
    if nuts3_sequence[i] != nuts3_sequence[i-1]:
        simplified_nuts3.append(nuts3_sequence[i])
```

**Result:**
```
Original:    [NUTS_A, NUTS_A, NUTS_A, NUTS_B, NUTS_B, NUTS_C]
Simplified:  [NUTS_A,          NUTS_B,          NUTS_C]
```

#### Step 3: Accumulate distances within each region

**Original distances (distance from previous node):**
```
Node:       [42,  43,  44,  67,  68,  91]
Distance:   [0,   15,  12,  45,  23,  38]  km
NUTS-3:     [A,   A,   A,   B,   B,   C]
```

**Aggregation logic (lines 202-215):**
```python
current_segment_distance = 0.0

for i in range(1, len(sequence)):
    current_segment_distance += distances[i]  # Accumulate distance

    # When entering new region, record accumulated distance
    if nuts3_sequence[i] != nuts3_sequence[i-1]:
        segment_distances.append(current_segment_distance)
        current_segment_distance = 0.0  # Reset for next segment
```

**Result:**
```
Simplified nodes:     [NUTS_A,  NUTS_B,  NUTS_C]
Distance from prev:   [0,       72,      61]     km
Cumulative distance:  [0,       72,      133]    km

Where:
- 72 km = 15 + 12 (within A) + 45 (A→B transition)
- 61 km = 23 (within B) + 38 (B→C transition)
```

#### Step 4: Map NUTS-3 regions to new node IDs

Each NUTS-3 region gets assigned a new sequential node ID:
```
NUTS_A → node 0
NUTS_B → node 5
NUTS_C → node 12
```

**Final aggregated path:**
```python
{
    'id': 0,
    'sequence': [0, 5, 12],
    'distance_from_previous': [0, 72, 61],
    'cumulative_distance': [0, 72, 133],
    'length': 133  # Total path length
}
```

### Key Insight: **Distances are PRESERVED**

The total path length remains exactly the same:
- Original: 0 + 15 + 12 + 45 + 23 + 38 = **133 km**
- Aggregated: 0 + 72 + 61 = **133 km** ✓

Only the number of nodes changes (fewer nodes in sequence).

---

## Method B: Creating Paths from Traffic Data

**Used when:** You're starting directly from NUTS-3 traffic data (truck traffic CSV).

### Step-by-Step Process

#### Step 1: Group traffic by NUTS-3 OD-pairs

Traffic data provides:
```
ID_origin_region: 1234 (NUTS-3 code)
ID_destination_region: 5678 (NUTS-3 code)
Total_distance: 347.5 km (reported by traffic data)
Traffic_flow_trucks_2030: 1523 trucks/year
```

#### Step 2: Map NUTS-3 regions to network node IDs

```python
# Look up which node represents each NUTS-3 region
origin_node = nuts3_to_node[1234]  # e.g., node 42
dest_node = nuts3_to_node[5678]    # e.g., node 89
```

#### Step 3: Try to find a path in the NUTS-3 network

**Option 3a: Direct edge exists**
```python
if (origin_node, dest_node) in edge_lookup:
    # Use network edge distance
    path_distance = edge_lookup[(origin_node, dest_node)]
    path_sequence = [origin_node, dest_node]
```

**Example:**
```python
# Network has direct edge: node 42 → node 89 (distance: 28 km)
path = {
    'sequence': [42, 89],
    'distance_from_previous': [0, 28],
    'cumulative_distance': [0, 28],
    'length': 28
}
```

**⚠️ PROBLEM:** Traffic data says distance = 347.5 km, but network edge = 28 km!
**This is the 81% error we found!**

---

**Option 3b: No direct edge - use pathfinding**

```python
else:
    # No direct edge - find multi-hop path
    intermediate_path = find_simple_path_nuts3(
        origin_node, dest_node, edge_lookup
    )
```

The `find_simple_path_nuts3()` function uses **BFS (Breadth-First Search)** to find a path:

```python
def find_simple_path_nuts3(origin, destination, edge_lookup, max_depth=5):
    # Build adjacency list from edges
    adjacency = {}
    for (a, b) in edge_lookup.keys():
        if a not in adjacency:
            adjacency[a] = []
        adjacency[a].append(b)

    # BFS search
    queue = [(origin, [origin])]
    visited = {origin}

    while queue:
        node, path = queue.pop(0)

        if node == destination:
            return path  # Found it!

        # Explore neighbors
        for neighbor in adjacency.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    # No path found - return direct anyway
    return [origin, destination]
```

**Example multi-hop path:**
```
origin = node 42 (NUTS_A)
destination = node 89 (NUTS_C)

BFS finds: [42, 55, 67, 89]
           ↓    ↓    ↓    ↓
         NUTS_A → NUTS_B → NUTS_D → NUTS_C

Network distances:
- 42→55: 45 km
- 55→67: 67 km
- 67→89: 102 km
Total: 214 km
```

**Result path:**
```python
path = {
    'sequence': [42, 55, 67, 89],
    'distance_from_previous': [0, 45, 67, 102],
    'cumulative_distance': [0, 45, 112, 214],
    'length': 214
}
```

---

**Option 3c: Still no path found - fallback to traffic distance**

```python
# If BFS fails or returns direct path with no edge
if not intermediate_path or intermediate_path == [origin, destination]:
    # Use reported distance from traffic data
    path_distance = row['Total_distance']  # 347.5 km
    path_sequence = [origin_node, dest_node]
```

**Result:**
```python
path = {
    'sequence': [42, 89],
    'distance_from_previous': [0, 347.5],
    'cumulative_distance': [0, 347.5],
    'length': 347.5  # Uses traffic-reported distance
}
```

---

## Visual Comparison

### Method A: Aggregation
```
BEFORE (detailed network):
  node_A1 --15km--> node_A2 --12km--> node_A3 --45km--> node_B1 --23km--> node_B2 --38km--> node_C1
    ↓                 ↓                 ↓                 ↓                 ↓                 ↓
  NUTS_A           NUTS_A           NUTS_A           NUTS_B           NUTS_B           NUTS_C

AFTER (NUTS-3 aggregated):
  NUTS_A --------72km-------> NUTS_B --------61km-------> NUTS_C

Distance preserved: 72 + 61 = 133 km (same as original)
```

### Method B: Traffic-based
```
Traffic data says:
  NUTS_A → NUTS_C: 347.5 km, 1523 trucks/year

Network has three scenarios:

Scenario 1: Direct edge exists
  NUTS_A --28km--> NUTS_C
  ❌ ERROR: 28 km ≠ 347.5 km (81% underestimate)

Scenario 2: Multi-hop path found
  NUTS_A --45km--> NUTS_B --67km--> NUTS_D --102km--> NUTS_C
  Total: 214 km (still 38% error)

Scenario 3: No path, use traffic distance
  NUTS_A ------347.5km------> NUTS_C
  ✓ Uses reported distance (no network edge)
```

---

## Summary Table

| Aspect | Method A (Aggregation) | Method B (Traffic-based) |
|--------|----------------------|-------------------------|
| **Input** | Existing detailed paths | NUTS-3 traffic data |
| **Node sequence** | Collapsed from detailed path | Created from network topology |
| **Distance source** | Accumulated original distances | Network edges OR traffic data |
| **Distance accuracy** | 100% preserved | Varies (0-81% error) |
| **When direct edge exists** | N/A (uses aggregated distance) | Uses network edge (often too short) |
| **When no direct edge** | N/A (always has path) | Uses BFS or falls back to traffic distance |
| **Typical use case** | Simplifying existing model | Building new model from traffic data |

---

## Why the Difference Matters

### Method A (Aggregation):
- **Pros:** Preserves exact distances from original network
- **Cons:** Requires pre-existing detailed model
- **Use when:** You have a high-resolution model and want to reduce complexity

### Method B (Traffic-based):
- **Pros:** Can build model directly from traffic data without detailed network
- **Cons:** Distance accuracy depends on network topology matching traffic routes
- **Use when:** Starting fresh with only NUTS-3 level data

---

## Current Issue

Your analysis found **81% average error** for the 0.2% of OD-pairs with direct edges because:

1. **Traffic data** reports full route distances (e.g., 347.5 km via highways)
2. **NUTS-3 network edges** represent simplified inter-regional connections (e.g., 28 km "as the crow flies")

The NUTS-3 network edges are NOT meant to represent actual travel routes - they're simplified topological connections!

---

## Recommendation

For the Scandinavian Mediterranean corridor model, you should:

1. **Use Method B** (traffic-based) since you're building from NUTS-3 traffic data
2. **Modify the preprocessing** to ALWAYS use traffic-reported distances, never network edge distances
3. **Use network edges only for topology** (which nodes connect), not for distance

This would eliminate the 81% error by treating network edges as connectivity information only, while preserving realistic travel distances from the traffic data.
