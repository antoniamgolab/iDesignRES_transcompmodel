# set generation
function generate_set_K_r(R, K, K_r)
    output_set = Set()
    for r in R
        for k in K_r[r]
            push!(output_set, (r, k))
        end
    end
    return output_set
end

function generate_yktg(Y, K, T, G)
    output_set = Set()
    for y in Y
        for k in K
            for t in T
                for g in G
                    push!(output_set, (y, k, t, g))
                end
            end
        end
    end
    return output_set
end

function generate_yrtg(Y, R, T, G)
    output_set = Set()
    for y in Y
        for r in R
            for t in T
                for g in G
                    push!(output_set, (y, r, t, g))
                end
            end
        end
    end
    return output_set
end

function generate_yr(Y, R)
    output_set = Set()
    for y in Y
        for r in R
            push!(output_set, (y, r))
        end
    end
    return output_set
end

function generate_later_yrtg(Y, R, T, G)
    output_set = Set()
    for y in Y
        for r in R
            for t in T
                for g in G
                    if y > 1
                        push!(output_set, (y, r, t, g))
                    end
                end
            end
        end
    end
    return output_set
end

function generate_rtg(R, T, G)
    output_set = Set()
    for r in R
        for t in T
            for g in G
                push!(output_set, (r, t, g))
            end
        end
    end
    return output_set
end
