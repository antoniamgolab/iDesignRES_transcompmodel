# Country Border Lines Implementation

## Summary

Added dashed horizontal lines to latitude visualizations to indicate country southern borders, helping to visualize where each country's NUTS2 regions begin.

## Files Created

### 1. `country_southern_borders.csv`
Contains the minimum (southern) latitude for each country's NUTS2 regions:

| Country | Southern Border | Region | Latitude Range |
|---------|----------------|--------|----------------|
| IT | 38.90°N | ITF6 | 38.90 - 46.66°N |
| AT | 47.18°N | AT33 | 47.18 - 48.13°N |
| DE | 47.99°N | DE13 | 47.99 - 54.13°N |
| DK | 55.35°N | DK03 | 55.35 - 57.21°N |
| SE | 56.09°N | SE22 | 56.09 - 59.50°N |
| NO | 59.07°N | NO09 | 59.07 - 61.26°N |

### 2. `calculate_country_borders.py`
Python script that:
- Reads GeographicElement.yaml
- Extracts NUTS2 regions by country
- Calculates the minimum (southern) latitude for each country
- Exports to country_southern_borders.csv

### 3. `country_centroids.csv` (Updated)
Previously used entire country centroids from NUTS shapefile, which placed Norway at 68.69°N (far outside plot range).

Now uses centroids calculated from actual NUTS2 regions in dataset:
- NO: 60.27°N (was 68.69°N)
- SE: 57.94°N (was 62.76°N)

This ensures country labels appear within the plot range.

## Notebook Changes

Updated three cells in `modal_shift.ipynb`:
1. **Cell 10**: Modal Split by Latitude visualization
2. **Cell 11**: Total TKM by Latitude visualization
3. **Cell 12**: Stacked Area by Latitude visualization

### Added Code

In each cell, two code blocks were added:

**1. Load border data:**
```python
# Load country southern borders for dashed lines
borders_df = pd.read_csv('country_southern_borders.csv')
```

**2. Plot border lines:**
```python
# Add dashed lines for country southern borders
corridor_countries = ['IT', 'AT', 'DE', 'DK', 'SE', 'NO']
if isinstance(axes, np.ndarray):
    ax_list = axes.flatten()
else:
    ax_list = [axes]

for ax in ax_list:
    ylim = ax.get_ylim()

    for _, row in borders_df.iterrows():
        country = row['CNTR_CODE']
        border_lat = row['southern_border_lat']

        if country in corridor_countries and ylim[0] <= border_lat <= ylim[1]:
            ax.axhline(y=border_lat, color='gray', linestyle='--',
                      linewidth=0.8, alpha=0.5, zorder=1)
```

## Visual Result

The plots now show:
- **Country code labels** at centroid latitudes (on the right Y-axis)
- **Gray dashed lines** at southern border latitudes
- This helps visualize which NUTS2 regions belong to which country

Example border positions:
- Southern Italy starts at ~39°N
- Austria starts at ~47°N
- Germany starts at ~48°N
- Denmark starts at ~55°N
- Sweden starts at ~56°N
- Norway starts at ~59°N

## How to Use

1. Run `calculate_country_borders.py` to regenerate borders if needed
2. The borders CSV is automatically loaded by the three visualization cells
3. Dashed lines appear automatically when running the cells
4. Lines only appear if they fall within the plot's Y-axis range

## Notes

- Border lines use `zorder=1` to appear behind data but above background
- Alpha=0.5 for subtle appearance
- Only corridor countries (IT, AT, DE, DK, SE, NO) are shown
- The southern borders represent the southernmost NUTS2 region in each country
