"""
This file contains the functions that are used in the model but are not directly related to the optimization problem but are supporting functions for this.

"""

include("structs.jl")
include("checks.jl")
using YAML, JuMP, Gurobi, Printf
using MathOptInterface

"""
	get_input_data(path_to_source::String)

This function reads input data either from a single YAML file or from a directory
structure where each component is stored in a separate YAML file.

# Arguments
- path_to_source::String: path to either a YAML file or a directory containing component YAML files

# Returns
- data_dict::Dict: dictionary with the input data
"""
function get_input_data(path_to_source::String)
    # Check if input is a directory or file
    if isdir(path_to_source)
        # Read from directory structure (new modular format)
        @info "Reading input data from directory: $path_to_source"

        # Define expected component files
        component_files = [
            "Model", "TechVehicle", "GeographicElement", "FinancialStatus",
            "Vehicletype", "Mode", "Technology", "Speed", "Regiontype",
            "InitialModeInfr", "InitialFuelInfr", "Odpair", "Path",
            "Fuel", "FuelCost", "FuelingInfrTypes", "InitialVehicleStock",
            "NetworkConnectionCosts", "Product", "SpatialFlexibilityEdges",
            "MandatoryBreaks",
        ]

        # Initialize data dictionary
        data_dict = Dict{String, Any}()

        # Read each component file
        for component in component_files
            filepath = joinpath(path_to_source, "$component.yaml")

            if isfile(filepath)
                component_data = YAML.load_file(filepath)
                data_dict[component] = component_data
                @info "  Loaded $component.yaml"
            else
                @warn "  Missing file: $component.yaml"
            end
        end

        # Validate that required components were loaded
        required_components = ["Model", "GeographicElement", "Odpair", "Path"]
        for comp in required_components
            if !haskey(data_dict, comp)
                error("Required component missing: $comp")
            end
        end

        # Add alias: InitialFuelingInfr -> InitialFuelInfr (for backward compatibility)
        if haskey(data_dict, "InitialFuelInfr") && !haskey(data_dict, "InitialFuelingInfr")
            data_dict["InitialFuelingInfr"] = data_dict["InitialFuelInfr"]
        end

        return data_dict
    else
        # Read from single YAML file (legacy format)
        @info "Reading input data from file: $path_to_source"
        check_input_file(path_to_source)
        data_dict = YAML.load_file(path_to_source)
        return data_dict
    end
    # check_required_keys(data_dict, struct_names_base)
    # # checking completion of model parametrization 
    # check_model_parametrization(
    #     data_dict,
    #     ["Y", "y_init", "pre_y", "gamma", "budget_penalty_plus", "budget_penalty_minus"],
    # )
    # # check each of the required keys 
    # check_required_sub_keys(
    #     data_dict,
    #     ["id", "type", "name", "carbon_price", "from", "to", "length"],
    #     "GeographicElement",
    # )
    # check_required_sub_keys(
    #     data_dict,
    #     [
    #         "id",
    #         "name",
    #         "VoT",
    #         "monetary_budget_purchase",
    #         "monetary_budget_purchase_lb",
    #         "monetary_budget_purchase_ub",
    #     ],
    #     "FinancialStatus",
    # )
    # check_required_sub_keys(
    #     data_dict,
    #     [
    #         "id",
    #         "name",
    #         "quantify_by_vehs",
    #         "costs_per_ukm",
    #         "emission_factor",
    #         "infrastructure_expansion_costs",
    #         "infrastructure_om_costs",
    #         "waiting_time",
    #     ],
    #     "Mode",
    # )
    # check_required_sub_keys(data_dict, ["id", "name"], "Product")
    # check_required_sub_keys(data_dict, ["id", "name", "sequence", "length"], "Path")
    # check_required_sub_keys(
    #     data_dict,
    #     [
    #         "id",
    #         "name",
    #         "cost_per_kWh",
    #         "cost_per_kW",
    #         "emission_factor",
    #         "fueling_infrastructure_om_costs",
    #     ],
    #     "Fuel",
    # )
    # check_required_sub_keys(data_dict, ["id", "name", "fuel"], "Technology")
    # check_required_sub_keys(data_dict, ["id", "name", "mode"], "Vehicletype")
    # check_required_sub_keys(
    #     data_dict,
    #     ["id", "name", "costs_var", "costs_fix"],
    #     "Regiontype",
    # )
    # check_required_sub_keys(
    #     data_dict,
    #     [
    #         "id",
    #         "name",
    #         "vehicle_type",
    #         "technology",
    #         "capital_cost",
    #         "maintnanace_cost_annual",
    #         "maintnance_cost_distance",
    #         "W",
    #         "spec_cons",
    #         "Lifetime",
    #         "AnnualRange",
    #         "products",
    #         "tank_capacity",
    #         "peak_fueling",
    #         "fueling_time",
    #     ],
    #     "TechVehicle",
    # )
    # check_required_sub_keys(
    #     data_dict,
    #     ["id", "techvehicle", "year_of_purchase", "stock"],
    #     "InitialVehicleStock",
    # )
    # check_required_sub_keys(
    #     data_dict,
    #     ["id", "fuel", "allocation", "installed_kW"],
    #     "InitialFuelingInfr",
    # )
    # check_required_sub_keys(
    #     data_dict,
    #     ["id", "mode", "allocation", "installed_ukm"],
    #     "InitialModeInfr",
    # )
    # check_required_sub_keys(
    #     data_dict,
    #     [
    #         "id",
    #         "from",
    #         "to",
    #         "path_id",
    #         "F",
    #         "product",
    #         "vehicle_stock_init",
    #         "financial_status",
    #         "region_type",
    #     ],
    #     "Odpair",
    # )
    # check_required_sub_keys(
    #     data_dict,
    #     ["id", "region_type", "vehicle_type", "travel_speed"],
    #     "Speed",
    # )

    # check_validity_of_model_parametrization(data_dict)
    # check_uniquness_of_ids(data_dict, struct_names_base)

    # res = data_dict["Model"]["Y"] + data_dict["Model"]["y_init"]
    # @info "The optimization horizon is $(data_dict["Model"]["y_init"]) - $res."
    # first_gen = data_dict["Model"]["y_init"] - data_dict["Model"]["pre_y"]
    # @info "Vehicle generations since $first_gen are considered."

    # # checking formats
    # check_correct_formats_GeographicElement(data_dict, data_dict["Model"]["Y"])
    # check_correct_formats_FinancialStatus(data_dict)
    # check_correct_format_Mode(data_dict, data_dict["Model"]["Y"])
    # check_correct_format_Product(data_dict)
    # check_correct_format_Path(data_dict)
    # check_correct_format_Fuel(data_dict, data_dict["Model"]["Y"])
    # check_correct_format_Technology(data_dict)
    # check_correct_format_Vehicletype(data_dict)
    # check_correct_format_Regiontype(data_dict, data_dict["Model"]["Y"])
    # check_correct_format_TechVehicle(
    #     data_dict,
    #     data_dict["Model"]["Y"],
    #     data_dict["Model"]["Y"] + data_dict["Model"]["pre_y"],
    # )
    # check_correct_format_InitialVehicleStock(
    #     data_dict,
    #     data_dict["Model"]["y_init"],
    #     first_gen,
    # )
    # check_correct_format_InitialFuelingInfr(data_dict)
    # check_correct_format_InitialModeInfr(data_dict)
    # check_correct_format_Odpair(data_dict, data_dict["Model"]["Y"])
    # check_correct_format_Speed(data_dict)

    # # printing key information for the user 

    # @info "Input data checks successfully completed."

    return data_dict
end

"""
	parse_data(data_dict::Dict)

Parses the input data into the corresponding parameters in struct format from structs.jl.

# Arguments
- data_dict::Dict: dictionary with the input data

# Returns
- data_structures::Dict: dictionary with the parsed data
"""
function parse_data(data_dict::Dict)
    geographic_element_list = [
        GeographicElement(
            geographic_element["id"],
            geographic_element["type"],
            geographic_element["name"],
            geographic_element["carbon_price"],
            geographic_element["from"],
            geographic_element["to"],
            geographic_element["length"],
        ) for geographic_element ∈ data_dict["GeographicElement"]
    ]
    financial_status_list = [
        FinancialStatus(
            financial_stat["id"],
            financial_stat["name"],
            financial_stat["VoT"],
            financial_stat["monetary_budget_purchase"],
            financial_stat["monetary_budget_purchase_lb"],
            financial_stat["monetary_budget_purchase_ub"],
            financial_stat["monetary_budget_purchase_time_horizon"],
        ) for financial_stat ∈ data_dict["FinancialStatus"]
    ]
    mode_list = [
        Mode(
            mode["id"],
            mode["name"],
            mode["quantify_by_vehs"],
            mode["costs_per_ukm"],
            mode["emission_factor"],
            mode["infrastructure_expansion_costs"],
            mode["infrastructure_om_costs"],
            mode["waiting_time"],
        ) for mode ∈ data_dict["Mode"]
    ]

    product_list =
        [Product(product["id"], product["name"]) for product ∈ data_dict["Product"]]
    path_list = [
        Path(
            path["id"],
            path["name"],
            path["length"],
            [
                geographic_element_list[findfirst(
                    geo -> geo.id == el,
                    geographic_element_list,
                )] for el ∈ path["sequence"]
            ],
            get(path, "cumulative_distance", zeros(Float64, length(path["sequence"]))),
            get(path, "distance_from_previous", zeros(Float64, length(path["sequence"]))),
        ) for path ∈ data_dict["Path"]
    ]
    fuel_list = [
        Fuel(
            fuel["id"],
            fuel["name"],
            fuel["emission_factor"],
            fuel["cost_per_kWh"],
            fuel["cost_per_kW"],
            fuel["fueling_infrastructure_om_costs"],
        ) for fuel ∈ data_dict["Fuel"]
    ]
    if haskey(data_dict, "FuelCost")
        fuel_cost_list = [
            FuelCost(
                item["id"],
                geographic_element_list[findfirst(ge -> ge.id == item["location"], geographic_element_list)],
                fuel_list[findfirst(f -> f.name == item["fuel"], fuel_list)],
                item["cost_per_kWh"],
            ) for item ∈ data_dict["FuelCost"]
        ]
    else
        fuel_cost_list = []
    end

    # Parse NetworkConnectionCosts if present
    if haskey(data_dict, "NetworkConnectionCosts")
        network_connection_costs_list = [
            NetworkConnectionCosts(
                item["id"],
                geographic_element_list[findfirst(ge -> ge.id == item["location"], geographic_element_list)],
                item["network_cost_per_kW"],
            ) for item ∈ data_dict["NetworkConnectionCosts"]
        ]
        @info "Network connection costs data loaded: $(length(network_connection_costs_list)) entries"
    else
        network_connection_costs_list = []
    end

    # Parse MandatoryBreaks if present
    if haskey(data_dict, "MandatoryBreaks")
        mandatory_break_list = [
            MandatoryBreak(
                idx,  # Generate ID from index
                mb["path_id"],
                mb["path_length"],
                mb["total_driving_time"],
                mb["break_number"],
                mb["latest_node_idx"],
                mb["latest_geo_id"],
                mb["cumulative_distance"],
                mb["cumulative_driving_time"],
                mb["time_with_breaks"],
            ) for (idx, mb) ∈ enumerate(data_dict["MandatoryBreaks"])
        ]
        @info "Mandatory breaks data loaded: $(length(mandatory_break_list)) breaks defined"
    else
        mandatory_break_list = []
    end

    technology_list = [
        Technology(
            technology["id"],
            technology["name"],
            fuel_list[findfirst(f -> f.name == technology["fuel"], fuel_list)],
        ) for technology ∈ data_dict["Technology"]
    ]
    vehicle_type_list = [
        Vehicletype(
            vehicletype["id"],
            vehicletype["name"],
            mode_list[findfirst(m -> m.id == vehicletype["mode"], mode_list)],
            [product_list[findfirst(p -> p.name == vehicletype["product"], product_list)]],
        ) for vehicletype ∈ data_dict["Vehicletype"]
    ]
    regiontype_list = [
        Regiontype(
            regiontype["id"],
            regiontype["name"],
            regiontype["costs_var"],
            regiontype["costs_fix"],
        ) for regiontype ∈ data_dict["Regiontype"]
    ]
    techvehicle_list = [
        TechVehicle(
            techvehicle["id"],
            techvehicle["name"],
            vehicle_type_list[findfirst(
                v -> v.name == techvehicle["vehicle_type"],
                vehicle_type_list,
            )],
            technology_list[findfirst(
                t -> t.id == techvehicle["technology"],
                technology_list,
            )],
            techvehicle["capital_cost"],
            techvehicle["maintenance_cost_annual"],
            techvehicle["maintenance_cost_distance"],
            techvehicle["W"],
            techvehicle["spec_cons"],
            techvehicle["Lifetime"],
            techvehicle["AnnualRange"],
            [
                product_list[findfirst(p -> p.name == prod, product_list)] for
                prod ∈ techvehicle["products"]
            ],
            techvehicle["tank_capacity"],
            techvehicle["peak_fueling"],
            techvehicle["fueling_time"],
        ) for techvehicle ∈ data_dict["TechVehicle"]
    ]
    initvehiclestock_list = [
        InitialVehicleStock(
            initvehiclestock["id"],
            techvehicle_list[findfirst(
                tv -> tv.id == initvehiclestock["techvehicle"],
                techvehicle_list,
            )],
            initvehiclestock["year_of_purchase"],
            initvehiclestock["stock"],
        ) for initvehiclestock ∈ data_dict["InitialVehicleStock"]
    ]

    # PERFORMANCE OPTIMIZATION: Create fast O(1) lookup dictionary for vehicle stock
    # This dramatically speeds up OD-pair parsing when there are millions of vehicle stock entries
    @info "Creating vehicle stock lookup dictionary ($(length(initvehiclestock_list)) entries)..."
    initvehiclestock_dict = Dict(ivs.id => ivs for ivs ∈ initvehiclestock_list)
    @info "✓ Vehicle stock lookup dictionary created"

    initialmodeinfr_list = [
        InitialModeInfr(
            initialmodeinfr["id"],
            mode_list[findfirst(m -> m.id == initialmodeinfr["mode"], mode_list)],
            initialmodeinfr["allocation"],
            initialmodeinfr["installed_ukm"],
        ) for initialmodeinfr ∈ data_dict["InitialModeInfr"]
    ]

    # odpair_list = [
    #     Odpair(
    #         odpair["id"],
    #         geographic_element_list[findfirst(
    #             nodes -> nodes.id == odpair["from"],
    #             geographic_element_list,
    #         )],
    #         geographic_element_list[findfirst(
    #             nodes -> nodes.id == odpair["to"],
    #             geographic_element_list,
    #         )],
    #         [path_list[findfirst(p -> p.id == odpair["path_id"], path_list)]],
    #         odpair["F"],
    #         product_list[findfirst(p -> p.name == odpair["product"], product_list)],
    #         [
    #             initvehiclestock_list[findfirst(
    #                 ivs -> ivs.id == vsi,
    #                 initvehiclestock_list,
    #             )] for vsi ∈ odpair["vehicle_stock_init"]
    #         ],
    #         financial_status_list[findfirst(
    #             fs -> fs.name == odpair["financial_status"],
    #             financial_status_list,
    #         )],
    #         regiontype_list[findfirst(
    #             rt -> rt.name == odpair["region_type"],
    #             regiontype_list,
    #         )],
    #         odpair["travel_time_budget"]
    #     ) for odpair ∈ data_dict["Odpair"]
    # ]
    odpair_list = []
    for odpair ∈ data_dict["Odpair"]
        if "purpose" in keys(odpair)
            purpose = odpair["purpose"]
        else
            purpose = "none"
        end
        
        push!(odpair_list, Odpair(odpair["id"],
            geographic_element_list[findfirst(
                nodes -> nodes.id == odpair["from"],
                geographic_element_list,
            )],
            geographic_element_list[findfirst(
                nodes -> nodes.id == odpair["to"],
                geographic_element_list,
            )],
            [path_list[findfirst(p -> p.id == odpair["path_id"], path_list)]],
            odpair["F"],
            product_list[findfirst(p -> p.name == odpair["product"], product_list)],
            [initvehiclestock_dict[vsi] for vsi ∈ odpair["vehicle_stock_init"]],
            financial_status_list[findfirst(
                fs -> fs.name == odpair["financial_status"],
                financial_status_list,
            )],
            regiontype_list[findfirst(
                rt -> rt.name == odpair["region_type"],
                regiontype_list,
            )],
            odpair["travel_time_budget"],
            purpose
        ))
    end
    odpair_list = Vector{Odpair}(odpair_list)

    
    # odpair_list = odpair_list[1:40]
    println("Number of Odpairs: ", length(odpair_list))
    speed_list = [
        Speed(
            speed["id"],
            regiontype_list[findfirst(
                rt -> rt.name == speed["region_type"],
                regiontype_list,
            )],
            vehicle_type_list[findfirst(
                vt -> vt.name == speed["vehicle_type"],
                vehicle_type_list,
            )],
            speed["travel_speed"],
        ) for speed ∈ data_dict["Speed"]
    ]

    if haskey(data_dict, "Market_shares")
        market_share_list = [
            Market_shares(
                market_share["id"],
                techvehicle_list[findfirst(tv -> tv.id == market_share["type"], techvehicle_list)],
                market_share["market_share"],
                market_share["year"],
            ) for market_share ∈ data_dict["Market_shares"]
        ]
        @info "Market shares are defined"
    else
        market_share_list = []
    end
    if haskey(data_dict["Model"], "investment_period")
        investment_period = data_dict["Model"]["investment_period"]
    else
        investment_period = 1
    end

    if haskey(data_dict, "Emission_constraints_by_mode")
        emission_constraint_by_mode_list = [
            EmissionConstraintByYear(
                emission_constraint["id"],
                mode_list[findfirst(m -> m.id == emission_constraint["mode"], mode_list)],
                emission_constraint["year"],
                emission_constraint["emission_constraint"],
            ) for emission_constraint ∈ data_dict["Emission_constraints_by_year"]
        ]
        @info "Emissions are defined by year"

    else
        emission_constraint_by_mode_list = []
    end

    if haskey(data_dict, "TripRatio")
        tripratio_list = [
            TripRatio(
                tripratio["id"],
                geographic_element_list[findfirst(
                    ge -> ge.id == tripratio["origin"],
                    geographic_element_list,
                )],
                tripratio["purpose"],
                tripratio["share"],
            ) for tripratio ∈ data_dict["TripRatio"]
        ]
    else
        tripratio_list = []
    end

    if haskey(data_dict, "Mode_shares")
        mode_shares_list = [
            ModeShare(
                mode_share["id"],
                mode_list[findfirst(m -> m.id == mode_share["mode"], mode_list)],
                mode_share["share"],
                mode_share["year"],
                [
                    regiontype_list[findfirst(rt -> rt.id == rt_id, regiontype_list)]
                    for rt_id ∈ mode_share["regiontype_list"]
                ],
            ) for mode_share ∈ data_dict["Mode_shares"]
        ]
        @info "Mode shares are defined by year"

    else
        mode_shares_list = []
    end

    # Spatial flexibility edges disabled - not being used
    spatial_flexibility_edges_list = []

    if haskey(data_dict, "Mode_share_max_by_year")
        max_mode_shares_list = [
            ModeShare(
                mode_share["id"],
                mode_list[findfirst(m -> m.id == mode_share["mode"], mode_list)],
                mode_share["share"],
                mode_share["year"],
                [
                    regiontype_list[findfirst(rt -> rt.id == rt_id, regiontype_list)]
                    for rt_id ∈ mode_share["regiontype_list"]
                ],
            ) for mode_share ∈ data_dict["Mode_shares"]
        ]
        @info "Max Mode shares are defined by year"

    else
        max_mode_shares_list = []
    end

    if haskey(data_dict, "Mode_share_min_by_year")
        min_mode_shares_list = [
            ModeShare(
                mode_share["id"],
                mode_list[findfirst(m -> m.id == mode_share["mode"], mode_list)],
                mode_share["share"],
                mode_share["year"],
                [
                    regiontype_list[findfirst(rt -> rt.id == rt_id, regiontype_list)]
                    for rt_id ∈ mode_share["regiontype_list"]
                ],
            ) for mode_share ∈ data_dict["Mode_shares"]
        ]
        @info "Min Mode shares are defined by year"

    else
        min_mode_shares_list = []
    end

    if haskey(data_dict, "VehicleSubsidy")
        vehicle_subsidy_list = [
            VehicleSubsidy(
                vehicle_subsidy["id"],
                vehicle_subsidy["name"],
                vehicle_subsidy["years"],
                techvehicle_list[findfirst(
                    tv -> tv.id == vehicle_subsidy["techvehicle"],
                    techvehicle_list,
                )],
                vehicle_subsidy["subsidy"],
            ) for vehicle_subsidy ∈ data_dict["VehicleSubsidy"]
        ]
    else
        vehicle_subsidy_list = []
    end

    # ===== PERFORMANCE OPTIMIZATION: Build lookup dictionaries for O(1) access =====
    @info "Building lookup dictionaries for fast O(1) access..."
    geo_element_dict = Dict(geo.id => geo for geo in geographic_element_list)
    path_dict = Dict(p.id => p for p in path_list)
    mode_dict = Dict(m.id => m for m in mode_list)
    tech_dict = Dict(t.id => t for t in technology_list)
    fuel_dict = Dict(f.id => f for f in fuel_list)
    vehicle_dict = Dict(v.id => v for v in vehicle_type_list)
    techvehicle_dict = Dict(tv.id => tv for tv in techvehicle_list)
    regiontype_dict = Dict(rt.id => rt for rt in regiontype_list)
    financial_status_dict = Dict(fs.id => fs for fs in financial_status_list)
    product_dict = Dict(p.id => p for p in product_list)

    # Build name-based dictionaries for lookups by name
    geo_element_by_name = Dict(geo.name => geo for geo in geographic_element_list)
    fuel_by_name = Dict(f.name => f for f in fuel_list)
    mode_by_name = Dict(m.name => m for m in mode_list)
    vehicle_by_name = Dict(v.name => v for v in vehicle_type_list)
    product_by_name = Dict(p.name => p for p in product_list)
    regiontype_by_name = Dict(rt.name => rt for rt in regiontype_list)
    financial_status_by_name = Dict(fs.name => fs for fs in financial_status_list)

    @info "✓ Lookup dictionaries created for $(length(geo_element_dict)) geo elements, $(length(path_dict)) paths, $(length(mode_dict)) modes, $(length(tech_dict)) technologies, $(length(fuel_dict)) fuels"
    # =================================================================================







    if haskey(data_dict, "SupplyType")
        supplytype_list = [
            SupplyType(
                item["id"],
                fuel_list[findfirst(
                    f -> f.name == item["fuel"],
                    fuel_list,
                )],
                geographic_element_list[findfirst(
                    ge -> ge.name == item["location"],
                    geographic_element_list,
                )],
                item["install_costs"],
                item["om_costs"],
            ) for item ∈ data_dict["SupplyType"]
        ]
    else
        supplytype_list = []
    end

    if haskey(data_dict, "InitialSupplyInfr")
        initialsupplyinfr_list = [
            EmissionConstraintByYear(
                item["id"],
                fuel_list[findfirst(
                    f -> f.name == item["fuel"],
                    fuel_list,
                )],
                supplytype_list[findfirst(
                    st -> st.id == item["supplytype"],
                    supplytype_list,
                )],
                geographic_element_list[findfirst(
                    ge -> ge.name == item["location"],
                    geographic_element_list,
                )],
                item["installed_kW"],
            ) for item ∈ data_dict["InitialSupplyInfr"]
        ]
    else
        initialsupplyinfr_list = []
    end

    if haskey(data_dict, "FuelingInfrastructureExpansion")
        fueling_infr_expansion_list = [
            FuelingInfrastructureExpansion(
                item["id"],
                fuel_list[findfirst(
                    f -> f.name == item["fuel"],
                    fuel_list,
                )],
                geographic_element_list[findfirst(
                    ge -> ge.name == item["location"],
                    geographic_element_list,
                )],
                item["alpha"],
                item["beta"],
            ) for item ∈ data_dict["FuelingInfrastructureExpansion"]
        ]
    else
        fueling_infr_expansion_list = []
    end

    if haskey(data_dict, "Tripratio")
        tripratio_list = [
            TripRatio(
                item["id"],
                geographic_element_list[findfirst(
                    ge -> ge.name == item["from"],
                    geographic_element_list,
                )],
                item["purpose"],
                item["share"],
            ) for item ∈ data_dict["Tripratio"]
        ]
    else
        tripratio_list = []
    end

    if haskey(data_dict, "FuelingInfrTypes")
        fueling_infr_types = [
            FuelingInfrTypes(
                item["id"],
                fuel_list[findfirst(
                    f -> f.name == item["fuel"],
                    fuel_list,
                )],
                item["fueling_type"],
                item["fueling_power"],
                item["additional_fueling_time"],
                item["max_occupancy_rate_veh_per_year"],
                item["by_route"],
                item["track_detour_time"],
                item["gamma"],
                item["cost_per_kW"],
                item["cost_per_kWh_network"],
                item["om_costs"],
            ) for item ∈ data_dict["FuelingInfrTypes"]
        ]
    else
        fueling_infr_types = []
    end
    if haskey(data_dict, "InitDetourTime")
        if haskey(data_dict, "FuelingInfrTypes")
            init_detour_times_list = [
                InitDetourTime(
                    init_detour_time["id"],
                    fuel_list[findfirst(f -> f.name == init_detour_time["fuel"], fuel_list)],
                    geographic_element_list[findfirst(
                        ge -> ge.name == init_detour_time["location"],
                        geographic_element_list,
                    )],
                    init_detour_time["detour_time"],
                    fueling_infr_types[findfirst(
                        f -> f.fueling_type == init_detour_time["fuel_infr_type"],
                        fueling_infr_types,
                    )],
                ) for init_detour_time ∈ data_dict["InitDetourTime"]
            ]
        else
            init_detour_times_list = [
                InitDetourTime(
                    init_detour_time["id"],
                    fuel_list[findfirst(f -> f.name == init_detour_time["fuel"], fuel_list)],
                    geographic_element_list[findfirst(
                        ge -> ge.name == init_detour_time["location"],
                        geographic_element_list,
                    )],
                    init_detour_time["detour_time"],
                    FuelingInfrTypes(0, fuel_list[1], "none", [0.0], false, 0.0, false, false, [0.0], [0.0], [0.0], [0.0]),
                ) for init_detour_time ∈ data_dict["InitDetourTime"]
            ]
        end
    else
        init_detour_times_list = []
    end
    if haskey(data_dict, "FuelingInfrTypes")
        initalfuelinginfr_list = [
            InitialFuelingInfr(
                initalfuelinginfr["id"],
                fuel_list[findfirst(f -> f.name == initalfuelinginfr["fuel"], fuel_list)],
                initalfuelinginfr["allocation"],
                initalfuelinginfr["installed_kW"],
                fueling_infr_types[findfirst(
                    f -> f.fueling_type == initalfuelinginfr["type"],
                    fueling_infr_types,
                )],
                initalfuelinginfr["by_income_class"],
                financial_status_list[findfirst(
                    fs -> fs.name == initalfuelinginfr["income_class"],
                    financial_status_list,
                )],
            ) for initalfuelinginfr ∈ data_dict["InitialFuelingInfr"]
        ]
    else
        initalfuelinginfr_list = [
            InitialFuelingInfr(
                initalfuelinginfr["id"],
                fuel_list[findfirst(f -> f.name == initalfuelinginfr["fuel"], fuel_list)],
                initalfuelinginfr["allocation"],
                initalfuelinginfr["installed_kW"],
                FuelingInfrTypes(0, fuel_list[1], "none", [0.0], false, 0.0, false, false, [0.0], [0.0], [0.0], [0.0]),
                initalfuelinginfr["by_income_class"],
                financial_status_list[findfirst(
                    fs -> fs.name == initalfuelinginfr["income_class"],
                    financial_status_list,
                )],
            ) for initalfuelinginfr ∈ data_dict["InitialFuelingInfr"]
        ]
    end
    if haskey(data_dict, "MaximumFuelingCapacityByTypeByYear")
        maximum_fueling_capacity_by_fuel_by_year = [
            MaximumFuelingCapacityByTypeByYear(
                item["id"],
                item["year"],
                geographic_element_list[findfirst(
                    ge -> ge.name == item["location"],
                    geographic_element_list,
                )],
                item["maximum_capacity"],
                fueling_infr_types[findfirst(
                    f -> f.fueling_type == item["fueling_type"],
                    fueling_infr_types,
                )],
                item["by_income_class"],
                financial_status_list[findfirst(
                    fs -> fs.name == item["income_class"],
                    financial_status_list,
                )],
            ) for item ∈ data_dict["MaximumFuelingCapacityByTypeByYear"]
        ]
    else
        maximum_fueling_capacity_by_fuel_by_year = []
    end
    if haskey(data_dict, "MaximumFuelingCapacityByType")
        maximum_fueling_capacity_by_fuel = [
            MaximumFuelingCapacityByFuel(
                item["id"],
                fuel_list[findfirst(
                    f -> f.name == item["fuel"],
                    fuel_list,
                )],
                geographic_element_list[findfirst(
                    ge -> ge.name == item["location"],
                    geographic_element_list,
                )],
                financial_status_list[findfirst(
                    fs -> fs.name == item["income_class"],
                    financial_status_list,
                )],
                item["maximum_fueling_capacity"],
                fueling_infr_types[findfirst(
                    f -> f.fueling_type == item["type"],
                    fueling_infr_types,
                )],
                item["by_income_class"]
            ) for item ∈ data_dict["MaximumFuelingCapacityByType"]
        ]
    else
        maximum_fueling_capacity_by_fuel = []
    
    end

    if haskey(data_dict, "DetourTimeReduction")
        @info "has detour reduction specified"
        if !haskey(data_dict, "FuelingInfrTypes")
            detour_time_reduction_list = [
                DetourTimeReduction(
                    detour_time_reduction["id"],
                    fuel_list[findfirst(
                        f -> f.name == detour_time_reduction["fuel"],
                        fuel_list,
                    )],
                    geographic_element_list[findfirst(
                        ge -> ge.name == detour_time_reduction["location"],
                        geographic_element_list,
                    )],
                    detour_time_reduction["reduction_id"],
                    detour_time_reduction["detour_time_reduction"],
                    detour_time_reduction["fueling_cap_lb"],
                    detour_time_reduction["fueling_cap_ub"],
                    FuelingInfrTypes(0, fuel_list[1], "none", [0.0], false, 0.0, false, false, [0.0], [0.0], [0.0], [0.0]),
                ) for detour_time_reduction ∈ data_dict["DetourTimeReduction"]
            ]
        else
            detour_time_reduction_list = [
                DetourTimeReduction(
                    detour_time_reduction["id"],
                    fuel_list[findfirst(
                        f -> f.name == detour_time_reduction["fuel"],
                        fuel_list,
                    )],
                    geographic_element_list[findfirst(
                        ge -> ge.name == detour_time_reduction["location"],
                        geographic_element_list,
                    )],
                    detour_time_reduction["reduction_id"],
                    detour_time_reduction["detour_time_reduction"],
                    detour_time_reduction["fueling_cap_lb"],
                    detour_time_reduction["fueling_cap_ub"],
                    fueling_infr_types[findfirst(
                        f -> f.fueling_type == detour_time_reduction["fueling_type"],
                        fueling_infr_types,
                    )],
                ) for detour_time_reduction ∈ data_dict["DetourTimeReduction"]
            ]
        end
        
    else
        detour_time_reduction_list = []
    end

    # TODO: extend here the list of possible data_dict structures
    data_structures = Dict(
        "Y" => data_dict["Model"]["Y"],
        "y_init" => data_dict["Model"]["y_init"],
        "pre_y" => data_dict["Model"]["pre_y"],
        "gamma" => data_dict["Model"]["gamma"],
        "discount_rate" => data_dict["Model"]["discount_rate"],
        "budget_penalty_plus" => data_dict["Model"]["budget_penalty_plus"],
        "budget_penalty_minus" => data_dict["Model"]["budget_penalty_minus"],
        "budget_penalty_yearly_plus" => data_dict["Model"]["budget_penalty_yearly_plus"],
        "budget_penalty_yearly_minus" => data_dict["Model"]["budget_penalty_yearly_minus"],
        "financial_status_list" => financial_status_list,
        "mode_list" => mode_list,
        "product_list" => product_list,
        "path_list" => path_list,
        "fuel_list" => fuel_list,
        "fuel_cost_list" => fuel_cost_list,
        "network_connection_costs_list" => network_connection_costs_list,
        "technology_list" => technology_list,
        "vehicletype_list" => vehicle_type_list,
        "regiontype_list" => regiontype_list,
        "techvehicle_list" => techvehicle_list,
        "initvehiclestock_list" => initvehiclestock_list,
        "odpair_list" => odpair_list,
        "speed_list" => speed_list,
        "market_share_list" => market_share_list,
        "emission_constraints_by_mode_list" => emission_constraint_by_mode_list,
        "mode_shares_list" => mode_shares_list,
        "max_mode_shares_list" => max_mode_shares_list,
        "min_mode_shares_list" => min_mode_shares_list,
        "initialfuelinginfr_list" => initalfuelinginfr_list,
        "initialmodeinfr_list" => initialmodeinfr_list,
        "initialsupplyinfr_list" => initialsupplyinfr_list,
        "vehicle_subsidy_list" => vehicle_subsidy_list,
        "geographic_element_list" => geographic_element_list,
        "init_detour_times_list" => init_detour_times_list,
        "detour_time_reduction_list" => detour_time_reduction_list,
        "supplytype_list" => supplytype_list,
        "investment_period"=> investment_period,
        "fueling_infr_expansion_list" => fueling_infr_expansion_list,
        "tripratio_list" => tripratio_list,
        "fueling_infr_types_list" => fueling_infr_types,
        "maximum_fueling_capacity_by_fuel_list" => maximum_fueling_capacity_by_fuel,
        "maximum_fueling_capacity_by_fuel_by_year_list" => maximum_fueling_capacity_by_fuel_by_year,
        "spatial_flexibility_edges_list" => spatial_flexibility_edges_list,
        "mandatory_break_list" => mandatory_break_list,
    )

    # Read pre_age_sell parameter from Model (defaults to true for backward compatibility)
    if haskey(data_dict["Model"], "pre_age_sell")
        pre_age_sell = data_dict["Model"]["pre_age_sell"]
        @info "Pre-age sell parameter set to: $pre_age_sell"
    else
        pre_age_sell = true
        @info "Pre-age sell parameter not specified, defaulting to: true (allows early retirement)"
    end
    data_structures["pre_age_sell"] = pre_age_sell

    for key ∈ keys(default_data)
        if haskey(data_dict["Model"], key)
            data_structures[key] = data_dict["Model"][key]
        else
            data_structures[key] = default_data[key]
        end
    end

    data_structures["G"] = data_dict["Model"]["pre_y"] + data_dict["Model"]["Y"]
    data_structures["g_init"] = data_dict["Model"]["y_init"] - data_dict["Model"]["pre_y"]
    data_structures["Y_end"] = data_dict["Model"]["y_init"] + data_dict["Model"]["Y"] - 1

    # Add lookup dictionaries for fast O(1) access throughout the model
    data_structures["geo_element_dict"] = geo_element_dict
    data_structures["path_dict"] = path_dict
    data_structures["mode_dict"] = mode_dict
    data_structures["tech_dict"] = tech_dict
    data_structures["fuel_dict"] = fuel_dict
    data_structures["vehicle_dict"] = vehicle_dict
    data_structures["techvehicle_dict"] = techvehicle_dict
    data_structures["regiontype_dict"] = regiontype_dict
    data_structures["financial_status_dict"] = financial_status_dict
    data_structures["product_dict"] = product_dict
    data_structures["geo_element_by_name"] = geo_element_by_name
    data_structures["fuel_by_name"] = fuel_by_name
    data_structures["mode_by_name"] = mode_by_name
    data_structures["vehicle_by_name"] = vehicle_by_name
    data_structures["product_by_name"] = product_by_name
    data_structures["regiontype_by_name"] = regiontype_by_name
    data_structures["financial_status_by_name"] = financial_status_by_name
    @info "✓ Lookup dictionaries added to data_structures for model-wide O(1) access"

    return data_structures
end
"""
    generate_exact_length_subsets(start_year::Int, end_year::Int, delta_y::Int)

Generates a list of subsets of years with a fixed length.

# Arguments
- `start_year::Int`: The first year.
- `end_year::Int`: The last year.
- `delta_y::Int`: The length of the subsets.
"""
function generate_exact_length_subsets(start_year::Int, end_year::Int, delta_y::Int)
    all_years = start_year:end_year
    subsets = []

    for i ∈ 1:(length(all_years)-delta_y+1)
        push!(subsets, collect(all_years[i:(i+delta_y-1)]))
    end

    return subsets
end

"""
    create_blocks(start_year::Int, end_year::Int, delta_y::Int)

Generates a list of subsets of years with a fixed length.

# Arguments
- `start_year::Int`: The first year.
- `end_year::Int`: The last year.
- `delta_y::Int`: The length of the subsets.
"""
function create_blocks(y_init::Int, Y_end::Int; block_size::Int=2)
    """
    Create non-overlapping blocks within a spending horizon in Julia.
    Last block may be shorter if remaining years < block_size.

    Args:
        y_init: Starting year of horizon
        Y_end: Ending year of horizon (inclusive)
        block_size: Number of years per block (default 2)

    Returns:
        Array of tuples, each containing the years in the block
    """
    blocks = []
    year = y_init
    while year <= Y_end
        block_end = min(year + block_size - 1, Y_end)
        push!(blocks, tuple(year:block_end...))
        year += block_size
    end
    return blocks
end

"""
	create_m_tv_pairs(techvehicle_list::Vector{TechVehicle}, mode_list::Vector{Mode})

Creates a set of pairs of mode and techvehicle IDs.

# Arguments
- techvehicle_list::Vector{TechVehicle}: list of techvehicles
- mode_list::Vector{Mode}: list of modes

# Returns
- m_tv_pairs::Set: set of pairs of mode and techvehicle IDs

"""
function create_m_tv_pairs(techvehicle_list::Vector{TechVehicle}, mode_list::Vector{Mode})
    m_tv_pairs = Set((tv.vehicle_type.mode.id, tv.id) for tv ∈ techvehicle_list)
    techvehicle_ids = [tv.id for tv ∈ techvehicle_list]
    global counter_additional_vehs = length(techvehicle_list)
    for m ∈ mode_list
        for v ∈ techvehicle_list
            if v.vehicle_type.mode.id == m.id
                push!(m_tv_pairs, (m.id, v.id))
            end
        end
        if !m.quantify_by_vehs
            push!(m_tv_pairs, (m.id, counter_additional_vehs + 1))
            push!(techvehicle_ids, counter_additional_vehs + 1)
            global counter_additional_vehs += 1
        end
    end
    return m_tv_pairs
end


"""
    create_f_l_set(fuel_infr_list::Vector{FuelingInfrTypes})

Creates a set of pairs of fuel and fueling infrastructure IDs.

# Arguments
- fuel_infr_list::Vector{FuelingInfrTypes}: list of fueling infrastructures
- fuel_list::Vector{Fuel}: list of fuels

# Returns
- f_l_pairs::Set: set of pairs of fuel and fueling infrastructure IDs
"""
function create_f_l_set(fuel_infr_list::Vector{FuelingInfrTypes})
    f_l_pairs = Set()
    for item ∈ fuel_infr_list
        push!(f_l_pairs, (item.fuel.id, item.id))
    end
    return f_l_pairs
end
"""
	create_tv_id_set(techvehicle_list::Vector{TechVehicle}, mode_list::Vector{Mode})

Creates a list of techvehicle IDs.

# Arguments
- techvehicle_list::Vector{TechVehicle}: list of techvehicles
- mode_list::Vector{Mode}: list of modes

# Returns
- techvehicle_ids_2::Set: set of techvehicle IDs
"""
function create_tv_id_set(techvehicle_list_2::Vector{TechVehicle}, mode_list::Vector{Mode})
    m_tv_pairs = Set((tv.vehicle_type.mode.id, tv.id) for tv ∈ techvehicle_list_2)
    techvehicle_ids_2 = Set([tv.id for tv ∈ techvehicle_list_2])
    global counter_additional_vehs_2 = length(techvehicle_list_2)

    for m ∈ mode_list
        if !m.quantify_by_vehs
            push!(techvehicle_ids_2, counter_additional_vehs_2 + 1)
            global counter_additional_vehs_2 += 1
        end
    end
    return techvehicle_ids_2
end

"""
	create_v_t_set(techvehicle_list::Vector{TechVehicle})

Creates a set of pairs of techvehicle IDs.

# Arguments
- techvehicle_list::Vector{TechVehicle}: list of techvehicles

# Returns
- t_v_pairs::Set: set of pairs of techvehicle IDs
"""
function create_v_t_set(techvehicle_list::Vector{TechVehicle})
    t_v_pairs = Set((tv.id, tv.id) for tv ∈ techvehicle_list)
    return t_v_pairs
end

"""
	create_p_r_k_set(odpairs::Vector{Odpair})

Creates a set of pairs of product, odpair, and path IDs.

# Arguments
- odpairs::Vector{Odpair}: list of odpairs

# Returns
- p_r_k_pairs::Set: set of pairs of product, odpair, and path IDs
"""
function create_p_r_k_set(odpairs::Vector{Odpair})
    p_r_k_pairs = Set((r.product.id, r.id, k.id) for r ∈ odpairs for k ∈ r.paths)
    return p_r_k_pairs
end

"""
	create_p_r_k_e_set(odpairs::Vector{Odpair})

Creates a set of pairs of product, odpair, path, and element IDs.

# Arguments
- odpairs::Vector{Odpair}: list of odpairs

# Returns
- p_r_k_e_pairs::Set: set of pairs of product, odpair, path, and element IDs
"""
function create_p_r_k_e_set(odpairs::Vector{Odpair})
    p_r_k_e_pairs = Set(
        (r.product.id, r.id, k.id, el) for r ∈ odpairs for k ∈ r.paths for
        el ∈ k.sequence if el.type == "edge"
    )
    return p_r_k_e_pairs
end

"""
	create_p_r_k_g_set(odpairs::Vector{Odpair})

Creates a set of pairs of product, odpair, path, and element IDs.

# Arguments
- odpairs::Vector{Odpair}: list of odpairs

# Returns
- p_r_k_g_pairs::Set: set of pairs of product, odpair, path, and element IDs
"""
function create_p_r_k_g_set(odpairs::Vector{Odpair})
    p_r_k_g_pairs = Set(
        (r.product.id, r.id, k.id, el.id) for r ∈ odpairs for k ∈ r.paths for
        el ∈ k.sequence
    )
    return p_r_k_g_pairs
end

"""
	create_p_r_k_n_set(odpairs::Vector{Odpair})

Creates a set of pairs of product, odpair, path, and element IDs.

# Arguments
- odpairs::Vector{Odpair}: list of odpairs

# Returns
- p_r_k_n_pairs::Set: set of pairs of product, odpair, path, and element IDs
"""
function create_p_r_k_n_set(odpairs::Vector{Odpair})
    p_r_k_n_pairs = Set(
        (r.product.id, r.id, k.id, el) for r ∈ odpairs for k ∈ r.paths for
        el ∈ k.sequence if el.type == "node"
    )
    return p_r_k_n_pairs
end

"""
	create_r_k_set(odpairs::Vector{Odpair})

Creates a set of pairs of odpair and path IDs.

# Arguments
- odpairs::Vector{Odpair}: list of odpairs

# Returns
- r_k_pairs::Set: set of pairs of odpair and path IDs
"""
function create_r_k_set(odpairs::Vector{Odpair})
    r_k_pairs = Set((r.id, k.id) for r ∈ odpairs for k ∈ r.paths)
    return r_k_pairs
end

"""
    create_model(data_structures, case_name::String; include_vars::Vector{String}=String[])

Create a JuMP optimization model with conditionally defined variables.

# Arguments
- data_structures: Dictionary containing model input data
- case_name: Name of the case study
- include_vars: Vector of variable groups to include. Options:
    - "f" - Flow/transport variables
    - "h" - Vehicle stock variables (h, h_exist, h_plus, h_minus)
    - "s" - Energy consumption variables
    - "n_fueling" - Fueling event variables
    - "detour_time" - Detour time variables
    - "budget_penalties" - Budget penalty variables
    - "q_mode_infr" - Mode infrastructure expansion variables
    - "q_fuel_infr" - Fuel infrastructure expansion variables
    - "q_supply_infr" - Supply infrastructure expansion variables
  If empty, all variables are created (default behavior)

# Returns
- model: JuMP model with conditionally defined variables
- data_structures: Updated data structures dictionary
"""
function create_model(data_structures, case_name::String; include_vars::Vector{String}=String[])
    model = Model(Gurobi.Optimizer)
    base_define_variables(model, data_structures, include_vars=include_vars)
    return model, data_structures
end

function create_geo_i_pairs(
    geographic_element_list::Vector{GeographicElement},
    detour_time_reduction_list::Vector{DetourTimeReduction},
)
    geo_i_pairs = Set(
        (geo.id, i.reduction_id) for geo ∈ geographic_element_list for
        i ∈ detour_time_reduction_list[findall(
            item -> item.location == geo.id,
            detour_time_reduction_list,
        )]
    )
    return geo_i_pairs
end

function create_geo_i_f_pairs(
    geographic_element_list::Vector{GeographicElement},
    detour_time_reduction_list::Vector{DetourTimeReduction},
)
    geo_i_f_pairs = Set()
    for item ∈ detour_time_reduction_list
        push!(geo_i_f_pairs, (item.location.id, item.reduction_id, item.fuel.id))
    end
    return geo_i_f_pairs
end


function create_geo_i_f_l_pairs(
    detour_time_reduction_list::Vector{DetourTimeReduction},
)
    geo_i_f_l_pairs = Set()
    for item ∈ detour_time_reduction_list
        push!(geo_i_f_l_pairs, (item.location.id, item.reduction_id, item.fuel.id, item.fueling_type.id))
    end
    return geo_i_f_l_pairs
end


"""
    depreciation_factor(y, g)

Calculate the depreciation factor for a vehicle based on its age.

# Arguments
- `y::Int`: The year of the vehicle.
- `g::Int`: The year the vehicle was purchased.

# Returns
- `Float64`: The depreciation factor.
"""
function depreciation_factor(y, g)
    age = y - g  # Lifetime of the vehicle
    if age == 0
        return 1.0  # No depreciation in the first year
    elseif age == 1
        return 0.75  # 25% depreciation in the second year
    else
        return max(0, 0.75 - 0.05 * (age - 1))  # Decrease by 5% for each subsequent year
    end
end

"""
    create_emission_price_along_path(k::Path, y::Int64, data_structures::Dict)

Calculating the carbon price along a given route based on the regions that the path lies in.
(currently simple calculation by averaging over all geometric items among the path).

# Arguments
- k::Path: path
- data_structures::Dict: dictionary with the input data 
"""
function create_emission_price_along_path(k::Path, y::Int64, data_structures::Dict)
    n = length(k.sequence)
    geographic_element_list = data_structures["geographic_element_list"]
    global total_carbon_price = 0.0
    for el ∈ k.sequence
        current_carbon_price =
            geographic_element_list[findfirst(
                e -> e.id == el.id,
                geographic_element_list,
            )].carbon_price
        # println(current_carbon_price, total_carbon_price)
        global total_carbon_price = total_carbon_price + current_carbon_price[y]
    end
    average_carbon_price = total_carbon_price / n
    # println(average_carbon_price)
    return average_carbon_price
end

function create_q_by_route(data_structures::Dict)
    maximum_fueling_capacity_by_fuel_list = data_structures["fueling_infr_types_list"]
    q_by_route = Set()
    q_not_by_route = Set()
    for item ∈ maximum_fueling_capacity_by_fuel_list
        if item.by_route
            push!(q_by_route, (item.fuel.id, item.id))
        else 
            push!(q_not_by_route, (item.fuel.id, item.id))
        end 
    end
    return q_by_route, q_not_by_route
end 

function create_detour_time_reduction_for_relevant(fuelinfr_type_list)
    detour_time_for_fueling_type = Set()
    for item ∈ fuelinfr_type_list
        if item.track_detour_time
            push!(detour_time_for_fueling_type, (item.fuel.id, item.id))
        end
    end
    return detour_time_for_fueling_type
end

function extract_geoelements_from_paths(path_list)
    """
    Extract all unique geographic elements that appear in any path sequence.
    This is used to limit iterations in the objective function to only relevant geographic elements.
    """
    geo_elements_in_paths = Set()
    for path in path_list
        for geo_elem in path.sequence
            push!(geo_elements_in_paths, geo_elem)
        end
    end
    return collect(geo_elements_in_paths)
end

function stringify_keys(dict::Dict)
    return Dict(
        string(k) => (v isa Float64 ? @sprintf("%.6f", v) : string(v)) for (k, v) ∈ dict
    )
end

"""
	save_results(model::Model, case_name::String)

Saves the results of the optimization model to YAML files.
# Arguments
- model::Model: JuMP model
- case_name::String: name of the case
- file_for_results::String: name of the file to save the results
- data_structures::Dict: dictionary with the input data
"""
function save_results(
    model::Model,
    case::String,
    data_structures::Dict,
    write_to_file::Bool = true,
    folder_for_results::String = "results",
    folder_for_logs::String = "logs",
)
    check_folder_writable(folder_for_results)

    @info "Saving results for defined variables only..."

    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    technologies = data_structures["technology_list"]
    fuel_list = data_structures["fuel_list"]
    mode_list = data_structures["mode_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    tech_vehicle_ids = data_structures["techvehicle_ids"]
    g_init = data_structures["g_init"]
    investment_period = data_structures["investment_period"]
    if data_structures["detour_time_reduction_list"] != []
        geo_i_f = data_structures["geo_i_f_pairs"]
    end

    # ------------------------
    # Collect variables
    # ------------------------

    f_dict = Dict()
    if haskey(object_dictionary(model), :f)
        @info "  Saving f (flow/transport) variable..."
        for y ∈ y_init:Y_end, (p, r, k) ∈ p_r_k_pairs, mv ∈ m_tv_pairs, g ∈ g_init:y
            val = value(model[:f][y, (p, r, k), mv, g])
            if !isnan(val) && val > 1e-6
                f_dict[(y, (p, r, k), mv, g)] = val
            end
        end
    end

    s_dict = Dict()
    if haskey(object_dictionary(model), :s)
        @info "  Saving s (energy consumption) variable..."
        if data_structures["fueling_infr_types_list"] != []
            f_l_pairs = data_structures["f_l_pairs"]
            for y ∈ y_init:Y_end, (p, r, k, g) ∈ p_r_k_g_pairs, tv_id ∈ tech_vehicle_ids, f_l in f_l_pairs, gen ∈ g_init:y
                val = value(model[:s][y, (p, r, k, g), tv_id, f_l, gen])
                if !isnan(val) && val > 1e-6
                    s_dict[(y, (p, r, k, g), tv_id, f_l, gen)] = val
                end
            end
        else
            for y ∈ y_init:Y_end, (p, r, k, g) ∈ p_r_k_g_pairs, tv_id ∈ tech_vehicle_ids, gen ∈ g_init:y
                val = value(model[:s][y, (p, r, k, g), tv_id, gen])
                if !isnan(val) && val > 1e-6
                    s_dict[(y, (p, r, k, g), tv_id, gen)] = val
                end
            end
        end
    end

    h_dict = Dict()
    if haskey(object_dictionary(model), :h)
        @info "  Saving h (vehicle stock) variable..."
        for y ∈ y_init:Y_end, r ∈ odpairs, tv ∈ techvehicles, g ∈ g_init:y
            val = value(model[:h][y, r.id, tv.id, g])
            if !isnan(val) && val > 1e-6
                h_dict[(y, r.id, tv.id, g)] = val
            end
        end
    end

    h_exist_dict = Dict()
    if haskey(object_dictionary(model), :h_exist)
        @info "  Saving h_exist variable..."
        for y ∈ y_init:Y_end, r ∈ odpairs, tv ∈ techvehicles, g ∈ g_init:y
            val = value(model[:h_exist][y, r.id, tv.id, g])
            if !isnan(val) && val > 1e-6
                h_exist_dict[(y, r.id, tv.id, g)] = val
            end
        end
    end

    h_plus_dict = Dict()
    if haskey(object_dictionary(model), :h_plus)
        @info "  Saving h_plus variable..."
        for y ∈ y_init:Y_end, r ∈ odpairs, tv ∈ techvehicles, g ∈ g_init:y
            val = value(model[:h_plus][y, r.id, tv.id, g])
            if !isnan(val) && val > 1e-6
                h_plus_dict[(y, r.id, tv.id, g)] = val
            end
        end
    end

    h_minus_dict = Dict()
    if haskey(object_dictionary(model), :h_minus)
        @info "  Saving h_minus variable..."
        for y ∈ y_init:Y_end, r ∈ odpairs, tv ∈ techvehicles, g ∈ g_init:y
            val = value(model[:h_minus][y, r.id, tv.id, g])
            if !isnan(val) && val > 1e-6
                h_minus_dict[(y, r.id, tv.id, g)] = val
            end
        end
    end

    q_fuel_infr_plus_dict = Dict()
    if haskey(object_dictionary(model), :q_fuel_infr_plus)
        @info "  Saving q_fuel_infr_plus (fuel infrastructure) variable..."
        saved_count = 0
        total_count = 0
        if haskey(data_structures, "f_l_not_by_route")
            # Complex mode: with fueling infrastructure types (only for non-by-route types)
            f_l_not_by_route = data_structures["f_l_not_by_route"]
            @info "    Using f_l_not_by_route set with $(length(f_l_not_by_route)) pairs"
            for y ∈ y_init:investment_period:Y_end, f_l ∈ f_l_not_by_route, geo ∈ geographic_element_list
                total_count += 1
                val = value(model[:q_fuel_infr_plus][y, f_l, geo.id])
                if !isnan(val) && val > 1e-6  # Only save non-zero values
                    q_fuel_infr_plus_dict[(y, f_l, geo.id)] = val
                    saved_count += 1
                end
            end
        elseif haskey(data_structures, "f_l_pairs")
            # Complex mode but no by_route split: use all f_l_pairs
            f_l_pairs = data_structures["f_l_pairs"]
            @info "    Using f_l_pairs set with $(length(f_l_pairs)) pairs"
            for y ∈ y_init:investment_period:Y_end, f_l ∈ f_l_pairs, geo ∈ geographic_element_list
                total_count += 1
                val = value(model[:q_fuel_infr_plus][y, f_l, geo.id])
                if !isnan(val) && val > 1e-6  # Only save non-zero values
                    q_fuel_infr_plus_dict[(y, f_l, geo.id)] = val
                    saved_count += 1
                end
            end
        else
            # Simple mode: without fueling infrastructure types
            @info "    Using simple mode (fuel_list)"
            for y ∈ y_init:investment_period:Y_end, f ∈ fuel_list, geo ∈ geographic_element_list
                total_count += 1
                val = value(model[:q_fuel_infr_plus][y, f.id, geo.id])
                if !isnan(val) && val > 1e-6  # Only save non-zero values
                    q_fuel_infr_plus_dict[(y, f.id, geo.id)] = val
                    saved_count += 1
                end
            end
        end
        @info "    Saved $saved_count non-zero values out of $total_count total variables"
    end

    q_mode_infr_plus_dict = Dict()
    if haskey(object_dictionary(model), :q_mode_infr_plus)
        @info "  Saving q_mode_infr_plus (mode infrastructure) variable..."
        for y ∈ y_init:investment_period:Y_end, m ∈ mode_list, geo ∈ geographic_element_list
            val = value(model[:q_mode_infr_plus][y, m.id, geo.id])
            if !isnan(val) && val > 1e-6
                q_mode_infr_plus_dict[(y, m.id, geo.id)] = val
            end
        end
    end

    # NEW: Save soc (state of charge) variable
    soc_dict = Dict()
    if haskey(object_dictionary(model), :soc)
        @info "  Saving soc (state of charge) variable..."
        if data_structures["fueling_infr_types_list"] != []
            f_l_pairs = data_structures["f_l_pairs"]
            for y ∈ y_init:Y_end, (p, r, k, g) ∈ p_r_k_g_pairs, tv_id ∈ tech_vehicle_ids, f_l in f_l_pairs, gen ∈ g_init:y
                val = value(model[:soc][y, (p, r, k, g), tv_id, f_l, gen])
                if !isnan(val) && val > 1e-6
                    soc_dict[(y, (p, r, k, g), tv_id, f_l, gen)] = val
                end
            end
        end
    end

    # NEW: Save q_fuel_abs variable
    q_fuel_abs_dict = Dict()
    if haskey(object_dictionary(model), :q_fuel_abs)
        @info "  Saving q_fuel_abs variable..."
        if data_structures["fueling_infr_types_list"] != []
            f_l_not_by_route = [f_l for f_l in data_structures["f_l_pairs"] if !data_structures["fueling_infr_types_dict"][f_l].by_route]
            for y ∈ y_init:investment_period:Y_end, (p, r, k, g) ∈ p_r_k_g_pairs, f_l in f_l_not_by_route, gen ∈ g_init:y
                val = value(model[:q_fuel_abs][y, (p, r, k, g), f_l, gen])
                if !isnan(val) && val > 1e-6
                    q_fuel_abs_dict[(y, (p, r, k, g), f_l, gen)] = val
                end
            end
        end
    end

    travel_time_dict = Dict()
    if haskey(object_dictionary(model), :travel_time)
        @info "  Saving travel_time variable..."
        if data_structures["fueling_infr_types_list"] != []
            f_l_pairs = data_structures["f_l_pairs"]
            for y ∈ y_init:Y_end, (p, r, k, g) ∈ p_r_k_g_pairs, tv_id ∈ tech_vehicle_ids, f_l in f_l_pairs, gen ∈ g_init:y
                val = value(model[:travel_time][y, (p, r, k, g), tv_id, f_l, gen])
                if !isnan(val) && val > 1e-6
                    travel_time_dict[(y, (p, r, k, g), tv_id, f_l, gen)] = val
                end
            end
        else
            for y ∈ y_init:Y_end, (p, r, k, g) ∈ p_r_k_g_pairs, tv_id ∈ tech_vehicle_ids, gen ∈ g_init:y
                val = value(model[:travel_time][y, (p, r, k, g), tv_id, gen])
                if !isnan(val) && val > 1e-6
                    travel_time_dict[(y, (p, r, k, g), tv_id, gen)] = val
                end
            end
        end
    end

    # NEW: Save extra_break_time slack variable
    extra_break_time_dict = Dict()
    if haskey(object_dictionary(model), :extra_break_time)
        @info "  Saving extra_break_time variable..."
        if data_structures["fueling_infr_types_list"] != []
            f_l_pairs = data_structures["f_l_pairs"]
            for y ∈ y_init:Y_end, (p, r, k, g) ∈ p_r_k_g_pairs, tv_id ∈ tech_vehicle_ids, f_l in f_l_pairs, gen ∈ g_init:y
                val = value(model[:extra_break_time][y, (p, r, k, g), tv_id, f_l, gen])
                if !isnan(val) && val > 1e-6  # Only save non-zero slack values
                    extra_break_time_dict[(y, (p, r, k, g), tv_id, f_l, gen)] = val
                end
            end
        end
    end

    # ------------------------
    # Prepare dicts for saving
    # ------------------------

    f_dict_str = stringify_keys(f_dict)
    h_dict_str = stringify_keys(h_dict)
    h_exist_dict_str = stringify_keys(h_exist_dict)
    h_plus_dict_str = stringify_keys(h_plus_dict)
    h_minus_dict_str = stringify_keys(h_minus_dict)
    s_dict_str = stringify_keys(s_dict)
    q_fuel_infr_plus_dict_str = stringify_keys(q_fuel_infr_plus_dict)
    q_mode_infr_plus_dict_str = stringify_keys(q_mode_infr_plus_dict)
    soc_dict_str = stringify_keys(soc_dict)
    q_fuel_abs_dict_str = stringify_keys(q_fuel_abs_dict)
    travel_time_dict_str = stringify_keys(travel_time_dict)
    extra_break_time_dict_str = stringify_keys(extra_break_time_dict)
    # ------------------------
    # Save to YAML only if not empty
    # ------------------------

    if write_to_file
        if !isempty(f_dict_str)
            YAML.write_file(joinpath(folder_for_results, case * "_f_dict.yaml"), f_dict_str)
            @info "f_dict.yaml written successfully"
        end

        if !isempty(h_dict_str)
            YAML.write_file(joinpath(folder_for_results, case * "_h_dict.yaml"), h_dict_str)
            @info "h_dict.yaml written successfully"
        end

        if !isempty(h_exist_dict_str)
            YAML.write_file(joinpath(folder_for_results, case * "_h_exist_dict.yaml"), h_exist_dict_str)
            @info "h_exist_dict.yaml written successfully"
        end

        if !isempty(h_plus_dict_str)
            YAML.write_file(joinpath(folder_for_results, case * "_h_plus_dict.yaml"), h_plus_dict_str)
            @info "h_plus_dict.yaml written successfully"
        end

        if !isempty(h_minus_dict_str)
            YAML.write_file(joinpath(folder_for_results, case * "_h_minus_dict.yaml"), h_minus_dict_str)
            @info "h_minus_dict.yaml written successfully"
        end

        if !isempty(s_dict_str)
            YAML.write_file(joinpath(folder_for_results, case * "_s_dict.yaml"), s_dict_str)
            @info "s.yaml written successfully"
        end

        if !isempty(q_fuel_infr_plus_dict_str)
            YAML.write_file(joinpath(folder_for_results, case * "_q_fuel_infr_plus_dict.yaml"), q_fuel_infr_plus_dict_str)
            @info "q_fuel_infr_plus.yaml written successfully"
        end

        if !isempty(q_mode_infr_plus_dict_str)
            YAML.write_file(joinpath(folder_for_results, case * "_q_mode_infr_plus_dict.yaml"), q_mode_infr_plus_dict_str)
            @info "q_mode_infr_plus_dict.yaml written successfully"
        end

        if !isempty(soc_dict_str)
            YAML.write_file(joinpath(folder_for_results, case * "_soc_dict.yaml"), soc_dict_str)
            @info "soc_dict.yaml written successfully"
        end

        if !isempty(q_fuel_abs_dict_str)
            YAML.write_file(joinpath(folder_for_results, case * "_q_fuel_abs_dict.yaml"), q_fuel_abs_dict_str)
            @info "q_fuel_abs_dict.yaml written successfully"
        end

        if !isempty(travel_time_dict_str)
            YAML.write_file(joinpath(folder_for_results, case * "_travel_time_dict.yaml"), travel_time_dict_str)
            @info "travel_time_dict.yaml written successfully"
        end

        if !isempty(extra_break_time_dict_str)
            YAML.write_file(joinpath(folder_for_results, case * "_extra_break_time_dict.yaml"), extra_break_time_dict_str)
            @info "extra_break_time_dict.yaml written successfully"
        end
    end

    # Save constraint summary information
    @info "Writing constraint summary file..."
    constraint_summary_path = joinpath(folder_for_results, case * "_constraints_applied.txt")

    open(constraint_summary_path, "w") do io
        println(io, "="^80)
        println(io, "CONSTRAINT SUMMARY FOR MODEL RUN: $case")
        println(io, "="^80)
        println(io, "Generated: $(Dates.format(Dates.now(), "yyyy-mm-dd HH:MM:SS"))")
        println(io, "")

        # Model statistics
        println(io, "MODEL STATISTICS:")
        println(io, "  Total constraints: $(num_constraints(model; count_variable_in_set_constraints=false))")
        println(io, "  Total variables: $(num_variables(model))")
        println(io, "")

        # List all constraint types in the model
        println(io, "CONSTRAINTS APPLIED:")
        println(io, "")

        constraint_type_list = list_of_constraint_types(model)

        for (idx, (func_type, set_type)) in enumerate(constraint_type_list)
            # Count constraints of this type
            count = num_constraints(model, func_type, set_type)

            # Format the constraint type name
            type_name = "$(func_type) in $(set_type)"

            println(io, "  $idx. $type_name")
            println(io, "     Number of constraints: $count")
            println(io, "")
        end

        # Variables present in the model
        println(io, "="^80)
        println(io, "DECISION VARIABLES:")
        println(io, "")

        var_idx = 1
        for var_symbol in [:f, :h, :h_plus, :h_minus, :h_exist, :s, :q_fuel_infr_plus,
                          :q_mode_infr_plus, :soc, :q_fuel_abs, :detour_time, :n_fueling,
                          :budget_penalties]
            if haskey(object_dictionary(model), var_symbol)
                var = model[var_symbol]
                println(io, "  $var_idx. $(var_symbol)")
                println(io, "     Number of variables: $(length(var))")
                println(io, "")
                var_idx += 1
            end
        end

        # Model parameters
        println(io, "="^80)
        println(io, "MODEL PARAMETERS:")
        println(io, "  Time horizon: $(data_structures["y_init"]) - $(data_structures["Y_end"])")
        println(io, "  Initial year: $(data_structures["y_init"])")
        println(io, "  Final year: $(data_structures["Y_end"])")
        println(io, "  Investment period: $(data_structures["investment_period"]) years")
        println(io, "  Number of OD pairs: $(length(data_structures["odpair_list"]))")
        println(io, "  Number of paths: $(length(data_structures["path_list"]))")
        println(io, "  Number of geographic elements: $(length(data_structures["geographic_element_list"]))")
        println(io, "  Number of tech vehicles: $(length(data_structures["techvehicle_list"]))")

        if haskey(data_structures, "spatial_flexibility_edges_list")
            println(io, "  Spatial flexibility entries: $(length(data_structures["spatial_flexibility_edges_list"]))")
        end

        println(io, "")
        println(io, "="^80)
        println(io, "END OF CONSTRAINT SUMMARY")
        println(io, "="^80)
    end

    @info "✓ Constraint summary written to: $(constraint_summary_path)"

    return f_dict,
           h_dict,
           h_exist_dict,
           h_plus_dict,
           h_minus_dict,
           s_dict,
           q_fuel_infr_plus_dict,
           q_mode_infr_plus_dict,
           soc_dict,
           q_fuel_abs_dict
end


function depreciated_inv_costs(inv_costs, age)
    global original_costs = inv_costs
    for y in 1:age
        if y == 1
            global original_costs = original_costs * 0.65
        else
            global original_costs = original_costs - 100 
        end
    end
    return original_costs
end

"""
    Function to disaggregate the total electricity load into hourly load profiles for a specific fuel type.

    # Arguments
    - `model::JuMP.Model`: The optimization model.
    - `data_structures::Dict`: The data structures.
    - `fuel_id::Int`: The fuel ID.
    - `year::Int`: The year.

    # Returns
    - `yearly_load_dict::Dict`: Demand distribution among different vehicle types.
"""

function disagreggate(model::JuMP.Model, data_structures::Dict, fuel_id::Int=2, year::Int=2020)
    # creating hourly load profile for each year
    y_init = data_structures["y_init"]
    g_init = data_structures["g_init"]
    Y_end = data_structures["Y_end"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    techvehicle_list = data_structures["techvehicle_list"]
    technology_list = data_structures["technology_list"]

    s = value.(model[:s])
    h = value.(model[:h])
    yearly_load_dict = Dict()
    y = year 
    for tv in techvehicle_list

        if tv.technology.fuel.id == fuel_id
            total_h = sum(h[y, r.id, tv.id, g] for r in data_structures["odpair_list"] for g in data_structures["g_init"]:y)
            
            # i need for each year the total electricity load
            total_load = sum(s[y, p_r_k_g, tv.id] for p_r_k_g in p_r_k_g_pairs for tv in techvehicle_list if tv.technology.fuel.id == fuel_id)
    
            # i need amount of vehicles driving this year  
            load_dict_h_g = Dict()

            for g in data_structures["g_init"]:y
                h_g = sum(h[y, r.id, tv.id, g] for r in data_structures["odpair_list"])
                share_load = h_g / total_h
                if share_load > 0
                    load_dict_h_g[g] = (h_g, share_load * total_load, tv.tank_capacity[g-g_init+1])
                    
                end
            end
            yearly_load_dict[tv.id] = load_dict_h_g

        end
    end

    return yearly_load_dict

end


function find_large_rhs(model::JuMP.Model)
    # Thresholds (adjust as needed)
    LOW_THRESHOLD = 1e-2
    HIGH_THRESHOLD = 1e3

    for (func_type, set_type) in list_of_constraint_types(model)
        if func_type == MOI.ScalarAffineFunction{Float64} &&
        (set_type == MOI.LessThan || set_type == MOI.GreaterThan || set_type == MOI.EqualTo)

            for con_ref in all_constraints(model, func_type, set_type; include_variable_in_set_constraints=false)
                # Extract RHS based on the set type
                rhs = nothing
                if set_type == MOI.LessThan
                    rhs = JuMP.constraint_set(con_ref).upper
                elseif set_type == MOI.GreaterThan
                    rhs = JuMP.constraint_set(con_ref).lower
                elseif set_type == MOI.EqualTo
                    rhs = JuMP.constraint_set(con_ref).value
                end

                if rhs !== nothing && (abs(rhs) < LOW_THRESHOLD || abs(rhs) > HIGH_THRESHOLD)
                    println("Constraint $(name(con_ref)) has extreme RHS: $rhs")
                end
            end
        end
    end
end

import Pkg
Pkg.add("ProgressMeter")
import ProgressMeter


"""
    apply_start_values_from_model(source_model::Model, target_model::Model; exclude=Set())

Copies solution values from `source_model` to `target_model` as start values,
excluding any variable names in the `exclude` set.

Arguments:
- `exclude`: a `Set{String}` of variable base names to skip (e.g., Set(["y", "z"]))

Returns: nothing; modifies `target_model` in place.
"""


function apply_start_values_fast_skip_progress(source_model::Model, target_model::Model; exclude=Set{String}(), copy_continuous=true)
    var_dict = Dict{String, VariableRef}(name(v) => v for v in all_variables(target_model))

    vars = all_variables(source_model)
    p = Progress(length(vars), desc="Applying start values")

    for var in vars
        varname = name(var)
        basename = split(varname, "[")[1]

        if basename in exclude
            next!(p)
            continue
        end

        val = value(var)
        if isnothing(val)
            next!(p)
            continue
        end

        if !copy_continuous && is_continuous(var)
            next!(p)
            continue
        end

        if haskey(var_dict, varname)
            set_start_value(var_dict[varname], val)
        end

        next!(p)
    end
end


# Helper: find variable by full name (e.g., "x[3]")
function find_variable_by_name(model::Model, fullname::String)
    for var in all_variables(model)
        if name(var) == fullname
            return var
        end
    end
    return nothing
end
# Helper functions
function has_variable(model::Model, var_name::String)
    return any(v -> v.name == var_name, all_variables(model))
end

function set_binary_start_x_c_from_relaxed!(
    model::JuMP.Model,
    relaxed_model::JuMP.Model,
    data_structures::Dict,
    q_fuel_infr_plus_sym::Symbol,
    x_c_sym::Symbol;
    ε::Float64 = 1e-5  # small tolerance to prevent tight-bound violations
)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    investment_period = data_structures["investment_period"]
    investment_years = collect(y_init:investment_period:Y_end)

    geographic_element_list = data_structures["geographic_element_list"]
    initialfuelinginfr_list = data_structures["initialfuelinginfr_list"]
    detour_time_reduction_list = data_structures["detour_time_reduction_list"]
    fueling_infr_types_list = data_structures["fueling_infr_types_list"]

    geo_i_f_pairs = data_structures["geo_i_f_pairs"]
    geo_i_f_l_pairs = data_structures["geo_i_f_l"]
    pairs_to_use = isempty(fueling_infr_types_list) ? geo_i_f_pairs : geo_i_f_l_pairs

    for geo_i_f in pairs_to_use
        # Find matching detour item
        match_idx = findfirst(item ->
            item.reduction_id == geo_i_f[2] &&
            item.location.id == geo_i_f[1] &&
            (isempty(fueling_infr_types_list) || item.fueling_type.id == geo_i_f[4]),
            detour_time_reduction_list
        )
        match_idx === nothing && continue
        match = detour_time_reduction_list[match_idx]

        lb = match.fueling_cap_lb * 1e-3 + 1e-4  # kW to MW with safety offset
        ub = match.fueling_cap_ub * 1e-3
        fuel = match.fuel
        f_l = isempty(fueling_infr_types_list) ? fuel.id : (fuel.id, match.fueling_type.id)

        for y in investment_years
            # Get initial installed kW
            installed_kW = begin
                idx = findfirst(i ->
                    i.fuel.id == (isempty(fueling_infr_types_list) ? f_l : f_l[1]) &&
                    (isempty(fueling_infr_types_list) || i.type.id == f_l[2]) &&
                    i.allocation == geo_i_f[1],
                    initialfuelinginfr_list
                )
                idx !== nothing ? initialfuelinginfr_list[idx].installed_kW : 0.0
            end

            # Compute total kW added from relaxed solution
            added_kW = sum(
                begin
                    val = try
                        value(relaxed_model[q_fuel_infr_plus_sym][y0, f_l, geo_i_f[1]])
                    catch
                        NaN
                    end
                    isnan(val) ? 0.0 : val
                end for y0 in y_init:investment_period:y
            )

            total_MW = (installed_kW + added_kW) / 1000

            # Only set x_c to 1 if we're clearly inside the feasible bounds
            x_c_val = (total_MW >= lb + ε && total_MW <= ub - ε) ? 1 : 0

            try
                set_start_value(model[x_c_sym][y, geo_i_f], x_c_val)
                println("Set start value for $x_c_sym[$y, $geo_i_f] = $x_c_val (total = $(round(total_MW, digits=5)) MW)")
            catch err
                @warn "Couldn't set start value for x_c[$y, $geo_i_f]: $err"
            end
        end
    end
end

