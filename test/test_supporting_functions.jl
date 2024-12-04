using Test

@testset "Test check_input_file" begin
    # Case 1: File exists and is a valid YAML file
    valid_file = mktemp(suffix=".yaml") do file, io
        write(io, "key: value")
        close(io)
        file  # Return the file path
    end
    @testset "Valid YAML file" begin
        @test check_input_file(valid_file) === nothing
    end

    # Case 2: File does not exist
    @testset "Non-existent file" begin
        @test_throws ErrorException check_input_file("nonexistent_file.yaml")
    end

    # Case 3: File exists but invalid extension
    invalid_file = mktemp(suffix=".txt") do file, io
        write(io, "key: value")
        close(io)
        file  # Return the file path
    end
    @testset "Invalid file extension" begin
        @test_throws ErrorException check_input_file(invalid_file)
    end
end

using Test

@testset "Test check_required_keys" begin
    # Case 1: All required keys are present
    data_dict = Dict("key1" => "value1", "key2" => "value2", "key3" => "value3")
    required_keys = ["key1", "key2"]
    @test check_required_keys(data_dict, required_keys) === nothing  # Should pass without errors

    # Case 2: Missing keys
    required_keys = ["key1", "key4"]  # key4 is missing
    @testset "Missing required keys" begin
        try
            check_required_keys(data_dict, required_keys)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, AssertionError)
            @test occursin("The key key4 is missing in the input file.", e.msg)
        end
    end

    # Case 3: No required keys (empty required_keys vector)
    required_keys = String[]  # No keys are required
    @test check_required_keys(data_dict, required_keys) === nothing  # Should pass without errors

    # Case 4: Empty data_dict
    data_dict = Dict()  # Empty dictionary
    required_keys = ["key1", "key2"]
    @testset "Empty data_dict" begin
        try
            check_required_keys(data_dict, required_keys)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, AssertionError)
            @test occursin("The key key1 is missing in the input file.", e.msg)
        end
    end
end

using Test

# Mock the check_required_keys function for isolated testing
function mock_check_required_keys(data_dict::Dict, required_keys::Vector{String})
    for key in required_keys
        if !haskey(data_dict, key)
            throw(AssertionError("The key $key is missing in the input file."))
        end
    end
    return nothing
end

# Replace the real function with the mock version (if needed)
# Uncomment this line if testing without defining check_required_keys
# const check_required_keys = mock_check_required_keys

@testset "Test check_model_parametrization" begin
    # Case 1: Valid input with all required keys in the "Model" dictionary
    data_dict = Dict(
        "Model" => Dict("key1" => "value1", "key2" => "value2", "key3" => "value3")
    )
    required_keys = ["key1", "key2"]
    @test check_model_parametrization(data_dict, required_keys) === true

    # Case 2: Missing "Model" key
    data_dict = Dict()  # No "Model" key
    @testset "Missing Model key" begin
        try
            check_model_parametrization(data_dict, required_keys)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, KeyError)  # Expect a KeyError for missing "Model"
        end
    end

    # Case 3: Missing required keys in the "Model" dictionary
    data_dict = Dict("Model" => Dict("key1" => "value1"))  # Missing "key2"
    @testset "Missing required keys in Model" begin
        try
            check_model_parametrization(data_dict, required_keys)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, AssertionError)
            @test occursin("The key key2 is missing", e.msg)
        end
    end

    # Case 4: Empty "Model" dictionary
    data_dict = Dict("Model" => Dict())  # Empty "Model" dictionary
    @testset "Empty Model dictionary" begin
        try
            check_model_parametrization(data_dict, required_keys)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, AssertionError)
            @test occursin("The key key1 is missing", e.msg)
        end
    end

    # Case 5: No required keys
    data_dict = Dict("Model" => Dict("key1" => "value1"))  # Any keys in Model
    required_keys = []  # Empty required keys
    @test check_model_parametrization(data_dict, required_keys) === true
end

using Test
using Random  # For generating unique test folder names

@testset "Test check_folder_writable" begin
    # Case 1: Folder exists and is writable
    writable_folder = mktempdir()  # Create a temporary writable folder
    @testset "Writable folder" begin
        @test check_folder_writable(writable_folder) === nothing  # Should pass without errors
    end

    # Case 2: Folder does not exist
    non_existent_folder = joinpath(writable_folder, "non_existent")
    @testset "Non-existent folder" begin
        try
            check_folder_writable(non_existent_folder)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, ErrorException)
            @test occursin("The folder does not exist.", e.msg)
        end
    end

    # Case 3: Folder exists but is not writable
    restricted_folder = mktempdir()
    chmod(restricted_folder, 0o444)  # Read-only permissions
    @testset "Non-writable folder" begin
        try
            check_folder_writable(restricted_folder)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, ErrorException)
            @test occursin("The folder is not writable", e.msg)
        end
    end
    chmod(restricted_folder, 0o755)  # Restore permissions for cleanup
    rm(restricted_folder, force=true)

    # Case 4: Edge case - Writable system folder (e.g., /tmp)
    system_folder = tempname()  # Use a writable system folder
    mkdir(system_folder)  # Ensure it exists
    @testset "System folder (e.g., /tmp)" begin
        @test check_folder_writable(system_folder) === nothing
    end
    rm(system_folder, force=true)
end

using Test
using Mocking  # For mocking dependencies

# Import the function to test
include("path_to_your_file_containing_get_input_data.jl")

@testset "Test get_input_data" begin
    # Case 1: Valid input
    @testset "Valid input file and data" begin
        # Mock the dependencies
        @mock check_input_file(path_to_source_file::String) => nothing
        @mock YAML.load_file(path_to_source_file::String) => Dict("key1" => "value1", "key2" => "value2")
        @mock check_required_keys(data_dict::Dict, struct_names_base::Vector{String}) => nothing

        # Define required arguments
        struct_names_base = ["key1", "key2"]
        path_to_source_file = "valid_file.yaml"

        # Call the function
        result = get_input_data(path_to_source_file)
        @test result == Dict("key1" => "value1", "key2" => "value2")
    end

    # Case 2: Input file does not exist
    @testset "Invalid input file" begin
        # Mock the dependencies
        @mock check_input_file(path_to_source_file::String) = throw(ErrorException("The input file does not exist."))

        path_to_source_file = "invalid_file.yaml"

        # Call the function and expect an error
        try
            get_input_data(path_to_source_file)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, ErrorException)
            @test occursin("The input file does not exist.", e.msg)
        end
    end

    # Case 3: Missing required keys
    @testset "Missing required keys in data" begin
        # Mock the dependencies
        @mock check_input_file(path_to_source_file::String) => nothing
        @mock YAML.load_file(path_to_source_file::String) => Dict("key1" => "value1")  # Missing key2
        @mock check_required_keys(data_dict::Dict, struct_names_base::Vector{String}) = 
            throw(AssertionError("The key key2 is missing in the input file."))

        path_to_source_file = "file_with_missing_keys.yaml"

        # Call the function and expect an error
        try
            get_input_data(path_to_source_file)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, AssertionError)
            @test occursin("The key key2 is missing", e.msg)
        end
    end

    # Case 4: Invalid YAML content
    @testset "Invalid YAML content" begin
        # Mock the dependencies
        @mock check_input_file(path_to_source_file::String) => nothing
        @mock YAML.load_file(path_to_source_file::String) = throw(ErrorException("Invalid YAML format"))

        path_to_source_file = "invalid_yaml_file.yaml"

        # Call the function and expect an error
        try
            get_input_data(path_to_source_file)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, ErrorException)
            @test occursin("Invalid YAML format", e.msg)
        end
    end
end

using Test

# Include parse_data and the struct definitions
include("parse_data.jl")
include("structs.jl")  # Ensure this file contains all required struct definitions

@testset "Test parse_data" begin
    # Case 1: Valid input
    @testset "Valid data_dict" begin
        # Mock valid input data
        data_dict = Dict(
            "Node" => [
                Dict("id" => 1, "name" => "NodeA", "carbon_price" => 10),
                Dict("id" => 2, "name" => "NodeB", "carbon_price" => 15)
            ],
            "Edge" => [
                Dict(
                    "id" => 1,
                    "name" => "Edge1",
                    "length" => 100,
                    "from" => "NodeA",
                    "to" => "NodeB",
                    "carbon_price" => 5
                )
            ],
            "Model" => Dict(
                "Y" => 100,
                "y_init" => 10,
                "pre_y" => 5,
                "gamma" => 0.9,
                "budget_constraint_penalty_plus" => 50,
                "budget_constraint_penalty_minus" => 30
            )
        )

        # Call the function
        result = parse_data(data_dict)

        # Verify the output
        @test typeof(result) == Dict
        @test length(result["node_list"]) == 2
        @test typeof(result["node_list"][1]) == Node
        @test result["node_list"][1].name == "NodeA"

        @test length(result["edge_list"]) == 1
        @test typeof(result["edge_list"][1]) == Edge
        @test result["edge_list"][1].length == 100
        @test result["edge_list"][1].from.name == "NodeA"
        @test result["edge_list"][1].to.name == "NodeB"
    end

    # Case 2: Missing keys
    @testset "Missing keys in data_dict" begin
        # Mock input data missing "Node"
        incomplete_data_dict = Dict(
            "Edge" => [
                Dict(
                    "id" => 1,
                    "name" => "Edge1",
                    "length" => 100,
                    "from" => "NodeA",
                    "to" => "NodeB",
                    "carbon_price" => 5
                )
            ]
        )

        # Expect an error when calling the function
        try
            parse_data(incomplete_data_dict)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, KeyError)
            @test occursin("Node", string(e))
        end
    end

    # Case 3: Empty input
    @testset "Empty data_dict" begin
        # Call the function with an empty dictionary
        empty_data_dict = Dict()

        # Expect an error
        try
            parse_data(empty_data_dict)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, KeyError)
            @test occursin("Model", string(e))
        end
    end

    # Case 4: Incorrect data types
    @testset "Invalid data types in data_dict" begin
        # Mock input with invalid data type for Node
        invalid_data_dict = Dict(
            "Node" => [
                Dict("id" => "InvalidID", "name" => "NodeA", "carbon_price" => "WrongType")
            ],
            "Model" => Dict(
                "Y" => 100,
                "y_init" => 10,
                "pre_y" => 5,
                "gamma" => 0.9,
                "budget_constraint_penalty_plus" => 50,
                "budget_constraint_penalty_minus" => 30
            )
        )

        # Expect an error
        try
            parse_data(invalid_data_dict)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, MethodError) || isa(e, ArgumentError)
        end
    end

    # Case 5: Invalid references
    @testset "Invalid references in data_dict" begin
        # Mock input with invalid references in Edge
        invalid_ref_data_dict = Dict(
            "Node" => [
                Dict("id" => 1, "name" => "NodeA", "carbon_price" => 10)
            ],
            "Edge" => [
                Dict(
                    "id" => 1,
                    "name" => "Edge1",
                    "length" => 100,
                    "from" => "NodeA",
                    "to" => "NonExistentNode",
                    "carbon_price" => 5
                )
            ],
            "Model" => Dict(
                "Y" => 100,
                "y_init" => 10,
                "pre_y" => 5,
                "gamma" => 0.9,
                "budget_constraint_penalty_plus" => 50,
                "budget_constraint_penalty_minus" => 30
            )
        )

        # Expect an error
        try
            parse_data(invalid_ref_data_dict)
            @test false  # Fail if no error is thrown
        catch e
            @test isa(e, BoundsError)
            @test occursin("NonExistentNode", string(e))
        end
    end
end

using Test

# Test create_m_tv_pairs function
@testset "create_m_tv_pairs tests" begin
    # Mock Data for testing
    mode1 = Mode(1, true)
    mode2 = Mode(2, false)
    
    vehicle_type1 = Vehicletype(1, mode1)
    vehicle_type2 = Vehicletype(2, mode2)
    
    techvehicle1 = TechVehicle(1, "Truck A", vehicle_type1, "Electric", [10000.0], [500.0], [0.1], [20.0], [0.2], [10], [50000.0], [], [100.0], [10.0])
    techvehicle2 = TechVehicle(2, "Truck B", vehicle_type2, "Diesel", [15000.0], [700.0], [0.15], [30.0], [0.25], [15], [60000.0], [], [120.0], [12.0])
    
    techvehicle_list = [techvehicle1, techvehicle2]
    mode_list = [mode1, mode2]
    
    result = create_m_tv_pairs(techvehicle_list, mode_list)
    
    @test length(result) == 3  # Since the total number of pairs should be 3 (2 techvehicles and 1 additional for mode2)
    @test (1, 1) in result  # Pair from techvehicle1 and mode1
    @test (2, 2) in result  # Pair from techvehicle2 and mode2
    @test (2, 3) in result  # New pair added for mode2 (additional techvehicle with id 3)
end

# Test create_tv_id_set function
@testset "create_tv_id_set tests" begin
    # Mock Data for testing
    mode1 = Mode(1, true)
    mode2 = Mode(2, false)
    
    vehicle_type1 = Vehicletype(1, mode1)
    vehicle_type2 = Vehicletype(2, mode2)
    
    techvehicle1 = TechVehicle(1, "Truck A", vehicle_type1, "Electric", [10000.0], [500.0], [0.1], [20.0], [0.2], [10], [50000.0], [], [100.0], [10.0])
    techvehicle2 = TechVehicle(2, "Truck B", vehicle_type2, "Diesel", [15000.0], [700.0], [0.15], [30.0], [0.25], [15], [60000.0], [], [120.0], [12.0])
    
    techvehicle_list = [techvehicle1, techvehicle2]
    mode_list = [mode1, mode2]
    
    result = create_tv_id_set(techvehicle_list, mode_list)
    
    @test length(result) == 3  # Should include the two techvehicles and one additional for mode2
    @test 1 in result  # TechVehicle 1 id
    @test 2 in result  # TechVehicle 2 id
    @test 3 in result  # Additional techvehicle id created for mode2
end

# Test create_v_t_set function
@testset "create_v_t_set tests" begin
    # Mock Data for testing
    mode1 = Mode(1, true)
    mode2 = Mode(2, true)
    
    vehicle_type1 = Vehicletype(1, mode1)
    vehicle_type2 = Vehicletype(2, mode2)
    
    techvehicle1 = TechVehicle(1, "Truck A", vehicle_type1, "Electric", [10000.0], [500.0], [0.1], [20.0], [0.2], [10], [50000.0], [], [100.0], [10.0])
    techvehicle2 = TechVehicle(2, "Truck B", vehicle_type2, "Diesel", [15000.0], [700.0], [0.15], [30.0], [0.25], [15], [60000.0], [], [120.0], [12.0])
    
    techvehicle_list = [techvehicle1, techvehicle2]
    
    result = create_v_t_set(techvehicle_list)
    
    @test length(result) == 2  # Should have 2 pairs of techvehicle IDs
    @test (1, 1) in result  # TechVehicle 1 ID pair
    @test (2, 2) in result  # TechVehicle 2 ID pair
end

# Test create_p_r_k_set function
@testset "create_p_r_k_set tests" begin
    # Mock Data for testing
    origin = Node(1, "Region A")
    destination = Node(2, "Region B")
    product1 = Product(1, "Product A")
    
    geo_el1 = GeographicElement("edge", 1)
    geo_el2 = GeographicElement("edge", 2)
    
    path1 = Path(1, [geo_el1, geo_el2])
    path2 = Path(2, [geo_el1])
    
    odpair1 = Odpair(1, origin, destination, [path1, path2], 1000, product1, [InitialVehicleStock(50)], FinancialStatus("Active"), RegionType("Urban"))
    odpair2 = Odpair(2, origin, destination, [path2], 500, product1, [InitialVehicleStock(30)], FinancialStatus("Inactive"), RegionType("Rural"))
    
    odpairs = [odpair1, odpair2]
    
    result = create_p_r_k_set(odpairs)
    
    @test length(result) == 3  # Three unique (product, odpair, path) combinations
    @test (1, 1, 1) in result  # Product 1, Odpair 1, Path 1
    @test (1, 1, 2) in result  # Product 1, Odpair 1, Path 2
    @test (1, 2, 2) in result  # Product 1, Odpair 2, Path 2
end

# Additional tests for create_p_r_k_e_set, create_p_r_k_g_set, create_p_r_k_n_set, create_r_k_set would be similarly written with mock objects.
