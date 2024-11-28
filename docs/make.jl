# Import Documenter.jl
using Documenter

# Include your module files manually
include("../src/TransComp.jl")  # Adjust the path based on where your TransComp module is located
using .TransComp
@info "this works"
# Define the documentation output directory
makedocs(
    sitename = "TransComp Documentation",  # Title of the docs site
    modules = [TransComp],
    authors = "Your Name",  # You can put your name or the team name
    pages = [
        "Home" => "index.md",  # Entry point to the docs
    ],
    # theme = Documenter.Themes.Calcite()  # Use a custom theme
    # format = Documenter.Markdown()  # Output format
    # Optional: You can customize the theme and navigation options here
    # Change theme if you prefer
)