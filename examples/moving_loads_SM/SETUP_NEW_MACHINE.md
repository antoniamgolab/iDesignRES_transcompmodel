# Setup Guide for New Machine

**Created**: 2025-10-17
**Purpose**: Transfer iDesignRES TransComp moving loads model to new computer with all critical fixes applied

---

## 🎯 Quick Start Checklist

- [ ] Install Julia 1.6+
- [ ] Install Gurobi (academic license)
- [ ] Install Python 3.8+ with packages: pandas, numpy, pyyaml, networkx
- [ ] Clone git repository
- [ ] Transfer source data files (not in git due to size)
- [ ] Run preprocessing to generate input data
- [ ] Run SM.jl model
- [ ] Verify: 64 GB RAM is sufficient (model uses 5-10 GB max)

---

## 🐛 CRITICAL BUG FIXES APPLIED

### Generation Index Fixes (g <= y)
**Problem**: Three BEV-related variables had inconsistent generation filtering causing KeyError when vehicles purchased in year y tried to operate in year y.

**Location**: `src/model_functions.jl`

**Fixed variables** (all must use `g <= y` not `g < y`):

1. **travel_time** (Line ~253):
   ```julia
   # BEFORE (WRONG):
   @variable(model, travel_time[y in y_init:Y_end, p_r_k_g_pairs, tv in techvehicle_ids, f_l in f_l_not_by_route, g in g_init:min(y-1, Y_end)] >= 0)

   # AFTER (CORRECT):
   @variable(model, travel_time[y in y_init:Y_end, p_r_k_g_pairs, tv in techvehicle_ids, f_l in f_l_not_by_route, g in g_init:y] >= 0)
   ```

2. **soc** (state of charge, Line ~247):
   ```julia
   # BEFORE (WRONG):
   @variable(model, soc[y in y_init:Y_end, p_r_k_g_pairs, tv in techvehicle_ids, f_l in f_l_not_by_route, g in g_init:min(y-1, Y_end)] >= 0)

   # AFTER (CORRECT):
   @variable(model, soc[y in y_init:Y_end, p_r_k_g_pairs, tv in techvehicle_ids, f_l in f_l_not_by_route, g in g_init:y] >= 0)
   ```

3. **extra_break_time** (Line ~259):
   ```julia
   # BEFORE (WRONG):
   @variable(model, extra_break_time[y in y_init:Y_end, p_r_k_g_pairs, tv in techvehicle_ids, f_l in f_l_not_by_route, g in g_init:min(y-1, Y_end)] >= 0)

   # AFTER (CORRECT):
   @variable(model, extra_break_time[y in y_init:Y_end, p_r_k_g_pairs, tv in techvehicle_ids, f_l in f_l_not_by_route, g in g_init:y] >= 0)
   ```

**Why this matters**: Vehicles purchased in year y CAN operate in year y. This is consistent with:
- `f` (flow) variable: uses `g <= y`
- `h`, `h_plus`, `h_exist`, `h_minus` (vehicle stock): all use `g <= y`

---

## 📊 Working Configuration

### Current Successful Run
- **Case**: `case_20251017_105556` (NUTS-2 aggregated)
- **Input size**: 8.3 MB (2,928 OD-pairs)
- **Mandatory breaks**: Fixed with 360km + cross-border threshold
- **Model size**: 56.6M rows, 86.6M columns (before presolve)
- **Presolved**: 896K rows, 1.0M columns
- **Solve time**: 152 seconds (barrier method)
- **Total runtime**: 29.3 minutes
- **Memory used**: ~1.2 GB for Gurobi solver, ~5-10 GB total

### Performance Metrics
- Optimal objective: 1.27e12
- Iterations: 751,075
- All diagnostics passed ✓
  - SOC validation ✓
  - Travel time validation ✓
  - Mandatory breaks validation (602,280 checks) ✓

---

## 💾 Memory Requirements

**Minimum**: 16 GB RAM
**Recommended**: 32 GB RAM
**Your new machine**: 64 GB RAM ✅ **More than sufficient**

**Actual usage breakdown**:
- Gurobi barrier factorization: ~1.2 GB
- Julia data structures + model: ~2-4 GB
- Variable storage: ~1-2 GB
- **Total peak usage**: 5-10 GB maximum

---

## 📁 File Structure & Git Setup

### What's in Git
```
src/model_functions.jl          # Core model (WITH g <= y fixes)
examples/moving_loads_SM/
  ├── SM.jl                      # Main execution script
  ├── SM_preprocessing*.py       # Preprocessing scripts
  ├── check_soc_simple.jl        # SOC diagnostic
  ├── check_travel_time_verbose.jl  # Travel time diagnostic
  ├── check_mandatory_breaks.jl  # Mandatory breaks diagnostic
  ├── *.md                       # Documentation (12 files)
  └── input_data/
      └── case_20251017_105556/  # Working case (8.3 MB)
```

### What's NOT in Git (too large)
```
examples/moving_loads_SM/
  ├── data/                      # Source data (~7 GB)
  │   ├── Trucktraffic_NUTS3/01_Trucktrafficflow.csv  (2.6 GB)
  │   ├── Trucktraffic/01_Trucktrafficflow.csv        (2.6 GB)
  │   └── electricity data/ & GENeSYS-MOD*/           (2.5 GB)
  ├── input_data/                # Generated inputs (~5 GB, except one case)
  ├── output_data/               # Preprocessing outputs
  └── results/                   # Model results
```

**Action required**: Transfer these large files separately (USB drive, network share, etc.)

---

## 🚀 Setup Instructions for New Machine

### 1. Software Installation

```bash
# Julia (version 1.11 or compatible)
# Download from: https://julialang.org/downloads/

# Install Julia packages
julia -e 'using Pkg; Pkg.add(["JuMP", "Gurobi", "YAML", "ProgressMeter"])'

# Python (3.8+)
pip install pandas numpy pyyaml networkx matplotlib

# Gurobi Optimizer
# Academic license: https://www.gurobi.com/academia/academic-program-and-licenses/
# Note: License must be activated on new machine
```

### 2. Clone Repository

```bash
git clone <your-repo-url>
cd iDesignRES_transcompmodel/examples/moving_loads_SM
```

### 3. Transfer Large Data Files

**Copy these directories from old machine**:
- `data/Trucktraffic_NUTS3/`
- `data/Trucktraffic/`
- `data/electricity data/`
- `data/GENeSYS-MOD*/`

**OR regenerate from source** if you have original truck traffic data.

### 4. Preprocessing (if needed)

```bash
# NUTS-2 aggregation with mandatory breaks (recommended)
python SM_preprocessing_nuts2_complete.py "data/Trucktraffic_NUTS3" "input_data/sm_nuts2_aggregated" None 360.0 true

# Then generate parameters
python SM_preprocessing.py
```

This creates a new input case folder with all required YAML files.

### 5. Run the Model

```julia
# Edit SM.jl to point to your input case:
# folder = "case_YYYYMMDD_HHMMSS"  # Your new case folder

julia SM.jl
```

### 6. Verify Results

Check that diagnostics pass:
- ✓ SOC validation
- ✓ Travel time validation
- ✓ Mandatory breaks validation

Results saved to: `results/<case_folder>/`

---

## 🔧 Gurobi Configuration

The model uses these solver settings (already in SM.jl):

```julia
set_optimizer_attribute(model, "TimeLimit", 3600)  # 1 hour max
# Threads: Uses all available cores by default
# Presolve: Gurobi default (aggressive)
# MIPGap: Default tolerance
```

**For faster testing**: Reduce problem size by filtering OD-pairs or using NUTS-2 aggregation

---

## 📝 Key Files Modified

### Core Model
- `src/model_functions.jl` - Lines 247, 253, 259 (g <= y fixes)

### Preprocessing
- `SM_preprocessing_nuts2_complete.py` - NUTS-2 aggregation with mandatory breaks
- `SM_preprocessing.py` - Parameter generation

### Execution
- `SM.jl` - Main model run script (includes diagnostics)

### Diagnostics (all in use)
- `check_soc_simple.jl`
- `check_travel_time_verbose.jl`
- `check_mandatory_breaks.jl`

---

## ⚠️ Known Issues & Solutions

### Issue: KeyError for (2020, ..., 2020)
**Cause**: Variables using `g < y` instead of `g <= y`
**Solution**: Fixed in model_functions.jl (see Critical Bug Fixes above)

### Issue: Preprocessing too slow
**Cause**: Full NUTS-3 resolution = too many OD-pairs
**Solution**: Use NUTS-2 aggregation (reduces from ~50K to ~3K OD-pairs)

### Issue: Out of memory
**Cause**: Model too large for available RAM
**Solution**: 64 GB is sufficient; if issues persist, use NUTS-2 aggregation

### Issue: Gurobi license error
**Cause**: License not activated on new machine
**Solution**: Run `grbgetkey <license-key>` on new computer

---

## 📚 Additional Documentation

Useful reference files (in repo):
- `NUTS3_PREPROCESSING_SUMMARY.md` - Preprocessing workflow
- `PREPROCESSING_WORKFLOW.md` - Detailed preprocessing steps
- `PARAMETER_GENERATION_COMPLETE.md` - Parameter generation guide
- `MANDATORY_BREAKS_VALIDATION_SUMMARY.md` - Mandatory breaks implementation
- `how_to_use_mandatory_breaks_constraint.md` - Constraint explanation

---

## 🔄 Workflow Summary

1. **Source data** → Preprocessing scripts → **Input YAML files**
2. **Input YAMLs** → SM.jl → **Optimization model**
3. **Model** → Gurobi solver → **Results**
4. **Results** → Python notebooks → **Analysis/Visualization**

---

## ✅ Final Checklist

Before running on new machine:

- [ ] Julia installed and packages added
- [ ] Gurobi installed and license activated
- [ ] Python installed with required packages
- [ ] Git repo cloned
- [ ] Large data files transferred
- [ ] Verified `src/model_functions.jl` has g <= y fixes
- [ ] SM.jl points to correct input folder
- [ ] Test run with case_20251017_105556 (known working case)
- [ ] All diagnostics pass ✓

---

## 🆘 Troubleshooting

If you encounter issues:

1. **Check git commit history** for recent changes to model_functions.jl
2. **Verify generation index filtering**: All BEV variables must use `g <= y`
3. **Compare with working case**: case_20251017_105556
4. **Check .gitignore**: Ensure large files are excluded but working case is included
5. **Memory monitoring**: Use system monitor during solve to check RAM usage

---

## 📧 Context for New Claude Instance

**Background**: This is a transportation optimization model (TransComp) for analyzing vehicle electrification and charging infrastructure at NUTS-2/3 geographic resolution.

**Recent work**: Fixed critical generation index bugs that prevented BEV constraints from working. Model now successfully optimizes with mandatory breaks, state-of-charge tracking, and travel time constraints.

**Next steps**:
- Run comparison notebook to validate Tkm preservation between NUTS-2 and NUTS-3
- Analyze optimal charging infrastructure deployment
- Generate visualizations for research paper

---

**Good luck with the new machine! This working configuration has been thoroughly tested.**
