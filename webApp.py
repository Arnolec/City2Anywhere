# webApp.py
import folium as fl
import import_ipynb
import AnalyzerGTFS as Ana # type: ignore
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd



def get_pos(lat, lng):
    return lat, lng

def print_map(lat, lon):
    AnalyzerTER = Ana.AnalyzerGTFS(lat,lon,'20240601','20240731','TER')
    DestinationsTER = AnalyzerTER.get_destinations()
    AnalyzerTGV = Ana.AnalyzerGTFS(lat,lon,'20240601','20240731','TGV')
    DestinationsTGV = AnalyzerTGV.get_destinations()
    AnalyzerINTERCITE= Ana.AnalyzerGTFS(lat,lon,'20240601','20240731','INTERCITE')
    DestinationsINTERCITE = AnalyzerINTERCITE.get_destinations()
    st.session_state["markers"] = []
    st.session_state["markers"].append(fl.Marker([lat, lon], popup="You are here", color = "red"))


    for row in DestinationsTER.itertuples():
        st.session_state["markers"].append(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, color = "green"))
        print(row.stop_name)
    for row in DestinationsTGV.itertuples():
        st.session_state["markers"].append(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, color = "yellow"))
        print(row.stop_name)
    for row in DestinationsINTERCITE.itertuples():
        st.session_state["markers"].append(fl.Marker([float(row.stop_lat), float(row.stop_lon)], popup=row.stop_name, color = "black"))
        print(row.stop_name)



if 'center' not in st.session_state:
    st.session_state.center = [46.903354, 1.888334]
if 'zoom' not in st.session_state:
    st.session_state.zoom = 5
if 'markers' not in st.session_state:
    st.session_state.markers = []

fg = fl.FeatureGroup("Markers")
for marker in st.session_state["markers"]:
    fg.add_child(marker)

m = fl.Map(location=[46.9,1.89], zoom_start=9)


data = None
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
    fg = print_map(data[0], data[1])
    st.write(data) # Writes to the app
    print(data) # Writes to terminal

