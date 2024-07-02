# webApp.py
import folium as fl
import import_ipynb
import AnalyzerGTFS as Ana # type: ignore
from streamlit_folium import st_folium
import streamlit as st


def get_pos(lat, lng):
    return lat, lng

def print_map(lat, lon):
    Analyzer = Ana.AnalyzerGTFS(lat,lon,'20240601','20240731')
    Destinations = Analyzer.all()
    #map = fl.Map(location=[lat, lon], zoom_start=7)
    feature_group = fl.FeatureGroup("Markers")

    feature_group.add_child(fl.Marker([lat, lon], popup="You are here"))
    #fl.CircleMarker([lat, lon], radius = 2, popup=lat+lon, color = "red").add_to(map)

    for row in Destinations.itertuples():
        feature_group.add_child(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name))
        print(row.stop_name, row.stop_lat, row.stop_lon)
        #fl.CircleMarker([float(row.stop_lat), float(row.stop_lon)], radius = 2, popup=row.stop_name).add_to(map)
    return feature_group

m = fl.Map()


fg = fl.FeatureGroup("Markers")

fg.add_child(fl.Marker(location=[45.5236, -122.6750], popup='Marker 1'))
fg.add_child(fl.Marker(location=[45.5318, -122.6748], popup='Marker 2'))

m.add_child(fg)

data = None
map = st_folium(m, height=500, width=1000, key = 'new' , feature_group_to_add=fg)


if map.get("last_clicked"):
    data = get_pos(map["last_clicked"]["lat"], map["last_clicked"]["lng"])

if data is not None:
    fg = print_map(data[0], data[1])
    print(fg)
    st.write(data) # Writes to the app
    print(data) # Writes to terminal

