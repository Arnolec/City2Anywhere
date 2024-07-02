import streamlit as st
import folium
from streamlit_folium import folium_static,st_folium
def get_pos(lat, lng):
    return lat, lng
# Create a Folium map
m = folium.Map(location=[46.903354, 1.888334], zoom_start=6)

# When the user interacts with the map
map = st_folium(
    m,
    width=620, height=580,
    key="folium_map"
)
data = None
if map.get("last_clicked"):
    data = get_pos(map["last_clicked"]["lat"], map["last_clicked"]["lng"])
if data is not None:
    st.write(data)