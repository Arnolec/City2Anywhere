# webApp.py
import folium as fl
from streamlit_folium import st_folium
import streamlit as st
import streamlit.components.v1 as components
import datetime
import back_requests as br

# import utils

st.set_page_config(layout="wide")

analyzers = br.load_analyzers()
cities = br.fetch_cities(analyzers)
centroid_cities = br.fetch_center(cities)
zoom_map, fg, previous_city, destinations, destination_selected, trips = br.initialize_variables()

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
            )
        destination_selected = st.selectbox("Destinations :", destinations.keys())
        col_settings_2_1, col_settings_2_2 = st.columns([0.5, 0.5], gap="small", vertical_alignment="top")
        with col_settings_2_1:
            departure_time = st.time_input("Heure de départ :", datetime.time(8, 0), step=datetime.timedelta(hours=1))
        with col_settings_2_2:
            max_trips_printed = st.selectbox("Nombre de trajets affichés :", [5, 10, 25, "Tout afficher"])

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
            destinations[destination_selected][0],
            destinations[destination_selected][1],
            date,
            analyzers,
            max_trips_printed,
            transport_type,
            departure_time,
        )
    st.subheader("Trajets : ", destination_selected)
    for key, values in trips.items():
        if not values.empty:
            with st.container():
                st.subheader(key + " :")
                for row in values.itertuples():
                    container = st.container(height=120, border=True)
                    with container:
                        if row.horaire_depart.day != row.horaire_arrivee.day:
                            st.write(
                                "Trajet nocturne sur 2 jours, du ",
                                datetime.datetime.strftime(row.horaire_depart, format="%d-%m"),
                                " au ",
                                datetime.datetime.strftime(row.horaire_arrivee, format="%d-%m"),
                            )
                        else:
                            st.write("Trajet du ", datetime.datetime.strftime(row.horaire_depart, format="%d-%m"))
                        col2_1, col2_2, col2_3 = st.columns([0.4, 0.2, 0.4], gap="small", vertical_alignment="top")
                        with col2_1:
                            st.write(city_selected)
                            st.write(
                                "Heure de départ : ", datetime.datetime.strftime(row.horaire_depart, format="%Hh%M")
                            )
                        with col2_2:
                            duree = (row.departure_time_y - row.departure_time_x).total_seconds()
                            st.write(
                                "Durée : ",
                                datetime.datetime.fromtimestamp(duree, tz=datetime.UTC).strftime("%Hh%M") + "",
                            )
                        with col2_3:
                            st.write(destination_selected)
                            st.write(
                                "Heure d'arrivée : ", datetime.datetime.strftime(row.horaire_arrivee, format="%Hh%M")
                            )
