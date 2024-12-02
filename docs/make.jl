# Import Documenter.jl
using Documenter

# Include your module files manually
include("../src/TransComp.jl")  # Adjust the path based on where your TransComp module is located
using .TransComp

@info "Module TransComp loaded."
@show TransComp
# Define the documentation output directory
makedocs(;
    sitename = "TransComp Documentation",  # Title of the docs site
    modules = [TransComp],
    authors = "Antonia Maria Golab",  # You can put your name or the team name
    pages = [
        "Home" => "index.md"
        "Manual" => Any[
            "Quick Start"=>"manual/quick-start.md",
            "Preparation of input data"=>"manual/input_data.md",
            "Types and functions"=> "manual/types_and_functions.md",
        ]  # Entry point to the docs
    ],
    # theme = Documenter.Themes.Calcite()  # Use a custom theme
    # format = Documenter.Markdown()  # Output format
    # Optional: You can customize the theme and navigation options here
    # Change theme if you prefer
)
deploydocs(; repo = "github.com/antoniamgolab/iDesignRES_transcompmodel.git")
