"""
File for specification of demand_allocation dictionary. This dictionary is used to specify the demand allocation 
for different charging infrastruce types (maximum power, start and end time of plug-in period, if charging is evenly distributed during
the time of being plugged in [mode="even"], or if it is concentrated at the beginning [mode="earliest"] or end [mode="latest"] of the plug-in period).
And, how many vehicles are services per pole (`cars_per_cs_per_day`).

Adapt this dictonary to the assumptions in your application case.


"""

demand_allocation = {
    "night_charging": {
        "share": 1,
        "start_time": 17,
        "end_time": 7,
        "strategy_split": {"even": 0.5, "earliest": 0.3, "latest": 0.2},
        "charging_power": 11,
        "cars_per_cs_per_day": 1
    },
    "day_quick_charging": {
        "share": 0,
        "start_time": 10,
        "end_time": 16,
        "strategy_split": {"even": 1, "earliest": 0, "latest": 0},
        "charging_power": 50,
        "cars_per_cs_per_day": 8
    },
}
