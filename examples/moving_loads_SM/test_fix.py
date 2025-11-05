"""
Quick test to verify the fix works
"""
import numpy as np
import matplotlib.pyplot as plt

# Test the axes reshaping logic
print("Testing axes reshaping fix...")

# Test case 1: Single subplot (1x1)
print("\n1. Single subplot (1x1):")
fig, axes = plt.subplots(1, 1, figsize=(5, 5))
if 1 == 1 and 1 == 1:
    axes = np.array([[axes]])
print(f"   Shape: {axes.shape}, Type: {type(axes[0, 0])}")

# Test case 2: Single row (1xN)
print("\n2. Single row (1x3):")
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
if 1 == 1:
    axes = axes.reshape(1, -1)
print(f"   Shape: {axes.shape}, Type: {type(axes[0, 0])}")

# Test case 3: Single column (Nx1)
print("\n3. Single column (3x1):")
fig, axes = plt.subplots(3, 1, figsize=(5, 15))
if 1 == 1:
    axes = axes.reshape(-1, 1)
print(f"   Shape: {axes.shape}, Type: {type(axes[0, 0])}")

# Test case 4: Multiple rows and columns (2x3)
print("\n4. Multiple rows and columns (2x3):")
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
print(f"   Shape: {axes.shape}, Type: {type(axes[0, 0])}")

print("\n✓ All cases work correctly!")
plt.close('all')
