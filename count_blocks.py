import re

with open("src/model_functions.jl", "r", encoding="utf-8") as f:
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

# Track balance from function start to end
balance = 0
max_line = min(func_start + 750, len(lines))

for i in range(func_start, max_line):
    line = lines[i]

    # Count openers (for, while, if, function, begin)
    # Ignore commented lines
    if not re.match(r"^\s*#", line):
        # Count keywords
        opens = len(re.findall(r'\b(for|while|if|function|begin)\b', line))
        # Count ends
        closes = len(re.findall(r'\bend\b', line))

        balance += opens - closes

        # Print around the problem area
        if i >= func_start + 670 and i <= func_start + 740:
            print(f"Line {i+1:4d} (balance={balance:3d}): {line.rstrip()}")

print(f"\nFinal balance at line {max_line}: {balance}")
print("Expected balance: 1 (for the function itself)")
if balance > 1:
    print(f"Missing {balance - 1} 'end' statement(s)")
elif balance < 1:
    print(f"Extra {1 - balance} 'end' statement(s)")
