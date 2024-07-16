# webApp.py
import folium as fl
from streamlit_folium import st_folium
import streamlit as st
import datetime
import back_requests as br
#import utils

st.set_page_config(layout="wide")




analyzers = br.load_analyzers()
cities = br.get_cities()
centroid_cities = br.get_center(cities)
zoom_map, fg, previous_city, destinations, destination_selected = br.init_var()

col1, col2= st.columns([0.6,0.4], gap= 'medium', vertical_alignment= "top")

with col1:
    city_selected = st.selectbox(
    "Sélectionnez une ville :", 
    cities.keys()
    )

    today = datetime.datetime.now()
    next_year = today.year + 1
    date = st.date_input(
        'Période envisagée pour le séjour :',
        (today, today),
        min_value=today,
        max_value=datetime.datetime(next_year, today.month, today.day))

    if (city_selected is not None) and (city_selected != previous_city):
        previous_city = city_selected
        if len(date) == 2:
            fg, destinations, analyzers = br.print_map(cities[city_selected][0], cities[city_selected][1], date, analyzers)

    m = fl.Map()

    map = st_folium(
        m,
        center=centroid_cities,
        zoom=zoom_map,
        height=600,
        width=1000,
        key = 'new',
        feature_group_to_add=fg)

with col2:
    destination_selected = st.selectbox(
        "Destinations :",
        destinations.keys()
    )
    if destination_selected is not None and destination_selected != '-':
        trips = br.get_trips_to_city(destinations[destination_selected][2], analyzers)
        st.write("Trajets disponibles pour la destination : ", destination_selected)
        for key, values in trips.items():
            if not values.empty:
                with st.container():
                    st.subheader(key + " :")
                    for row in values.itertuples():
                        container = st.container(height=120,border=True)
                        with container:
                            col2_1, col2_2 = st.columns([0.5, 0.5], gap= 'small' , vertical_alignment= "top")
                            with col2_1:
                                st.write("Départ :", city_selected)
                                st.write("Heure de départ : ", row.horaire_depart)
                                #date_dep = row.date + datetime.timedelta(days = row.jour_suivant_depart)
                                #st.write("Jour de départ : ", date_dep)
                            with col2_2:
                                st.write("Arrivée :", destination_selected)
                                st.write("Heure d'arrivée : ", row.horaire_arrivee)
                                #date_arr = row.date + datetime.timedelta(days = row.jour_suivant_arrivee)

