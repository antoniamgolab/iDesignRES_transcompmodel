"""
This file contains the functions that are used in the model but are not directly related to the optimization problem.

"""

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
