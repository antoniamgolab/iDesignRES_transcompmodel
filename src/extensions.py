"""

Script containing functionalities for the dissaggregation of yearly energy demand to hourly demand.

created to support TransComp
current assumption: constant daily demand for all vehicletypes 
dictionary `demand_allocation` is imported from demand_allocation_dict.py and contains distribution
among different charging possibilities

"""
import numpy as np
from demand_allocation_dict import demand_allocation


def determine_nb_of_charging_vehs_per_day(total_nb_of_vehs, batt_cap, daily_demand, dod=0.8):
    """
    Function to determine the number of charging vehicles per day 

    Parameters
    ----------
    total_nb_of_vehs : int
        total number of vehicles to be charged
    batt_cap : float
        battery capacity of the vehicle in kWh
    daily_demand : float
        daily demand of the vehicle in kWh
    dod : float, optional
        depth of discharge of the battery. The default is 0.8.    
    """
    # determine the number of vehicles that can be charged per day
    vehs_to_be_charged_per_day = 0
    day_intervals = (batt_cap * dod) / daily_demand
    vehs_to_be_charged_per_day = total_nb_of_vehs / day_intervals
    return vehs_to_be_charged_per_day
 


def capacity_sizing(vehs_to_be_charged_per_day, utilization_nb, charging_cap):
    """
    Sizing the capacity of the charging infrastructure

    Parameters
    ----------
    vehs_to_be_charged_per_day : int
        number of vehicles to be charged per day
    utilization_nb : int
        utilization of the charging infrastructure
    charging_cap : int
        charging capacity of the infrastructure in kW
    """
    # determine the capacity of the charging infrastructure
    charging_infra_capacity = (vehs_to_be_charged_per_day /utilization_nb) * charging_cap

    return charging_infra_capacity


def hourly_dissagregation(energy_demand, installed_cap, hours, mode="even"):

    """
    Function to disaggregate yearly energy demand to hourly demand

    Parameters
    ----------
    energy_demand : float
        yearly energy demand in kWh
    installed_cap : float
        installed capacity in kW
    mode : str, optional
        mode of disaggregation. The default is "equal".

    Returns
    -------
    hourly_profile : np.array
        hourly energy demand profile
    """
    assert mode in ["even", "earliest", "latest"], "Mode must be 'earliest', 'latest' or 'even'"
    assert hours > 1 or hours < 24, "Hours must be between 1 and 24"

    # determine the hourly energy demand
    if mode == "even":
        demand_per_hour = energy_demand / hours
        if demand_per_hour > installed_cap:
            raise Warning("The demand per hour is higher than the installed capacity")
            demand_per_hour = installed_cap
        hourly_profile = np.array([demand_per_hour] * hours)
    
        return hourly_profile
    
    elif mode == "earliest" or mode == "latest":
        current_energy_demand = energy_demand
        current_hour = 0
        hourly_profile = np.zeros(hours)
        while current_hour < hours and current_energy_demand > 0:
            if current_energy_demand - installed_cap >= 0:
                part_energy = installed_cap
            else:
                part_energy = current_energy_demand
            hourly_profile[current_hour] = part_energy
            current_energy_demand = current_energy_demand - part_energy
            current_hour += 1
        if mode == "latest":
            hourly_profile = np.flip(hourly_profile)
        if current_energy_demand > 0:
            raise Warning("The demand per hour is higher than the installed capacity")
        return hourly_profile
    else:
        return np.zeros(hours)


def adding_hours_demand(hourly_demand_profiles):
    """
    Function to add the hourly demand profiles

    Parameters
    ----------
    hourly_demand_profiles : list
        list of hourly demand profiles

    Returns
    -------
    hourly_demand_dict : dict
        dictionary containing the hourly demand
    
    """
    hourly_demand_dict = {hour: 0 for hour in range(24)}
    for profile in hourly_demand_profiles:
        for hour, demand in profile.items():
            hourly_demand_dict[hour] += demand
    return hourly_demand_dict

    

def disaggregate_energy_and_vehs(total_energy_demand, total_vehs, perc):
    """
    Function to disaggregate the energy demand and the number of vehicles

    Parameters
    ----------
    total_energy_demand : float
        total energy demand in kWh
    total_vehs : int
        total number of vehicles
    perc : float
        percentage of energy demand to be allocated to the vehicles

    Returns
    -------
    energy_demand : float
        energy demand allocated to the vehicles
    vehs_demand : int
        number of vehicles to be charged
    """
    energy_demand = total_energy_demand * perc
    vehs_demand = total_vehs * perc
    return energy_demand, vehs_demand


def create_total_yearly_demand_profile(day_demand_profile, nb_days):
    """
    Function to create the total yearly demand profile

    Parameters
    ----------
    day_demand_profile : np.array
        daily demand profile
    nb_days : int
        number of days
    
    Returns
    -------
    total_yearly_profile : np.array
        total yearly demand profile
    """
    profile_day = [day_demand_profile[h] for h in range(0, 24)]
    total_yearly_profile = profile_day * nb_days

    return total_yearly_profile


def determine_total_hours_of_charging(start_time, end_time):
    """
    Function to determine the total hours of charging

    Parameters
    ----------
    demand_allocation : dict
        dictionary containing the demand allocation

    Returns
    -------
    total_hours : int
        total hours of charging
    """
    start_hour = start_time
    end_hour = end_time

    if end_hour < start_hour:
        total_hours = (24 - start_hour) + end_hour
    else:
        total_hours = end_hour - start_hour
    return total_hours


def creating_hour_demand_dict(start_time, end_time, hour_profile):
    """
    Function to create a dictionary of hourly demand with hour of the day as key

    Parameters
    ----------
    start_time : int
        starting time of the charging
    end_time : int
        ending time of the charging
    
    Returns
    -------
    hour_demand_profile : dict
        dictionary of hourly demand
    
    """

    hour_demand_profile = {hour: 0 for hour in range(24)}
    if end_time < start_time:
        fake_end_time = end_time + 24
    else:
        fake_end_time = end_time
    for hour in range(start_time, fake_end_time):
        charging_demand = hour_profile[hour-start_time]
        if hour > 23:
            hour_demand_profile[hour-24] = charging_demand
        else:
            hour_demand_profile[hour] = charging_demand

    return hour_demand_profile


def create_total_hourly_profile(load_distribution: dict, year: int):
    """
    Function for creating a list of total hourly demand profile for a given year.

    Parameters
    ----------
    load_distribution : dict
        dictionary containing the load distribution (keys are vehicle technologies, 
        values are dictionaries with different groups of vehicles with values (number of vehicles, 
        total yearly demand, battery capacity))
    year : int
        year to be modeled
    
    
    Returns
    -------
    total_yearly_profile : list
        list of hourly demand profile for entire year
    
    
    """
    hourly_profiles_total = []
    year_to_be_modeled = year
    nb_days = 366 if (year_to_be_modeled % 4 == 0 and (year_to_be_modeled % 100 != 0 or year_to_be_modeled % 400 == 0)) else 365
    daily_demand = total_demand / nb_days

    for tv in load_distribution.keys():
        for g in load_distribution[tv].keys():
            total_vehs = load_distribution[tv][g][0]
            total_demand = load_distribution[tv][g][1]
            batt_cap = load_distribution[tv][g][2]
            for charging_strategy in demand_allocation.keys():
                share = demand_allocation[charging_strategy]["share"]
                start_time = demand_allocation[charging_strategy]["start_time"]
                end_time = demand_allocation[charging_strategy]["end_time"]
                charging_power = demand_allocation[charging_strategy]["charging_power"]
                cars_per_cs_per_day = demand_allocation[charging_strategy]["cars_per_cs_per_day"]
                # Determine the number of days in the year

                # step 1: determine the number of vehs and energy for this charging strategy
                if share > 0:
                    curr_energy_demand, vehs = disaggregate_energy_and_vehs(total_demand, total_vehs, share)
                    curr_daily_demand = daily_demand * share

                    # step 2: determine the number of vehs to be charged per day
                    vehs_to_be_charged_per_day = determine_nb_of_charging_vehs_per_day(vehs, batt_cap, curr_daily_demand/vehs)

                    # step 3: determine the capacity of the charging infrastructure
                    charging_infra_capacity = capacity_sizing(vehs_to_be_charged_per_day, cars_per_cs_per_day, charging_power)
                    
                    # step 4: determine the hourly demand profile
                    charging_hours = determine_total_hours_of_charging(start_time, end_time)
                    hour_profiles = []
                    for mode in demand_allocation[charging_strategy]["strategy_split"]:
                        curr_energy_demand_by_mode = curr_energy_demand * demand_allocation[charging_strategy]["strategy_split"][mode]
                        hour_profile = hourly_dissagregation(curr_energy_demand_by_mode/nb_days, charging_infra_capacity, charging_hours, mode=mode)
                        hour_profiles.append(hour_profile)

                    # step 5: make dictionary of hourly demand
                    hour_profiles_dicts = []
                    for h_profile in hour_profiles:
                        hour_profile_dict = creating_hour_demand_dict(start_time, end_time, h_profile)
                        hour_profiles_dicts.append(hour_profile_dict)
                        hourly_profiles_total.append(hour_profile_dict)
    # final step: summing up all profiles
    hourly_demand_dict = adding_hours_demand(hourly_profiles_total)
    total_yearly_profile = create_total_yearly_demand_profile(hourly_demand_dict, nb_days)

    
    return total_yearly_profile



