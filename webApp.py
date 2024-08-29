# webApp.py
import folium as fl
from streamlit_folium import st_folium
import streamlit as st
import datetime
import back_requests as br
from streamlit_extras.no_default_selectbox import selectbox
import pandas as pd

st.set_page_config(layout="wide")

br.update_data()
analyzers = br.load_analyzers()
cities = br.fetch_cities(analyzers)
centroid_cities = br.fetch_center(cities)
zoom_map, fg, previous_city, destinations, destination_selected, trips, trips_to_print = br.initialize_variables()

if not "previous_trips" in st.session_state:
    st.session_state.previous_trips = pd.DataFrame()
if not "max_trips_printed" in st.session_state:
    st.session_state.max_trips_printed = 10
if not "trips_to_print" in st.session_state:
    st.session_state.trips_to_print = pd.DataFrame()


def callback_increment(max_trips: int, dataframe_len) -> None:
    st.session_state.max_trips_printed = min(max_trips + 10, dataframe_len)


with st.container():
    col_settings_1, col_settings_2 = st.columns([0.6, 0.4], gap="small", vertical_alignment="top")
    with col_settings_1:
        col_settings_1_1, col_settings_1_2 = st.columns([0.5, 0.5], gap="small", vertical_alignment="top")
        with col_settings_1_1:
            city_selected = st.selectbox("Sélectionnez une ville :", cities.index)
            today = datetime.datetime.now()
            next_year = today.year + 1
            date = st.date_input(
                "Période du départ :",
                (today, today),
                min_value=today,
                max_value=datetime.datetime(next_year, today.month, today.day),
            )
        with col_settings_1_2:
            transport_type = st.multiselect(
                "Type de transport :",
                ["TER", "TGV", "INTERCITE", "FLIXBUS"],
                default=["TER", "TGV", "INTERCITE", "FLIXBUS"],
            )
    with col_settings_2:
        if len(date) == 2:
            destinations_mixed_transport, destinations = br.get_destinations(
                cities.loc[city_selected]["stop_lat"],
                cities.loc[city_selected]["stop_lon"],
                date,
                transport_type,
                analyzers,
                cities,
            )
        destination_selected = selectbox("Destinations :", destinations.index)
        col_settings_2_1, col_settings_2_2 = st.columns([0.5, 0.5], gap="small", vertical_alignment="top")
        with col_settings_2_1:
            departure_time = st.time_input("Heure de départ :", datetime.time(8, 0), step=datetime.timedelta(hours=1))

col1, col2 = st.columns([0.6, 0.4], gap="medium", vertical_alignment="top")

with col1:
    if (city_selected is not None) and (city_selected != previous_city):
        previous_city = city_selected
        if len(date) == 2:
            fg = br.generate_map_with_marker(
                cities.loc[city_selected]["stop_lat"],
                cities.loc[city_selected]["stop_lon"],
                destinations_mixed_transport,
            )

    m = fl.Map()

    map = st_folium(
        m, center=centroid_cities, zoom=zoom_map, height=600, width=1000, key="new", feature_group_to_add=fg
    )

with col2:
    if (destination_selected is not None) and (destination_selected != "-"):
        trips = br.get_trips_to_city(
            cities.loc[city_selected]["stop_lat"],
            cities.loc[city_selected]["stop_lon"],
            destinations.loc[destination_selected]["stop_lat"],
            destinations.loc[destination_selected]["stop_lon"],
            date,
            analyzers,
            transport_type,
            departure_time,
        )
        if not trips.equals(st.session_state.previous_trips):
            st.session_state.previous_trips = trips
            st.session_state.max_trips_printed = 10

    st.session_state.trips_to_print = trips.iloc[: st.session_state.max_trips_printed]
    st.subheader("Trajets : ", destination_selected)
    for trip in st.session_state.trips_to_print.itertuples():
        container = st.container(height=150, border=True)
        with container:
            if trip.dep_time.day != trip.arr_time.day:
                st.write(
                    "Trajet nocturne sur 2 jours, du ",
                    datetime.datetime.strftime(trip.dep_time, format="%d-%m"),
                    " au ",
                    datetime.datetime.strftime(trip.arr_time, format="%d-%m"),
                )
            else:
                st.write("Trajet du ", datetime.datetime.strftime(trip.dep_time, format="%d-%m"))
            col2_1, col2_2, col2_3 = st.columns([0.4, 0.2, 0.4], gap="small", vertical_alignment="top")
            with col2_1:
                st.write(city_selected)
                st.write("Heure de départ : ", datetime.datetime.strftime(trip.dep_time, format="%Hh%M"))
            with col2_2:
                duree = (trip.departure_time_y - trip.departure_time_x).total_seconds()
                st.write(
                    "Durée : ",
                    datetime.datetime.fromtimestamp(duree, tz=datetime.UTC).strftime("%Hh%M") + "",
                )
                st.write("Transport : ", trip.transport_type)
            with col2_3:
                st.write(destination_selected)
                st.write("Heure d'arrivée : ", datetime.datetime.strftime(trip.arr_time, format="%Hh%M"))
    if len(trips) > st.session_state.max_trips_printed:
        show_more = st.button(
            "Afficher plus de trajets",
            on_click=callback_increment,
            args=(st.session_state.max_trips_printed, len(trips)),
        )
