# webApp.py
import datetime

import folium as fl
import front_utils as utils
import pandas as pd
import pytz
import streamlit as st
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

cities = utils.get_cities()
centroid_cities = utils.get_center()
transports = utils.get_transport()
(
    zoom_map,
    fg,
    previous_city,
    destinations,
    destination_selected,
    trips,
    trips_to_print,
) = utils.initialize_variables()

if "previous_trips" not in st.session_state:
    st.session_state.previous_trips = pd.DataFrame()
if "max_trips_printed" not in st.session_state:
    st.session_state.max_trips_printed = 10
if "trips_to_print" not in st.session_state:
    st.session_state.trips_to_print = pd.DataFrame()


def callback_increment(max_trips: int, dataframe_len) -> None:
    st.session_state.max_trips_printed = min(max_trips + 10, dataframe_len)


with st.container():
    col_settings_1, col_settings_2 = st.columns([0.6, 0.4], gap="small")
    with col_settings_1:
        col_settings_1_1, col_settings_1_2 = st.columns([0.5, 0.5], gap="small")
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
                transports,
                default=transports,
            )
    with col_settings_2:
        if len(date) == 2 and city_selected is not None:
            destinations = utils.get_destinations(
                cities.loc[city_selected]["stop_lat"],
                cities.loc[city_selected]["stop_lon"],
                transport_type,
                date,
            )
        destination_selected = selectbox("Destinations :", destinations.index)
        col_settings_2_1, col_settings_2_2 = st.columns([0.5, 0.5], gap="small")
        with col_settings_2_1:
            departure_time = st.time_input(
                "Heure de départ :",
                datetime.time(8, 0),
                step=datetime.timedelta(hours=1),
            )

col1, col2 = st.columns([0.6, 0.4], gap="medium")

with col1:
    if (city_selected is not None) and (city_selected != previous_city):
        previous_city = city_selected
        if len(date) == 2:
            fg = utils.generate_map_with_marker(
                cities.loc[city_selected]["stop_lat"],
                cities.loc[city_selected]["stop_lon"],
                destinations,
            )

    m = fl.Map()

    map = st_folium(
        m,
        center=centroid_cities,
        zoom=zoom_map,
        height=600,
        width=1000,
        key="new",
        feature_group_to_add=fg,
    )

with col2:
    if (destination_selected is not None) and (destination_selected != "-"):
        trips = utils.get_trips(
            cities.loc[city_selected]["stop_lat"],
            cities.loc[city_selected]["stop_lon"],
            destinations.loc[destination_selected]["stop_lat"],
            destinations.loc[destination_selected]["stop_lon"],
            date,
            transport_type,
            departure_time,
        )
        if not trips.equals(st.session_state.previous_trips):
            st.session_state.previous_trips = trips
            st.session_state.max_trips_printed = 10

        if len(trips) == 0:
            st.write("Aucun trajet trouvé")

    st.session_state.trips_to_print = trips.iloc[: st.session_state.max_trips_printed]
    st.subheader("Trajets : ", destination_selected)
    with st.container(height=550, border=True):
        for trip in st.session_state.trips_to_print.itertuples():
            container = st.container(height=180, border=True)
            with container:
                dep_time = trip.dep_time
                arr_time = trip.arr_time
                departure_time = dep_time.astimezone(pytz.timezone(trip.stop_timezone_x))
                arrival_time = arr_time.astimezone(pytz.timezone(trip.stop_timezone_y))

                if dep_time.day != arr_time.day:
                    st.write(
                        "Trajet nocturne sur 2 jours, du ",
                        datetime.datetime.strftime(dep_time, format="%d-%m"),
                        " au ",
                        datetime.datetime.strftime(arr_time, format="%d-%m"),
                    )
                else:
                    st.write(
                        "Trajet du ",
                        datetime.datetime.strftime(dep_time, format="%d-%m"),
                    )
                col2_1, col2_2, col2_3 = st.columns([0.4, 0.2, 0.4], gap="small")
                with col2_1:
                    st.write(trip.stop_name_x)
                    st.write(
                        "Heure de départ : ",
                        datetime.datetime.strftime(departure_time, format="%Hh%M"),
                    )
                    if (
                        departure_time.utcoffset() != arrival_time.utcoffset()
                        or departure_time.utcoffset()
                        != datetime.datetime.now(pytz.timezone("Europe/Paris")).utcoffset()
                    ):
                        st.write("Fuseau horaire : ", trip.stop_timezone_x)
                with col2_2:
                    duration = (arr_time - dep_time).total_seconds()
                    string_duration = datetime.datetime.fromtimestamp(duration, tz=pytz.UTC).strftime("%Hh%M")
                    days = f"{int(duration/86400)} jour " if int(duration / 86400) > 0 else ""
                    st.write(
                        "Durée : ",
                        days + string_duration + "",
                    )
                    st.write("Transport : ", trip.transport_type)
                with col2_3:
                    st.write(trip.stop_name_y)
                    st.write(
                        "Heure d'arrivée : ",
                        datetime.datetime.strftime(arrival_time, format="%Hh%M"),
                    )
                    if (
                        departure_time.utcoffset() != arrival_time.utcoffset()
                        or departure_time.utcoffset()
                        != datetime.datetime.now(pytz.timezone("Europe/Paris")).utcoffset()
                    ):
                        st.write("Fuseau horaire : ", trip.stop_timezone_y)
        if len(trips) > st.session_state.max_trips_printed:
            show_more = st.button(
                "Afficher plus de trajets",
                on_click=callback_increment,
                args=(st.session_state.max_trips_printed, len(trips)),
            )
