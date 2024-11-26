# Transcomp Model Documentation
[![Documenter: dev](https://img.shields.io/badge/docs-dev-blue.svg)](https://domluna.github.io/JuliaFormatter.jl/dev/)

The *Transcomp* model is a linear optimization model developed within the EU Horizon project [iDesignRES](https://idesignres.eu/) in workpage 1. It is implemented in Julia and is based on the JuMP package. 

The *Transcomp* model is aimed at modeling developments in subsectors of the transport sector. It is designed in a way that it can be adoptable in its complexity in the representation of the transport sector - being flexible in its ability to adjust in to the level of availibility of granular data - and being costumizable in the scope if representation of the the transport sector, i.e. included transport segments. Further, features are provided that allow the soft linking to traditional transport models and energy system models.

## Manual outline


```@autodocs
Modules = [TransComp]
Order   = [:function, :type]
```
