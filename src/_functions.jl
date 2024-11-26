# set generation
function generate_set_K_r(R, K, K_r)
    output_set = Set()
    for r ∈ R
        for k ∈ K_r[r]
            push!(output_set, (r, k))
        end
    end
    return output_set
end

function generate_yktg(Y, K, T, G)
    output_set = Set()
    for y ∈ Y
        for k ∈ K
            for t ∈ T
                for g ∈ G
                    push!(output_set, (y, k, t, g))
                end
            end
        end
    end
    return output_set
end

function generate_yrtg(Y, R, T, G)
    output_set = Set()
    for y ∈ Y
        for r ∈ R
            for t ∈ T
                for g ∈ G
                    push!(output_set, (y, r, t, g))
                end
            end
        end
    end
    return output_set
end

function generate_yr(Y, R)
    output_set = Set()
    for y ∈ Y
        for r ∈ R
            push!(output_set, (y, r))
        end
    end
    return output_set
end

function generate_later_yrtg(Y, R, T, G)
    output_set = Set()
    for y ∈ Y
        for r ∈ R
            for t ∈ T
                for g ∈ G
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
    for r ∈ R
        for t ∈ T
            for g ∈ G
                push!(output_set, (r, t, g))
            end
        end
    end
    return output_set
end
