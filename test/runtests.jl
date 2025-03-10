using TransComp
using JuMP
import HiGHS
using Test

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

@testset "Minimum viable case | Parameter testing" begin+
    @testset "Model robustness" begin
        include("test_model_robustness.jl")
    end
end 