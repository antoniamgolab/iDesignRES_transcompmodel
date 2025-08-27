# Mathematical model
@anchor(math_formulation)

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


## Objective function

```math
\min_{x} Z
```

```math
{C}^{infrastructure, total} = \sum_{t} \sum_{y} \left( \sum_{e} C^{fuel\_infr}_{yte} q^{+, fuel\_infr}_{yte} + \sum_{y' \in \mathcal{Y}^y} C_{yte}^{fuel\_infr, OM, fix}\left( Q^{fuel\_infr}_{te} + q^{+, fuel\_infr}_{y'te}\right) \right) \\ + \sum_{m} \sum_{y} \left( \sum_{e} C^{mode\_infr}_{yme} q^{+, mode\_infr}_{yme} + \sum_{y' \in \mathcal{Y}^y} C_{yme}^{mode\_infr, OM, fix}\left( Q^{fuel\_infr}_{me} + q^{+, fuel\_infr}_{y'me}\right) \right) \\ + \sum_{l} \sum_{y} \left( \sum_{e} C^{supply\_infr}_{yle} q^{+, supply\_infr}_{yle} + \sum_{y' \in \mathcal{Y}^y} C_{yle}^{supply\_infr, OM, fix, supply}\left( Q^{supply\_infr}_{te} + q^{+, supply\_infr}_{y'te}\right) \right) \\ 
```

```math
{C}^{vehiclestock, total} = \sum_y \sum_m \sum_v \sum_t \sum_g \left( C^{CAPEX}_{yvtg} h^{+}_{yprvtg} + C^{h, OM, fix}_{yvtg} h_{yprvtg} + \sum_l \sum_{e \in E^k} C^{fuelcosts}_{yle}* s_{ypkmvtle} \right)
```

```math
{C}^{transportactivity, total} = \sum_y \left( C^{OM, fix, dist}_{mvt} f_{y,prkmvtg} + \sum_k C^{OM, var, dist}_{mvt} \sum_k L_k f_{y,prkmvtg} \right)
```

```math
{C}^{intangiblecosts, total} = \sum_y \sum_m \sum_r \sum_{kvt} VoT_{ykvt, ic} * LoS^{f}_{ykvt} * f_{yprkmvtg} 
```

```math
LoS^f_{yk} = \frac{L_k}{Speed_yvmt} + Fueling\_time_{ykvmt} + Waiting\_time_{ykm}
```

```math
{C}^{paneltycosts, total} = \sum_y \sum_p \sum_r penalty^{budget}_{pry} 
```

```math
\sum_{kmvtg} f_{yprkmvtg} = F_{yrp} \quad :  \forall y \in \mathcal{Y},  r \in \mathcal{R}, p \in \mathcal{P}

```

## Constraints
### Vehicle stock modelling
```math
h_{yprmvtg} = h^{exist}_{yprmvt(g-1)} + h^{+}_{yprmvtg} - h^{-}_{yprmvtg} : \forall y \in \mathcal{Y}\setminus \{y_0\}, r \in \mathcal{R}, p \in \mathcal{P}, m \in \mathcal{M}, v \in \mathcal{V}, t \in \mathcal{T}, g \in \mathcal{G}
```

```math
h^{exist}_{yprmvt(g-1)} = h_{(y-1)prmvtg} \quad : y = y_0, r \in \mathcal{R}, p \in \mathcal{P}, m \in \mathcal{M}, v \in \mathcal{V}, t \in \mathcal{T}, g \in \mathcal{G}
```

### Fueling demand
```math
\sum_{l \in \mathcal{L}_t} \sum_{e \in \mathcal{E}_{k}} s_{ypkmvtle} = \sum_{g \in \mathcal{G}} \sum_{a \in \mathcal{A}^p}  \sum_{e \in \mathcal{E}_{k}} \sum_{n \in \mathcal{N}_{k}} \gamma \frac{D^{spec}_{yt} L_{ke}}{W_{ymvt}} f_{ypakmvtg}  : \forall y \in \mathcal{Y}, p \in \mathcal{P}, k \in \mathcal{K},  m \in \mathcal{M}, t \in \mathcal{T}_m
``` 

```math
\sum_{l \in \mathcal{L}_t} \sum_{e \in \mathcal{U}_{ke}} s_{ypkmvtle} \leq \gamma \sum_{g \in \mathcal{G}} \frac{1}{W_{gmvt}} f_{ypkmvtg} * Q^{tank}_{gmvt} :\forall y, p, k, m, t
```

### Vehicle stock shift

```math
\pm \left( \sum_g h_{yprmvt} - \sum_g h_{(y-1)prmvt} \right) \leq \alpha \sum_{gvt} h_{yprmvt} + \beta \sum_g h_{(y-1)prmvtg} : \forall y \in \mathcal{Y}\setminus \{ y_0\}, r \in \mathcal{R}, m \in \mathcal{M}, v \in \mathcal{V}, t \in \mathcal{T}_m
```
```math
\pm \left( \sum_g h_{yprmvtg} - \sum_g h^{exist}_{yprmvtg} \right) \leq \alpha \sum_{gvt} h_{yprmvt} + \beta \sum_g h^{exist}_{yprmvtg} : \forall y \in \{y_0\}, r \in \mathcal{R}, m \in \mathcal{M}, v \in \mathcal{V}, t \in \mathcal{T}_m
```

### Mode shift

```math
\left( \sum_{kg} f_{yprkmvtg} - \sum_{kg}  f_{(y-1)prkmvtg} \right) \leq \alpha F_{yrp} + sum_{kg} f_{(y-1)prkmvtg } : \forall y \in \mathcal{Y}\setminus \{ y_0\}, r \in \mathcal{R}, m \in \mathcal{M}
```
```math
\left( \sum_g h_{yprmvtg} - \sum_g h^{exist}_{yprmvtg} \right) \leq \alpha \sum_{gvt} h_{yprmvt} + \beta \sum_g h^{exist}_{yprmvtg} : \forall y \in \{y_0\}, r \in \mathcal{R}, m \in \mathcal{M}, v \in \mathcal{V}, t \in \mathcal{T}_m
```
### Mode infrastructure expansion

```math
Q^{mode\_infr}_{me}  +  \sum_{y \in \mathcal{Y}_y} q^{+, mode\_infr}_{yme} \geq  \gamma \sum_{e \in \mathcal{K}_e} \sum_{p \in \mathcal{P}} \sum_{t \in T_{m}} f_{ypkmtg} : \forall y \in \mathcal{Y}, m \in \mathcal{M}, e \in \mathcal{E}
```

### Fueling Infrastructure expansion
```math
Q^{fuel\_infr}_{te} + \sum_{y \in \mathcal{Y}_y} q^{+, fuel\_infr}_{yte} \geq \sum_{k \in \mathcal{K}_e} \sum_{p \in \mathcal{P}} \sum_{m \in \mathcal{M}} \sum_{l \in \mathcal{L}_t} s_{ypkmtle} : \forall y \in \mathcal{Y}, t \in \mathcal{T}, e \in \mathcal{E}
```

```math
 Q^{supply\_infr}_{le}  +  \sum_{y \in \mathcal{Y}_y} q^{+, supply\_infr}_{yle} \geq \sum_{e \in \mathcal{K}_e} \sum_{p \in \mathcal{P}} \sum_{m \in M} \sum_{t \in \mathcal{T}_l} s_{ypkmtle} : \forall y \in \mathcal{Y}, l \in \mathcal{L}, e \in \mathcal{E}
```

### Monetary budget
```math
\sum_y C^{CAPEX}_{yvtg} * h^{+}_{yr} \leq Budget_{ic} * f * |Y| + penalty^{+, invbudget}
```

```math
\sum_y C^{CAPEX}_{yvtg} * h^{+}_{yr} \geq Budget_{ic} * f * |Y|- penalty^{-, invbudget}
```

```math
\sum_{y'\in Y_i} C^{CAPEX}_{y'vtg} * h^{+}_{y'r} \leq Budget_{ic} * f * \tau^i + penalty^{+, invbudget} 
```

```math
\sum_{y'\in Y_i} C^{CAPEX}_{y'vtg} * h^{+}_{y'r} \geq Budget_{ic} * f *  \tau^i - penalty^{+, invbudget}
```
