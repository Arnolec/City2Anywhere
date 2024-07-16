
import folium as fl
from AnalyzerGTFS import AnalyzerGTFS as Ana
import pandas as pd
import streamlit as st
import geopandas as gpd
from shapely.geometry import Point
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
def get_center(cities):
    serie = pd.Series(cities)
    serie_points = serie.apply(lambda x: Point(x[0], x[1]))
    geo_series = gpd.GeoSeries(serie_points)
    centroid = geo_series.unary_union.centroid
    return (centroid.x, centroid.y)

@st.cache_data
def load_analyzers():
    analyzers = {}
    analyzers['TER'] = Ana(path ='TER')
    analyzers['TGV'] = Ana(path = 'TGV')
    analyzers['INTERCITE'] = Ana(path = 'INTERCITE')
    return analyzers

@st.cache_data
def get_trips_to_city(city_id, _analyzers): # analyzers pas hashable donc paramètre pas pris en compte pour cache
    trips = {}
    for key, analyzer in _analyzers.items():
        trips[key] = analyzer.trajet_destination(city_id)
    return trips

@st.cache_data
def print_map(lat, lon, periode, _analyzers):
    date_min = periode[0].strftime('%Y%m%d')
    date_max = periode[1].strftime('%Y%m%d')

    destinations_duplicates = {}

    for key, analyzer in _analyzers.items():
        destinations_duplicates[key] = analyzer.get_destinations(lat, lon, date_min, date_max)

    destinations = {}
    i = 0
    destinations['-'] = (lat, lon, '0')
    fg = fl.FeatureGroup("Markers")
    fg.add_child(fl.Marker([float(lat), float(lon)], popup="Ville de départ", icon=fl.Icon(color="blue")))
    color = ['red', 'black', 'gray']

    for key, destinations_analyzer in destinations_duplicates.items():
        for row in destinations_analyzer.itertuples():
            fg.add_child(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, icon=fl.Icon(color=color[i])))
            destinations[row.stop_name] = (row.stop_lat, row.stop_lon, row.stop_id)
        i = i + 1
    return fg, destinations, _analyzers