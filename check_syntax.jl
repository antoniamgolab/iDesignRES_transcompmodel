using JuliaSyntax

code = read("src/model_functions.jl", String)

try
    parsed = JuliaSyntax.parseall(JuliaSyntax.SyntaxNode, code)
    println("✓ Syntax is valid!")
catch e
    println("✗ Syntax error found:")
    println(e)
    if isdefined(e, :msg)
        println("Message: ", e.msg)
    end
end
