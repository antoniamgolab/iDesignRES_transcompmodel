# Mathematical equation

In the following, the mathematical description of the optimization model is explained, elaborating on all relevant functionalities.

## Nomenclature
### Table: Sets, decision variables and parameters

| Notation | Description | Unit |
|----------|-------------|------|
| $$y \in \mathcal{Y}$$ | year | |
| $$p \in \mathcal{M}$$ | product type (incl. passengers) |  |
| $$m \in \mathcal{M}$$ | mode | |
| $$r \in \mathcal{R}$$ | O-D pair | |
| $$k \in \mathcal{K}$$ | route | |
| $$v \in \mathcal{V}$$ | vehicle type | |
| $$t \in \mathcal{T}$$ | drive-train technology - fuel pair | |
| $$l \in \mathcal{L}_t$$ | fuel supply options for technology $$t$$ | |
| $$e \in \mathcal{E}$$ | location | |
| $$ic \in \mathcal{IC}$$ | income class | |
| $$b \in \mathcal{B}_{kmtg}$$ | subset for each route $$k$$ and technology $$t$$ for year $$y$$ | |
| $$g \in \mathcal{G}$$ | generation of vehicle fleet | |
| $$\mathcal{V}_k$$ | $$(e_1, e_2, e_3, \dots, e_I)$$ | |
| $$\mathcal{U}_k$$ | $$\{(i, e_i) \mid e_i \in \mathcal{V}_k, 1 \leq i \leq I \}$$ | |
| $$\mathcal{Y}_y$$ | $$\{0, \dots, y\}$$ | |
| $$\mathcal{E}_{kmtgb}$$ | subset of edges within the driving range of technology $$t$$ in year $$y$$ along route $$k$$ | |

#### Decision variables

| Notation | Description | Unit |
|----------|-------------|------|
| $$f_{yprkmvtg}$$ | transport volumes using tech $$t$$ on mode $$m$$, route $$k$$ in year $$y$$ | T |
| $$h_{yprmtg}$$ | vehicle fleet for mode $$m$$ with technology $$t$$ | # |
| $$h^{+}_{yprmtg}$$ | vehicle fleet growth for mode $$m$$ with technology $$t$$ | # |
| $$h^{-}_{yprmtg}$$ | vehicle fleet reduction for mode $$m$$ with technology $$t$$ | # |
| $$h^{exist}_{yprmtg}$$ | vehicle fleet existing at start of year $$y$$ | # |
| $$s_{ypkmvtle}$$ | fueling demand during peak hour at edge $$e$$ for tech $$t$$ via supply option $$l$$, route $$k$$ in year $$y$$ | kWh |
| $$s_{ypkmtln}$$ | fueling demand during peak hour at node $$n$$ for tech $$t$$ via supply option $$l$$, route $$k$$ in year $$y$$ | kWh |
| $$q^{+, mode\_infr}_{yet}$$ | installed mode infrastructure for tech $$t$$ on edge $$e$$ in year $$y$$ | kW |
| $$q^{+, fuel\_infr}_{yet}$$ | installed fueling infrastructure for tech $$t$$ on edge $$e$$ in year $$y$$ | kW |
| $$q^{+, supply\_infr}_{yle}$$ | capacity of supply infrastructure $$l$$ on edge $$e$$ in year $$y$$ | kW |

#### Parameters

| Notation | Description | Unit |
|----------|-------------|------|
| $$LoS_{yktv}$$ | level of service | h |
| $$F_{yrp}$$ | transport demand between O-D pair $$r$$ for product $$p$$ in year $$y$$ | T |
| $$D^{spec}_{yvtg}$$ | specific energy consumption of tech $$t$$ in year $$y$$ | kWh/km |
| $$W_{yvtg}$$ | average load of a vehicle of tech $$t$$ bought in year $$g$$ | T |
| $$L^a_{gmvt}$$ | max annual mileage of vehicle | km |
| $$L_k$$ | length of path $$k$$ | km |


### Objective function

```math
\min_{x} Z
```

```math
{C}^{infrastructure, total} = \sum_{t} \sum_{y} \left( \sum_{e} C^{fuel\_infr}_{yte} q^{+, fuel\_infr}_{yte} + \sum_{y' \in \mathcal{Y}^y} C_{yte}^{fuel\_infr, OM, fix}\left( Q^{fuel\_infr}_{te} + q^{+, fuel\_infr}_{y'te}\right) \right) \\ + \sum_{m} \sum_{y} \left( \sum_{e} C^{mode\_infr}_{yme} q^{+, mode\_infr}_{yme} + \sum_{y' \in \mathcal{Y}^y} C_{yme}^{mode\_infr, OM, fix}\left( Q^{fuel\_infr}_{me} + q^{+, fuel\_infr}_{y'me}\right) \right) \\ + \sum_{l} \sum_{y} \left( \sum_{e} C^{supply\_infr}_{yle} q^{+, supply\_infr}_{yle} + \sum_{y' \in \mathcal{Y}^y} C_{yle}^{supply\_infr, OM, fix, supply}\left( Q^{supply\_infr}_{te} + q^{+, supply\_infr}_{y'te}\right) \right) \\ 
````