# Import Documenter.jl
using Documenter
using DocumenterInterLinks
# Include your module files manually
# include("../src/TransComp.jl")  # Adjust the path based on where your TransComp module is located
using TransComp

@info "Module TransComp loaded."


# Define the documentation output directory
makedocs(;
    sitename = "TransComp Documentation",  # Title of the docs site
    modules = [TransComp],
    authors = "Antonia Maria Golab (with AI assistance for documentation)",  # You can put your name or the team name
    format = Documenter.HTML(;
        prettyurls = get(ENV, "CI", "false") == "true",
        edit_link = "main",
        assets = ["assets/custom.css", "assets/remove-prefix.js"],
        ansicolor = true,
        canonical = "https://antoniamgolab.github.io/iDesignRES_transcompmodel",
    ),
    pages = [
        "Home" => "index.md",
        "Manual" => Any[
            "Quick Start"=>"manual/quick-start.md",
            "How to use"=>"manual/how-to-use.md",
            "Preparation of input data"=>"manual/input_data.md",
            "Output data"=>"manual/output_data.md",
            "Mathematical model"=>"manual/math_formulation.md",
        ],
        "Types and functions" => Any[
            "Model Types"=>"manual/types.md",
            "Functions"=>"manual/functions.md",
            "Optimization functions"=>"manual/constraints_and_objective.md",
        ],
        "Examples" => Any["Basque Country"=>"examples/basque-case.md",],
    ],
    checkdocs = :none,
    doctest = false,
    clean = true,
    warnonly = [:missing_docs],
    # theme = Documenter.Themes.Calcite()  # Use a custom theme
    # format = Documenter.Markdown()  # Output format
    # Optional: You can customize the theme and navigation options here
    # Change theme if you prefer
)
deploydocs(
    repo = "git@github.com:antoniamgolab/iDesignRES_transcompmodel.git",
    branch = "gh-pages",    # adding to the gh-pages branch
    push_preview = false, # Set to true if you want to push preview builds
    deploy_config = Documenter.GitHubActions(),
)
