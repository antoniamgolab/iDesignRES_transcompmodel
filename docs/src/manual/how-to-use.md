# How to use?

In the following, we describe the purposeful usage of the model.

## Preliminary knowledge for usage
Given the complex nature of transport systems that is highly variable in different spatial environments and geography, the user should have some experience with the formulation and application of optimization models. In preparation to the application, we urge to familiarize yourself with the content of the `Model design` chapter. A mathematical formulation of the model can be found in the repository in `math/mathematical_formulation.pdf`.

## Design of a case study
In designing and quantifying a case study for the transport component model, the following questions need to be addressed:
* What region is modeled and at which geographic resolution? The model has been previously applied at NUTS-2 and NUTS-3 level (more information on NUTS classification [here](https://ec.europa.eu/eurostat/de/web/nuts)).
* What temporal horizon is modelled? The suggested modeling horizon is at least five years to find implications for modal and technological shift.
* Which transport modes, drivetrain technologies and fuels are part of the analysis? 
* How granular are the modes modeled? Based on vehicle stock investments or using levelized costs representing the total costs of a mode? This decision depends on the desired granularity of the analysis as well as available data.

## Preparing input data

The input data is in [JAML](https://yaml.org/) format. The minimal required input data and its format is defined in `Input data`.

