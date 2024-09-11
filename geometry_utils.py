import geopandas as gpd

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import (
    MultiLineString,
    LineString,
    MultiPoint,
    Point,
    Polygon,
    MultiPolygon,
)
from shapely.ops import split, linemerge
from itertools import tee
from shapely.geometry.base import BaseGeometry
import pyproj
from math import *
from geopy.distance import geodesic


def get_exteriors(geometry):
    if isinstance(geometry, Polygon):
        exterior = geometry.exterior
    elif isinstance(geometry, MultiPolygon):
        exteriors = []
        for polygon in geometry:
            exteriors.append(polygon.exterior)
        exterior = MultiLineString(exteriors)

    return exterior


def haversine_distance(lon1, lat1, lon2, lat2):
    # Convert to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371 * c * 1000  # Earth radius in meters

    return distance


def calculate_true_distance(mercator_linestring):
    # mercator_linestring is a list of (x, y) coordinate tuples in EPSG:3857

    # Create a projection transformer from EPSG:3857 to EPSG:4326
    transformer = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

    # Convert each point in the linestring to lon-lat coordinates
    lon_lat_linestring = [transformer.transform(x, y) for x, y in mercator_linestring]

    # Calculate the true distance
    distance = sum(
        haversine_distance(lon1, lat1, lon2, lat2)
        for (lon1, lat1), (lon2, lat2) in zip(
            lon_lat_linestring, lon_lat_linestring[1:]
        )
    )

    return distance


def make_gdf_from_df_with_points(df, column_name_x, column_name_y):
    column_x_coord = df[column_name_x].to_list()
    column_y_coord = df[column_name_y].to_list()

    point_column = [
        Point(column_x_coord[ij], column_y_coord[ij])
        for ij in range(0, len(column_x_coord))
    ]
    df["geometry"] = point_column
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

    return gdf


def eliminate_adjacent_duplicates(lst):
    return [val for i, val in enumerate(lst) if i == 0 or lst[i - 1] != val]


def get_projected_point(point, graph_points):
    distances = np.linalg.norm(graph_points - point, axis=1)
    nearest_point_index = np.argmin(distances)
    projected_point = graph_points[nearest_point_index]
    return projected_point


def transform_point(point, source_epsg, target_epsg):
    gdf_source = gpd.GeoDataFrame(geometry=[point], crs=source_epsg)
    gdf_target = gdf_source.to_crs(target_epsg)
    point_target = gdf_target['geometry'].iloc[0]
    return (point_target.x, point_target.y)


def calculate_true_length(line_geometry, epsg="EPSG:3857", stepsize=1000):
    # collect coordinates
    if line_geometry.geom_type == "LineString":
        total_distance = 0
        line = line_geometry
        coordinates = [Point(line.xy[0][0], line.xy[1][0])]
        d = 0
        while d < line.length:
            point = line.interpolate(d)
            coordinates.append(point)
            d += stepsize

        for kl in range(len(coordinates) - 1):
            point1 = transform_point(coordinates[kl], epsg, "EPSG:4326")
            point2 = transform_point(coordinates[kl + 1], epsg, "EPSG:4326")
            distance = geodesic((point1[0], point1[1]), (point2[0], point2[1])).meters
            total_distance += distance

        return total_distance

    elif line_geometry.geom_type == "MultiLineString":
        total_distance = 0
        for line in line_geometry:
            coordinates = [Point(line.xy[0][0], line.xy[1][0])]
            d = 0
            while d < line.length:
                point = line.interpolate(d)
                coordinates.append(point)
                d += stepsize

            for kl in range(len(coordinates) - 1):
                point1 = transform_point(coordinates[kl], epsg, "EPSG:4326")
                point2 = transform_point(coordinates[kl + 1], epsg, "EPSG:4326")
                distance = geodesic((point1[0], point1[1]), (point2[0], point2[1])).meters
                total_distance += distance

        return total_distance

    else:
        return 0


def get_centroid_from_nuts_id(NUTS_ID, nuts_table):
    centroid_point = nuts_table[nuts_table.NUTS_ID == NUTS_ID].centroid.to_list()[0]
    return centroid_point


def clip_geopandas_frame(gdf_1, gdf_2):
    """
    returns the geometries of gdf_1 that overlap with gdf_2
    :return: gpd.GeoDataFrame in the crs of gdf_2
    """
    # making sure that the crs is the same
    crs_gdf_2 = gdf_2.crs
    gdf_1_transformed = gdf_1.to_crs(crs_gdf_2)
    # gdf_1_transformed['line_length'] = gdf_1_transformed['geometry'].length
    # intersection_result = gpd.overlay(gdf_1_transformed, gdf_2, how='intersection')
    # intersection_result['overlap_length'] = intersection_result['geometry'].length
    # gdf_1_transformed['overlap_percentage'] = (intersection_result['overlap_length'] / gdf_1_transformed['line_length'])\
    #                                           * 100
    # # checking for if 50% of the geometry overlaps with gdf_2
    # filtered_gdf_1 = gdf_1_transformed[gdf_1_transformed['overlap_percentage'] >= 50]
    mask = gdf_1_transformed.intersects(gdf_2.unary_union)
    filtered_gdf_1 = gdf_1_transformed[mask]
    # filtered_gdf_1 = gpd.clip(gdf_1_transformed, gdf_2)
    return filtered_gdf_1


def parse_route_to_linestrings(linestring_geometry):
    coordinates = list(linestring_geometry.coords)
    linestrings = [LineString([coordinates[i], coordinates[j]]) for i in range(len(coordinates) - 1) for j in
                   range(i + 1, len(coordinates))]
    return linestrings


def identify_linestrings_within_geometry(linestring_list, polygon):
    filtered_linestrings = []

    for line_string in linestring_list:
        # Check if both ending points of the LineString are inside the polygon
        start_point, end_point = line_string.coords[0], line_string.coords[-1]
        if polygon.contains(Point(start_point)) and polygon.contains(Point(end_point)):
            filtered_linestrings.append(line_string)

    return filtered_linestrings


def match_route_to_network(route_geometry, network, match_OD=True, OD=()):
    return None


def nearest_points(line_string, multi_line_string):
    # Find the two closest points between LineString and MultiLineString
    # credits to chatGPT

    closest_points = []
    min_distance = float('inf')

    for line in multi_line_string:
        for point in line.coords:
            distance = line_string.distance(Point(point))
            if distance < min_distance:
                min_distance = distance
                closest_points = [Point(point), line_string.interpolate(line_string.project(Point(point)))]

    return closest_points


def calculate_closest_distance(line_string, multi_line_string):
    # Convert the LineString and MultiLineString to Shapely geometries
    # credits to chatGPT
    # Find the two closest points
    closest_points = nearest_points(line_string, multi_line_string)

    # Create a LineString between the two closest points
    connecting_line = LineString(closest_points)
    length = calculate_true_length(connecting_line)
    return length


def get_point_from_linestring(linestring, point_to_get="first"):
    if not linestring:
        return None  # Handle empty linestring case

    if point_to_get == "last":
        point = linestring.coords[-1]
    else:
        point = linestring.coords[0] if point_to_get == "first" else linestring.coords[point_to_get]

    return Point(point)


def get_region_from_point(nuts_gdf, point):
    nuts_gdf['distance_to_given_point'] = nuts_gdf['geometry'].distance(point)

    # Find the index of the closest point
    closest_point_index = nuts_gdf['distance_to_given_point'].idxmin()

    # Retrieve the closest point
    closest_region_id = nuts_gdf.loc[closest_point_index, 'NUTS_ID']

    return closest_region_id


def _match_edge_route(route, edge_gdf):
    """
    generating edge route
    :param route:
    :param edge_gdf:
    :return:
    """
    edge_route = []
    for ij in range(0, len(route)):
        current_edge = route[ij]
        edge_extract = edge_gdf[edge_gdf.node_pair == tuple(sorted(current_edge))]
        current_edge_id = edge_extract.edge_id.to_list()[0]
        edge_route.append(current_edge_id)

    return edge_route


def _fetch_elec_price(nut_id, elec_prices):
    extract = elec_prices[elec_prices.NUTS_region == nut_id[0:2]]
    elec_price_2020 = extract[extract.year == "2020"]["elec_price_EURperkWh"].to_list()[0]
    elec_price_2035 = extract[extract.year == "2035"]["elec_price_EURperkWh"].to_list()[0]
    elec_price_2050 = extract[extract.year == "2050"]["elec_price_EURperkWh"].to_list()[0]

    return [elec_price_2020, elec_price_2035, elec_price_2050]


def _calculate_labor_costs_for_route(labor_costs, route_distance, driving_speed, charging_time, driving_range):
    required_hours = route_distance * (1/driving_speed)
    possible_driving_hours = driving_range * (1/driving_speed)

    if 4.5 < possible_driving_hours:
        time_slice = 4.5
    else:
        time_slice = possible_driving_hours

    amount_of_breaks = np.floor(9/time_slice)
    break_time = 0.75
    pause_time = 0
    if charging_time < break_time:
        pause_time =0.75
    else:
        pause_time = charging_time
    if required_hours < time_slice:
        totally_required_hours_one_driver = required_hours
        totally_required_hours_two_drivers = required_hours
    else:
        totally_required_hours_one_driver = (np.floor(required_hours/time_slice) - 1) * pause_time + required_hours
        totally_required_hours_two_drivers = required_hours

    costs_one_driver = totally_required_hours_one_driver * labor_costs
    costs_two_driver = totally_required_hours_two_drivers * labor_costs * 2

    if costs_two_driver > costs_one_driver:
        total_labor_costs = costs_one_driver/route_distance
    else:
        total_labor_costs = costs_two_driver/route_distance

    return total_labor_costs


def remove_consecutive_duplicates(input_list):
    # Use a list comprehension to create a new list with consecutive duplicates removed
    filtered_list = [input_list[i] for i in range(len(input_list)) if i == 0 or input_list[i] != input_list[i - 1]]

    return filtered_list


def identify_dead_ends(network_gdf: gpd.GeoDataFrame):
    """
    for the identification of dead-end edges in a network
    :param network_gdf:
    :return:
    """
    # making copy to not overwrite existing data frame
    network_gdf_copy = network_gdf.copy()

    # delete combinations
    network_gdf_copy['combined'] = network_gdf_copy.apply(lambda row: tuple(sorted([row['from'], row['to']])), axis=1)

    network_gdf_copy["id"] = range(0, len(network_gdf_copy))
    network_gdf_copy = network_gdf_copy.set_index("id")

    # collect all nodes and make list of the existing nodes
    nodes_names_all = network_gdf_copy["from"].to_list() + network_gdf_copy["to"].to_list()
    node_names = list(set(nodes_names_all))

    # empty geopandas dataframe to fill
    dead_end_gdf = gpd.GeoDataFrame(columns=network_gdf_copy.columns)

    for node in node_names:
        number_of_appearances = nodes_names_all.count(node)
        if number_of_appearances == 1:
            # find
            dead_end_row = network_gdf_copy[network_gdf_copy['combined'].apply(lambda x: node in x)]
            row_dict = dead_end_row.iloc[0].to_dict()
            dead_end_gdf = dead_end_gdf.append(row_dict, ignore_index=True)

    dead_end_gdf.crs = "EPSG:3857"
    dead_end_gdf = dead_end_gdf.drop(columns="combined")
    return dead_end_gdf