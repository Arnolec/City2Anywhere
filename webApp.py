# webApp.py
import folium as fl
from AnalyzerGTFS import AnalyzerGTFS as Ana
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd
import datetime
import geopandas as gpd
from shapely.geometry import Point

st.set_page_config(layout="wide")

def get_pos(lat, lng):
    return lat, lng

# Dans le cache car effectué qu'une seule fois pour initialiser les variables au lancement de l'application
@st.cache_data
def init_var():
    zoom = 5
    fg = fl.FeatureGroup("Markers")
    previous_city = None
    destinations = {}
    destination_selected = None
    return zoom, fg, previous_city, destinations, destination_selected

@st.cache_data
def get_cities():
    cities = {}
    cities_TER = Ana.list_of_cities('TER') 
    cities_TGV = Ana.list_of_cities('TGV') 
    cities_INTERCITE = Ana.list_of_cities('INTERCITE') 
    cities_concat = pd.concat([cities_TER, cities_TGV, cities_INTERCITE])
    cities_concat = cities_concat.drop_duplicates(subset=['stop_id'])

    for row in cities_concat.itertuples():
        cities[row.stop_name] = (row.stop_lat, row.stop_lon, row.stop_id)
    return cities

@st.cache_data
def get_center():
    serie = pd.Series(cities)
    serie_points = serie.apply(lambda x: Point(x[0], x[1]))
    geo_series = gpd.GeoSeries(serie_points)
    centroid = geo_series.unary_union.centroid
    return (centroid.x, centroid.y)

@st.cache_data
def load_analyzers():
    analyzer_TER = Ana(path ='TER')
    analyzer_TGV = Ana(path = 'TGV')
    analyzer_INTERCITE = Ana(path = 'INTERCITE')
    return analyzer_TER, analyzer_TGV, analyzer_INTERCITE

def get_trips_to_city(city_id):
    trips_TER = analyzer_TER.trajet_destination(city_id)
    trips_TGV = analyzer_TGV.trajet_destination(city_id)
    trips_INTERCITE = analyzer_INTERCITE.trajet_destination(city_id)
    return trips_TER, trips_TGV, trips_INTERCITE

def print_map(lat, lon, periode):
    date_min = periode[0].strftime('%Y%m%d')
    date_max = periode[1].strftime('%Y%m%d')

    analyzer_TER.load_search(lat, lon, date_min, date_max)
    destinations_TER = analyzer_TER.get_destinations()
    
    analyzer_TGV.load_search(lat, lon, date_min, date_max)
    destinations_TGV = analyzer_TGV.get_destinations()

    analyzer_INTERCITE.load_search(lat, lon, date_min, date_max)
    destinations_INTERCITE = analyzer_INTERCITE.get_destinations()

    destinations = {}
    destinations['-'] = (lat, lon, '0')
    fg = fl.FeatureGroup("Markers")
    fg.add_child(fl.Marker([float(lat), float(lon)], popup="Ville de départ", icon=fl.Icon(color="blue")))

    for row in destinations_TER.itertuples():
        fg.add_child(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, icon=fl.Icon(color="red")))
        destinations[row.stop_name] = (row.stop_lat, row.stop_lon, row.stop_id)
    for row in destinations_TGV.itertuples():
        fg.add_child(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, icon=fl.Icon(color="black")))
        destinations[row.stop_name] = (row.stop_lat, row.stop_lon, row.stop_id)
    for row in destinations_INTERCITE.itertuples():
        fg.add_child(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, icon=fl.Icon(color="gray")))
        destinations[row.stop_name] = (row.stop_lat, row.stop_lon, row.stop_id)
    #fg.on('click', lambda e: print(e))
    return fg, destinations

analyzer_TER,analyzer_TGV,analyzer_INTERCITE = load_analyzers()
cities = get_cities()
centroid_cities = get_center()
zoom_map, fg, previous_city, destinations, destination_selected = init_var()

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
            fg, destinations = print_map(cities[city_selected][0], cities[city_selected][1], date)

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
        trips_TER, trips_TGV, trips_INTERCITE = get_trips_to_city(destinations[destination_selected][2])
        st.write("Trajets disponibles pour la destination : ", destination_selected)
        if not trips_TER.empty:
            with st.container():
                st.subheader("TER :")
                for row in trips_TER.itertuples():
                    container = st.container(height=80,border=True)
                    with container:
                        col2_1, col2_2 = st.columns([0.5, 0.5], gap= 'small' , vertical_alignment= "top")
                        with col2_1:
                            st.write("Départ :", city_selected)
                            st.write("Heure de départ : ", row.temps_ville)
                            #st.write("Jour suivant départ : ", row.jour_suivant_depart)
                        with col2_2:
                            st.write("Arrivée :", destination_selected)
                            st.write("Heure d'arrivée : ", row.departure_time)
                            #st.write("Jour suivant arrivée : ", row.jour_suivant_arrivee)
        if not trips_TGV.empty:
            with st.container():
                st.subheader("TGV :")
                for row in trips_TGV.itertuples():
                    container = st.container(height=80,border=True)
                    with container:
                        col2_1, col2_2 = st.columns([0.5, 0.5], gap= 'small' , vertical_alignment= "top")
                        with col2_1:
                            st.write("Départ :", city_selected)
                            st.write("Heure de départ : ", row.temps_ville)
                        with col2_2:
                            st.write("Arrivée :", destination_selected)
                            st.write("Heure d'arrivée : ", row.departure_time)
        if not trips_INTERCITE.empty:
            with st.container():
                st.subheader("INTERCITE :")
                for row in trips_INTERCITE.itertuples():
                    container = st.container(height=80,border=True)
                    with container:
                        col2_1, col2_2 = st.columns([0.5, 0.5], gap= 'small' , vertical_alignment= "top")
                        with col2_1:
                            st.write("Départ :", city_selected)
                            st.write("Heure de départ : ", row.temps_ville)
                        with col2_2:
                            st.write("Arrivée :", destination_selected)
                            st.write("Heure d'arrivée : ", row.departure_time)