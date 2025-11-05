"""
IMPORTANT: Copy this cell to reload both modules properly

When you update sub_border_regions.py, you need to reload BOTH modules
in the correct order because sub_border_regions_cross_case imports from sub_border_regions.
"""

# Reload BOTH modules in correct order
import importlib
import sub_border_regions
import sub_border_regions_cross_case

# Reload the base module first (contains SUB_BORDER_REGIONS)
importlib.reload(sub_border_regions)

# Then reload the cross-case module (imports from sub_border_regions)
importlib.reload(sub_border_regions_cross_case)

# Import everything
from sub_border_regions_cross_case import *

print("✓ Modules reloaded successfully!")
print("\nAvailable clusters:")
from sub_border_regions import SUB_BORDER_REGIONS
for name in SUB_BORDER_REGIONS.keys():
    print(f"  - {name}")
