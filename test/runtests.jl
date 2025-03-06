include("../src/structs.jl")
include("../src/model_functions.jl")
include("../src/support_functions.jl")
include(joinpath(@__DIR__, "../src/TransComp.jl"))
using .TransComp
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
