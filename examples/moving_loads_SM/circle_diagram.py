import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Create figure and axis
fig, ax = plt.subplots(figsize=(6, 6))

# Circle parameters
radius = 1.0
center = (0, 0)

# Create upper half (semicircle) - one color
upper_half = patches.Wedge(center, radius, 0, 180, facecolor='#b8e0d2', edgecolor='none', alpha=0.9)
ax.add_patch(upper_half)

# Create lower half (semicircle) - different color
lower_half = patches.Wedge(center, radius, 180, 360, facecolor='#b8b8ff', edgecolor='none', alpha=0.9)
ax.add_patch(lower_half)

# Add dashed circle outline
circle_outline = patches.Circle(center, radius, fill=False, edgecolor='gray',
                                 linestyle='--', linewidth=2)
ax.add_patch(circle_outline)

# Draw axes through origin
ax.axhline(y=0, color='gray', linewidth=1.5)
ax.axvline(x=0, color='gray', linewidth=1.5)

# Set symmetric axis limits (longer axes)
limit = 2.0
ax.set_xlim(-limit, limit)
ax.set_ylim(-limit, limit)

# Remove ticks and labels
ax.set_xticks([])
ax.set_yticks([])

# Remove spines (the box around the plot)
for spine in ax.spines.values():
    spine.set_visible(False)

# Equal aspect ratio
ax.set_aspect('equal')

# Save as SVG
plt.savefig('circle_diagram.svg', format='svg', bbox_inches='tight', transparent=True)
print("Saved: circle_diagram.svg")

# plt.show()
