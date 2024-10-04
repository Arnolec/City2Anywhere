import os
from collections import Counter
from datetime import datetime, time

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from app.backend.analyzer import Analyzer
from app.backend.analyzerCalendar import AnalyzerCalendar
from app.backend.analyzerCalendarDates import AnalyzerCalendarDates
from app.backend.analyzerSNCF import AnalyzerCalendarDatesSNCF
from app.backend.data_updater import DataUpdater
from app.backend.models import Coords, CoordsDistance


def load_class_analyzer(path: str) -> Analyzer:
    check_file = os.path.isfile(os.path.join("Data", path, "calendar.txt"))
    if check_file:
        return AnalyzerCalendar(path)
    else:
        if path not in ["TGV", "TER", "INTERCITE"]:
            return AnalyzerCalendarDates(path)
        else:
            return AnalyzerCalendarDatesSNCF(path)


# Utilisation de DBSCAN avec distance Haversine pour regrouper les arrêts proches en "villes"
def group_stops_by_city(dataframe: pd.DataFrame, eps_km=1.0, min_samples=1) -> pd.DataFrame:
    # Convertir les coordonnées en radians
    coords = np.radians(dataframe[["stop_lat", "stop_lon"]].values)

    # Appliquer DBSCAN avec distance haversine
    db = DBSCAN(eps=eps_km / 6371.0, min_samples=min_samples, metric="haversine")
    labels = db.fit_predict(coords)

    # Ajouter les labels (villes) au dataframe
    dataframe["city_cluster"] = labels
    return dataframe


# Liste de mots à ignorer (mots de bruit)
mots_bruit = {
    "de",
    "des",
    "le",
    "la",
    "les",
    "et",
    "du",
    "un",
    "une",
    "dans",
    "au",
    "aux",
    "avec",
    "pour",
}


# Fonction modifiée pour trouver le meilleur nom basé sur les mots fréquents
def choosing_city_name(names, threshold=0.5):
    # Séparer chaque nom en mots tout en ignorant les mots de bruit
    word_list = []
    for name in names:
        words = name.lower().split()
        word_without_noise = [word for word in words if word not in mots_bruit]
        word_list.append(word_without_noise)

    # Compter la fréquence d'apparition de chaque mot
    counter = Counter(word for words in word_list for word in words)

    # Calculer le nombre minimal d'apparitions pour qu'un mot soit considéré fréquent
    name_count = len(names)
    min_apparitions = int(name_count * threshold)

    # Sélectionner les mots qui apparaissent au moins dans 'seuil' pourcentage des noms
    frequent_words = [mot for mot, freq in counter.items() if freq >= min_apparitions]

    # Recomposer le meilleur nom avec les mots fréquents
    best_name = " ".join(frequent_words)
    naming = best_name.capitalize()
    if naming == " " or naming == "":
        naming = names[0]
    return naming


def euclidean_distance(lat1, lon1, lat2, lon2):
    return np.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)


def load_analyzers() -> dict[str, Analyzer]:
    analyzers = {}
    analyzers["TER"] = load_class_analyzer("TER")
    analyzers["TGV"] = load_class_analyzer("TGV")
    analyzers["INTERCITE"] = load_class_analyzer("INTERCITE")
    analyzers["FLIXBUS"] = load_class_analyzer("FLIXBUS")
    analyzers["BLABLABUS"] = load_class_analyzer("BLABLABUS")
    analyzers["DB-LONG"] = load_class_analyzer("DB-LONG")
    analyzers["DB-REGIONAL"] = load_class_analyzer("DB-REGIONAL")
    analyzers["EUROSTAR"] = load_class_analyzer("EUROSTAR")
    return analyzers


def get_center(cities: pd.DataFrame) -> tuple[float, float]:
    gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
        cities,
        geometry=gpd.points_from_xy(cities.stop_lat, cities.stop_lon),
        crs="EPSG:4326",
    )
    centroid = gdf.unary_union.centroid
    return centroid


def get_list_of_stops(analyzers) -> pd.DataFrame:
    cities: pd.DataFrame = pd.DataFrame()
    cities_analyzers: list[pd.DataFrame] = []
    for analyzer in analyzers.values():
        cities_analyzers.append(analyzer.get_list_of_cities())
    cities_concat = pd.concat(cities_analyzers)
    cities_concat_index = cities_concat.assign(ids=cities_concat.index)
    sum_appearance_on_index = (
        cities_concat_index.groupby("ids").sum().sort_values(by="number_of_appearance", ascending=False)
    )
    cities_concat = cities_concat[~cities_concat.index.duplicated(keep="first")]
    cities_concat["number_of_appearance"] = sum_appearance_on_index["number_of_appearance"]
    cities_sorted = cities_concat.sort_values(by="number_of_appearance", ascending=False)
    cities = cities_sorted.set_index("stop_name")
    cities = cities[~cities.index.duplicated(keep="first")]
    return cities


def get_cities(analyzers) -> pd.DataFrame:
    list_of_stops = get_list_of_stops(analyzers)
    list_of_stops = list_of_stops.assign(stop_name=list_of_stops.index)
    df_with_clusters = group_stops_by_city(list_of_stops, eps_km=8.0)  # Ajuste eps_km selon la densité des villes
    cluster_grouped = df_with_clusters.groupby("city_cluster")
    cities = pd.DataFrame()
    cities["stop_lat"] = cluster_grouped["stop_lat"].mean()
    cities["stop_lon"] = cluster_grouped["stop_lon"].mean()
    cities_list_stops = cluster_grouped.apply(lambda x: x["stop_name"].tolist(), include_groups=False)
    cities["max_distance"] = cluster_grouped.apply(
        lambda x: euclidean_distance(
            x["stop_lat"],
            x["stop_lon"],
            cities.loc[x.name, "stop_lat"],
            cities.loc[x.name, "stop_lon"],
        ).max(),
        include_groups=False,
    )
    cities["stop_name"] = cities_list_stops.apply(choosing_city_name)
    cities = cities.set_index("stop_name")
    return cities


def update_data() -> None:
    DataUpdater().update_data()


def get_city_max_distance(coords: Coords, cities: pd.DataFrame) -> CoordsDistance:
    cities = cities[np.sqrt((cities["stop_lat"] - coords.lat) ** 2 + (cities["stop_lon"] - coords.lon) ** 2) < 0.1]
    if cities.empty:
        return None
    cities = cities.assign(
        distance=np.sqrt((cities["stop_lat"] - coords.lat) ** 2 + (cities["stop_lon"] - coords.lon) ** 2)
    )
    closest_city = cities["distance"].idxmin()
    return CoordsDistance(
        lat=cities.loc[closest_city, "stop_lat"],
        lon=cities.loc[closest_city, "stop_lon"],
        max_distance=cities.loc[closest_city, "max_distance"],
    )


# A Modifier car maintenant cities n'est plus un dataframe mais un dict


def get_destinations(
    coords: Coords,
    periode: tuple[datetime, datetime],
    transport_type: list[str],
    _analyzers: dict[str, Analyzer],
    cities: pd.DataFrame,
) -> dict:
    date_min = periode[0]
    date_max = periode[1]
    df_concat = pd.DataFrame()

    cities["present"] = False
    cities["transport"] = None

    for key, analyzer in _analyzers.items():
        if key in transport_type:
            destinations_transport = analyzer.find_destinations_from_location(coords, date_min, date_max)
            destinations_transport["transport_type"] = key
            df_concat = pd.concat([df_concat, destinations_transport])

    # Convertir les colonnes utiles en arrays NumPy pour une meilleure performance
    city_latitudes = cities["stop_lat"].values
    city_longitudes = cities["stop_lon"].values
    city_max_distances = cities["max_distance"].values
    stop_latitudes = df_concat["stop_lat"].values
    stop_longitudes = df_concat["stop_lon"].values
    stop_transport_types = df_concat["transport_type"].values

    # Calculer les distances euclidiennes pour toutes les combinaisons de villes et destinations
    distances = np.sqrt(
        (city_latitudes[:, np.newaxis] - stop_latitudes) ** 2 + (city_longitudes[:, np.newaxis] - stop_longitudes) ** 2
    )

    # Trouver les indices des destinations qui respectent la condition de distance
    within_max_dist = distances <= city_max_distances[:, np.newaxis]

    # Trouver le premier indice qui respecte la condition pour chaque ville
    first_match_idx = np.argmax(within_max_dist, axis=1)

    # Vérifier si une destination a été trouvée pour chaque ville
    found_match = np.any(within_max_dist, axis=1)

    # Mettre à jour le DataFrame cities
    cities.loc[found_match, "present"] = True
    cities.loc[found_match, "transport"] = np.array(stop_transport_types)[first_match_idx[found_match]]

    cities_present = cities[cities["present"]]
    return cities_present.to_dict()


def get_trips_to_city(
    dep_coords: Coords,
    arr_coords: Coords,
    periode: tuple[datetime, datetime],
    _analyzers: dict[str, Analyzer],
    transport_type: list[str],
    departure_time: time,
) -> pd.DataFrame:
    date_min = periode[0]
    date_max = periode[1]

    datetime_departure = pd.Timedelta(hours=departure_time.hour)

    raw_trips = get_raw_trips_to_city(
        dep_coords, arr_coords, date_min, date_max, _analyzers, transport_type, datetime_departure
    )

    trips_duplicated = raw_trips.drop_duplicates(subset=["dep_time"], keep="first")
    trips = trips_duplicated.fillna(0)
    trips = trips.sort_values(by="dep_time", ascending=True)
    return trips.to_dict()


# Function called in order to get dataframes of trips, and then dataframes are sorted and shaped to be displayed in the webApp by the above function
def get_raw_trips_to_city(
    dep_coords: Coords,
    arr_coords: Coords,
    date_min: datetime,
    date_max: datetime,
    _analyzers: dict[str, Analyzer],
    transport_type: list[str],
    departure_time: pd.Timedelta,
) -> pd.DataFrame:
    df_concat = pd.DataFrame()
    for key, analyzer in _analyzers.items():
        if key in transport_type:
            trips_transport = fetch_trips_one_transport(
                dep_coords, arr_coords, date_min, date_max, analyzer, key, departure_time
            )
            df_concat = pd.concat([df_concat, trips_transport])
    return df_concat


def fetch_trips_one_transport(
    dep_coords: Coords,
    arr_coords: Coords,
    date_min: datetime,
    date_max: datetime,
    _analyzer: Analyzer,
    transport: str,
    departure_time: pd.Timedelta,
) -> pd.DataFrame:
    trips = _analyzer.find_trips_between_locations(dep_coords, arr_coords, date_min, date_max, departure_time)
    trips["transport_type"] = transport
    return trips
