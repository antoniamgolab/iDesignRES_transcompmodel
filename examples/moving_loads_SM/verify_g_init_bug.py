"""
Verify the g_init calculation bug.

If pre_y = 8, then:
- g_init = y_init - pre_y = 2020 - 8 = 2012
- But it should be g_init = 2020

This causes wrong array indexing in the constraint.
"""

import yaml

base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"
case_name = "case_20251110_160646_reverse"
input_dir = f"{base_path}/input_data/{case_name}"

print(f"\n{'='*100}")
print(f"VERIFYING g_init CALCULATION BUG")
print(f"{'='*100}\n")

# Load Model parameters
with open(f"{input_dir}/Model.yaml", 'r', encoding='utf-8') as f:
    model_data = yaml.safe_load(f)

y_init = model_data["y_init"]
pre_y = model_data["pre_y"]
Y = model_data["Y"]
time_step = model_data.get("time_step", 4)

Y_end = y_init + Y - 1

print(f"Model parameters:")
print(f"  y_init:    {y_init}")
print(f"  pre_y:     {pre_y}")
print(f"  Y:         {Y}")
print(f"  time_step: {time_step}")
print(f"  Y_end:     {Y_end}\n")

# Calculate g_init as the code does it
g_init_wrong = y_init - pre_y
g_init_correct = y_init

print(f"g_init calculation:")
print(f"  Code calculates:  g_init = y_init - pre_y = {y_init} - {pre_y} = {g_init_wrong}")
print(f"  Should be:        g_init = y_init = {y_init}\n")

# Generate modeled_generations with both methods
modeled_generations_wrong = list(range(g_init_wrong, Y_end + 1, time_step))
modeled_generations_correct = list(range(g_init_correct, Y_end + 1, time_step))

print(f"modeled_generations (WRONG calculation):")
print(f"  {modeled_generations_wrong}\n")
print(f"modeled_generations (CORRECT calculation):")
print(f"  {modeled_generations_correct}\n")

# Load TechVehicle to show indexing impact
with open(f"{input_dir}/TechVehicle.yaml", 'r', encoding='utf-8') as f:
    techvehicles = yaml.safe_load(f)

bev = next(tv for tv in techvehicles if tv['id'] == 1)

print(f"{'='*100}")
print(f"IMPACT ON ARRAY INDEXING")
print(f"{'='*100}\n")

# Check a few generations
test_generations = [2020, 2032, 2040, 2052, 2056]

print(f"When constraint loops 'for g in modeled_generations' and uses W[g-g_init+1]:\n")
print(f"{'Generation':<12} {'Wrong Index':<15} {'Wrong W':<12} {'Correct Index':<15} {'Correct W':<12} {'Match?':<10}")
print("-" * 85)

for gen in test_generations:
    if gen in modeled_generations_wrong:
        # Wrong calculation
        idx_wrong_julia = gen - g_init_wrong + 1  # Julia 1-indexed
        idx_wrong_python = idx_wrong_julia - 1    # Python 0-indexed

        # Correct calculation
        idx_correct_julia = gen - g_init_correct + 1
        idx_correct_python = idx_correct_julia - 1

        # Get values if indices are valid
        W_wrong = bev['W'][idx_wrong_python] if 0 <= idx_wrong_python < len(bev['W']) else "OUT OF RANGE"
        W_correct = bev['W'][idx_correct_python] if 0 <= idx_correct_python < len(bev['W']) else "OUT OF RANGE"

        match = "YES" if W_wrong == W_correct else "NO"

        print(f"{gen:<12} {idx_wrong_python:<15} {str(W_wrong):<12} {idx_correct_python:<15} {str(W_correct):<12} {match:<10}")

# Now check which generation would give us index 44
print(f"\n{'='*100}")
print(f"FINDING WHICH GENERATION GIVES INDEX 44 (Python 0-indexed)")
print(f"{'='*100}\n")

target_idx_python = 44
target_idx_julia = target_idx_python + 1  # = 45

# Solve: g - g_init + 1 = 45
# g = 45 + g_init - 1 = 44 + g_init
gen_for_idx_44 = target_idx_python + g_init_wrong

print(f"Using WRONG g_init = {g_init_wrong}:")
print(f"  To get index 44 (Python) = 45 (Julia):")
print(f"  Need generation g where: g - {g_init_wrong} + 1 = 45")
print(f"  Solving: g = 44 + {g_init_wrong} = {gen_for_idx_44}")
print(f"  Is {gen_for_idx_44} in modeled_generations? {gen_for_idx_44 in modeled_generations_wrong}\n")

# Check what the model would output for generation 2052
print(f"For the ACTUAL generation 2052 that we're checking:")
idx_used_julia = 2052 - g_init_wrong + 1
idx_used_python = idx_used_julia - 1
print(f"  Model uses: W[{2052} - {g_init_wrong} + 1] = W[{idx_used_julia}] (Julia) = W[{idx_used_python}] (Python)")
print(f"  W[{idx_used_python}] = {bev['W'][idx_used_python]:.4f} tonnes\n")

idx_should_julia = 2052 - g_init_correct + 1
idx_should_python = idx_should_julia - 1
print(f"  Should use: W[{2052} - {g_init_correct} + 1] = W[{idx_should_julia}] (Julia) = W[{idx_should_python}] (Python)")
print(f"  W[{idx_should_python}] = {bev['W'][idx_should_python]:.4f} tonnes\n")

ratio = bev['W'][idx_should_python] / bev['W'][idx_used_python]
print(f"  Ratio W[{idx_should_python}] / W[{idx_used_python}] = {ratio:.8f}")
print(f"  This matches the observed ratio of 0.80645154? {abs(ratio - 0.80645154) < 0.0001}")

print(f"\n{'='*100}\n")
