# How to Integrate Mandatory Breaks into SM-preprocessing.ipynb

## Step 1: Copy the functions into your notebook

In SM-preprocessing.ipynb, after your imports, add a new cell with:

```python
import numpy as np

# Parameters for mandatory breaks (EU regulations)
MAX_DRIVING_TIME = 4.5  # hours
BREAK_DURATION = 45 / 60  # 45 minutes in hours

def calculate_mandatory_breaks(path, speed=80):
    """
    Calculate where mandatory breaks must be taken along a path.
    Returns a flat list of break entries for this path.
    """
    sequence = path['sequence']
    cumulative_distance = path['cumulative_distance']
    path_id = path['id']
    total_length = path['length']

    # Calculate total driving time (no breaks)
    total_driving_time = total_length / speed

    # Calculate number of breaks required
    num_breaks_required = int(np.floor(total_driving_time / MAX_DRIVING_TIME))

    break_list = []

    for break_num in range(1, num_breaks_required + 1):
        # Maximum cumulative driving time before this break must occur
        max_time_before_break = break_num * MAX_DRIVING_TIME
        max_distance_before_break = max_time_before_break * speed

        # Find the latest node where this break can occur
        latest_node_idx = None
        latest_geo_id = None
        actual_cum_distance = None

        for i, cum_dist in enumerate(cumulative_distance):
            if cum_dist <= max_distance_before_break:
                latest_node_idx = i
                latest_geo_id = sequence[i]['id'] if isinstance(sequence[i], dict) else sequence[i]
                actual_cum_distance = cum_dist
            else:
                break  # Exceeded max distance

        # If we couldn't find a node, use the last node
        if latest_node_idx is None and len(sequence) > 0:
            latest_node_idx = len(sequence) - 1
            latest_geo_id = sequence[latest_node_idx]['id'] if isinstance(sequence[latest_node_idx], dict) else sequence[latest_node_idx]
            actual_cum_distance = cumulative_distance[latest_node_idx] if latest_node_idx < len(cumulative_distance) else total_length

        # Calculate cumulative time at this point
        cumulative_driving_time = actual_cum_distance / speed

        # Total elapsed time including ALL breaks (including this one)
        time_with_breaks = cumulative_driving_time + break_num * BREAK_DURATION

        # Create flat entry - one per break
        break_list.append({
            'path_id': path_id,
            'path_length': total_length,
            'total_driving_time': total_driving_time,
            'break_number': break_num,
            'latest_node_idx': latest_node_idx,
            'latest_geo_id': latest_geo_id,
            'cumulative_distance': actual_cum_distance,
            'cumulative_driving_time': cumulative_driving_time,
            'time_with_breaks': time_with_breaks
        })

    return break_list


def create_mandatory_breaks_list(path_list, speed=80):
    """
    Create a flat list of mandatory break information for all paths.
    Returns one entry per break across all paths.
    """
    mandatory_breaks_list = []

    for path in path_list:
        breaks_for_path = calculate_mandatory_breaks(path, speed)
        mandatory_breaks_list.extend(breaks_for_path)

    return mandatory_breaks_list
```

## Step 2: Calculate breaks AFTER you've created path_list

Find the section in your notebook where you finish creating `path_list` (probably after calculating cumulative distances for each path). Add a new cell:

```python
# Calculate mandatory breaks for all paths
# Use the average speed from your Speed data (adjust if needed)
speed = 80  # km/h

print("Calculating mandatory breaks...")
mandatory_breaks_list = create_mandatory_breaks_list(path_list, speed=speed)

print(f"\n✓ Created {len(mandatory_breaks_list)} mandatory break entries")
```

## Step 3: Print summary to verify

Add another cell to see what was created:

```python
from collections import defaultdict

print(f"\nMANDATORY BREAKS SUMMARY:")
print(f"="*80)

# Group by path for display
breaks_by_path = defaultdict(list)
for entry in mandatory_breaks_list:
    breaks_by_path[entry['path_id']].append(entry)

for path_id, breaks in breaks_by_path.items():
    if len(breaks) > 0:
        first_entry = breaks[0]
        print(f"\nPath {path_id}:")
        print(f"  Length: {first_entry['path_length']:.2f} km")
        print(f"  Driving time: {first_entry['total_driving_time']:.2f} hours")
        print(f"  Breaks required: {len(breaks)}")

        for entry in breaks:
            print(f"    Break {entry['break_number']}: "
                  f"Latest at node idx {entry['latest_node_idx']} (geo_id={entry['latest_geo_id']})")
            print(f"      Distance: {entry['cumulative_distance']:.2f} km")
            print(f"      Time with breaks: {entry['time_with_breaks']:.2f} hours")
```

## Step 4: Export to YAML (in your export section)

In the section where you export all the YAML files, add:

```python
# Export mandatory breaks
output_path = os.path.join(output_dir, 'MandatoryBreaks.yaml')
with open(output_path, 'w') as f:
    yaml.dump(mandatory_breaks_list, f, default_flow_style=False)

print(f"✓ Saved {len(mandatory_breaks_list)} mandatory break entries to MandatoryBreaks.yaml")
```

## Example Output Structure

The YAML file will have a flat structure like this:

```yaml
- path_id: 0
  path_length: 720.0
  total_driving_time: 9.0
  break_number: 1
  latest_node_idx: 45
  latest_geo_id: 123456
  cumulative_distance: 360.0
  cumulative_driving_time: 4.5
  time_with_breaks: 5.25

- path_id: 0
  path_length: 720.0
  total_driving_time: 9.0
  break_number: 2
  latest_node_idx: 90
  latest_geo_id: 234567
  cumulative_distance: 720.0
  cumulative_driving_time: 9.0
  time_with_breaks: 10.5

- path_id: 1
  path_length: 400.0
  total_driving_time: 5.0
  break_number: 1
  latest_node_idx: 30
  latest_geo_id: 345678
  cumulative_distance: 360.0
  cumulative_driving_time: 4.5
  time_with_breaks: 5.25
```

## What Each Field Means:

- `path_id`: Which path this break belongs to
- `path_length`: Total length of the path (km)
- `total_driving_time`: Total driving time for entire path (hours, excluding breaks)
- `break_number`: 1st break, 2nd break, etc.
- `latest_node_idx`: Index in path.sequence where break must occur
- `latest_geo_id`: Geographic element ID of that node
- `cumulative_distance`: How far you've traveled when you reach this break (km)
- `cumulative_driving_time`: Driving time up to this break (hours, excluding breaks)
- `time_with_breaks`: Total elapsed time AFTER taking this break (hours, including break time)

## Using in Julia Model

In your Julia model, you can read this data and use it to:
1. Constrain that vehicles must stop at or before `latest_geo_id` for each break
2. Add the break time to travel time calculations
3. Enforce that charging can occur during breaks

The flat structure makes it easy to iterate over all breaks and create constraints!
