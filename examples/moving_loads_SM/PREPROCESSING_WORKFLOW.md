# SM Preprocessing Workflow - Complete Guide

## Overview

The Scandinavian-Mediterranean (SM) corridor preprocessing is split into **two stages**:

1. **Stage 1**: Generate NUTS-3 geographic and path data (one-time setup)
2. **Stage 2**: Generate parameter files with different configurations (repeatable for scenarios)

This design allows you to **create multiple input file sets with varying parameters** while reusing the same geographic/path data!

---

## Stage 1: Generate NUTS-3 Geographic/Path Data

**Script**: `SM_preprocessing_nuts3_complete.py`

**What it does**:
- Loads truck traffic data from `data/Trucktraffic_NUTS3/`
- Aggregates network nodes to NUTS-3 level (1,675 regional nodes)
- Creates collapsed path sequences (fewer nodes)
- Preserves original traffic-reported distances
- Keeps individual OD-pairs (not aggregated)
- Calculates mandatory breaks based on collapsed nodes

**Output files** (in `output_data/sm_nuts3_complete/`):
- `GeographicElement.yaml` - NUTS-3 nodes with coordinates
- `Path.yaml` - Collapsed paths with original distances
- `Odpair.yaml` - Individual OD-pairs
- `InitialVehicleStock.yaml` - Vehicle stock per OD-pair
- `MandatoryBreaks.yaml` - Driver break constraints

### Running Stage 1:

**Test mode** (100 OD-pairs):
```bash
cd examples/moving_loads_SM
python SM_preprocessing_nuts3_complete.py
```

**Full run** (all ~1.3M OD-pairs):
Edit line 529 in `SM_preprocessing_nuts3_complete.py`:
```python
test_mode = False  # Change from True
```
Then run:
```bash
python SM_preprocessing_nuts3_complete.py
```

**Expected runtime**:
- Test mode: ~30 seconds
- Full run: ~10-30 minutes

---

## Stage 2: Generate Parameter Files

**Script**: `SM_preprocessing.py`

**What it does**:
- Loads preprocessed NUTS-3 data from Stage 1
- Generates all parameter files with configurable settings:
  - Technology definitions
  - Fuel types and costs
  - Fueling infrastructure types (with `om_costs`!)
  - Vehicle types and tech-vehicle combinations
  - Speed parameters
  - Initial infrastructure
  - Model configuration

**Output**: Complete input data set in `input_data/case_YYYYMMDD_HHMMSS/`

### Running Stage 2:

**Default parameters**:
```bash
cd examples/moving_loads_SM
python SM_preprocessing.py
```

**Custom case name**:
```bash
python SM_preprocessing.py output_data/sm_nuts3_complete case_baseline
```

**Different source data**:
```bash
python SM_preprocessing.py output_data/sm_nuts3_full case_full_data
```

---

## Creating Different Parameter Scenarios

To create multiple scenarios with different parameters:

### Method 1: Edit the Script

Modify the `generate_*_params()` methods in `SM_preprocessing.py`:

```python
def generate_fueling_infr_types(self) -> List[Dict]:
    """Generate FuelingInfrTypes parameter list."""
    return [
        {
            'id': 1,
            'name': 'fast_charger',
            'fuel': 1,
            'capacity': 100.0,
            'capex': 200000.0,  # INCREASED from 150000
            'om_costs': 8000.0,  # INCREASED from 5000
            'lifetime': 15,
        },
        # ... other infrastructure types
    ]
```

Then run:
```bash
python SM_preprocessing.py output_data/sm_nuts3_complete case_high_capex
```

### Method 2: Create Custom Script

Create a new script (e.g., `SM_preprocessing_custom.py`) that imports and extends:

```python
from SM_preprocessing import SMParameterGenerator

class CustomParameterGenerator(SMParameterGenerator):
    def generate_fueling_infr_types(self):
        # Your custom implementation
        return [...]

# Run with custom generator
generator = CustomParameterGenerator(
    nuts3_data_dir="output_data/sm_nuts3_complete",
    case_name="case_custom_scenario"
)
generator.run()
```

---

## Complete Workflow Example

### 1. Generate NUTS-3 data (once):
```bash
cd examples/moving_loads_SM
python SM_preprocessing_nuts3_complete.py
```

Output: `output_data/sm_nuts3_complete/`

### 2. Create baseline scenario:
```bash
python SM_preprocessing.py output_data/sm_nuts3_complete case_baseline
```

Output: `input_data/case_baseline/`

### 3. Create high CAPEX scenario:
Edit `generate_fueling_infr_types()` to increase CAPEX values, then:
```bash
python SM_preprocessing.py output_data/sm_nuts3_complete case_high_capex
```

Output: `input_data/case_high_capex/`

### 4. Create low fuel cost scenario:
Edit `generate_fuel_cost_params()` to decrease costs, then:
```bash
python SM_preprocessing.py output_data/sm_nuts3_complete case_low_fuel
```

Output: `input_data/case_low_fuel/`

### 5. Use in Julia:
```julia
# In SM.jl:

# Baseline scenario
input_path = joinpath(@__DIR__, "input_data/case_baseline")
data_dict = get_input_data(input_path)
# ... continue with model setup

# High CAPEX scenario
input_path = joinpath(@__DIR__, "input_data/case_high_capex")
data_dict = get_input_data(input_path)
# ... continue with model setup
```

---

## Parameter File Details

### Files Generated in Stage 2:

| File | Purpose | Configurable Parameters |
|------|---------|------------------------|
| `Technology.yaml` | Vehicle technologies | Technology names/IDs |
| `Fuel.yaml` | Fuel types | Fuel names/IDs |
| `FuelCost.yaml` | Fuel costs over time | Costs by fuel and year |
| `FuelingInfrTypes.yaml` | Infrastructure types | Capacity, CAPEX, OM costs, lifetime |
| `Mode.yaml` | Transport modes | Mode definitions |
| `Vehicletype.yaml` | Vehicle types | Capacity, max range |
| `TechVehicle.yaml` | Tech-vehicle combos | Fuel consumption, CAPEX, OPEX, emissions |
| `Product.yaml` | Transported goods | Product types |
| `FinancialStatus.yaml` | Financial parameters | Financial categories |
| `Regiontype.yaml` | Region classifications | Region types |
| `Speed.yaml` | Average speeds | Speed by mode/region |
| `Model.yaml` | Model configuration | Years, discount rate, carbon price |
| `NetworkConnectionCosts.yaml` | Connection costs | Infrastructure connection costs |
| `InitialModeInfr.yaml` | Initial mode infra | Existing mode infrastructure |
| `InitialFuelInfr.yaml` | Initial fuel infra | Existing fueling stations |

### Files Copied from Stage 1:

| File | Description |
|------|-------------|
| `GeographicElement.yaml` | 1,675 NUTS-3 nodes with coordinates |
| `Path.yaml` | Collapsed paths with original distances |
| `Odpair.yaml` | Individual OD-pairs (not aggregated) |
| `InitialVehicleStock.yaml` | Vehicle stock per OD-pair |
| `MandatoryBreaks.yaml` | Driver break constraints |

---

## Key Features

### Efficient Geographic Aggregation:
- **1,675 NUTS-3 nodes** instead of 10,000+ detailed nodes
- Faster optimization solve times
- Appropriate scale for regional infrastructure planning

### Accurate Distances:
- **Original traffic-reported distances preserved**
- No 81% error from network topology
- Distances distributed across collapsed nodes

### Demand Detail Preserved:
- **Individual OD-pairs NOT aggregated**
- Full heterogeneity maintained
- Can analyze route-specific patterns

### Configurable Parameters:
- **Create multiple scenarios easily**
- Vary CAPEX, OPEX, fuel costs, etc.
- Test policy sensitivities

---

## Troubleshooting

### Error: "GeographicElement.yaml not found"
**Solution**: Run Stage 1 first (`SM_preprocessing_nuts3_complete.py`)

### Error: "FileNotFoundError: data/Trucktraffic_NUTS3/"
**Solution**: Ensure traffic data is in correct location

### Want to modify fuel costs:
**Solution**: Edit `generate_fuel_cost_params()` in `SM_preprocessing.py`

### Want to add new technology:
**Solution**:
1. Add to `generate_technology_params()`
2. Add fuel type to `generate_fuel_params()`
3. Add tech-vehicle combo to `generate_tech_vehicle_params()`

### Want to test with fewer OD-pairs:
**Solution**: Stage 1 has test mode (100 OD-pairs) enabled by default

---

## File Size Reference

Typical file sizes for test mode (100 OD-pairs):

| File | Size |
|------|------|
| GeographicElement.yaml | ~670 KB |
| Path.yaml | ~22 KB |
| Odpair.yaml | ~91 KB |
| InitialVehicleStock.yaml | ~301 KB |
| InitialFuelInfr.yaml | ~155 KB |
| Parameter files | < 5 KB each |

Full run (~1.3M OD-pairs) will be proportionally larger.

---

## Summary

**Two-stage workflow enables flexible scenario creation:**

1. **Generate geographic/path data once** (computationally expensive)
2. **Generate parameter files many times** (fast, configurable)
3. **Create multiple input datasets** with different parameter values
4. **Test policy scenarios** without re-processing geographic data

This approach gives you maximum flexibility for parameter sensitivity analysis!

---

## Questions?

- Check console output for detailed progress messages
- Review parameter methods in `SM_preprocessing.py` for customization
- Verify YAML files can be loaded with `yaml.safe_load()`
- Test with small OD-pair count first (100) before full run

**Happy preprocessing!**
