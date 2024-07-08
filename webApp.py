# webApp.py
import folium as fl
from AnalyzerGTFS import AnalyzerGTFS as Ana
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd
import datetime



def get_pos(lat, lng):
    return lat, lng

def get_cities():
    cities = {}
    cities_TER = Ana.list_of_cities('TER') 
    cities_TGV = Ana.list_of_cities('TGV') 
    cities_INTERCITE = Ana.list_of_cities('INTERCITE') 
    cities_concat = pd.concat([cities_TER, cities_TGV, cities_INTERCITE])
    cities_concat = cities_concat.drop_duplicates(subset=['stop_id'])

    for row in cities_concat.itertuples():
        #cities.append((row.stop_name, row.stop_lat, row.stop_lon))
        cities[row.stop_name] = (row.stop_lat, row.stop_lon,row.stop_id)
    return cities
    

def print_map(lat, lon, periode):
    date_min = periode[0].strftime('%Y%m%d')
    date_max = periode[1].strftime('%Y%m%d')

    analyzer_TER = Ana(lat, lon, date_min, date_max, path ='TER' )
    destinations_TER = analyzer_TER.get_destinations()
    
    analyzer_TGV = Ana(lat, lon, date_min, date_max, path = 'TGV')
    destinations_TGV = analyzer_TGV.get_destinations()

    analyzer_INTERCITE= Ana(lat, lon, date_min, date_max, path = 'INTERCITE')
    destinations_INTERCITE = analyzer_INTERCITE.get_destinations()

    st.session_state["markers"] = []
    st.session_state["markers"].append(fl.Marker([lat, lon], popup="You are here", color = "red"))

    for row in destinations_TER.itertuples():
        st.session_state["markers"].append(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, color = "green"))
    for row in destinations_TGV.itertuples():
        st.session_state["markers"].append(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, color = "yellow"))
    for row in destinations_INTERCITE.itertuples():
        st.session_state["markers"].append(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, color = "black"))

if 'center' not in st.session_state:
    st.session_state.center = [46.903354, 1.888334]
if 'zoom' not in st.session_state:
    st.session_state.zoom = 5
if 'markers' not in st.session_state:
    st.session_state.markers = []

if 'cities' not in st.session_state:
    st.session_state.cities = get_cities()

# Permet d'éviter des actualisations inutiles si la ville n'a pas changé
if 'previous_city' not in st.session_state:
    st.session_state.previous_city = None

city_selected = st.selectbox(
    "Sélectionnez une ville :", 
    st.session_state.cities.keys()
    )


data = None

today = datetime.datetime.now()
next_year = today.year + 1
date = st.date_input('Période envisagée pour le séjour :', (today, today), min_value=today, max_value=datetime.datetime(next_year, today.month, today.day))

if (city_selected is not None) and (city_selected != st.session_state.previous_city):
    st.session_state.center = [st.session_state.cities[city_selected][0], st.session_state.cities[city_selected][1]]
    st.session_state.zoom = 7
    st.session_state.previous_city = city_selected
    if len(date) == 2:
        print_map(st.session_state.cities[city_selected][0], st.session_state.cities[city_selected][1], date)


fg = fl.FeatureGroup("Markers")
for marker in st.session_state["markers"]:
    fg.add_child(marker)

m = fl.Map(location=[46.9,1.89], zoom_start=9)

map = st_folium(
    m,
    center=st.session_state["center"],
    zoom=st.session_state["zoom"],
    height=500,
    width=1000,
    key = 'new',
    feature_group_to_add=fg)


if map.get("last_clicked"):
    data = get_pos(map["last_clicked"]["lat"], map["last_clicked"]["lng"])

if data is not None:
    fg = print_map(data[0], data[1], date)
    st.write(data) # Writes to the app
    print(data) # Writes to terminal

