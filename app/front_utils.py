from typing import Optional

import folium as fl
import pandas as pd
import streamlit as st

# Useful file to build front and ask request only once if needed and parameters do not change


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
    zoom = 5
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
