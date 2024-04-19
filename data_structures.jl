"""
Creation of data structures used for the parametrization of the TransportSecModel. 

    @Author: Antonia Golab
    @Dateofcreation: 2024-04-18
"""






"""
    add_numbers(x, y)

Add two numbers together.

# Arguments
- `x`: The first number.
- `y`: The second number.

# Returns
The sum of `x` and `y`.
"""
function add_numbers(x, y)
    return x + y
end


# define the model with its parameters as a struct!! 

"""
    struct module_activation

A struct to store the activation of different modules in the model.

# Fields
- `vehicle_stock::Bool`: Whether the vehicle stock module is activated.
- `regional::Bool`: Whether the regional module is activated.
- `interregional::Bool`: Whether the interregional module is activated.
- `mode_infrastructure::Bool`: Whether the mode infrastructure module is activated.
- `fueling_infrastructure::Bool`: Whether the fueling infrastructure module is activated.
- `fuel_supply_infrastructure::Bool`: Whether the fuel supply infrastructure module is activated.
"""
struct module_activation
    vehicle_stock::Bool
    regional::Bool
    interregional::Bool
    mode_infrastructure::Bool
    fueling_infrastructure::Bool
    fuel_supply_infrastructure::Bool
    # add more parameters as needed
end