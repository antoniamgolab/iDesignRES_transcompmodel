# Border Infrastructure Analysis - Quick Start

## ✅ Use This File

**File:** `border_infrastructure_notebook_cells.py`

**NOT:** `border_infrastructure_analysis.py` (has errors)

---

## Copy These Cells into Your Notebook

Open `border_infrastructure_notebook_cells.py` and copy the following cells into your `results_representation.ipynb`:

### After your data loading cells, add these:

```python
# ============================================================================
# NEW CELL: Import Infrastructure Functions
# ============================================================================

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from infrastructure_analysis import get_infrastructure_data

def load_border_region_codes(border_codes_file="border_nuts2_codes.txt"):
    """Load border region codes from file."""
    with open(border_codes_file, 'r') as f:
        codes = {line.strip() for line in f if line.strip()}
    return codes

def calculate_border_infrastructure_capacity(
    input_data, output_data, border_nuts2_codes, year, fuel_name='electricity'
):
    """Calculate infrastructure capacity for border regions only."""
    infra_data = get_infrastructure_data(input_data, output_data)
    fuel_list = infra_data['fuel_list']
    fueling_infr_types_list = infra_data['fueling_infr_types_list']
    initial_fueling_infr = infra_data['initial_fueling_infr']
    investment_years = infra_data['investment_years']

    geographic_element_list = {d["id"]: d for d in input_data["GeographicElement"]}

    # Extract energy consumption
    energy_by_location = {}
    if 's' in output_data:
        for key, value in output_data['s'].items():
            s_year = key[0]
            if s_year != year:
                continue
            if len(key) >= 4:
                f_l = key[3]
                fuel_id, infr_id = f_l[0], f_l[1]
                geo_id = key[1] if isinstance(key[1], int) else (key[2] if len(key) > 2 and isinstance(key[2], int) else None)
                if geo_id is not None:
                    energy_key = (s_year, geo_id, fuel_id, infr_id)
                    energy_by_location[energy_key] = energy_by_location.get(energy_key, 0.0) + value

    records = []
    for geo_id, geo_data in geographic_element_list.items():
        geo_nuts2 = geo_data.get('nuts2_region')
        if geo_nuts2 not in border_nuts2_codes:
            continue

        country = geo_data.get('country', 'Unknown')
        for infr_id, infr_data in fueling_infr_types_list.items():
            for fuel_id, fuel_data in fuel_list.items():
                current_fuel_name = fuel_data["name"]
                if fuel_name and current_fuel_name != fuel_name:
                    continue
                if infr_data["fuel"] != current_fuel_name:
                    continue

                initial_key = (current_fuel_name, infr_id, geo_id)
                initial_capacity = initial_fueling_infr[initial_key]["installed_kW"] if initial_key in initial_fueling_infr else 0.0

                added_capacity = 0.0
                f_l = (fuel_id, infr_id)
                for inv_year in investment_years:
                    if inv_year <= year:
                        key_q = (inv_year, f_l, geo_id)
                        if key_q in output_data["q_fuel_infr_plus"]:
                            added_capacity += output_data["q_fuel_infr_plus"][key_q]

                total_capacity = initial_capacity + added_capacity
                energy_key = (year, geo_id, fuel_id, infr_id)
                energy_consumed = energy_by_location.get(energy_key, 0.0)

                utilization_rate = None
                if total_capacity > 0:
                    max_possible_energy = total_capacity * 8760
                    utilization_rate = energy_consumed / max_possible_energy if max_possible_energy > 0 else 0.0

                if total_capacity > 0:
                    records.append({
                        'geo_id': geo_id,
                        'geo_name': geo_data.get('name', 'Unknown'),
                        'nuts2_region': geo_nuts2,
                        'country': country,
                        'fuel': current_fuel_name,
                        'infrastructure_type': infr_data['fueling_type'],
                        'initial_capacity_kW': initial_capacity,
                        'added_capacity_kW': added_capacity,
                        'total_capacity_kW': total_capacity,
                        'energy_consumed_kWh': energy_consumed,
                        'utilization_rate': utilization_rate,
                        'utilization_pct': utilization_rate * 100 if utilization_rate else None
                    })

    return pd.DataFrame(records)

print("Infrastructure analysis functions loaded!")
```

Then just copy cells 2-8 from `border_infrastructure_notebook_cells.py` one by one.

---

## OR Use This One-Liner

If you want to run everything at once:

```python
# NEW CELL: Run complete infrastructure analysis
%run border_infrastructure_notebook_cells.py
```

This will execute all 8 cells automatically.

---

## What NOT to Do

❌ **Don't run:** `%run border_infrastructure_analysis.py` (has errors)

✅ **Do run:** `%run border_infrastructure_notebook_cells.py` (fixed version)

---

## The 8 Cells You'll Add

1. **Cell 1:** Import functions (copy from line 1-150 of border_infrastructure_notebook_cells.py)
2. **Cell 2:** Load data and calculate (copy from "CELL 2")
3. **Cell 3:** Calculate deltas (copy from "CELL 3")
4. **Cell 4:** Plot 1 - Capacity by scenario (copy from "CELL 4")
5. **Cell 5:** Plot 2 - Capacity deltas (copy from "CELL 5")
6. **Cell 6:** Plot 3 - Utilization (copy from "CELL 6")
7. **Cell 7:** Plot 4 - Summary table (copy from "CELL 7")
8. **Cell 8:** Export data (copy from "CELL 8")

---

## Expected Output

When you run these cells, you'll get:

✅ 14 border regions loaded
✅ Data calculated for all scenarios
✅ 4 plots generated (PNG files)
✅ 3 CSV files exported

---

## Troubleshooting

### Still getting IndentationError?
You're trying to run the OLD file. Use `border_infrastructure_notebook_cells.py` instead.

### NameError about loaded_runs?
Make sure you run the infrastructure analysis AFTER loading your data.

### No plots appearing?
Check that matplotlib is displaying inline: `%matplotlib inline`

---

Ready to use! Just use the notebook cells file, not the analysis.py file. 🎯
