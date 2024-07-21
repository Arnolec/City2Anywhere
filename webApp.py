# webApp.py
import folium as fl
from streamlit_folium import st_folium
import streamlit as st
import datetime
import back_requests as br

# import utils

st.set_page_config(layout="wide")

analyzers = br.load_analyzers()
cities = br.get_cities()
centroid_cities = br.get_center(cities)
zoom_map, fg, previous_city, destinations, destination_selected, trips = br.init_var()

with st.container():
    col_settings_1, col_settings_2 = st.columns([0.6, 0.4], gap="small", vertical_alignment="top")
    with col_settings_1:
        col_settings_1_1, col_settings_1_2, col_settings_1_3 = st.columns(
            [0.4, 0.4, 0.2], gap="small", vertical_alignment="top"
        )
        with col_settings_1_1:
            city_selected = st.selectbox("Sélectionnez une ville :", cities.index)
        with col_settings_1_2:
            transport_type = st.multiselect(
                "Type de transport :", ["TER", "TGV", "INTERCITE"], default=["TER", "TGV", "INTERCITE"]
            )
        with col_settings_1_3:
            today = datetime.datetime.now()
            next_year = today.year + 1
            date = st.date_input(
                "Période envisagée pour le séjour :",
                (today, today),
                min_value=today,
                max_value=datetime.datetime(next_year, today.month, today.day),
            )

    with col_settings_2:
        destinations_mixed_transport, destinations = br.get_destinations(
            cities.loc[city_selected]["stop_lat"],
            cities.loc[city_selected]["stop_lon"],
            date,
            transport_type,
            analyzers,
        )
        destination_selected = st.selectbox("Destinations :", destinations.keys())
        col_settings_2_1, col_settings_2_2, col_settings_2_3 = st.columns(
            [0.4, 0.3, 0.3], gap="small", vertical_alignment="top"
        )
        with col_settings_2_1:
            sort = st.selectbox("Tri :", ["Jour", "Heure de départ", "Heure d'arrivée"])
        with col_settings_2_2:
            max_trips_printed = st.selectbox("Nombre de trajets affichés :", [5, 10, 25, "Tout afficher"])
        with col_settings_2_3:
            departure_time = st.time_input("Heure de départ :", datetime.time(8, 0), step=datetime.timedelta(hours=1))
col1, col2 = st.columns([0.6, 0.4], gap="medium", vertical_alignment="top")

with col1:
    if (city_selected is not None) and (city_selected != previous_city):
        previous_city = city_selected
        if len(date) == 2:
            fg = br.print_map(
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
            sort,
            max_trips_printed,
            transport_type,
            departure_time,
        )
    st.subheader("Trajets trouvé selon les critères : ", destination_selected)
    for key, values in trips.items():
        if not values.empty:
            with st.container():
                st.subheader(key + " :")
                for row in values.itertuples():
                    container = st.container(height=120, border=True)
                    with container:
                        col2_1, col2_2 = st.columns([0.5, 0.5], gap="small", vertical_alignment="top")
                        with col2_1:
                            st.write("Départ :", city_selected)
                            st.write("Heure de départ : ", row.horaire_depart)
                            # date_dep = row.date + datetime.timedelta(days = row.jour_suivant_depart)
                            # st.write("Jour de départ : ", date_dep)
                        with col2_2:
                            st.write("Arrivée :", destination_selected)
                            st.write("Heure d'arrivée : ", row.horaire_arrivee)
                            # date_arr = row.date + datetime.timedelta(days = row.jour_suivant_arrivee)
