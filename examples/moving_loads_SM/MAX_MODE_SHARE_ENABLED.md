# Max Mode Share Constraint - NOW ENABLED

## What Was Changed

### 1. Modified `src/support_functions.jl`
**Line 36**: Added "MaxModeShare" to the list of files that get loaded:

```julia
component_files = [
    "Model", "TechVehicle", "GeographicElement", "FinancialStatus",
    "Vehicletype", "Mode", "Technology", "Speed", "Regiontype",
    "InitialModeInfr", "InitialFuelInfr", "Odpair", "Path",
    "Fuel", "FuelCost", "FuelingInfrTypes", "InitialVehicleStock",
    "NetworkConnectionCosts", "Product", "SpatialFlexibilityEdges",
    "MandatoryBreaks", "MaxModeShare",  # <-- ADDED THIS
]
```

### 2. Updated `examples/moving_loads_SM/SM.jl`
**Lines 248-254**: Added max mode share timing to the summary:

```julia
@info "    - Max mode share:   $(round(t_max_mode_share, digits=2))s"
...
t_constraint_total = ... + t_max_mode_share + ...
```

The constraint itself was already enabled in the code (lines 156-165).

## What This Does

The model will now enforce the constraints defined in `MaxModeShare.yaml`:

```yaml
- year: 2020-2060 (all years)
  mode: 2 (rail)
  share: 0.3 (30%)
```

**Constraint**: Rail can carry at most **30% of total freight** in any given year.

## Expected Impact

### Before (No Constraint)
With rail at €0.05/tkm (cheaper than road at €0.082/tkm):
- **Modal split**: 100% rail
- **Objective**: €4.63B
- Rail wins purely on cost

### After (With 30% Rail Cap)
With rail at €0.05/tkm:
- **Modal split**: 30% rail, 70% road (constrained)
- **Objective**: Higher than €4.63B (forced to use more expensive road)
- Rail hits its capacity limit

## Implementation Details

### Constraint Formula
For each year `y`:
```
sum(flow on rail) / sum(total flow across all modes) <= 0.30
```

This is implemented in `constraint_max_mode_share()` function in `src/model_functions.jl`.

### Data Source
- **File**: `input_data/case_20251102_093733/MaxModeShare.yaml`
- **Entries**: 21 constraints (one per modeled year 2020-2060)
- **All identical**: 30% cap for mode 2 (rail)

## Use Cases

This constraint is useful for modeling:

1. **Infrastructure capacity limits**: Rail network can only handle X% of freight
2. **Policy scenarios**: Government limits on modal share for various reasons
3. **Realistic transitions**: Gradual shift to rail rather than instant 100% switch
4. **Sensitivity analysis**: How does capping rail affect costs and emissions?

## Testing

Run the model with:
```bash
cd examples/moving_loads_SM
julia SM.jl
```

Look for in the log:
```
[ Info: Step 4.6/5: Adding max mode share constraint...
[ Info: ✓ Max mode share constraint added in X.XX seconds
```

If you see "Skipping max mode share constraint (no constraints defined)", then MaxModeShare.yaml wasn't loaded properly.

## Modifying the Constraint

To change the rail capacity limit, edit `MaxModeShare.yaml`:

```yaml
- id: 0
  year: 2020
  mode: 2
  share: 0.5  # Change to 50% cap instead of 30%
```

You can also:
- Add different caps for different years (e.g., increasing rail capacity over time)
- Add caps for other modes (mode 1 = road)
- Remove the file entirely to disable the constraint

## Status

✅ **MaxModeShare constraint is now ENABLED**
✅ **Rail capped at 30% of total freight**
✅ **Running test with cheap rail to verify constraint works**

The model is currently running to verify that the constraint properly limits rail to 30% even when rail is cheaper than road.
