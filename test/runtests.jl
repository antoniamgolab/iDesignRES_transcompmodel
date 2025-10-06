using TransComp
using JuMP
import HiGHS
using Test
using YAML

@testset "Model testing" begin
    @testset "Basic function | Technology shift" begin
        @testset "Tech shift test" begin
            include("test_techshift.jl")
        end
    end

    @testset "Basic function | Mode shift" begin
        @testset "Mode shift test" begin
            include("test_mode_shift.jl")
        end
    end

    @testset "Minimum viable case" begin
        @testset "Vehicle stock shift test" begin
            include("test_minimum_viable_case.jl")
        end
    end

    @testset "Minimum viable case | Parameter testing" begin
        @testset "Model robustness" begin
            include("test_model_robustness.jl")
        end
    end

    @testset "Minimum viable case | Supply infrastructure" begin
        @testset "Supply infrastructure test" begin
            include("test_supply_infrastructure.jl")
        end
    end

    @testset "Model workflow functions" begin
        include("test_model_workflows.jl")
    end

    @testset "Constraining market share" begin
        @testset "Constraining market share test" begin
            include("test_market_share_restrict.jl")
        end
    end

    @testset "Input data reading" begin
        @testset "Input data test" begin
            include("test_input_data_reading.jl")
        end
    end
    @testset "Checks functions" begin
        include("test_checks.jl")
    end

end

