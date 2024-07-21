import folium as fl
from AnalyzerV2 import AnalyzerGTFS as Ana
import pandas as pd
import streamlit as st
import geopandas as gpd
from shapely.geometry import Point
from typing import Optional
from datetime import datetime
from datetime import time


@st.cache_data
def init_var() -> (
    tuple[int, fl.FeatureGroup, Optional[str], dict[str, tuple[float, float, str]], Optional[str], list[str]]
):
    zoom = 5
    fg = fl.FeatureGroup("Markers")
    previous_city: Optional[str] = None
    destinations: dict[str, tuple[float, float, str]] = {}
    destination_selected: Optional[str] = None
    trips: dict[str, pd.DataFrame] = {}
    return zoom, fg, previous_city, destinations, destination_selected, trips


@st.cache_data
def get_cities() -> pd.DataFrame:
    cities: pd.DataFrame = {}
    cities_TER = Ana.list_of_cities("TER")
    cities_TGV = Ana.list_of_cities("TGV")
    cities_INTERCITE = Ana.list_of_cities("INTERCITE")
    cities_concat = pd.concat([cities_TER, cities_TGV, cities_INTERCITE])
    cities_concat = cities_concat.drop_duplicates(subset=["stop_id"])

    cities = cities_concat[["stop_name", "stop_lat", "stop_lon", "stop_id"]].set_index("stop_name")
    return cities


@st.cache_data
def get_center(cities: pd.DataFrame) -> tuple[float, float]:
    # serie = pd.Series(cities)
    # print(serie)
    # serie_points = cities.apply(lambda x: Point(x['stop_lat'], x['stop_lon']))
    gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
        cities, geometry=gpd.points_from_xy(cities.stop_lat, cities.stop_lon), crs="EPSG:4326"
    )
    centroid = gdf.unary_union.centroid
    return centroid.x, centroid.y


@st.cache_data
def load_analyzers() -> dict:
    analyzers = {}
    analyzers["TER"] = Ana("TER")
    analyzers["TGV"] = Ana("TGV")
    analyzers["INTERCITE"] = Ana("INTERCITE")
    return analyzers


@st.cache_data
def get_trips_to_city(
    departure_lat: float,
    departure_lon: float,
    arrival_lat: float,
    arrival_lon: float,
    periode: tuple[datetime, datetime],
    _analyzers: dict[str, Ana],
    sort: str,
    max_trips_printed: int | str,
    transport_type: list[str],
    departure_time: time,
) -> dict[str, pd.DataFrame]:  # analyzers pas hashable donc paramètre pas pris en compte pour cache
    date_min = periode[0]
    date_max = periode[1]
    trips_dict: dict[str, pd.DataFrame] = {}
    dict_sort: dict[str, str] = {
        "Jour": "horaire_depart",
        "Heure de départ": "departure_time_x",
        "Heure d'arrivée": "departure_time_y",
    }
    if not isinstance(max_trips_printed, int):
        max_trips_printed = None
    if sort not in dict_sort:
        sort = "horaire_depart"
    else:
        sort = dict_sort[sort]
    datetime_departure = pd.Timedelta(hours=departure_time.hour)

    raw_trips_dict = get_raw_trips_to_city(
        departure_lat,
        departure_lon,
        arrival_lat,
        arrival_lon,
        date_min,
        date_max,
        _analyzers,
        transport_type,
        datetime_departure,
    )

    for key, trips_df in raw_trips_dict.items():
        trip = trips_df.sort_values(by=sort, ascending=True)
        trips_dict[key] = trip.head(max_trips_printed)
    return trips_dict


# Function called in order to get dataframes of trips, and then dataframes are sorted and shaped to be displayed in the webApp by the above function
@st.cache_data
def get_raw_trips_to_city(
    departure_lat: float,
    departure_lon: float,
    arrival_lat: float,
    arrival_lon: float,
    date_min: datetime,
    date_max: datetime,
    _analyzers: dict[str, Ana],
    transport_type: list[str],
    departure_time: pd.Timedelta,
) -> dict[str, pd.DataFrame]:
    trips_dict: dict[str, pd.DataFrame] = {}
    for key, analyzer in _analyzers.items():
        if key in transport_type:
            trips_dict[key] = analyzer.get_trajets(
                departure_lat, departure_lon, arrival_lat, arrival_lon, date_min, date_max, departure_time
            )
    return trips_dict


@st.cache_data
def get_destinations(
    lat: float, lon: float, periode: tuple[datetime, datetime], transport_type: tuple[str], _analyzers: dict[str, Ana]
) -> tuple[dict[str, pd.DataFrame], dict[str, tuple[float, float, str]]]:
    date_min = periode[0]
    date_max = periode[1]

    destinations_duplicates = {}

    for key, analyzer in _analyzers.items():
        if key in transport_type:
            destinations_duplicates[key] = analyzer.get_set_destinations(lat, lon, date_min, date_max)

    destinations = {}
    destinations["-"] = (lat, lon, "0")

    for key, destinations_analyzer in destinations_duplicates.items():
        for row in destinations_analyzer.itertuples():
            destinations[row.stop_name] = (row.stop_lat, row.stop_lon, row.stop_id)
    return destinations_duplicates, destinations


@st.cache_data
def print_map(lat: float, lon: float, destinations: dict[str, pd.DataFrame]) -> fl.FeatureGroup:
    i = 0
    fg = fl.FeatureGroup("Markers")
    fg.add_child(fl.Marker([lat, lon], popup="Ville de départ", icon=fl.Icon(color="blue")))
    color = {"TER": "red", "TGV": "black", "INTERCITE": "gray"}
    for key, destinations_analyzer in destinations.items():
        color_transport = color[key]
        for row in destinations_analyzer.itertuples():
            fg.add_child(
                fl.Marker(
                    [float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, icon=fl.Icon(color=color_transport)
                )
            )
        i = i + 1
    return fg
