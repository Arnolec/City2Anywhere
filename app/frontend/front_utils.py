from datetime import datetime, time
from typing import Optional

import folium as fl
import pandas as pd
import requests
import streamlit as st
import os

# Useful file to build front and ask request only once if needed and parameters do not change
backend_url = os.getenv(
    "BACKEND_URL", "http://localhost:8000"
)  # Valeur par défaut : localhost pour l'environnement local


@st.cache_data
def initialize_variables() -> tuple[
    int,
    fl.FeatureGroup,
    Optional[str],
    pd.DataFrame,
    Optional[str],
    pd.DataFrame,
    pd.DataFrame,
]:
    zoom = 8
    fg = fl.FeatureGroup("Markers")
    previous_city: Optional[str] = None
    destinations: pd.DataFrame = pd.DataFrame()
    destination_selected: Optional[str] = None
    trips: pd.DataFrame = pd.DataFrame()
    trips_to_print: pd.DataFrame = pd.DataFrame()
    return (
        zoom,
        fg,
        previous_city,
        destinations,
        destination_selected,
        trips,
        trips_to_print,
    )


@st.cache_data
def generate_map_with_marker(lat: float, lon: float, destinations: pd.DataFrame) -> fl.FeatureGroup:
    fg = fl.FeatureGroup("Markers")
    fg.add_child(fl.Marker([lat, lon], popup="Ville de départ", icon=fl.Icon(color="white")))
    color = {
        "TER": "red",
        "TGV": "black",
        "INTERCITE": "gray",
        "FLIXBUS": "green",
        "BLABLABUS": "blue",
        "DB-LONG": "orange",
        "EUROSTAR": "purple",
        "DB-REGIONAL": "pink",
    }
    for dest in destinations.itertuples():
        fg.add_child(
            fl.Marker(
                [dest.stop_lat, dest.stop_lon],
                popup=dest.Index,
                icon=fl.Icon(color=color[dest.transport]),
            )
        )

    return fg


@st.cache_data
def get_cities() -> pd.DataFrame:
    try:
        cities = requests.get(f"{backend_url}/v1/list_cities/").json()
    except requests.ConnectionError:
        return pd.DataFrame()
    return pd.DataFrame(cities)


@st.cache_data
def get_destinations(lat: float, lon: float, transport_type: list[str], periode: tuple[str, str]) -> pd.DataFrame:
    start = periode[0].strftime("%Y-%m-%dT%H:%M:%S")
    end = periode[1].strftime("%Y-%m-%dT%H:%M:%S")
    params = {"coords": {"lat": lat, "lon": lon}, "periode": {"start": start, "end": end}, "transport": transport_type}
    try:
        destinations = requests.patch(f"{backend_url}/v1/destinations/", json=params).json()
    except requests.ConnectionError:
        return pd.DataFrame()
    return pd.DataFrame(destinations)


@st.cache_data
def get_trips(
    dep_lat: float,
    dep_lon: float,
    arr_lat: float,
    arr_lon: float,
    periode: tuple[datetime, datetime],
    transport_type: list[str],
    departure_time: time,
) -> pd.DataFrame:
    start = periode[0].strftime("%Y-%m-%dT%H:%M:%S")
    end = periode[1].strftime("%Y-%m-%dT%H:%M:%S")
    params = {
        "dep_coords": {"lat": dep_lat, "lon": dep_lon},
        "arr_coords": {"lat": arr_lat, "lon": arr_lon},
        "periode": {"start": start, "end": end},
        "transport": transport_type,
        "dep_time": departure_time.strftime("%H:%M:%S"),
    }
    try:
        trips = requests.patch(f"{backend_url}/v1/trips/", json=params).json()
    except requests.ConnectionError:
        return pd.DataFrame()
    df = pd.DataFrame(trips)
    df["dep_time"] = df["dep_time"].apply(lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S%z"))
    df["arr_time"] = df["arr_time"].apply(lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S%z"))
    df = df.sort_values(by="dep_time")
    return pd.DataFrame(df)


@st.cache_data
def get_center() -> Optional[tuple[float, float]]:
    try:
        center = requests.get(f"{backend_url}/v1/center/").json()
    except requests.ConnectionError:
        return [0, 0]
    if center is None:
        return [0, 0]
    return center


@st.cache_data
def get_transport() -> Optional[list[str]]:
    try:
        transport = requests.get(f"{backend_url}/v1/transports/").json()
    except requests.ConnectionError:
        return []
    transport = transport["transport_types"]
    if transport is None:
        return []
    return transport
