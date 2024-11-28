<div id="documenter">
<div class="docs-package-name">
<span class="docs-autofit"><a href="">TransComp Documentation</a></span>
</div>
Search docs (Ctrl + /)
<ul>
<li><a href="" class="tocitem">Home</a>
<ul>
<li><a href="#Getting-Started" class="tocitem"><span>Getting
Started</span></a></li>
</ul></li>
</ul>
<div class="docs-version-selector field has-addons">
<div class="control">
<span class="docs-label button is-static is-size-7">Version</span>
</div>
<div class="docs-selector control is-expanded">
<div class="select is-fullwidth is-size-7">

</div>
</div>
</div>
<div class="docs-main">
<div class="docs-navbar">
<a href="#" id="documenter-sidebar-button"
class="docs-sidebar-button docs-navbar-link fa-solid fa-bars is-hidden-desktop"></a>
<ul>
<li><a href="">Home</a></li>
</ul>
<ul>
<li><a href="">Home</a></li>
</ul>
<div class="docs-right">
<a href="https://github.com/antoniamgolab/iDesignRES_transcompmodel"
class="docs-navbar-link" title="View the repository on GitHub"><span
class="docs-icon fa-brands"></span><span
class="docs-label is-hidden-touch">GitHub</span></a><a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/main/docs/src/index.md"
class="docs-navbar-link" title="Edit source on GitHub"><span
class="docs-icon fa-solid"></span></a><a href="#"
id="documenter-settings-button"
class="docs-settings-button docs-navbar-link fa-solid fa-gear"
title="Settings"></a><a href="javascript:;"
id="documenter-article-toggle-button"
class="docs-article-toggle-button fa-solid fa-chevron-up"
title="Collapse all docstrings"></a>
</div>
</div>
<h1 id="TransComp-Documentation"><a href="#TransComp-Documentation"
class="docs-heading-anchor">TransComp Documentation</a><span
id="TransComp-Documentation-1"></span><a href="#TransComp-Documentation"
class="docs-heading-anchor-permalink" title="Permalink"></a></h1>
<p>Welcome to the documentation for the <code>TransComp</code> package.
This package provides tools for transportation modeling and
optimization.</p>
<h2 id="Getting-Started"><a href="#Getting-Started"
class="docs-heading-anchor">Getting Started</a><span
id="Getting-Started-1"></span><a href="#Getting-Started"
class="docs-heading-anchor-permalink" title="Permalink"></a></h2>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.Edge"
id="Main.TransComp.Edge"
class="docstring-binding"><code>Main.TransComp.Edge</code></a> — <span
class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb1"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb1-1"><a href="#cb1-1" aria-hidden="true" tabindex="-1"></a>Edge</span></code></pre></div>
<p>An 'Edge' represents a connection between two nodes and is a
representation of connecting transport infrastructure.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the edge</li>
<li><code>name::String</code>: name of the connection</li>
<li><code>length::Float64</code>: length of the connection in km</li>
<li><code>from::Node</code>: the node from which the edge starts</li>
<li><code>to::Node</code>: the node to which the edge ends</li>
<li><code>carbon_price::Array{Float64,1}</code>: carbon price in €/tCO2
for each year</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L17-L29"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.Emission_constraints_by_mode"
id="Main.TransComp.Emission_constraints_by_mode"
class="docstring-binding"><code>Main.TransComp.Emission_constraints_by_mode</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb2"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb2-1"><a href="#cb2-1" aria-hidden="true" tabindex="-1"></a>Emission_constraints_by_mode</span></code></pre></div>
<p>An 'Emission<em>constraints</em>by_mode' describes emissions
constrained for a mode.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the emission
constraint</li>
<li><code>mode::Mode</code>: mode of transport</li>
<li><code>emission::Float64</code>: emission constraint of the vehicle
type (tCO2/year)</li>
<li><code>year::Int</code>: year of the expected emission
constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L721-L731"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.Emission_constraints_by_year"
id="Main.TransComp.Emission_constraints_by_year"
class="docstring-binding"><code>Main.TransComp.Emission_constraints_by_year</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb3"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb3-1"><a href="#cb3-1" aria-hidden="true" tabindex="-1"></a>Emission_constraints_by_year</span></code></pre></div>
<p>An 'Emission<em>constraints</em>by_year' describes an emission goal
for a specific year for the total emissions.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the emission
constraint</li>
<li><code>emission::Float64</code>: emission constraint</li>
<li><code>year::Int</code>: year of the expected emission
constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L739-L748"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.FinancialStatus"
id="Main.TransComp.FinancialStatus"
class="docstring-binding"><code>Main.TransComp.FinancialStatus</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb4"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb4-1"><a href="#cb4-1" aria-hidden="true" tabindex="-1"></a>FinancialStatus</span></code></pre></div>
<p>A 'FinancialStatus' describes a demographic group based on what there
average budget for transportation-related expenses is.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the financial status</li>
<li><code>name::String</code>: name of the financial status</li>
<li><code>VoT</code>: value of time in €/h</li>
<li><code>monetary_budget_operational</code>: budget for operational
costs in €/year</li>
<li><code>monetary_budget_operational_lb</code>: lower bound of the
budget for operational costs in €/year</li>
<li><code>monetary_budget_operational_ub</code>: upper bound of the
budget for operational costs in €/year</li>
<li><code>monetary_budget_purchase</code>: budget for purchasing costs
in €/year</li>
<li><code>monetary_budget_purchase_lb</code>: lower bound of the budget
for purchasing costs in €/year</li>
<li><code>monetary_budget_purchase_ub</code>: upper bound of the budget
for purchasing costs in €/year</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L256-L271"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.Fuel"
id="Main.TransComp.Fuel"
class="docstring-binding"><code>Main.TransComp.Fuel</code></a> — <span
class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb5"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb5-1"><a href="#cb5-1" aria-hidden="true" tabindex="-1"></a>Fuel</span></code></pre></div>
<p>A 'Fuel' represents the energy source used for the vehicle
propulsion.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the fuel</li>
<li><code>name::String</code>: name of the fuel</li>
<li><code>emission_factor::Float64</code>: emission factor of the fuel
in gCO2/kWh</li>
<li><code>cost_per_kWh</code>: cost per kWh of the fuel in €</li>
<li><code>cost_per_kW</code>: cost per kW of the fuel in €</li>
<li><code>fueling_infrastructure_om_costs::Array{Float64,1}</code>:
fueling infrastructure operation and maintenance costs in €/year</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L123-L135"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.GeographicElement"
id="Main.TransComp.GeographicElement"
class="docstring-binding"><code>Main.TransComp.GeographicElement</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb6"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb6-1"><a href="#cb6-1" aria-hidden="true" tabindex="-1"></a>GeographicElement</span></code></pre></div>
<p>A 'Graph_item' represents a graph item that is either a node or an
edge.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the graph item</li>
<li><code>type::String</code>: type of the graph item (either 'node' or
'edge')</li>
<li><code>name::String</code>: name of the graph item</li>
<li><code>carbon_price::Array{Float64,1}</code>: carbon price in €/tCO2
for each year</li>
<li><code>from::Node</code>: the node from which the edge starts</li>
<li><code>to::Node</code>: the node to which the edge ends</li>
<li><code>length::Float64</code>: length of the connection in km</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L39-L52"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.InitialFuelingInfr"
id="Main.TransComp.InitialFuelingInfr"
class="docstring-binding"><code>Main.TransComp.InitialFuelingInfr</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb7"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb7-1"><a href="#cb7-1" aria-hidden="true" tabindex="-1"></a>InitialFuelingInfr</span></code></pre></div>
<p>An 'InitialFuelingInfr' represents the fueling infrastructure that
exists at the initial year of the optimization horizon.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the initial fueling
infrastructure</li>
<li><code>technology::Technology</code>: technology of the fueling
infrastructure</li>
<li><code>allocation</code>: allocation of the fueling
infrastructure</li>
<li><code>installed_kW::Float64</code>: installed capacity of the
fueling infrastructure in kW</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L219-L229"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.InitialModeInfr"
id="Main.TransComp.InitialModeInfr"
class="docstring-binding"><code>Main.TransComp.InitialModeInfr</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb8"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb8-1"><a href="#cb8-1" aria-hidden="true" tabindex="-1"></a>InitialModeInfr</span></code></pre></div>
<p>An 'InitialModeInfr' represents the mode infrastructure that exists
at the initial year of the optimization horizon.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the initial mode
infrastructure</li>
<li><code>mode::Mode</code>: mode of transport</li>
<li><code>allocation</code>: allocation of the mode infrastructure</li>
<li><code>installed_ukm::Float64</code>: installed transport capacity of
the mode infrastructure in Ukm</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L237-L248"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.InitialVehicleStock"
id="Main.TransComp.InitialVehicleStock"
class="docstring-binding"><code>Main.TransComp.InitialVehicleStock</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb9"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb9-1"><a href="#cb9-1" aria-hidden="true" tabindex="-1"></a>InitialVehicleStock</span></code></pre></div>
<p>An 'InitialVehicleStock' represents a vehicle fleet that exisits at
the initial year of the optimization horizon.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the initial vehicle
stock</li>
<li><code>techvehicle::TechVehicle</code>: vehicle type and technology
of the vehicle</li>
<li><code>year_of_purchase::Int</code>: year in which the vehicle was
purchased</li>
<li><code>stock::Float64</code>: number of vehicles of this type in the
initial vehicle stock</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L200-L211"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.Mode"
id="Main.TransComp.Mode"
class="docstring-binding"><code>Main.TransComp.Mode</code></a> — <span
class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb10"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb10-1"><a href="#cb10-1" aria-hidden="true" tabindex="-1"></a>Mode</span></code></pre></div>
<p>A 'Mode' represents a transport mode. Transport modes may differ
either by the infrastructure used (for example, road vs. rail) or by the
used vehicle type (for example, private passenger car vs. bus) that
directly influences the travel time but excludes a differentiation based
on technology.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the mode</li>
<li><code>name::String</code>: name of the mode</li>
<li><code>quantify_by_vehs::Bool</code>: if for this mode vehicles stock
is sized or not. If this mode is considered with levelized costs,
including the costs for vehicles and related costs.</li>
<li><code>cost_per_ukm::Array{Float64, 1}</code>: cost per km in €/km
(only relevant when quantify<em>by</em>vehs is false)</li>
<li><code>emission_factor::Array{Float64,1}</code>: emission factor of
the mode in gCO2/ukm (only relevant when quantify<em>by</em>vehs is
false)</li>
<li><code>infrastructure_expansion_costs::Array{Float64,1}</code>:
infrastructure expansion costs in € (only relevant when
quantify<em>by</em>vehs is false)</li>
<li><code>infrastructure_om_costs::Array{Float64,1}</code>:
infrastructure operation and maintenance costs in €/year (only relevant
when quantify<em>by</em>vehs is false)</li>
<li><code>waiting_time::Array{Float64,1}</code>: waiting time in h</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L63-L77"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.Mode_share_max"
id="Main.TransComp.Mode_share_max"
class="docstring-binding"><code>Main.TransComp.Mode_share_max</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb11"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb11-1"><a href="#cb11-1" aria-hidden="true" tabindex="-1"></a>Mode_share_max</span></code></pre></div>
<p>Maximum mode shares of a transport mode independent of year, i.e.
over total horizon.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the mode share</li>
<li><code>mode::Mode</code>: mode of transport</li>
<li><code>share::Float64</code>: maximum share of the mode</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: array of
financial status that is affected by this mode share constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L430-L441"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.Mode_share_max_by_year"
id="Main.TransComp.Mode_share_max_by_year"
class="docstring-binding"><code>Main.TransComp.Mode_share_max_by_year</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb12"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb12-1"><a href="#cb12-1" aria-hidden="true" tabindex="-1"></a>Mode_share_max_by_year</span></code></pre></div>
<p>Maximum mode shares of a transport mode in a specific year.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the mode share</li>
<li><code>mode::Mode</code>: mode of transport</li>
<li><code>share::Float64</code>: maximum share of the mode</li>
<li><code>year::Int</code>: year of the maximum mode share</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L389-L400"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.Mode_share_min"
id="Main.TransComp.Mode_share_min"
class="docstring-binding"><code>Main.TransComp.Mode_share_min</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb13"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb13-1"><a href="#cb13-1" aria-hidden="true" tabindex="-1"></a>Mode_share_min</span></code></pre></div>
<p>Maximum mode shares of a transport mode independent of year, i.e.
over total horizon.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the mode share</li>
<li><code>mode::Mode</code>: mode of transport</li>
<li><code>share::Float64</code>: maximum share of the mode</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: array of
financial status that is affected by this mode share constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L450-L461"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.Mode_share_min_by_year"
id="Main.TransComp.Mode_share_min_by_year"
class="docstring-binding"><code>Main.TransComp.Mode_share_min_by_year</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb14"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb14-1"><a href="#cb14-1" aria-hidden="true" tabindex="-1"></a>Mode_share_min_by_year</span></code></pre></div>
<p>Minimum mode shares of a transport mode in a specific year.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the mode share</li>
<li><code>mode::Mode</code>: mode of transport</li>
<li><code>share::Float64</code>: minimum share of the mode</li>
<li><code>year::Int</code>: year of the minimum mode share</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L409-L420"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.Node"
id="Main.TransComp.Node"
class="docstring-binding"><code>Main.TransComp.Node</code></a> — <span
class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb15"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb15-1"><a href="#cb15-1" aria-hidden="true" tabindex="-1"></a>Node</span></code></pre></div>
<p>A 'Node' represents geographic region.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the node</li>
<li><code>name::String</code>: name the region</li>
<li><code>carbon_price::Array{Float64,1}</code>: carbon price in €/tCO2
for each year</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L1-L10"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.Odpair"
id="Main.TransComp.Odpair"
class="docstring-binding"><code>Main.TransComp.Odpair</code></a> — <span
class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb16"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb16-1"><a href="#cb16-1" aria-hidden="true" tabindex="-1"></a>Odpair</span></code></pre></div>
<p>An 'Odpair' describes transport demand. It may take place between two
regions but origin and destination may al so</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the odpair</li>
<li><code>origin::Node</code>: origin of the transport demand</li>
<li><code>destination::Node</code>: destination of the transport
demand</li>
<li><code>paths::Array{Path, 1}</code>: possible paths between origin
and destination</li>
<li><code>F</code>: number of trips in p/year or t/year</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L304-L315"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.Path"
id="Main.TransComp.Path"
class="docstring-binding"><code>Main.TransComp.Path</code></a> — <span
class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb17"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb17-1"><a href="#cb17-1" aria-hidden="true" tabindex="-1"></a>Path</span></code></pre></div>
<p>A 'Path' represents a possible route between two nodes. This sequence
includes the nodes that are passed through and the length of the
path.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the path</li>
<li><code>name::String</code>: name of the path</li>
<li><code>length::Float64</code>: length of the path in km</li>
<li><code>sequence</code>: sequence of nodes and edges that are passed
through</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L104-L115"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.Product"
id="Main.TransComp.Product"
class="docstring-binding"><code>Main.TransComp.Product</code></a> —
<span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb18"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb18-1"><a href="#cb18-1" aria-hidden="true" tabindex="-1"></a>Product</span></code></pre></div>
<p>A 'Product' represents either a good or a service that is being
transported. This may include passengers, or different types of products
in the freight transport. The differentiation of transported products
related to the different needs for transportation and, therefore,
different possible sets of transport modes, vehicle types and drivetrain
technologies are available for transport.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the product</li>
<li><code>name::String</code>: name of the product</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L89-L98"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.Regiontype"
id="Main.TransComp.Regiontype"
class="docstring-binding"><code>Main.TransComp.Regiontype</code></a> —
<span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb19"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb19-1"><a href="#cb19-1" aria-hidden="true" tabindex="-1"></a>Regiontype</span></code></pre></div>
<p>A 'Regiontype' describes a region based on its characteristics that
induces differences in transportation needs (for example, urban vs.
rural area).</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the regiontype</li>
<li><code>name::String</code>: name of the regiontype</li>
<li><code>speed::Float64</code>: average speed in km/h</li>
<li><code>costs_var::Array{Float64, 1}</code>: variable costs in
€/vehicle-km</li>
<li><code>costs_fix::Array{Float64, 1}</code>: fixed costs in
€/year</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L284-L296"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.TechVehicle"
id="Main.TransComp.TechVehicle"
class="docstring-binding"><code>Main.TransComp.TechVehicle</code></a> —
<span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb20"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb20-1"><a href="#cb20-1" aria-hidden="true" tabindex="-1"></a>TechVehicle</span></code></pre></div>
<p>A 'TechVehicle' represents a vehicle that is used for transportation.
This includes the vehicle type, the technology used in the vehicle, the
capital and maintenance costs, the load capacity, the specific
consumption, the lifetime, the annual range, the number of vehicles of
this type, the battery capacity, and the peak charging power.</p>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L178-L182"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.TechVehicle_share_max"
id="Main.TransComp.TechVehicle_share_max"
class="docstring-binding"><code>Main.TransComp.TechVehicle_share_max</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb21"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb21-1"><a href="#cb21-1" aria-hidden="true" tabindex="-1"></a>TechVehicle_share_max</span></code></pre></div>
<p>Maximum vehicle type shares of a TechVehicle independent of year,
i.e. over total horizon.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the TechVehicle
share</li>
<li><code>techvehicle::TechVehicle</code>: TechVehicle</li>
<li><code>share::Float64</code>: maximum share of the TechVehicle</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: array of
financial status that is affected by this TechVehicle share
constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L681-L692"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.TechVehicle_share_max_by_year"
id="Main.TransComp.TechVehicle_share_max_by_year"
class="docstring-binding"><code>Main.TransComp.TechVehicle_share_max_by_year</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb22"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb22-1"><a href="#cb22-1" aria-hidden="true" tabindex="-1"></a>TechVehicle_share_max_by_year</span></code></pre></div>
<p>Maximum vehicle type shares of a TechVehicle in a specific year.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the TechVehicle
share</li>
<li><code>techvehicle::TechVehicle</code>: TechVehicle</li>
<li><code>share::Float64</code>: maximum share of the TechVehicle</li>
<li><code>year::Int</code>: year of the maximum TechVehicle share</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: financial
status that is affected by this TechVehicle share constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L637-L649"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.TechVehicle_share_min"
id="Main.TransComp.TechVehicle_share_min"
class="docstring-binding"><code>Main.TransComp.TechVehicle_share_min</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb23"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb23-1"><a href="#cb23-1" aria-hidden="true" tabindex="-1"></a>TechVehicle_share_min</span></code></pre></div>
<p>Minimum vehicle type shares of a TechVehicle independent of year,
i.e. over total horizon.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the TechVehicle
share</li>
<li><code>techvehicle::TechVehicle</code>: TechVehicle</li>
<li><code>share::Float64</code>: minimum share of the TechVehicle</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: array of
financial status that is affected by this TechVehicle share
constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L701-L712"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.TechVehicle_share_min_by_year"
id="Main.TransComp.TechVehicle_share_min_by_year"
class="docstring-binding"><code>Main.TransComp.TechVehicle_share_min_by_year</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb24"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb24-1"><a href="#cb24-1" aria-hidden="true" tabindex="-1"></a>TechVehicle_share_min_by_year</span></code></pre></div>
<p>Minimum vehicle type shares of a TechVehicle in a specific year.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the TechVehicle
share</li>
<li><code>techvehicle::TechVehicle</code>: TechVehicle</li>
<li><code>share::Float64</code>: minimum share of the TechVehicle</li>
<li><code>year::Int</code>: year of the minimum TechVehicle share</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: financial
status that is affected by this TechVehicle share constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L659-L671"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.Technology"
id="Main.TransComp.Technology"
class="docstring-binding"><code>Main.TransComp.Technology</code></a> —
<span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb25"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb25-1"><a href="#cb25-1" aria-hidden="true" tabindex="-1"></a>Technology</span></code></pre></div>
<p>A 'Technology' represents the drivetrain technology used in the
vehicle.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the technology</li>
<li><code>name::String</code>: name of the technology</li>
<li><code>fuel::Fuel</code>: fuel used by the technology</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L144-L153"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.Technology_share_max"
id="Main.TransComp.Technology_share_max"
class="docstring-binding"><code>Main.TransComp.Technology_share_max</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb26"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb26-1"><a href="#cb26-1" aria-hidden="true" tabindex="-1"></a>Technology_share_max</span></code></pre></div>
<p>Maximum technology shares of a vehicle technology independent of
year, i.e. over total horizon.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the technology share</li>
<li><code>technology::Technology</code>: vehicle technology</li>
<li><code>share::Float64</code>: maximum share of the technology</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: array of
financial status that is affected by this technology share
constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L514-L525"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.Technology_share_max_by_year"
id="Main.TransComp.Technology_share_max_by_year"
class="docstring-binding"><code>Main.TransComp.Technology_share_max_by_year</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb27"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb27-1"><a href="#cb27-1" aria-hidden="true" tabindex="-1"></a>Technology_share_max_by_year</span></code></pre></div>
<p>Maximum technology shares of a vehicle technology in a specific
year.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the technology share</li>
<li><code>technology::Technology</code>: vehicle technology</li>
<li><code>share::Float64</code>: maximum share of the technology</li>
<li><code>year::Int</code>: year of the maximum technology share</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: financial
status that is affected by this technology share constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L470-L482"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.Technology_share_min"
id="Main.TransComp.Technology_share_min"
class="docstring-binding"><code>Main.TransComp.Technology_share_min</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb28"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb28-1"><a href="#cb28-1" aria-hidden="true" tabindex="-1"></a>Technology_share_min</span></code></pre></div>
<p>Minimum technology shares of a vehicle technology independent of
year, i.e. over total horizon.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the technology share</li>
<li><code>technology::Technology</code>: vehicle technology</li>
<li><code>share::Float64</code>: minimum share of the technology</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: array of
financial status that is affected by this technology share
constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L534-L545"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.Technology_share_min_by_year"
id="Main.TransComp.Technology_share_min_by_year"
class="docstring-binding"><code>Main.TransComp.Technology_share_min_by_year</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb29"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb29-1"><a href="#cb29-1" aria-hidden="true" tabindex="-1"></a>Technology_share_min_by_year</span></code></pre></div>
<p>Minimum technology shares of a vehicle technology in a specific
year.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the technology share</li>
<li><code>technology::Technology</code>: vehicle technology</li>
<li><code>share::Float64</code>: minimum share of the technology</li>
<li><code>year::Int</code>: year of the minimum technology share</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: financial
status that is affected by this technology share constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L492-L504"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.Transportation_speeds"
id="Main.TransComp.Transportation_speeds"
class="docstring-binding"><code>Main.TransComp.Transportation_speeds</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb30"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb30-1"><a href="#cb30-1" aria-hidden="true" tabindex="-1"></a>Transportation_speeds</span></code></pre></div>
<p>A 'Speed' describes the speed of a vehicle type in a specific
year.</p>
<p><strong>Fields</strong></p>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L755-L763"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.VehicleSubsidy"
id="Main.TransComp.VehicleSubsidy"
class="docstring-binding"><code>Main.TransComp.VehicleSubsidy</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb31"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb31-1"><a href="#cb31-1" aria-hidden="true" tabindex="-1"></a>VehicleSubsidy</span></code></pre></div>
<p>A 'VehicleSubsidy' describes the subsidy for a vehicle type in a
specific year.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the subsidy</li>
<li><code>name::String</code>: name of the subsidy</li>
<li><code>years::Array{Int,1}</code>: years in which the subsidy is
valid</li>
<li><code>techvehicle::TechVehicle</code>: vehicle type and
technology</li>
<li><code>subsidy::Float64</code>: subsidy in €</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L773-L784"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.VehicleType_share_max"
id="Main.TransComp.VehicleType_share_max"
class="docstring-binding"><code>Main.TransComp.VehicleType_share_max</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb32"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb32-1"><a href="#cb32-1" aria-hidden="true" tabindex="-1"></a>VehicleType_share_max</span></code></pre></div>
<p>Maximum vehicle type shares of a vehicle type independent of year,
i.e. over total horizon.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the vehicle type
share</li>
<li><code>vehicle_type::Vehicletype</code>: vehicle type</li>
<li><code>share::Float64</code>: maximum share of the vehicle type</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: array of
financial status that is affected by this vehicle type share
constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L598-L609"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.VehicleType_share_max_by_year"
id="Main.TransComp.VehicleType_share_max_by_year"
class="docstring-binding"><code>Main.TransComp.VehicleType_share_max_by_year</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb33"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb33-1"><a href="#cb33-1" aria-hidden="true" tabindex="-1"></a>VehicleType_share_max_by_year</span></code></pre></div>
<p>Maximum vehicle type shares of a vehicle type in a specific year.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the vehicle type
share</li>
<li><code>vehicle_type::Vehicletype</code>: vehicle type</li>
<li><code>share::Float64</code>: maximum share of the vehicle type</li>
<li><code>year::Int</code>: year of the maximum vehicle type share</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: financial
status that is affected by this vehicle type share constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L554-L566"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.VehicleType_share_min"
id="Main.TransComp.VehicleType_share_min"
class="docstring-binding"><code>Main.TransComp.VehicleType_share_min</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb34"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb34-1"><a href="#cb34-1" aria-hidden="true" tabindex="-1"></a>VehicleType_share_min</span></code></pre></div>
<p>Minimum vehicle type shares of a vehicle type independent of year,
i.e. over total horizon.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the vehicle type
share</li>
<li><code>vehicle_type::Vehicletype</code>: vehicle type</li>
<li><code>share::Float64</code>: minimum share of the vehicle type</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: array of
financial status that is affected by this vehicle type share
constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L618-L629"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.VehicleType_share_min_by_year"
id="Main.TransComp.VehicleType_share_min_by_year"
class="docstring-binding"><code>Main.TransComp.VehicleType_share_min_by_year</code></a>
— <span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb35"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb35-1"><a href="#cb35-1" aria-hidden="true" tabindex="-1"></a>VehicleType_share_min_by_year</span></code></pre></div>
<p>Minimum vehicle type shares of a vehicle type in a specific year.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the vehicle type
share</li>
<li><code>vehicle_type::Vehicletype</code>: vehicle type</li>
<li><code>share::Float64</code>: minimum share of the vehicle type</li>
<li><code>year::Int</code>: year of the minimum vehicle type share</li>
<li><code>financial_status::Array{FinancialStatus, 1}</code>: financial
status that is affected by this vehicle type share constraint</li>
<li><code>region_type::Array{Regiontype,1}</code>: array of region types
that are affected by this TechVehicle share constraint</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L576-L588"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a href="#Main.TransComp.Vehicletype"
id="Main.TransComp.Vehicletype"
class="docstring-binding"><code>Main.TransComp.Vehicletype</code></a> —
<span class="docstring-category">Type</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb36"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb36-1"><a href="#cb36-1" aria-hidden="true" tabindex="-1"></a>Vehicletype</span></code></pre></div>
<p>A 'Vehicletype' represents a type of vehicle that is used for
transportation. This may be for example, small passenger cars, buses, or
light-duty trucks.</p>
<p><strong>Fields</strong></p>
<ul>
<li><code>id::Int</code>: unique identifier of the vehicle type</li>
<li><code>name::String</code>: name of the vehicle type</li>
<li><code>mode::Mode</code>: mode of transport that the vehicle type is
used for</li>
<li><code>product::Product</code>: product that the vehicle type is used
for</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/structs.jl#L160-L170"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.base_define_variables-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.base_define_variables-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.base_define_variables</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb37"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb37-1"><a href="#cb37-1" aria-hidden="true" tabindex="-1"></a><span class="fu">base_define_variables</span>(model<span class="op">::</span><span class="dt">Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Defines the variables for the model.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L10-L18"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.check_folder_writable-Tuple%7BString%7D"
id="Main.TransComp.check_folder_writable-Tuple{String}"
class="docstring-binding"><code>Main.TransComp.check_folder_writable</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb38"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb38-1"><a href="#cb38-1" aria-hidden="true" tabindex="-1"></a><span class="fu">check_folder_writable</span>(folder_path<span class="op">::</span><span class="dt">String</span>)</span></code></pre></div>
<p>Check if the folder exists and can be written in.</p>
<p><strong>Arguments</strong></p>
<ul>
<li><code>folder_path::String</code>: The path to the folder.</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/checks.jl#L52-L59"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.check_input_file-Tuple%7BString%7D"
id="Main.TransComp.check_input_file-Tuple{String}"
class="docstring-binding"><code>Main.TransComp.check_input_file</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb39"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb39-1"><a href="#cb39-1" aria-hidden="true" tabindex="-1"></a><span class="fu">check_input_file</span>(path_to_source_file<span class="op">::</span><span class="dt">String</span>)</span></code></pre></div>
<p>Check if the input file exists and is a YAML file.</p>
<p><strong>Arguments</strong></p>
<ul>
<li><code>path_to_source_file::String</code>: The path to the input
file.</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/checks.jl#L5-L12"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.check_model_parametrization-Tuple%7BDict,%20Vector%7BString%7D%7D"
id="Main.TransComp.check_model_parametrization-Tuple{Dict, Vector{String}}"
class="docstring-binding"><code>Main.TransComp.check_model_parametrization</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb40"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb40-1"><a href="#cb40-1" aria-hidden="true" tabindex="-1"></a><span class="fu">check_model_parametrization</span>(data_dict<span class="op">::</span><span class="dt">Dict</span>, required_keys<span class="op">::</span><span class="dt">Vector{String}</span>)</span></code></pre></div>
<p>Check if the required keys are present in the model data.</p>
<p><strong>Arguments</strong></p>
<ul>
<li><code>data_dict::Dict</code>: The input data.</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li><code>Bool</code>: True if the required keys are present, false
otherwise.</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/checks.jl#L37-L47"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.check_required_keys-Tuple%7BDict,%20Vector%7BString%7D%7D"
id="Main.TransComp.check_required_keys-Tuple{Dict, Vector{String}}"
class="docstring-binding"><code>Main.TransComp.check_required_keys</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb41"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb41-1"><a href="#cb41-1" aria-hidden="true" tabindex="-1"></a><span class="fu">check_required_keys</span>(data_dict<span class="op">::</span><span class="dt">Dict</span>, required_keys<span class="op">::</span><span class="dt">Vector{String}</span>)</span></code></pre></div>
<p>Check if the required keys are present in the input data.</p>
<p><strong>Arguments</strong></p>
<ul>
<li><code>data_dict::Dict</code>: The input data.</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/checks.jl#L23-L30"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_demand_coverage-Tuple%7BJuMP.Model,%20Any%7D"
id="Main.TransComp.constraint_demand_coverage-Tuple{JuMP.Model, Any}"
class="docstring-binding"><code>Main.TransComp.constraint_demand_coverage</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb42"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb42-1"><a href="#cb42-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_demand_coverage</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Creates constraint for demand coverage.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L138-L146"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_emissions_by_mode-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_emissions_by_mode-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_emissions_by_mode</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb43"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb43-1"><a href="#cb43-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_emissions_by_mode</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Emissions given per mode for a specific year. Attention: This
constraint may be a source for infeasibility if mode or technology shift
cannot be achieved due to restrictions in the shift of modes (see
parametrization of parameters alpha<em>f and beta</em>f), or due to the
lifetimes of technologies as well as the lack of available low emission
or zero emission technologies.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L875-L883"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_fueling_demand-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_fueling_demand-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_fueling_demand</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb44"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb44-1"><a href="#cb44-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_fueling_demand</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Constraints for fueling demand at nodes and edges.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L633-L641"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_fueling_infrastructure-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_fueling_infrastructure-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_fueling_infrastructure</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb45"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb45-1"><a href="#cb45-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_vehicle_purchase</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Constraints for the sizing of fueling infrastructure at nodes and
edges.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L563-L571"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_market_share-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_market_share-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_market_share</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb46"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb46-1"><a href="#cb46-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_market_share</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>If share are given for specific vehicle types, this function will
create constraints for the newly bought vehicle share of vehicles the
modes.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L855-L863"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_max_mode_share-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_max_mode_share-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_max_mode_share</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb47"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb47-1"><a href="#cb47-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_max_mode_share</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>If share are given for specific modes, this function will create
constraints for the share of the modes. When this constraint is active,
it can be a source of infeasibility for the model as it may be not
possible to reach certain mode shares due to restrictions in the shift
of modes (see parametrization of parameters alpha<em>f and beta</em>f).
Or when multiple constraints for the mode share are active.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L815-L823"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_min_mode_share-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_min_mode_share-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_min_mode_share</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb48"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb48-1"><a href="#cb48-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_min_mode_share</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>If share are given for specific modes, this function will create
constraints for the share of the modes. When this constraint is active,
it can be a source of infeasibility for the model as it may be not
possible to reach certain mode shares due to restrictions in the shift
of modes (see parametrization of parameters alpha<em>f and beta</em>f).
Or when multiple constraints for the mode share are active.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L835-L843"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_mode_infrastructure-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_mode_infrastructure-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_mode_infrastructure</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<p>constraint<em>mode</em>infrastructure(model::JuMP.Model,
data_structures::Dict)</p>
<p>Constraints for sizing of mode infrastructure at nodes and edges.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L599-L607"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_mode_share-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_mode_share-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_mode_share</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb49"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb49-1"><a href="#cb49-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_mode_share</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>If share are given for specific modes, this function will create
constraints for the share of the modes. When this constraint is active,
it can be a source of infeasibility for the model as it may be not
possible to reach certain mode shares due to restrictions in the shift
of modes (see parametrization of parameters alpha<em>f and beta</em>f).
Especially also when constraints for minimum/maximum mode shares are
active.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L795-L803"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_mode_shift-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_mode_shift-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_mode_shift</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb50"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb50-1"><a href="#cb50-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_mode_shift</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Constraints for the rate of the mode shfit.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L730-L738"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_monetary_budget-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_monetary_budget-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_monetary_budget</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb51"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb51-1"><a href="#cb51-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_vehicle_purchase</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Creates constraints for monetary budget for vehicle purchase by
route.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L501-L509"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_vehicle_aging-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_vehicle_aging-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_vehicle_aging</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb52"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb52-1"><a href="#cb52-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_vehicle_aging</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Creates constraints for vehicle aging.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model with the constraints added</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L277-L288"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_vehicle_sizing-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_vehicle_sizing-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_vehicle_sizing</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb53"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb53-1"><a href="#cb53-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_vehicle_sizing</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Creates constraint for vehicle sizing.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L161-L169"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.constraint_vehicle_stock_shift-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.constraint_vehicle_stock_shift-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.constraint_vehicle_stock_shift</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb54"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb54-1"><a href="#cb54-1" aria-hidden="true" tabindex="-1"></a><span class="fu">constraint_vehicle_stock_shift</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Constraints for vehicle stock turnover.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L669-L677"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.create_emission_price_along_path-Tuple%7BPath,%20Dict%7D"
id="Main.TransComp.create_emission_price_along_path-Tuple{Path, Dict}"
class="docstring-binding"><code>Main.TransComp.create_emission_price_along_path</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb55"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb55-1"><a href="#cb55-1" aria-hidden="true" tabindex="-1"></a><span class="fu">create_emission_price_along_path</span>(k<span class="op">::</span><span class="dt">Path</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Calculating the carbon price along a given route based on the regions
that the path lies in. (currently simple calculation by averaging over
all geometric items among the path).</p>
<p><strong>Arguments</strong></p>
<ul>
<li>k::Path: path</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L569-L578"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.create_m_tv_pairs-Tuple%7BVector%7BTechVehicle%7D,%20Vector%7BMode%7D%7D"
id="Main.TransComp.create_m_tv_pairs-Tuple{Vector{TechVehicle}, Vector{Mode}}"
class="docstring-binding"><code>Main.TransComp.create_m_tv_pairs</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb56"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb56-1"><a href="#cb56-1" aria-hidden="true" tabindex="-1"></a><span class="fu">create_m_tv_pairs</span>(techvehicle_list<span class="op">::</span><span class="dt">Vector{TechVehicle}</span>, mode_list<span class="op">::</span><span class="dt">Vector{Mode}</span>)</span></code></pre></div>
<p>Creates a set of pairs of mode and techvehicle IDs.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>techvehicle_list::Vector{TechVehicle}: list of techvehicles</li>
<li>mode_list::Vector{Mode}: list of modes</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li>m<em>tv</em>pairs::Set: set of pairs of mode and techvehicle
IDs</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L363-L375"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.create_model-Tuple%7BAny,%20String%7D"
id="Main.TransComp.create_model-Tuple{Any, String}"
class="docstring-binding"><code>Main.TransComp.create_model</code></a> —
<span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb57"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb57-1"><a href="#cb57-1" aria-hidden="true" tabindex="-1"></a><span class="fu">create_model</span>(model<span class="op">::</span><span class="dt">JuMP.Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Definition of JuMP.model and adding of variables.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data and parsing of
the input parameters</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li>model::JuMP.Model: JuMP model with the variables added</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L526-L538"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.create_p_r_k_e_set-Tuple%7BVector%7BOdpair%7D%7D"
id="Main.TransComp.create_p_r_k_e_set-Tuple{Vector{Odpair}}"
class="docstring-binding"><code>Main.TransComp.create_p_r_k_e_set</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb58"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb58-1"><a href="#cb58-1" aria-hidden="true" tabindex="-1"></a><span class="fu">create_p_r_k_e_set</span>(odpairs<span class="op">::</span><span class="dt">Vector{Odpair}</span>)</span></code></pre></div>
<p>Creates a set of pairs of product, odpair, path, and element IDs.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>odpairs::Vector{Odpair}: list of odpairs</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li>p<em>r</em>k<em>e</em>pairs::Set: set of pairs of product, odpair,
path, and element IDs</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L453-L463"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.create_p_r_k_g_set-Tuple%7BVector%7BOdpair%7D%7D"
id="Main.TransComp.create_p_r_k_g_set-Tuple{Vector{Odpair}}"
class="docstring-binding"><code>Main.TransComp.create_p_r_k_g_set</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb59"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb59-1"><a href="#cb59-1" aria-hidden="true" tabindex="-1"></a><span class="fu">create_p_r_k_g_set</span>(odpairs<span class="op">::</span><span class="dt">Vector{Odpair}</span>)</span></code></pre></div>
<p>Creates a set of pairs of product, odpair, path, and element IDs.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>odpairs::Vector{Odpair}: list of odpairs</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li>p<em>r</em>k<em>g</em>pairs::Set: set of pairs of product, odpair,
path, and element IDs</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L472-L482"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.create_p_r_k_n_set-Tuple%7BVector%7BOdpair%7D%7D"
id="Main.TransComp.create_p_r_k_n_set-Tuple{Vector{Odpair}}"
class="docstring-binding"><code>Main.TransComp.create_p_r_k_n_set</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb60"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb60-1"><a href="#cb60-1" aria-hidden="true" tabindex="-1"></a><span class="fu">create_p_r_k_n_set</span>(odpairs<span class="op">::</span><span class="dt">Vector{Odpair}</span>)</span></code></pre></div>
<p>Creates a set of pairs of product, odpair, path, and element IDs.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>odpairs::Vector{Odpair}: list of odpairs</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li>p<em>r</em>k<em>n</em>pairs::Set: set of pairs of product, odpair,
path, and element IDs</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L491-L501"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.create_p_r_k_set-Tuple%7BVector%7BOdpair%7D%7D"
id="Main.TransComp.create_p_r_k_set-Tuple{Vector{Odpair}}"
class="docstring-binding"><code>Main.TransComp.create_p_r_k_set</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb61"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb61-1"><a href="#cb61-1" aria-hidden="true" tabindex="-1"></a><span class="fu">create_p_r_k_set</span>(odpairs<span class="op">::</span><span class="dt">Vector{Odpair}</span>)</span></code></pre></div>
<p>Creates a set of pairs of product, odpair, and path IDs.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>odpairs::Vector{Odpair}: list of odpairs</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li>p<em>r</em>k_pairs::Set: set of pairs of product, odpair, and path
IDs</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L437-L447"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.create_r_k_set-Tuple%7BVector%7BOdpair%7D%7D"
id="Main.TransComp.create_r_k_set-Tuple{Vector{Odpair}}"
class="docstring-binding"><code>Main.TransComp.create_r_k_set</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb62"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb62-1"><a href="#cb62-1" aria-hidden="true" tabindex="-1"></a><span class="fu">create_r_k_set</span>(odpairs<span class="op">::</span><span class="dt">Vector{Odpair}</span>)</span></code></pre></div>
<p>Creates a set of pairs of odpair and path IDs.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>odpairs::Vector{Odpair}: list of odpairs</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li>r<em>k</em>pairs::Set: set of pairs of odpair and path IDs</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L510-L520"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.create_tv_id_set-Tuple%7BVector%7BTechVehicle%7D,%20Vector%7BMode%7D%7D"
id="Main.TransComp.create_tv_id_set-Tuple{Vector{TechVehicle}, Vector{Mode}}"
class="docstring-binding"><code>Main.TransComp.create_tv_id_set</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb63"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb63-1"><a href="#cb63-1" aria-hidden="true" tabindex="-1"></a><span class="fu">create_tv_id_set</span>(techvehicle_list<span class="op">::</span><span class="dt">Vector{TechVehicle}</span>, mode_list<span class="op">::</span><span class="dt">Vector{Mode}</span>)</span></code></pre></div>
<p>Creates a list of techvehicle IDs.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>techvehicle_list::Vector{TechVehicle}: list of techvehicles</li>
<li>mode_list::Vector{Mode}: list of modes</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li>techvehicle<em>ids</em>2::Set: set of techvehicle IDs</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L395-L406"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.create_v_t_set-Tuple%7BVector%7BTechVehicle%7D%7D"
id="Main.TransComp.create_v_t_set-Tuple{Vector{TechVehicle}}"
class="docstring-binding"><code>Main.TransComp.create_v_t_set</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb64"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb64-1"><a href="#cb64-1" aria-hidden="true" tabindex="-1"></a><span class="fu">create_v_t_set</span>(techvehicle_list<span class="op">::</span><span class="dt">Vector{TechVehicle}</span>)</span></code></pre></div>
<p>Creates a set of pairs of techvehicle IDs.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>techvehicle_list::Vector{TechVehicle}: list of techvehicles</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li>t<em>v</em>pairs::Set: set of pairs of techvehicle IDs</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L421-L431"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.depreciation_factor-Tuple%7BAny,%20Any%7D"
id="Main.TransComp.depreciation_factor-Tuple{Any, Any}"
class="docstring-binding"><code>Main.TransComp.depreciation_factor</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb65"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb65-1"><a href="#cb65-1" aria-hidden="true" tabindex="-1"></a><span class="fu">depreciation_factor</span>(y, g)</span></code></pre></div>
<p>Calculate the depreciation factor for a vehicle based on its age.</p>
<p><strong>Arguments</strong></p>
<ul>
<li><code>y::Int</code>: The year of the vehicle.</li>
<li><code>g::Int</code>: The year the vehicle was purchased.</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li><code>Float64</code>: The depreciation factor.</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L546-L557"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.get_input_data-Tuple%7BString%7D"
id="Main.TransComp.get_input_data-Tuple{String}"
class="docstring-binding"><code>Main.TransComp.get_input_data</code></a>
— <span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb66"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb66-1"><a href="#cb66-1" aria-hidden="true" tabindex="-1"></a><span class="fu">get_input_data</span>(path_to_source_file<span class="op">::</span><span class="dt">String</span>)</span></code></pre></div>
<p>This function reads the input data and checks requirements for the
content of the file.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>path<em>to</em>source_file::String: path to the source file</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li>data_dict::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L6-L16"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.objective-Tuple%7BJuMP.Model,%20Dict%7D"
id="Main.TransComp.objective-Tuple{JuMP.Model, Dict}"
class="docstring-binding"><code>Main.TransComp.objective</code></a> —
<span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb67"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb67-1"><a href="#cb67-1" aria-hidden="true" tabindex="-1"></a><span class="fu">objective</span>(model<span class="op">::</span><span class="dt">Model</span>, data_structures<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Definition of the objective function for the optimization model.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::Model: JuMP model</li>
<li>data_structures::Dict: dictionary with the input data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/model_functions.jl#L905-L913"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.parse_data-Tuple%7BDict%7D"
id="Main.TransComp.parse_data-Tuple{Dict}"
class="docstring-binding"><code>Main.TransComp.parse_data</code></a> —
<span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb68"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb68-1"><a href="#cb68-1" aria-hidden="true" tabindex="-1"></a><span class="fu">parse_data</span>(data_dict<span class="op">::</span><span class="dt">Dict</span>)</span></code></pre></div>
<p>Parses the input data into the corresponding parameters in struct
format from structs.jl.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>data_dict::Dict: dictionary with the input data</li>
</ul>
<p><strong>Returns</strong></p>
<ul>
<li>data_structures::Dict: dictionary with the parsed data</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L25-L35"
class="docs-sourcelink" target="_blank">source</a>
</section>
<div>
<a href="javascript:;"
class="docstring-article-toggle-button fa-solid fa-chevron-down"
title="Collapse docstring"></a><a
href="#Main.TransComp.save_results-Tuple%7BJuMP.Model,%20String,%20String%7D"
id="Main.TransComp.save_results-Tuple{JuMP.Model, String, String}"
class="docstring-binding"><code>Main.TransComp.save_results</code></a> —
<span class="docstring-category">Method</span><span
class="is-flex-grow-1 docstring-article-toggle-button"
title="Collapse docstring"></span>
</div>
<section>
<div>
<div class="sourceCode" id="cb69"><pre
class="sourceCode julia hljs"><code class="sourceCode julia"><span id="cb69-1"><a href="#cb69-1" aria-hidden="true" tabindex="-1"></a><span class="fu">save_results</span>(model<span class="op">::</span><span class="dt">Model</span>, case_name<span class="op">::</span><span class="dt">String</span>)</span></code></pre></div>
<p>Saves the results of the optimization model to YAML files.</p>
<p><strong>Arguments</strong></p>
<ul>
<li>model::Model: JuMP model</li>
<li>case_name::String: name of the case</li>
<li>file<em>for</em>results::String: name of the file to save the
results</li>
</ul>
</div>
<a
href="https://github.com/antoniamgolab/iDesignRES_transcompmodel/blob/55ee1be4a1d32211e479d805003347cf3abce2bc/src/support_functions.jl#L593-L602"
class="docs-sourcelink" target="_blank">source</a>
</section>
<p>Powered by <a
href="https://github.com/JuliaDocs/Documenter.jl">Documenter.jl</a> and
the <a href="https://julialang.org/">Julia Programming Language</a>.</p>
</div>
<div id="documenter-settings" class="modal">
<div class="modal-background">

</div>
<div class="modal-card">
<div class="modal-card-head">
<p>Settings</p>
</div>
<section class="modal-card-body">
<p>Theme</p>
<div class="select">
Automatic
(OS)documenter-lightdocumenter-darkcatppuccin-lattecatppuccin-frappecatppuccin-macchiatocatppuccin-mocha
</div>
<hr />
<p>This document was generated with <a
href="https://github.com/JuliaDocs/Documenter.jl">Documenter.jl</a>
version 1.8.0 on <span class="colophon-date"
title="Thursday 28 November 2024 11:26">Thursday 28 November
2024</span>. Using Julia version 1.11.0.</p>
</section>
</div>
</div>
</div>
