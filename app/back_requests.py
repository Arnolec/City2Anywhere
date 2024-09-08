from datetime import datetime, time
from typing import Optional

import folium as fl
import geopandas as gpd
import pandas as pd
import streamlit as st

import app.utils as utils
from app.analyzer import Analyzer
from app.data_updater import DataUpdater


@st.cache_data
def initialize_variables() -> (
    tuple[int, fl.FeatureGroup, Optional[str], pd.DataFrame, Optional[str], pd.DataFrame, pd.DataFrame]
):
    zoom = 5
    fg = fl.FeatureGroup("Markers")
    previous_city: Optional[str] = None
    destinations: pd.DataFrame = pd.DataFrame()
    destination_selected: Optional[str] = None
    trips: pd.DataFrame = pd.DataFrame()
    trips_to_print: pd.DataFrame = pd.DataFrame()
    return zoom, fg, previous_city, destinations, destination_selected, trips, trips_to_print


@st.cache_data
def update_data() -> None:
    DataUpdater().update_data()


@st.cache_data
def fetch_list_of_stops(_analyzers: dict[str, Analyzer]) -> pd.DataFrame:
    cities: pd.DataFrame = pd.DataFrame()
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

def fetch_cities(_analyzers: dict[str, Analyzer]) -> pd.DataFrame:
    list_of_stops = fetch_list_of_stops(_analyzers)
    list_of_stops = list_of_stops.assign(stop_name = list_of_stops.index)
    df_with_clusters = utils.group_stops_by_city(list_of_stops, eps_km=8.0)  # Ajuste eps_km selon la densité des villes
    cluster_grouped = df_with_clusters.groupby('city_cluster')
    cities = pd.DataFrame()
    cities['stop_lat'] = cluster_grouped['stop_lat'].mean()
    cities['stop_lon'] = cluster_grouped['stop_lon'].mean()
    cities_list_stops = cluster_grouped.apply(lambda x: x['stop_name'].tolist(), include_groups = False)
    cities['max_distance'] = cluster_grouped.apply(lambda x: utils.euclidean_distance(x['stop_lat'], x['stop_lon'], cities.loc[x.name, 'stop_lat'], cities.loc[x.name, 'stop_lon']).max(), include_groups=False)
    cities['stop_name'] = cities_list_stops.apply(utils.choosing_city_name)
    cities = cities.set_index('stop_name')
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
    analyzers["BLABLABUS"] = utils.load_class_analyzer("BLABLABUS")
    analyzers["DB-LONG"] = utils.load_class_analyzer("DB-LONG")
    analyzers["DB-REGIONAL"] = utils.load_class_analyzer("DB-REGIONAL")
    analyzers["EUROSTAR"] = utils.load_class_analyzer("EUROSTAR")
    return analyzers


@st.cache_data
def get_trips_to_city(
    departure_lat: float,
    departure_lon: float,
    arrival_lat: float,
    arrival_lon: float,
    periode: tuple[datetime, datetime],
    _analyzers: dict[str, Analyzer],
    transport_type: list[str],
    departure_time: time,
    max_distance: float
) -> pd.DataFrame:
    date_min = periode[0]
    date_max = periode[1]

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
        max_distance
    )

    # Drop les duplicates (SNCF et DB ont des doublons en communs, comment comparer deux datetime avec des timezones différentes ?)
    trips_duplicated = raw_trips.drop_duplicates(subset=["dep_time"], keep="first")
    trips = trips_duplicated.sort_values(by="dep_time", ascending=True)
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
    max_distance: float
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
                max_distance
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
    max_distance: float
) -> pd.DataFrame:
    trips = _analyzer.find_trips_between_locations(
        departure_lat, departure_lon, arrival_lat, arrival_lon, date_min, date_max, departure_time, max_distance
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
    max_distance: float,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    date_min = periode[0]
    date_max = periode[1]
    destinations_duplicates = {}
    df_concat = pd.DataFrame()

    for key, analyzer in _analyzers.items():
        if key in transport_type:
            destinations_duplicates[key] = analyzer.find_destinations_from_location(lat, lon, date_min, date_max, max_distance)
            df_concat = pd.concat([df_concat, destinations_duplicates[key]])
    # 
    destinations = cities[cities.index.isin(df_concat["stop_name"])]
    return destinations_duplicates, destinations


@st.cache_data
def generate_map_with_marker(lat: float, lon: float, destinations: dict[str, pd.DataFrame]) -> fl.FeatureGroup:
    fg = fl.FeatureGroup("Markers")
    fg.add_child(fl.Marker([lat, lon], popup="Ville de départ", icon=fl.Icon(color="white")))
    color = {"TER": "red", "TGV": "black", "INTERCITE": "gray", "FLIXBUS": "green", "BLABLABUS": "blue", "DB-LONG": "orange", "EUROSTAR": "purple", "DB-REGIONAL": "pink"}
    for key, destinations_analyzer in destinations.items():
        color_transport = color[key]
        for row in destinations_analyzer.itertuples():
            fg.add_child(
                fl.Marker(
                    [float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, icon=fl.Icon(color=color_transport)
                )
            )
    return fg
