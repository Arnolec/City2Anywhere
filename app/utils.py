import os
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from app.analyzer import Analyzer
from app.analyzerCalendar import AnalyzerCalendar
from app.analyzerCalendarDates import AnalyzerCalendarDates
from app.analyzerSNCF import AnalyzerCalendarDatesSNCF


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
