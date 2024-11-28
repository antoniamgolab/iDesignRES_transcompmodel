::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: {#documenter}
::: docs-package-name
[[TransComp Documentation]()]{.docs-autofit}
:::

Search docs (Ctrl + /)

-   [Home](){.tocitem}
    -   [Getting Started](#Getting-Started){.tocitem}

:::::: {.docs-version-selector .field .has-addons}
::: control
[Version]{.docs-label .button .is-static .is-size-7}
:::

:::: {.docs-selector .control .is-expanded}
::: {.select .is-fullwidth .is-size-7}
:::
::::
::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: docs-main
:::: docs-navbar
[](#){#documenter-sidebar-button .docs-sidebar-button .docs-navbar-link
.fa-solid .fa-bars .is-hidden-desktop}

-   [Home]()

<!-- -->

-   [Home]()

::: docs-right
[[]{.docs-icon .fa-brands}[GitHub]{.docs-label
.is-hidden-touch}](https://github.com/antoniamgolab/iDesignRES_transcompmodel "View the repository on GitHub"){.docs-navbar-link}[[]{.docs-icon
.fa-solid}](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/main/docs/src/index.md "Edit source on GitHub"){.docs-navbar-link}[](# "Settings"){#documenter-settings-button
.docs-settings-button .docs-navbar-link .fa-solid
.fa-gear}[](javascript:; "Collapse all docstrings"){#documenter-article-toggle-button
.docs-article-toggle-button .fa-solid .fa-chevron-up}
:::
::::

# [TransComp Documentation](#TransComp-Documentation){.docs-heading-anchor}[]{#TransComp-Documentation-1}[](#TransComp-Documentation "Permalink"){.docs-heading-anchor-permalink} {#TransComp-Documentation}

Welcome to the documentation for the `TransComp` package. This package
provides tools for transportation modeling and optimization.

## [Getting Started](#Getting-Started){.docs-heading-anchor}[]{#Getting-Started-1}[](#Getting-Started "Permalink"){.docs-heading-anchor-permalink} {#Getting-Started}

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Edge`](#Main.TransComp.Edge){#Main.TransComp.Edge
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Edge
```

An \'Edge\' represents a connection between two nodes and is a
representation of connecting transport infrastructure.

**Fields**

-   `id::Int`: unique identifier of the edge
-   `name::String`: name of the connection
-   `length::Float64`: length of the connection in km
-   `from::Node`: the node from which the edge starts
-   `to::Node`: the node to which the edge ends
-   `carbon_price::Array{Float64,1}`: carbon price in €/tCO2 for each
    year

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L17-L29){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Emission_constraints_by_mode`](#Main.TransComp.Emission_constraints_by_mode){#Main.TransComp.Emission_constraints_by_mode
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Emission_constraints_by_mode
```

An \'Emission*constraints*by_mode\' describes emissions constrained for
a mode.

**Fields**

-   `id::Int`: unique identifier of the emission constraint
-   `mode::Mode`: mode of transport
-   `emission::Float64`: emission constraint of the vehicle type
    (tCO2/year)
-   `year::Int`: year of the expected emission constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L721-L731){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Emission_constraints_by_year`](#Main.TransComp.Emission_constraints_by_year){#Main.TransComp.Emission_constraints_by_year
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Emission_constraints_by_year
```

An \'Emission*constraints*by_year\' describes an emission goal for a
specific year for the total emissions.

**Fields**

-   `id::Int`: unique identifier of the emission constraint
-   `emission::Float64`: emission constraint
-   `year::Int`: year of the expected emission constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L739-L748){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.FinancialStatus`](#Main.TransComp.FinancialStatus){#Main.TransComp.FinancialStatus
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
FinancialStatus
```

A \'FinancialStatus\' describes a demographic group based on what there
average budget for transportation-related expenses is.

**Fields**

-   `id::Int`: unique identifier of the financial status
-   `name::String`: name of the financial status
-   `VoT`: value of time in €/h
-   `monetary_budget_operational`: budget for operational costs in
    €/year
-   `monetary_budget_operational_lb`: lower bound of the budget for
    operational costs in €/year
-   `monetary_budget_operational_ub`: upper bound of the budget for
    operational costs in €/year
-   `monetary_budget_purchase`: budget for purchasing costs in €/year
-   `monetary_budget_purchase_lb`: lower bound of the budget for
    purchasing costs in €/year
-   `monetary_budget_purchase_ub`: upper bound of the budget for
    purchasing costs in €/year

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L256-L271){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Fuel`](#Main.TransComp.Fuel){#Main.TransComp.Fuel
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Fuel
```

A \'Fuel\' represents the energy source used for the vehicle propulsion.

**Fields**

-   `id::Int`: unique identifier of the fuel
-   `name::String`: name of the fuel
-   `emission_factor::Float64`: emission factor of the fuel in gCO2/kWh
-   `cost_per_kWh`: cost per kWh of the fuel in €
-   `cost_per_kW`: cost per kW of the fuel in €
-   `fueling_infrastructure_om_costs::Array{Float64,1}`: fueling
    infrastructure operation and maintenance costs in €/year

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L123-L135){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.GeographicElement`](#Main.TransComp.GeographicElement){#Main.TransComp.GeographicElement
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
GeographicElement
```

A \'Graph_item\' represents a graph item that is either a node or an
edge.

**Fields**

-   `id::Int`: unique identifier of the graph item
-   `type::String`: type of the graph item (either \'node\' or \'edge\')
-   `name::String`: name of the graph item
-   `carbon_price::Array{Float64,1}`: carbon price in €/tCO2 for each
    year
-   `from::Node`: the node from which the edge starts
-   `to::Node`: the node to which the edge ends
-   `length::Float64`: length of the connection in km

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L39-L52){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.InitialFuelingInfr`](#Main.TransComp.InitialFuelingInfr){#Main.TransComp.InitialFuelingInfr
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
InitialFuelingInfr
```

An \'InitialFuelingInfr\' represents the fueling infrastructure that
exists at the initial year of the optimization horizon.

**Fields**

-   `id::Int`: unique identifier of the initial fueling infrastructure
-   `technology::Technology`: technology of the fueling infrastructure
-   `allocation`: allocation of the fueling infrastructure
-   `installed_kW::Float64`: installed capacity of the fueling
    infrastructure in kW

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L219-L229){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.InitialModeInfr`](#Main.TransComp.InitialModeInfr){#Main.TransComp.InitialModeInfr
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
InitialModeInfr
```

An \'InitialModeInfr\' represents the mode infrastructure that exists at
the initial year of the optimization horizon.

**Fields**

-   `id::Int`: unique identifier of the initial mode infrastructure
-   `mode::Mode`: mode of transport
-   `allocation`: allocation of the mode infrastructure
-   `installed_ukm::Float64`: installed transport capacity of the mode
    infrastructure in Ukm

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L237-L248){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.InitialVehicleStock`](#Main.TransComp.InitialVehicleStock){#Main.TransComp.InitialVehicleStock
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
InitialVehicleStock
```

An \'InitialVehicleStock\' represents a vehicle fleet that exisits at
the initial year of the optimization horizon.

**Fields**

-   `id::Int`: unique identifier of the initial vehicle stock
-   `techvehicle::TechVehicle`: vehicle type and technology of the
    vehicle
-   `year_of_purchase::Int`: year in which the vehicle was purchased
-   `stock::Float64`: number of vehicles of this type in the initial
    vehicle stock

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L200-L211){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Mode`](#Main.TransComp.Mode){#Main.TransComp.Mode
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Mode
```

A \'Mode\' represents a transport mode. Transport modes may differ
either by the infrastructure used (for example, road vs. rail) or by the
used vehicle type (for example, private passenger car vs. bus) that
directly influences the travel time but excludes a differentiation based
on technology.

**Fields**

-   `id::Int`: unique identifier of the mode
-   `name::String`: name of the mode
-   `quantify_by_vehs::Bool`: if for this mode vehicles stock is sized
    or not. If this mode is considered with levelized costs, including
    the costs for vehicles and related costs.
-   `cost_per_ukm::Array{Float64, 1}`: cost per km in €/km (only
    relevant when quantify*by*vehs is false)
-   `emission_factor::Array{Float64,1}`: emission factor of the mode in
    gCO2/ukm (only relevant when quantify*by*vehs is false)
-   `infrastructure_expansion_costs::Array{Float64,1}`: infrastructure
    expansion costs in € (only relevant when quantify*by*vehs is false)
-   `infrastructure_om_costs::Array{Float64,1}`: infrastructure
    operation and maintenance costs in €/year (only relevant when
    quantify*by*vehs is false)
-   `waiting_time::Array{Float64,1}`: waiting time in h

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L63-L77){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Mode_share_max`](#Main.TransComp.Mode_share_max){#Main.TransComp.Mode_share_max
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Mode_share_max
```

Maximum mode shares of a transport mode independent of year, i.e. over
total horizon.

**Fields**

-   `id::Int`: unique identifier of the mode share
-   `mode::Mode`: mode of transport
-   `share::Float64`: maximum share of the mode
-   `financial_status::Array{FinancialStatus, 1}`: array of financial
    status that is affected by this mode share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L430-L441){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Mode_share_max_by_year`](#Main.TransComp.Mode_share_max_by_year){#Main.TransComp.Mode_share_max_by_year
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Mode_share_max_by_year
```

Maximum mode shares of a transport mode in a specific year.

**Fields**

-   `id::Int`: unique identifier of the mode share
-   `mode::Mode`: mode of transport
-   `share::Float64`: maximum share of the mode
-   `year::Int`: year of the maximum mode share
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L389-L400){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Mode_share_min`](#Main.TransComp.Mode_share_min){#Main.TransComp.Mode_share_min
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Mode_share_min
```

Maximum mode shares of a transport mode independent of year, i.e. over
total horizon.

**Fields**

-   `id::Int`: unique identifier of the mode share
-   `mode::Mode`: mode of transport
-   `share::Float64`: maximum share of the mode
-   `financial_status::Array{FinancialStatus, 1}`: array of financial
    status that is affected by this mode share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L450-L461){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Mode_share_min_by_year`](#Main.TransComp.Mode_share_min_by_year){#Main.TransComp.Mode_share_min_by_year
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Mode_share_min_by_year
```

Minimum mode shares of a transport mode in a specific year.

**Fields**

-   `id::Int`: unique identifier of the mode share
-   `mode::Mode`: mode of transport
-   `share::Float64`: minimum share of the mode
-   `year::Int`: year of the minimum mode share
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L409-L420){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Node`](#Main.TransComp.Node){#Main.TransComp.Node
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Node
```

A \'Node\' represents geographic region.

**Fields**

-   `id::Int`: unique identifier of the node
-   `name::String`: name the region
-   `carbon_price::Array{Float64,1}`: carbon price in €/tCO2 for each
    year

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L1-L10){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Odpair`](#Main.TransComp.Odpair){#Main.TransComp.Odpair
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Odpair
```

An \'Odpair\' describes transport demand. It may take place between two
regions but origin and destination may al so

**Fields**

-   `id::Int`: unique identifier of the odpair
-   `origin::Node`: origin of the transport demand
-   `destination::Node`: destination of the transport demand
-   `paths::Array{Path, 1}`: possible paths between origin and
    destination
-   `F`: number of trips in p/year or t/year

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L304-L315){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Path`](#Main.TransComp.Path){#Main.TransComp.Path
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Path
```

A \'Path\' represents a possible route between two nodes. This sequence
includes the nodes that are passed through and the length of the path.

**Fields**

-   `id::Int`: unique identifier of the path
-   `name::String`: name of the path
-   `length::Float64`: length of the path in km
-   `sequence`: sequence of nodes and edges that are passed through

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L104-L115){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Product`](#Main.TransComp.Product){#Main.TransComp.Product
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Product
```

A \'Product\' represents either a good or a service that is being
transported. This may include passengers, or different types of products
in the freight transport. The differentiation of transported products
related to the different needs for transportation and, therefore,
different possible sets of transport modes, vehicle types and drivetrain
technologies are available for transport.

**Fields**

-   `id::Int`: unique identifier of the product
-   `name::String`: name of the product

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L89-L98){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Regiontype`](#Main.TransComp.Regiontype){#Main.TransComp.Regiontype
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Regiontype
```

A \'Regiontype\' describes a region based on its characteristics that
induces differences in transportation needs (for example, urban vs.
rural area).

**Fields**

-   `id::Int`: unique identifier of the regiontype
-   `name::String`: name of the regiontype
-   `speed::Float64`: average speed in km/h
-   `costs_var::Array{Float64, 1}`: variable costs in €/vehicle-km
-   `costs_fix::Array{Float64, 1}`: fixed costs in €/year

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L284-L296){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.TechVehicle`](#Main.TransComp.TechVehicle){#Main.TransComp.TechVehicle
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
TechVehicle
```

A \'TechVehicle\' represents a vehicle that is used for transportation.
This includes the vehicle type, the technology used in the vehicle, the
capital and maintenance costs, the load capacity, the specific
consumption, the lifetime, the annual range, the number of vehicles of
this type, the battery capacity, and the peak charging power.

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L178-L182){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.TechVehicle_share_max`](#Main.TransComp.TechVehicle_share_max){#Main.TransComp.TechVehicle_share_max
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
TechVehicle_share_max
```

Maximum vehicle type shares of a TechVehicle independent of year, i.e.
over total horizon.

**Fields**

-   `id::Int`: unique identifier of the TechVehicle share
-   `techvehicle::TechVehicle`: TechVehicle
-   `share::Float64`: maximum share of the TechVehicle
-   `financial_status::Array{FinancialStatus, 1}`: array of financial
    status that is affected by this TechVehicle share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L681-L692){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.TechVehicle_share_max_by_year`](#Main.TransComp.TechVehicle_share_max_by_year){#Main.TransComp.TechVehicle_share_max_by_year
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
TechVehicle_share_max_by_year
```

Maximum vehicle type shares of a TechVehicle in a specific year.

**Fields**

-   `id::Int`: unique identifier of the TechVehicle share
-   `techvehicle::TechVehicle`: TechVehicle
-   `share::Float64`: maximum share of the TechVehicle
-   `year::Int`: year of the maximum TechVehicle share
-   `financial_status::Array{FinancialStatus, 1}`: financial status that
    is affected by this TechVehicle share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L637-L649){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.TechVehicle_share_min`](#Main.TransComp.TechVehicle_share_min){#Main.TransComp.TechVehicle_share_min
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
TechVehicle_share_min
```

Minimum vehicle type shares of a TechVehicle independent of year, i.e.
over total horizon.

**Fields**

-   `id::Int`: unique identifier of the TechVehicle share
-   `techvehicle::TechVehicle`: TechVehicle
-   `share::Float64`: minimum share of the TechVehicle
-   `financial_status::Array{FinancialStatus, 1}`: array of financial
    status that is affected by this TechVehicle share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L701-L712){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.TechVehicle_share_min_by_year`](#Main.TransComp.TechVehicle_share_min_by_year){#Main.TransComp.TechVehicle_share_min_by_year
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
TechVehicle_share_min_by_year
```

Minimum vehicle type shares of a TechVehicle in a specific year.

**Fields**

-   `id::Int`: unique identifier of the TechVehicle share
-   `techvehicle::TechVehicle`: TechVehicle
-   `share::Float64`: minimum share of the TechVehicle
-   `year::Int`: year of the minimum TechVehicle share
-   `financial_status::Array{FinancialStatus, 1}`: financial status that
    is affected by this TechVehicle share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L659-L671){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Technology`](#Main.TransComp.Technology){#Main.TransComp.Technology
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Technology
```

A \'Technology\' represents the drivetrain technology used in the
vehicle.

**Fields**

-   `id::Int`: unique identifier of the technology
-   `name::String`: name of the technology
-   `fuel::Fuel`: fuel used by the technology

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L144-L153){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Technology_share_max`](#Main.TransComp.Technology_share_max){#Main.TransComp.Technology_share_max
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Technology_share_max
```

Maximum technology shares of a vehicle technology independent of year,
i.e. over total horizon.

**Fields**

-   `id::Int`: unique identifier of the technology share
-   `technology::Technology`: vehicle technology
-   `share::Float64`: maximum share of the technology
-   `financial_status::Array{FinancialStatus, 1}`: array of financial
    status that is affected by this technology share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L514-L525){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Technology_share_max_by_year`](#Main.TransComp.Technology_share_max_by_year){#Main.TransComp.Technology_share_max_by_year
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Technology_share_max_by_year
```

Maximum technology shares of a vehicle technology in a specific year.

**Fields**

-   `id::Int`: unique identifier of the technology share
-   `technology::Technology`: vehicle technology
-   `share::Float64`: maximum share of the technology
-   `year::Int`: year of the maximum technology share
-   `financial_status::Array{FinancialStatus, 1}`: financial status that
    is affected by this technology share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L470-L482){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Technology_share_min`](#Main.TransComp.Technology_share_min){#Main.TransComp.Technology_share_min
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Technology_share_min
```

Minimum technology shares of a vehicle technology independent of year,
i.e. over total horizon.

**Fields**

-   `id::Int`: unique identifier of the technology share
-   `technology::Technology`: vehicle technology
-   `share::Float64`: minimum share of the technology
-   `financial_status::Array{FinancialStatus, 1}`: array of financial
    status that is affected by this technology share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L534-L545){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Technology_share_min_by_year`](#Main.TransComp.Technology_share_min_by_year){#Main.TransComp.Technology_share_min_by_year
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Technology_share_min_by_year
```

Minimum technology shares of a vehicle technology in a specific year.

**Fields**

-   `id::Int`: unique identifier of the technology share
-   `technology::Technology`: vehicle technology
-   `share::Float64`: minimum share of the technology
-   `year::Int`: year of the minimum technology share
-   `financial_status::Array{FinancialStatus, 1}`: financial status that
    is affected by this technology share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L492-L504){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Transportation_speeds`](#Main.TransComp.Transportation_speeds){#Main.TransComp.Transportation_speeds
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Transportation_speeds
```

A \'Speed\' describes the speed of a vehicle type in a specific year.

**Fields**

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L755-L763){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.VehicleSubsidy`](#Main.TransComp.VehicleSubsidy){#Main.TransComp.VehicleSubsidy
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
VehicleSubsidy
```

A \'VehicleSubsidy\' describes the subsidy for a vehicle type in a
specific year.

**Fields**

-   `id::Int`: unique identifier of the subsidy
-   `name::String`: name of the subsidy
-   `years::Array{Int,1}`: years in which the subsidy is valid
-   `techvehicle::TechVehicle`: vehicle type and technology
-   `subsidy::Float64`: subsidy in €

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L773-L784){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.VehicleType_share_max`](#Main.TransComp.VehicleType_share_max){#Main.TransComp.VehicleType_share_max
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
VehicleType_share_max
```

Maximum vehicle type shares of a vehicle type independent of year, i.e.
over total horizon.

**Fields**

-   `id::Int`: unique identifier of the vehicle type share
-   `vehicle_type::Vehicletype`: vehicle type
-   `share::Float64`: maximum share of the vehicle type
-   `financial_status::Array{FinancialStatus, 1}`: array of financial
    status that is affected by this vehicle type share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L598-L609){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.VehicleType_share_max_by_year`](#Main.TransComp.VehicleType_share_max_by_year){#Main.TransComp.VehicleType_share_max_by_year
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
VehicleType_share_max_by_year
```

Maximum vehicle type shares of a vehicle type in a specific year.

**Fields**

-   `id::Int`: unique identifier of the vehicle type share
-   `vehicle_type::Vehicletype`: vehicle type
-   `share::Float64`: maximum share of the vehicle type
-   `year::Int`: year of the maximum vehicle type share
-   `financial_status::Array{FinancialStatus, 1}`: financial status that
    is affected by this vehicle type share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L554-L566){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.VehicleType_share_min`](#Main.TransComp.VehicleType_share_min){#Main.TransComp.VehicleType_share_min
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
VehicleType_share_min
```

Minimum vehicle type shares of a vehicle type independent of year, i.e.
over total horizon.

**Fields**

-   `id::Int`: unique identifier of the vehicle type share
-   `vehicle_type::Vehicletype`: vehicle type
-   `share::Float64`: minimum share of the vehicle type
-   `financial_status::Array{FinancialStatus, 1}`: array of financial
    status that is affected by this vehicle type share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L618-L629){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.VehicleType_share_min_by_year`](#Main.TransComp.VehicleType_share_min_by_year){#Main.TransComp.VehicleType_share_min_by_year
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
VehicleType_share_min_by_year
```

Minimum vehicle type shares of a vehicle type in a specific year.

**Fields**

-   `id::Int`: unique identifier of the vehicle type share
-   `vehicle_type::Vehicletype`: vehicle type
-   `share::Float64`: minimum share of the vehicle type
-   `year::Int`: year of the minimum vehicle type share
-   `financial_status::Array{FinancialStatus, 1}`: financial status that
    is affected by this vehicle type share constraint
-   `region_type::Array{Regiontype,1}`: array of region types that are
    affected by this TechVehicle share constraint

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L576-L588){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.Vehicletype`](#Main.TransComp.Vehicletype){#Main.TransComp.Vehicletype
.docstring-binding} --- [Type]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
Vehicletype
```

A \'Vehicletype\' represents a type of vehicle that is used for
transportation. This may be for example, small passenger cars, buses, or
light-duty trucks.

**Fields**

-   `id::Int`: unique identifier of the vehicle type
-   `name::String`: name of the vehicle type
-   `mode::Mode`: mode of transport that the vehicle type is used for
-   `product::Product`: product that the vehicle type is used for

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/structs.jl#L160-L170){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.base_define_variables`](#Main.TransComp.base_define_variables-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.base_define_variables-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
base_define_variables(model::Model, data_structures::Dict)
```

Defines the variables for the model.

**Arguments**

-   model::Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L10-L18){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.check_folder_writable`](#Main.TransComp.check_folder_writable-Tuple%7BString%7D){#Main.TransComp.check_folder_writable-Tuple{String}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
check_folder_writable(folder_path::String)
```

Check if the folder exists and can be written in.

**Arguments**

-   `folder_path::String`: The path to the folder.

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/checks.jl#L52-L59){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.check_input_file`](#Main.TransComp.check_input_file-Tuple%7BString%7D){#Main.TransComp.check_input_file-Tuple{String}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
check_input_file(path_to_source_file::String)
```

Check if the input file exists and is a YAML file.

**Arguments**

-   `path_to_source_file::String`: The path to the input file.

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/checks.jl#L5-L12){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.check_model_parametrization`](#Main.TransComp.check_model_parametrization-Tuple%7BDict,%20Vector%7BString%7D%7D){#Main.TransComp.check_model_parametrization-Tuple{Dict, Vector{String}}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
check_model_parametrization(data_dict::Dict, required_keys::Vector{String})
```

Check if the required keys are present in the model data.

**Arguments**

-   `data_dict::Dict`: The input data.

**Returns**

-   `Bool`: True if the required keys are present, false otherwise.

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/checks.jl#L37-L47){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.check_required_keys`](#Main.TransComp.check_required_keys-Tuple%7BDict,%20Vector%7BString%7D%7D){#Main.TransComp.check_required_keys-Tuple{Dict, Vector{String}}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
check_required_keys(data_dict::Dict, required_keys::Vector{String})
```

Check if the required keys are present in the input data.

**Arguments**

-   `data_dict::Dict`: The input data.

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/checks.jl#L23-L30){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_demand_coverage`](#Main.TransComp.constraint_demand_coverage-Tuple%7BJuMP.Model,%20Any%7D){#Main.TransComp.constraint_demand_coverage-Tuple{JuMP.Model, Any}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_demand_coverage(model::JuMP.Model, data_structures::Dict)
```

Creates constraint for demand coverage.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L138-L146){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_emissions_by_mode`](#Main.TransComp.constraint_emissions_by_mode-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_emissions_by_mode-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_emissions_by_mode(model::JuMP.Model, data_structures::Dict)
```

Emissions given per mode for a specific year. Attention: This constraint
may be a source for infeasibility if mode or technology shift cannot be
achieved due to restrictions in the shift of modes (see parametrization
of parameters alpha*f and beta*f), or due to the lifetimes of
technologies as well as the lack of available low emission or zero
emission technologies.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L875-L883){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_fueling_demand`](#Main.TransComp.constraint_fueling_demand-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_fueling_demand-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_fueling_demand(model::JuMP.Model, data_structures::Dict)
```

Constraints for fueling demand at nodes and edges.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L633-L641){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_fueling_infrastructure`](#Main.TransComp.constraint_fueling_infrastructure-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_fueling_infrastructure-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_vehicle_purchase(model::JuMP.Model, data_structures::Dict)
```

Constraints for the sizing of fueling infrastructure at nodes and edges.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L563-L571){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_market_share`](#Main.TransComp.constraint_market_share-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_market_share-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_market_share(model::JuMP.Model, data_structures::Dict)
```

If share are given for specific vehicle types, this function will create
constraints for the newly bought vehicle share of vehicles the modes.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L855-L863){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_max_mode_share`](#Main.TransComp.constraint_max_mode_share-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_max_mode_share-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_max_mode_share(model::JuMP.Model, data_structures::Dict)
```

If share are given for specific modes, this function will create
constraints for the share of the modes. When this constraint is active,
it can be a source of infeasibility for the model as it may be not
possible to reach certain mode shares due to restrictions in the shift
of modes (see parametrization of parameters alpha*f and beta*f). Or when
multiple constraints for the mode share are active.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L815-L823){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_min_mode_share`](#Main.TransComp.constraint_min_mode_share-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_min_mode_share-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_min_mode_share(model::JuMP.Model, data_structures::Dict)
```

If share are given for specific modes, this function will create
constraints for the share of the modes. When this constraint is active,
it can be a source of infeasibility for the model as it may be not
possible to reach certain mode shares due to restrictions in the shift
of modes (see parametrization of parameters alpha*f and beta*f). Or when
multiple constraints for the mode share are active.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L835-L843){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_mode_infrastructure`](#Main.TransComp.constraint_mode_infrastructure-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_mode_infrastructure-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

constraint*mode*infrastructure(model::JuMP.Model, data_structures::Dict)

Constraints for sizing of mode infrastructure at nodes and edges.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L599-L607){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_mode_share`](#Main.TransComp.constraint_mode_share-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_mode_share-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_mode_share(model::JuMP.Model, data_structures::Dict)
```

If share are given for specific modes, this function will create
constraints for the share of the modes. When this constraint is active,
it can be a source of infeasibility for the model as it may be not
possible to reach certain mode shares due to restrictions in the shift
of modes (see parametrization of parameters alpha*f and beta*f).
Especially also when constraints for minimum/maximum mode shares are
active.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L795-L803){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_mode_shift`](#Main.TransComp.constraint_mode_shift-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_mode_shift-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_mode_shift(model::JuMP.Model, data_structures::Dict)
```

Constraints for the rate of the mode shfit.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L730-L738){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_monetary_budget`](#Main.TransComp.constraint_monetary_budget-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_monetary_budget-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_vehicle_purchase(model::JuMP.Model, data_structures::Dict)
```

Creates constraints for monetary budget for vehicle purchase by route.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L501-L509){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_vehicle_aging`](#Main.TransComp.constraint_vehicle_aging-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_vehicle_aging-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_vehicle_aging(model::JuMP.Model, data_structures::Dict)
```

Creates constraints for vehicle aging.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

**Returns**

-   model::JuMP.Model: JuMP model with the constraints added

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L277-L288){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_vehicle_sizing`](#Main.TransComp.constraint_vehicle_sizing-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_vehicle_sizing-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_vehicle_sizing(model::JuMP.Model, data_structures::Dict)
```

Creates constraint for vehicle sizing.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L161-L169){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.constraint_vehicle_stock_shift`](#Main.TransComp.constraint_vehicle_stock_shift-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.constraint_vehicle_stock_shift-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
constraint_vehicle_stock_shift(model::JuMP.Model, data_structures::Dict)
```

Constraints for vehicle stock turnover.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L669-L677){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.create_emission_price_along_path`](#Main.TransComp.create_emission_price_along_path-Tuple%7BPath,%20Dict%7D){#Main.TransComp.create_emission_price_along_path-Tuple{Path, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
create_emission_price_along_path(k::Path, data_structures::Dict)
```

Calculating the carbon price along a given route based on the regions
that the path lies in. (currently simple calculation by averaging over
all geometric items among the path).

**Arguments**

-   k::Path: path
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L569-L578){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.create_m_tv_pairs`](#Main.TransComp.create_m_tv_pairs-Tuple%7BVector%7BTechVehicle%7D,%20Vector%7BMode%7D%7D){#Main.TransComp.create_m_tv_pairs-Tuple{Vector{TechVehicle}, Vector{Mode}}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
create_m_tv_pairs(techvehicle_list::Vector{TechVehicle}, mode_list::Vector{Mode})
```

Creates a set of pairs of mode and techvehicle IDs.

**Arguments**

-   techvehicle_list::Vector{TechVehicle}: list of techvehicles
-   mode_list::Vector{Mode}: list of modes

**Returns**

-   m*tv*pairs::Set: set of pairs of mode and techvehicle IDs

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L363-L375){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.create_model`](#Main.TransComp.create_model-Tuple%7BAny,%20String%7D){#Main.TransComp.create_model-Tuple{Any, String}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
create_model(model::JuMP.Model, data_structures::Dict)
```

Definition of JuMP.model and adding of variables.

**Arguments**

-   model::JuMP.Model: JuMP model
-   data_structures::Dict: dictionary with the input data and parsing of
    the input parameters

**Returns**

-   model::JuMP.Model: JuMP model with the variables added
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L526-L538){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.create_p_r_k_e_set`](#Main.TransComp.create_p_r_k_e_set-Tuple%7BVector%7BOdpair%7D%7D){#Main.TransComp.create_p_r_k_e_set-Tuple{Vector{Odpair}}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
create_p_r_k_e_set(odpairs::Vector{Odpair})
```

Creates a set of pairs of product, odpair, path, and element IDs.

**Arguments**

-   odpairs::Vector{Odpair}: list of odpairs

**Returns**

-   p*r*k*e*pairs::Set: set of pairs of product, odpair, path, and
    element IDs

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L453-L463){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.create_p_r_k_g_set`](#Main.TransComp.create_p_r_k_g_set-Tuple%7BVector%7BOdpair%7D%7D){#Main.TransComp.create_p_r_k_g_set-Tuple{Vector{Odpair}}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
create_p_r_k_g_set(odpairs::Vector{Odpair})
```

Creates a set of pairs of product, odpair, path, and element IDs.

**Arguments**

-   odpairs::Vector{Odpair}: list of odpairs

**Returns**

-   p*r*k*g*pairs::Set: set of pairs of product, odpair, path, and
    element IDs

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L472-L482){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.create_p_r_k_n_set`](#Main.TransComp.create_p_r_k_n_set-Tuple%7BVector%7BOdpair%7D%7D){#Main.TransComp.create_p_r_k_n_set-Tuple{Vector{Odpair}}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
create_p_r_k_n_set(odpairs::Vector{Odpair})
```

Creates a set of pairs of product, odpair, path, and element IDs.

**Arguments**

-   odpairs::Vector{Odpair}: list of odpairs

**Returns**

-   p*r*k*n*pairs::Set: set of pairs of product, odpair, path, and
    element IDs

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L491-L501){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.create_p_r_k_set`](#Main.TransComp.create_p_r_k_set-Tuple%7BVector%7BOdpair%7D%7D){#Main.TransComp.create_p_r_k_set-Tuple{Vector{Odpair}}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
create_p_r_k_set(odpairs::Vector{Odpair})
```

Creates a set of pairs of product, odpair, and path IDs.

**Arguments**

-   odpairs::Vector{Odpair}: list of odpairs

**Returns**

-   p*r*k_pairs::Set: set of pairs of product, odpair, and path IDs

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L437-L447){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.create_r_k_set`](#Main.TransComp.create_r_k_set-Tuple%7BVector%7BOdpair%7D%7D){#Main.TransComp.create_r_k_set-Tuple{Vector{Odpair}}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
create_r_k_set(odpairs::Vector{Odpair})
```

Creates a set of pairs of odpair and path IDs.

**Arguments**

-   odpairs::Vector{Odpair}: list of odpairs

**Returns**

-   r*k*pairs::Set: set of pairs of odpair and path IDs

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L510-L520){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.create_tv_id_set`](#Main.TransComp.create_tv_id_set-Tuple%7BVector%7BTechVehicle%7D,%20Vector%7BMode%7D%7D){#Main.TransComp.create_tv_id_set-Tuple{Vector{TechVehicle}, Vector{Mode}}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
create_tv_id_set(techvehicle_list::Vector{TechVehicle}, mode_list::Vector{Mode})
```

Creates a list of techvehicle IDs.

**Arguments**

-   techvehicle_list::Vector{TechVehicle}: list of techvehicles
-   mode_list::Vector{Mode}: list of modes

**Returns**

-   techvehicle*ids*2::Set: set of techvehicle IDs

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L395-L406){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.create_v_t_set`](#Main.TransComp.create_v_t_set-Tuple%7BVector%7BTechVehicle%7D%7D){#Main.TransComp.create_v_t_set-Tuple{Vector{TechVehicle}}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
create_v_t_set(techvehicle_list::Vector{TechVehicle})
```

Creates a set of pairs of techvehicle IDs.

**Arguments**

-   techvehicle_list::Vector{TechVehicle}: list of techvehicles

**Returns**

-   t*v*pairs::Set: set of pairs of techvehicle IDs

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L421-L431){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.depreciation_factor`](#Main.TransComp.depreciation_factor-Tuple%7BAny,%20Any%7D){#Main.TransComp.depreciation_factor-Tuple{Any, Any}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
depreciation_factor(y, g)
```

Calculate the depreciation factor for a vehicle based on its age.

**Arguments**

-   `y::Int`: The year of the vehicle.
-   `g::Int`: The year the vehicle was purchased.

**Returns**

-   `Float64`: The depreciation factor.

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L546-L557){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.get_input_data`](#Main.TransComp.get_input_data-Tuple%7BString%7D){#Main.TransComp.get_input_data-Tuple{String}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
get_input_data(path_to_source_file::String)
```

This function reads the input data and checks requirements for the
content of the file.

**Arguments**

-   path*to*source_file::String: path to the source file

**Returns**

-   data_dict::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L6-L16){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.objective`](#Main.TransComp.objective-Tuple%7BJuMP.Model,%20Dict%7D){#Main.TransComp.objective-Tuple{JuMP.Model, Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
objective(model::Model, data_structures::Dict)
```

Definition of the objective function for the optimization model.

**Arguments**

-   model::Model: JuMP model
-   data_structures::Dict: dictionary with the input data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/model_functions.jl#L905-L913){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.parse_data`](#Main.TransComp.parse_data-Tuple%7BDict%7D){#Main.TransComp.parse_data-Tuple{Dict}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
parse_data(data_dict::Dict)
```

Parses the input data into the corresponding parameters in struct format
from structs.jl.

**Arguments**

-   data_dict::Dict: dictionary with the input data

**Returns**

-   data_structures::Dict: dictionary with the parsed data

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L25-L35){.docs-sourcelink
target="_blank"}
::::

<div>

[](javascript:; "Collapse docstring"){.docstring-article-toggle-button
.fa-solid
.fa-chevron-down}[`Main.TransComp.save_results`](#Main.TransComp.save_results-Tuple%7BJuMP.Model,%20String,%20String%7D){#Main.TransComp.save_results-Tuple{JuMP.Model, String, String}
.docstring-binding} --- [Method]{.docstring-category}[]{.is-flex-grow-1
.docstring-article-toggle-button title="Collapse docstring"}

</div>

:::: section
<div>

``` {.julia .hljs}
save_results(model::Model, case_name::String)
```

Saves the results of the optimization model to YAML files.

**Arguments**

-   model::Model: JuMP model
-   case_name::String: name of the case
-   file*for*results::String: name of the file to save the results

</div>

[source](https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/fc5fd38666c4f6c5833ebc6d45ed5f58f57f28ed/src/support_functions.jl#L593-L602){.docs-sourcelink
target="_blank"}
::::

Powered by [Documenter.jl](https://github.com/JuliaDocs/Documenter.jl)
and the [Julia Programming Language](https://julialang.org/).
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:::::::: {#documenter-settings .modal}
::: modal-background
:::

:::::: modal-card
::: modal-card-head
Settings
:::

:::: {.section .modal-card-body}
Theme

::: select
Automatic
(OS)documenter-lightdocumenter-darkcatppuccin-lattecatppuccin-frappecatppuccin-macchiatocatppuccin-mocha
:::

------------------------------------------------------------------------

This document was generated with
[Documenter.jl](https://github.com/JuliaDocs/Documenter.jl) version
1.8.0 on [Thursday 28 November 2024]{.colophon-date
title="Thursday 28 November 2024 11:10"}. Using Julia version 1.11.0.
::::
::::::
::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
