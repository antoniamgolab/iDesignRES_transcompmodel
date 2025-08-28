# Mathematical Model

## Overview

This document presents the complete mathematical formulation of the TransComp optimization model. The model is designed as a linear programming problem that minimizes the total cost of providing transportation services while satisfying various technical, operational, and policy constraints.

The optimization framework considers multiple dimensions:
- **Temporal**: Multi-year planning horizon with dynamic fleet evolution
- **Spatial**: Origin-destination pairs connected by multiple routes
- **Modal**: Different transportation modes (road, rail, etc.)
- **Technological**: Various vehicle technologies and fuel types
- **Economic**: Investment costs, operational costs, and budget constraints

## Mathematical Formulation

## Nomenclature

### Sets, Decision Variables and Parameters

The following tables define the mathematical notation used throughout the model formulation.

#### Sets

| **Notation** | **Description** | **Unit** |
|:-------------|:----------------|:---------|
| $$y \in \mathcal{Y}$$ | Planning years | - |
| $$p \in \mathcal{P}$$ | Product types (including passengers) | - |
| $$m \in \mathcal{M}$$ | Transportation modes | - |
| $$r \in \mathcal{R}$$ | Origin-destination pairs | - |
| $$k \in \mathcal{K}$$ | Routes between origin-destination pairs | - |
| $$v \in \mathcal{V}$$ | Vehicle types | - |
| $$t \in \mathcal{T}$$ | Drive-train technology and fuel combinations | - |
| $$l \in \mathcal{L}_t$$ | Fuel supply options for technology $$t$$ | - |
| $$e \in \mathcal{E}$$ | Geographic locations/edges | - |
| $$ic \in \mathcal{IC}$$ | Income classes | - |
| $$g \in \mathcal{G}$$ | Vehicle fleet generations | - |
| $$\mathcal{V}_k$$ | Sequence of edges for route $$k$$: $$(e_1, e_2, e_3, \ldots, e_I)$$ | - |
| $$\mathcal{U}_k$$ | Set of indexed edges: $$\{(i, e_i) \mid e_i \in \mathcal{V}_k, 1 \leq i \leq I \}$$ | - |
| $$\mathcal{Y}_y$$ | Years up to year $$y$$: $$\{0, \ldots, y\}$$ | - |
| $$\mathcal{E}_{kmtg}$$ | Edges within driving range of technology $$t$$ for route $$k$$ | - |

#### Decision Variables

| **Notation** | **Description** | **Unit** |
|:-------------|:----------------|:---------|
| $$f_{yprkmvtg}$$ | Transport volumes using technology $$t$$ on mode $$m$$, route $$k$$ in year $$y$$ | T |
| $$h_{yprmtg}$$ | Vehicle fleet size for mode $$m$$ with technology $$t$$ and generation $$g$$ | vehicles |
| $$h^{+}_{yprmtg}$$ | Vehicle fleet additions (investments) for mode $$m$$ with technology $$t$$ | vehicles |
| $$h^{-}_{yprmtg}$$ | Vehicle fleet reductions (retirements) for mode $$m$$ with technology $$t$$ | vehicles |
| $$h^{exist}_{yprmtg}$$ | Existing vehicle fleet at start of year $$y$$ | vehicles |
| $$s_{ypkmvtle}$$ | Fueling demand during peak hour at edge $$e$$ for technology $$t$$ | kWh |
| $$s_{ypkmtln}$$ | Fueling demand during peak hour at node $$n$$ for technology $$t$$ | kWh |
| $$q^{+, mode\_infr}_{yme}$$ | Installed mode infrastructure capacity for mode $$m$$ on edge $$e$$ in year $$y$$ | kW |
| $$q^{+, fuel\_infr}_{yte}$$ | Installed fueling infrastructure capacity for technology $$t$$ on edge $$e$$ in year $$y$$ | kW |
| $$q^{+, supply\_infr}_{yle}$$ | Installed supply infrastructure capacity for supply option $$l$$ on edge $$e$$ in year $$y$$ | kW |

#### Parameters

| **Notation** | **Description** | **Unit** |
|:-------------|:----------------|:---------|
| $$LoS_{yktv}$$ | Level of service (travel time) for route $$k$$ and technology $$t$$ | h |
| $$F_{yrp}$$ | Transport demand between O-D pair $$r$$ for product $$p$$ in year $$y$$ | T |
| $$D^{spec}_{yvtg}$$ | Specific energy consumption of technology $$t$$ and generation $$g$$ | kWh/km |
| $$W_{yvtg}$$ | Average payload capacity of vehicle with technology $$t$$ and generation $$g$$ | T |
| $$L^a_{gmvt}$$ | Maximum annual mileage of vehicle | km |
| $$L_k$$ | Length of route $$k$$ | km |
| $$C^{CAPEX}_{yvtg}$$ | Capital expenditure for vehicle technology $$t$$ and generation $$g$$ | € |
| $$C^{fuel\_infr}_{yte}$$ | Investment cost for fueling infrastructure | € |
| $$C^{mode\_infr}_{yme}$$ | Investment cost for mode infrastructure | € |
| $$VoT_{ykvt,ic}$$ | Value of time for income class $$ic$$ | €/h |


## Objective Function

The model minimizes the total system cost, which includes infrastructure investments, vehicle costs, operational expenses, and penalty costs:

```math
\min_{x} Z = C^{infrastructure} + C^{vehicle} + C^{transport} + C^{intangible} + C^{penalty}
```

Where each cost component is defined as follows:

### Infrastructure Costs
Total costs for fueling, mode, and supply infrastructure investments and operations:

```math
C^{infrastructure} = \sum_{t} \sum_{y} \left( \sum_{e} C^{fuel\_infr}_{yte} q^{+, fuel\_infr}_{yte} + \sum_{y' \in \mathcal{Y}^y} C_{yte}^{fuel\_infr, OM, fix}\left( Q^{fuel\_infr}_{te} + q^{+, fuel\_infr}_{y'te}\right) \right) \\ + \sum_{m} \sum_{y} \left( \sum_{e} C^{mode\_infr}_{yme} q^{+, mode\_infr}_{yme} + \sum_{y' \in \mathcal{Y}^y} C_{yme}^{mode\_infr, OM, fix}\left( Q^{mode\_infr}_{me} + q^{+, mode\_infr}_{y'me}\right) \right) \\ + \sum_{l} \sum_{y} \left( \sum_{e} C^{supply\_infr}_{yle} q^{+, supply\_infr}_{yle} + \sum_{y' \in \mathcal{Y}^y} C_{yle}^{supply\_infr, OM, fix}\left( Q^{supply\_infr}_{le} + q^{+, supply\_infr}_{y'le}\right) \right)
```

### Vehicle Costs
Capital and operational costs for vehicle fleets, including fuel costs:

```math
C^{vehicle} = \sum_y \sum_m \sum_v \sum_t \sum_g \left( C^{CAPEX}_{yvtg} h^{+}_{yprvtg} + C^{OM, fix}_{yvtg} h_{yprvtg} + \sum_l \sum_{e \in E^k} C^{fuel}_{yle} s_{ypkmvtle} \right)
```

### Transport Activity Costs
Distance-based operational costs:

```math
C^{transport} = \sum_y \left( C^{OM, fix, dist}_{mvt} f_{yprkmvtg} + \sum_k C^{OM, var, dist}_{mvt} L_k f_{yprkmvtg} \right)
```

### Intangible Costs
User costs related to travel time and service quality:

```math
C^{intangible} = \sum_y \sum_m \sum_r \sum_{kvt} VoT_{ykvt, ic} \cdot LoS^{f}_{ykvt} \cdot f_{yprkmvtg}
```

Where the level of service includes:
```math
LoS^f_{yk} = \frac{L_k}{Speed_{yvmt}} + FuelingTime_{ykvmt} + WaitingTime_{ykm}
```

### Penalty Costs
Costs for violating budget or other soft constraints:

```math
C^{penalty} = \sum_y \sum_p \sum_r penalty^{budget}_{pry}
```

## Constraints

The optimization model includes several categories of constraints that ensure feasible and realistic solutions:

### Demand Coverage Constraint
Ensures that all transport demand is satisfied:

```math
\sum_{kmvtg} f_{yprkmvtg} = F_{yrp} \quad \forall y \in \mathcal{Y}, r \in \mathcal{R}, p \in \mathcal{P}
```

This fundamental constraint guarantees that the total transport flow across all modes, routes, vehicles, technologies, and generations equals the exogenous demand for each origin-destination pair and product type.

### Vehicle Stock Evolution Constraints
These constraints model the dynamic evolution of vehicle fleets over time, accounting for existing stock, new investments, and retirements.

#### Fleet Balance Equation
```math
h_{yprmvtg} = h^{exist}_{yprmvt(g-1)} + h^{+}_{yprmvtg} - h^{-}_{yprmvtg} \quad \forall y \in \mathcal{Y}\setminus \{y_0\}, r, p, m, v, t, g
```

#### Initial Fleet Definition
```math
h^{exist}_{yprmvt(g-1)} = h_{(y-1)prmvtg} \quad \forall y = y_0, r, p, m, v, t, g
```

These constraints ensure continuity in fleet evolution, where the fleet size in each year equals the previous year's fleet plus new additions minus retirements.

### Fueling Demand Constraints
These constraints link transport activity to energy demand and ensure adequate fueling infrastructure.

#### Energy Demand Calculation
```math
\sum_{l \in \mathcal{L}_t} \sum_{e \in \mathcal{E}_{k}} s_{ypkmvtle} = \sum_{g \in \mathcal{G}} \sum_{a \in \mathcal{A}^p} \sum_{e \in \mathcal{E}_{k}} \sum_{n \in \mathcal{N}_{k}} \gamma \frac{D^{spec}_{yt} L_{ke}}{W_{ymvt}} f_{ypakmvtg} \quad \forall y, p, k, m, t
```

This constraint calculates the fueling demand based on transport volumes, specific energy consumption, and route characteristics.

#### Vehicle Range Constraint
```math
\sum_{l \in \mathcal{L}_t} \sum_{e \in \mathcal{U}_{ke}} s_{ypkmvtle} \leq \gamma \sum_{g \in \mathcal{G}} \frac{1}{W_{gmvt}} f_{ypkmvtg} \cdot Q^{tank}_{gmvt} \quad \forall y, p, k, m, t
```

This ensures that vehicles do not exceed their fuel tank capacity and range limitations.

### Technology Shift Constraints
These constraints limit the speed of technological transitions to reflect realistic market dynamics and policy constraints.

#### Vehicle Stock Technology Shift
```math
\pm \left( \sum_g h_{yprmvt} - \sum_g h_{(y-1)prmvt} \right) \leq \alpha \sum_{gvt} h_{yprmvt} + \beta \sum_g h_{(y-1)prmvtg} \quad \forall y \in \mathcal{Y}\setminus \{y_0\}, r, m, v, t
```

For the initial year:
```math
\pm \left( \sum_g h_{yprmvtg} - \sum_g h^{exist}_{yprmvtg} \right) \leq \alpha \sum_{gvt} h_{yprmvt} + \beta \sum_g h^{exist}_{yprmvtg} \quad \forall y \in \{y_0\}, r, m, v, t
```

These constraints prevent unrealistic rapid shifts in vehicle technology adoption by limiting year-over-year changes.

### Mode Shift Constraints
Similar to technology shift, these constraints limit the speed of modal transitions.

#### Transport Volume Mode Shift
```math
\left( \sum_{kg} f_{yprkmvtg} - \sum_{kg} f_{(y-1)prkmvtg} \right) \leq \alpha F_{yrp} + \sum_{kg} f_{(y-1)prkmvtg} \quad \forall y \in \mathcal{Y}\setminus \{y_0\}, r, m
```

This constraint ensures that mode share changes occur gradually, reflecting user behavior and infrastructure limitations.

### Infrastructure Expansion Constraints
These constraints ensure adequate infrastructure capacity to support transport activity.

#### Mode Infrastructure Capacity
```math
Q^{mode\_infr}_{me} + \sum_{y \in \mathcal{Y}_y} q^{+, mode\_infr}_{yme} \geq \gamma \sum_{e \in \mathcal{K}_e} \sum_{p \in \mathcal{P}} \sum_{t \in T_{m}} f_{ypkmtg} \quad \forall y, m, e
```

#### Fueling Infrastructure Capacity
```math
Q^{fuel\_infr}_{te} + \sum_{y \in \mathcal{Y}_y} q^{+, fuel\_infr}_{yte} \geq \sum_{k \in \mathcal{K}_e} \sum_{p \in \mathcal{P}} \sum_{m \in \mathcal{M}} \sum_{l \in \mathcal{L}_t} s_{ypkmtle} \quad \forall y, t, e
```

#### Supply Infrastructure Capacity
```math
Q^{supply\_infr}_{le} + \sum_{y \in \mathcal{Y}_y} q^{+, supply\_infr}_{yle} \geq \sum_{e \in \mathcal{K}_e} \sum_{p \in \mathcal{P}} \sum_{m \in M} \sum_{t \in \mathcal{T}_l} s_{ypkmtle} \quad \forall y, l, e
```

These constraints ensure that infrastructure capacity (existing plus new investments) meets the demand generated by transport activities.

### Monetary Budget Constraints
These constraints model financial limitations on investments, either as hard constraints or with penalty functions.

#### Total Budget Constraint (with penalties)
```math
\sum_y C^{CAPEX}_{yvtg} \cdot h^{+}_{yr} \leq Budget_{ic} \cdot f \cdot |Y| + penalty^{+, budget}
```

```math
\sum_y C^{CAPEX}_{yvtg} \cdot h^{+}_{yr} \geq Budget_{ic} \cdot f \cdot |Y| - penalty^{-, budget}
```

#### Periodic Budget Constraints
```math
\sum_{y'\in Y_i} C^{CAPEX}_{y'vtg} \cdot h^{+}_{y'r} \leq Budget_{ic} \cdot f \cdot \tau^i + penalty^{+, budget}
```

```math
\sum_{y'\in Y_i} C^{CAPEX}_{y'vtg} \cdot h^{+}_{y'r} \geq Budget_{ic} \cdot f \cdot \tau^i - penalty^{-, budget}
```

These constraints can enforce budget limits either as hard constraints (when penalties are prohibitively expensive) or as soft constraints (allowing violations with associated costs), enabling flexible policy modeling.

