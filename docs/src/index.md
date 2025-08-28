# TransComp Documentation

Welcome to the documentation for the `TransComp` package. This package provides tools for transportation modeling and optimization.

The *TransComp* model is a linear optimization model developed within the EU Horizon project [iDesignRES](https://idesignres.eu/) in work package 1. It is implemented in Julia and is based on the JuMP package. 

The *TransComp* model is aimed at modeling developments in subsectors of the transport sector. It is designed in a way that it can be adaptable in its complexity in the representation of the transport sector - being flexible in its ability to adjust to the level of availability of granular data - and being customizable in the scope of representation of the transport sector, i.e. included transport segments. Further, features are provided that allow the soft linking to traditional transport models and energy system models.


## Manual outline

- [Quick Start](manual/quick-start.md)
- [How to Use](manual/how-to-use.md)
- [Input Data](manual/input_data.md)
- [Output Data](manual/output_data.md)
- [Math Formulation](manual/math_formulation.md)

## Types and functions

- [Types](manual/types.md)
- [Functions](manual/functions.md)
- [Optimization functions](manual/constraints_and_objective.md)

## Examples of application

- [Basque Case](examples/basque-case.md)

## Scientific publications

This section lists peer-reviewed publications that utilize the TransComp model for transportation analysis and optimization studies.

*Currently, no publications are available. This section will be updated as research using the TransComp model is published.*

**How to cite TransComp:**
If you use the TransComp model in your research, please cite the following:

```
TransComp: A Transport Component Optimization Model
iDesignRES Project, Work Package 1
https://github.com/antoniamgolab/iDesignRES_transcompmodel
```

For questions about citing the model or collaborating on research, please contact the development team through the repository's issue tracker.

---

**Note**: Parts of this documentation were developed with AI assistance to improve clarity and organization. All technical content and model formulations have been reviewed and validated by the development team.
