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

@st.cache_data
def get_cities():
    cities = {}
    cities_TER = Ana.list_of_cities('TER') 
    cities_TGV = Ana.list_of_cities('TGV') 
    cities_INTERCITE = Ana.list_of_cities('INTERCITE') 
    cities_concat = pd.concat([cities_TER, cities_TGV, cities_INTERCITE])
    cities_concat = cities_concat.drop_duplicates(subset=['stop_id'])

    for row in cities_concat.itertuples():
        #cities.append((row.stop_name, row.stop_lat, row.stop_lon))
        cities[row.stop_name] = (row.stop_lat, row.stop_lon)
    return cities

@st.cache_data
def get_center():
    serie = pd.Series(st.session_state.cities)
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

def print_map(lat, lon, periode):
    date_min = periode[0].strftime('%Y%m%d')
    date_max = periode[1].strftime('%Y%m%d')

    analyzer_TER.load_search(lat, lon, date_min, date_max)
    destinations_TER = analyzer_TER.get_destinations()
    
    analyzer_TGV.load_search(lat, lon, date_min, date_max)
    destinations_TGV = analyzer_TGV.get_destinations()

    analyzer_INTERCITE.load_search(lat, lon, date_min, date_max)
    destinations_INTERCITE = analyzer_INTERCITE.get_destinations()

    st.session_state["markers"] = []
    st.session_state["markers"].append(fl.Marker([lat, lon], popup="You are here", color = "red"))

    for row in destinations_TER.itertuples():
        st.session_state["markers"].append(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, icon=fl.Icon(color="red")))
    for row in destinations_TGV.itertuples():
        st.session_state["markers"].append(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, icon=fl.Icon(color="black")))
    for row in destinations_INTERCITE.itertuples():
        st.session_state["markers"].append(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, color = "yellow"))

analyzer_TER,analyzer_TGV,analyzer_INTERCITE = load_analyzers()

if 'zoom' not in st.session_state:
    st.session_state.zoom = 5
if 'markers' not in st.session_state:
    st.session_state.markers = []
if 'cities' not in st.session_state:
    st.session_state.cities = get_cities()
if 'center' not in st.session_state:
    st.session_state.center = get_center()

# Permet d'éviter des actualisations inutiles si la ville n'a pas changé
if 'previous_city' not in st.session_state:
    st.session_state.previous_city = None



col1, col2, col3 = st.columns(3)

with col1:
    city_selected = st.selectbox(
    "Sélectionnez une ville :", 
    st.session_state.cities.keys()
    )


today = datetime.datetime.now()
next_year = today.year + 1
with col2:
    date = st.date_input('Période envisagée pour le séjour :',
                            (today, today),
                            min_value=today,
                            max_value=datetime.datetime(next_year, today.month, today.day))


if (city_selected is not None) and (city_selected != st.session_state.previous_city):
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
    height=700,
    width=1200,
    key = 'new',
    feature_group_to_add=fg)