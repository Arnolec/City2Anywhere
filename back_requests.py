import folium as fl
import utils
from Analyzer import Analyzer
import pandas as pd
import streamlit as st
import geopandas as gpd
from typing import Optional
from datetime import datetime
from datetime import time


@st.cache_data
def initialize_variables() -> tuple[int, fl.FeatureGroup, Optional[str], pd.DataFrame, Optional[str], pd.DataFrame]:
    zoom = 5
    fg = fl.FeatureGroup("Markers")
    previous_city: Optional[str] = None
    destinations: pd.DataFrame = pd.DataFrame()
    destination_selected: Optional[str] = None
    trips: pd.DataFrame = pd.DataFrame()
    return zoom, fg, previous_city, destinations, destination_selected, trips


@st.cache_data
def fetch_cities(_analyzers: dict[str, Analyzer]) -> pd.DataFrame:
    cities: pd.DataFrame = {}
    cities_analyzers: list[pd.DataFrame] = []
    for analyzer in _analyzers.values():
        cities_analyzers.append(analyzer.get_list_of_cities())
    cities_concat = pd.concat(cities_analyzers)
    cities_concat_index = cities_concat.assign(ids=cities_concat.index)
    sum_appearance_on_index = (
        cities_concat_index.groupby("ids").sum().sort_values(by="number_of_appearance", ascending=False)
    )
    cities_concat = cities_concat[~cities_concat.index.duplicated(keep="first")]
    cities_concat["number_of_appearance"] = sum_appearance_on_index["number_of_appearance"]
    cities_sorted = cities_concat.sort_values(by="number_of_appearance", ascending=False)
    cities = cities_sorted.set_index("stop_name")
    cities = cities[~cities.index.duplicated(keep="first")]
    return cities


@st.cache_data
def fetch_center(cities: pd.DataFrame) -> tuple[float, float]:
    gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
        cities, geometry=gpd.points_from_xy(cities.stop_lat, cities.stop_lon), crs="EPSG:4326"
    )
    centroid = gdf.unary_union.centroid
    return centroid.x, centroid.y


@st.cache_data
def load_analyzers() -> dict[str, Analyzer]:
    analyzers = {}
    analyzers["TER"] = utils.load_class_analyzer("TER")
    analyzers["TGV"] = utils.load_class_analyzer("TGV")
    analyzers["INTERCITE"] = utils.load_class_analyzer("INTERCITE")
    analyzers["FLIXBUS"] = utils.load_class_analyzer("FLIXBUS")
    return analyzers


@st.cache_data
def get_trips_to_city(
    departure_lat: float,
    departure_lon: float,
    arrival_lat: float,
    arrival_lon: float,
    periode: tuple[datetime, datetime],
    _analyzers: dict[str, Analyzer],
    max_trips_printed: int | str,
    transport_type: list[str],
    departure_time: time,
) -> pd.DataFrame:
    date_min = periode[0]
    date_max = periode[1]
    # trips_dict: dict[str, pd.DataFrame] = {}
    if not isinstance(max_trips_printed, int):
        max_trips_printed = None

    datetime_departure = pd.Timedelta(hours=departure_time.hour)

    raw_trips = get_raw_trips_to_city(
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

    trips = raw_trips.sort_values(by="horaire_depart", ascending=True)
    trips = trips.head(max_trips_printed)
    return trips


# Function called in order to get dataframes of trips, and then dataframes are sorted and shaped to be displayed in the webApp by the above function
@st.cache_data
def get_raw_trips_to_city(
    departure_lat: float,
    departure_lon: float,
    arrival_lat: float,
    arrival_lon: float,
    date_min: datetime,
    date_max: datetime,
    _analyzers: dict[str, Analyzer],
    transport_type: list[str],
    departure_time: pd.Timedelta,
) -> pd.DataFrame:
    df_concat = pd.DataFrame()
    for key, analyzer in _analyzers.items():
        if key in transport_type:
            trips_transport = fetch_trips_one_transport(
                departure_lat,
                departure_lon,
                arrival_lat,
                arrival_lon,
                date_min,
                date_max,
                analyzer,
                key,
                departure_time,
            )
            df_concat = pd.concat([df_concat, trips_transport])
    return df_concat


@st.cache_data
def fetch_trips_one_transport(
    departure_lat: float,
    departure_lon: float,
    arrival_lat: float,
    arrival_lon: float,
    date_min: datetime,
    date_max: datetime,
    _analyzer: Analyzer,
    transport: str,
    departure_time: pd.Timedelta,
) -> pd.DataFrame:
    trips = _analyzer.find_trips_between_locations(
        departure_lat, departure_lon, arrival_lat, arrival_lon, date_min, date_max, departure_time
    )
    trips["transport_type"] = transport
    return trips


@st.cache_data
def get_destinations(
    lat: float,
    lon: float,
    periode: tuple[datetime, datetime],
    transport_type: tuple[str],
    _analyzers: dict[str, Analyzer],
    cities: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    date_min = periode[0]
    date_max = periode[1]
    destinations_duplicates = {}
    df_concat = pd.DataFrame()

    for key, analyzer in _analyzers.items():
        if key in transport_type:
            destinations_duplicates[key] = analyzer.find_destinations_from_location(lat, lon, date_min, date_max)
            df_concat = pd.concat([df_concat, destinations_duplicates[key]])
    destinations = cities[cities.index.isin(df_concat["stop_name"])]
    return destinations_duplicates, destinations


@st.cache_data
def generate_map_with_marker(lat: float, lon: float, destinations: dict[str, pd.DataFrame]) -> fl.FeatureGroup:
    fg = fl.FeatureGroup("Markers")
    fg.add_child(fl.Marker([lat, lon], popup="Ville de départ", icon=fl.Icon(color="blue")))
    color = {"TER": "red", "TGV": "black", "INTERCITE": "gray", "FLIXBUS": "green"}
    for key, destinations_analyzer in destinations.items():
        color_transport = color[key]
        for row in destinations_analyzer.itertuples():
            fg.add_child(
                fl.Marker(
                    [float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, icon=fl.Icon(color=color_transport)
                )
            )
    return fg
