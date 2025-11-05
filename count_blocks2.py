import re

with open("src/model_functions.jl", "r", encoding="utf-8", errors='ignore') as f:
    lines = f.readlines()

# Find the objective function
func_start = None
for i, line in enumerate(lines):
    if re.match(r"^function objective", line):
        func_start = i
        break

if func_start is None:
    print("Could not find objective function")
    exit(1)

print(f"Function starts at line {func_start + 1}")

# Track balance from function start
balance = 0
max_line = min(func_start + 750, len(lines))

for i in range(func_start, max_line):
    line = lines[i]

    # Skip commented lines
    if re.match(r"^\s*#", line):
        continue

    # Count keywords - be more careful
    # Only count if not in a string or comment
    opens = len(re.findall(r'\b(for|while|if|function|begin)\b', line))
    closes = len(re.findall(r'\bend\b', line))

    old_balance = balance
    balance += opens - closes

    # Print lines where balance changes significantly or near problem area
    if abs(opens - closes) > 0 and (i >= func_start + 460 and i <= func_start + 530):
        try:
            print(f"Line {i+1:4d}: balance {old_balance:2d} -> {balance:2d} (open={opens}, close={closes})")
        except:
            print(f"Line {i+1:4d}: balance {old_balance:2d} -> {balance:2d} (open={opens}, close={closes}) [encoding error]")

print(f"\nFinal balance: {balance}")
print("Expected: 1 (for the function)")
if balance > 1:
    print(f"Missing {balance - 1} 'end' statement(s)")
