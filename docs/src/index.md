# TransComp Documentation

Welcome to the documentation for the `TransComp` package. This package provides tools for transportation modeling and optimization.

The *Transcomp* model is a linear optimization model developed within the EU Horizon project [iDesignRES](https://idesignres.eu/) in workpage 1. It is implemented in Julia and is based on the JuMP package. 

The *Transcomp* model is aimed at modeling developments in subsectors of the transport sector. It is designed in a way that it can be adoptable in its complexity in the representation of the transport sector - being flexible in its ability to adjust in to the level of availibility of granular data - and being costumizable in the scope if representation of the the transport sector, i.e. included transport segments. Further, features are provided that allow the soft linking to traditional transport models and energy system models.


# Overview

```@contents

Pages = [
    "manual/quickstart.md"
    ]
Depth=1
```

```@autodocs
Modules = [TransComp]
```