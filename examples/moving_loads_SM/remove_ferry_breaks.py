"""
Remove ferry routes from mandatory breaks analysis
Creates a filtered MandatoryBreaks.yaml without ferry routes
"""

import yaml
import os
import shutil
from datetime import datetime

case_folder = "case_20251106_112933"
input_path = os.path.join("input_data", case_folder)

def load_yaml_file(filename):
    filepath = os.path.join(input_path, filename)
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def save_yaml_file(data, filename):
    filepath = os.path.join(input_path, filename)
    with open(filepath, 'w') as f:
        yaml.dump(data, f)

print("="*80)
print("REMOVING FERRY ROUTES FROM MANDATORY BREAKS")
print("="*80)

# ============================================================================
# STEP 1: Identify ferry paths (edges > 800 km)
# ============================================================================

print("\nStep 1: Identifying ferry paths...")

paths = load_yaml_file('Path.yaml')
ferry_path_ids = set()

for path in paths:
    if 'distance_from_previous' in path:
        distances = path['distance_from_previous']

        # Check if any segment is > 800 km (ferry)
        for i, dist in enumerate(distances):
            if i > 0 and dist > 800:
                ferry_path_ids.add(path['id'])
                break

print(f"Found {len(ferry_path_ids)} paths with ferry edges (>800km)")
print(f"Ferry path IDs: {sorted(ferry_path_ids)}")

# ============================================================================
# STEP 2: Load original mandatory breaks
# ============================================================================

print("\nStep 2: Loading original mandatory breaks...")

mandatory_breaks = load_yaml_file('MandatoryBreaks.yaml')
print(f"Original mandatory breaks: {len(mandatory_breaks)} entries")

# ============================================================================
# STEP 3: Filter out ferry routes
# ============================================================================

print("\nStep 3: Filtering out ferry routes...")

# Backup original file
backup_file = os.path.join(input_path, 'MandatoryBreaks_original.yaml')
if not os.path.exists(backup_file):
    original_file = os.path.join(input_path, 'MandatoryBreaks.yaml')
    shutil.copy2(original_file, backup_file)
    print(f"  Created backup: MandatoryBreaks_original.yaml")

# Filter breaks
filtered_breaks = [mb for mb in mandatory_breaks if mb['path_id'] not in ferry_path_ids]

removed_count = len(mandatory_breaks) - len(filtered_breaks)
print(f"  Removed {removed_count} mandatory break entries from ferry routes")
print(f"  Remaining: {len(filtered_breaks)} entries")

# ============================================================================
# STEP 4: Save filtered mandatory breaks
# ============================================================================

print("\nStep 4: Saving filtered mandatory breaks...")

# Save filtered version
save_yaml_file(filtered_breaks, 'MandatoryBreaks.yaml')
print(f"  Saved filtered version: MandatoryBreaks.yaml")

# Also save with timestamp for reference
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
save_yaml_file(filtered_breaks, f'MandatoryBreaks_no_ferries_{timestamp}.yaml')
print(f"  Saved timestamped copy: MandatoryBreaks_no_ferries_{timestamp}.yaml")

# ============================================================================
# STEP 5: Summary
# ============================================================================

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\nFerry paths excluded from mandatory breaks:")
for path_id in sorted(ferry_path_ids):
    path = next((p for p in paths if p['id'] == path_id), None)
    if path:
        print(f"  Path {path_id}: {path['length']:.1f} km")

print(f"\nMandatory breaks statistics:")
print(f"  Original:  {len(mandatory_breaks)} entries")
print(f"  Removed:   {removed_count} entries ({removed_count/len(mandatory_breaks)*100:.1f}%)")
print(f"  Remaining: {len(filtered_breaks)} entries ({len(filtered_breaks)/len(mandatory_breaks)*100:.1f}%)")

print(f"\nFiles created:")
print(f"  - MandatoryBreaks_original.yaml (backup of original)")
print(f"  - MandatoryBreaks.yaml (filtered version, OVERWRITES original)")
print(f"  - MandatoryBreaks_no_ferries_{timestamp}.yaml (timestamped copy)")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("""
1. The filtered MandatoryBreaks.yaml is now in your input_data folder
2. Re-run your Julia model with this filtered data
3. The ferry routes will no longer have mandatory break constraints
4. This should eliminate the 22h+ break times

To restore original:
  - Copy MandatoryBreaks_original.yaml back to MandatoryBreaks.yaml
""")

print("\n" + "="*80)
