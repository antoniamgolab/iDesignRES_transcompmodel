# Import Documenter.jl
using Documenter

# Include your module files manually
include("../src/structures/TransComp.jl")  # Adjust the path based on where your TransComp module is located
using .TransComp

# Define the documentation output directory
makedocs(;
    sitename = "TransComp Documentation",  # Title of the docs site
    authors = "Your Name",  # You can put your name or the team name
    pages = [
        "Home" => "index.md",  # Entry point to the docs
    ],
    # Optional: You can customize the theme and navigation options here
    # Change theme if you prefer
)
