import pandas as pd
from datetime import datetime
import os
from Analyzer import Analyzer

MARGE_DISTANCE: float = 0.03
THRESHOLD_CONNECTION: int = 100

# Nouvelle version de la classe AnalyzerGTFS, version qui est optimisée


class Analyzer_calendar_dates(Analyzer):
    arrets_depart: pd.DataFrame = pd.DataFrame()
    city_list: pd.DataFrame = pd.DataFrame()
    stops: pd.DataFrame = pd.DataFrame()
    calendar_dates: pd.DataFrame = pd.DataFrame()
    routes: pd.DataFrame = pd.DataFrame()
    stop_times: pd.DataFrame = pd.DataFrame()
    trips: pd.DataFrame = pd.DataFrame()
    stops_id: pd.DataFrame = pd.DataFrame()
    stops_area: pd.DataFrame = pd.DataFrame()
    stop_times_trips: pd.DataFrame = pd.DataFrame()
    nearby_stops: pd.DataFrame = pd.DataFrame()

    def __init__(self, transport_type="TER"):
        self.calendar_dates = pd.read_csv(os.path.join("Data", transport_type, "calendar_dates.txt"))
        self.stop_times = pd.read_csv(os.path.join("Data", transport_type, "stop_times.txt"))[
            ["trip_id", "stop_id", "departure_time"]
        ]
        self.stops = pd.read_csv(os.path.join("Data", transport_type, "stops.txt"))[
            ["stop_id", "stop_name", "stop_lat", "stop_lon", "parent_station"]
        ]
        self.trips = pd.read_csv(os.path.join("Data", transport_type, "trips.txt"))[
            ["service_id", "trip_id", "route_id"]
        ]
        self.calendar_dates.date = pd.to_datetime(self.calendar_dates["date"], format="%Y%m%d")
        self.stop_times["departure_time"] = pd.to_timedelta(self.stop_times["departure_time"])
        self.stops_id = self.stops[~self.stops["parent_station"].isna()]
        self.stops_area = self.stops[self.stops["parent_station"].isna()]

    # Retourne les StopPoints proche du point de départ
    def find_nearby_stops(self, lat: float, lon: float):  # Stop ID pour Global, parent_station pour SNCF
        return self.stops_id[
            (self.stops_id["stop_lat"] > lat - MARGE_DISTANCE)
            & (self.stops_id["stop_lat"] < lat + MARGE_DISTANCE)
            & (self.stops_id["stop_lon"] > lon - MARGE_DISTANCE)
            & (self.stops_id["stop_lon"] < lon + MARGE_DISTANCE)
        ]

    def get_trips_nearby_location(self, lat: float, lon: float) -> pd.Series:
        self.nearby_stops: pd.DataFrame = self.find_nearby_stops(lat, lon)
        trips: pd.DataFrame = self.stop_times[self.stop_times["stop_id"].isin(self.nearby_stops["stop_id"])]
        # trips = pd.merge(self.stop_times_sorted, stops_proches, on = "stop_id")[['trip_id', 'stop_id', 'departure_time']]
        # trips: pd.DataFrame = self.stop_times.query('stop_id in @stops_proches["stop_id"]', engine='python')
        self.arrets_depart = trips.drop_duplicates(subset="trip_id")
        trips_ids: pd.Series = self.arrets_depart["trip_id"]
        return trips_ids

    def filter_trips_within_period(self, lat: float, lon: float, date_min: datetime, date_max: datetime) -> pd.Series:
        date_min = pd.to_datetime(date_min)
        date_max = pd.to_datetime(date_max)
        trips_ids: pd.Series = self.get_trips_nearby_location(lat, lon)
        trips: pd.DataFrame = self.trips[self.trips["trip_id"].isin(trips_ids)]
        services: pd.DataFrame = self.calendar_dates[self.calendar_dates["service_id"].isin(trips["service_id"])]
        services_dans_periode: pd.DataFrame = services[(services["date"] >= date_min) & (services["date"] <= date_max)]
        services_dans_periode.drop_duplicates(subset="service_id")
        trips_dans_periode: pd.DataFrame = trips[trips["service_id"].isin(services_dans_periode["service_id"])]
        return trips_dans_periode["trip_id"]

    def find_destinations_from_location(self, lat: float, lon: float, date_min: datetime, date_max: datetime) -> pd.DataFrame:
        trips_ids_dans_periode: pd.Series = self.filter_trips_within_period(lat, lon, date_min, date_max)
        stop_times_arret_correct: pd.DataFrame = self.stop_times[
            self.stop_times["trip_id"].isin(trips_ids_dans_periode)
        ]
        stop_times_temps_superieur: pd.DataFrame = stop_times_arret_correct.assign(temps_depart="", stop_id_ville="")

        stop_ids_depart: pd.Series = self.arrets_depart["stop_id"]
        stop_ids_depart.index = self.arrets_depart["trip_id"]
        stop_id_depart = stop_ids_depart.loc[stop_times_temps_superieur["trip_id"]]
        stop_times_temps_superieur["stop_id_ville"] = stop_id_depart.array

        temps_depart: pd.Series = self.arrets_depart["departure_time"]  # StopTime trip
        temps_depart.index = self.arrets_depart["trip_id"]
        colonne_temps_depart = temps_depart.loc[stop_times_temps_superieur["trip_id"]]
        stop_times_temps_superieur["temps_ville"] = colonne_temps_depart.array

        destinations_doublons_stop_points: pd.DataFrame = stop_times_temps_superieur[
            stop_times_temps_superieur["departure_time"] > stop_times_temps_superieur["temps_ville"]
        ]
        destinations_doublons_stop_points = self.stops_id[
            self.stops_id["stop_id"].isin(destinations_doublons_stop_points["stop_id"])
        ]
        destinations_doublons_stop_area: pd.DataFrame = self.stops_area[
            self.stops_area["stop_id"].isin(destinations_doublons_stop_points["parent_station"])
        ]
        destinations_stop_area = destinations_doublons_stop_area.drop_duplicates(subset="stop_id")
        destinations: pd.DataFrame = destinations_stop_area[
            ~destinations_stop_area["stop_id"].isin(self.nearby_stops["parent_station"])
        ]

        return destinations

    def find_trips_between_locations(
        self,
        departure_lat,
        departure_lon,
        arrival_lat: float,
        arrival_lon: float,
        date_min: datetime,
        date_max: datetime,
        departure_time: pd.Timedelta,
    ) -> pd.DataFrame:
        date_min = pd.to_datetime(date_min)
        date_max = pd.to_datetime(date_max)
        stops_depart: pd.DataFrame = self.stops_id[
            (self.stops_id["stop_lat"] > departure_lat - MARGE_DISTANCE)
            & (self.stops_id["stop_lat"] < departure_lat + MARGE_DISTANCE)
            & (self.stops_id["stop_lon"] > departure_lon - MARGE_DISTANCE)
            & (self.stops_id["stop_lon"] < departure_lon + MARGE_DISTANCE)
        ]
        stops_arrivee: pd.DataFrame = self.stops_id[
            (self.stops_id["stop_lat"] > arrival_lat - MARGE_DISTANCE / 2)
            & (self.stops_id["stop_lat"] < arrival_lat + MARGE_DISTANCE / 2)
            & (self.stops_id["stop_lon"] > arrival_lon - MARGE_DISTANCE / 2)
            & (self.stops_id["stop_lon"] < arrival_lon + MARGE_DISTANCE / 2)
        ]
        trajets_avec_stops_depart: pd.DataFrame = self.stop_times[
            self.stop_times["stop_id"].isin(stops_depart["stop_id"])
        ]
        trajets_avec_stops_depart = trajets_avec_stops_depart[
            trajets_avec_stops_depart["departure_time"] > departure_time
        ]
        trajets_avec_stops_arrivee: pd.DataFrame = self.stop_times[
            self.stop_times["stop_id"].isin(stops_arrivee["stop_id"])
        ]
        trips_avec_depart_arrivee: pd.DataFrame = pd.merge(
            trajets_avec_stops_depart, trajets_avec_stops_arrivee, on="trip_id"
        )
        trips_heure: pd.DataFrame = trips_avec_depart_arrivee[
            trips_avec_depart_arrivee["departure_time_x"] < trips_avec_depart_arrivee["departure_time_y"]
        ]
        trips: pd.DataFrame = pd.merge(trips_heure, self.trips, on="trip_id")
        trips_et_jours: pd.DataFrame = pd.merge(trips, self.calendar_dates, on="service_id")
        trajets: pd.DataFrame = trips_et_jours[
            (trips_et_jours["date"] >= date_min) & (trips_et_jours["date"] <= date_max)
        ]
        trajets = trajets.assign(horaire_depart="", horaire_arrivee="")
        trajets["horaire_depart"] = trajets["date"] + trajets["departure_time_x"]
        trajets["horaire_arrivee"] = trajets["date"] + trajets["departure_time_y"]
        return trajets

    @staticmethod
    def get_list_of_cities_static(path: str) -> pd.DataFrame:
        stops: pd.DataFrame = pd.read_csv(os.path.join("Data", path, "stops.txt"))[
            ["stop_id", "stop_name", "stop_lat", "stop_lon", "parent_station"]
        ]
        stop_times: pd.DataFrame = pd.read_csv(os.path.join("Data", path, "stop_times.txt"))[
            ["trip_id", "stop_id", "departure_time"]
        ]
        appearance_count = stop_times.groupby("stop_id").count()["trip_id"]
        appearance_stop_id = pd.merge(appearance_count, stops, on="stop_id")
        appeareance_stop_area = appearance_stop_id.groupby("parent_station").sum()["trip_id"]
        df_stop_area = stops[stops["stop_id"].str.contains("StopArea")][
            ["stop_name", "stop_lat", "stop_lon", "stop_id"]
        ].set_index("stop_id")
        df_stop_area = df_stop_area.assign(number_of_appearance=appeareance_stop_area)
        return df_stop_area

    def get_list_of_cities(self) -> pd.DataFrame:
        appearance_count = self.stop_times.groupby("stop_id").count()["trip_id"]
        appearance_stop_id = pd.merge(appearance_count, self.stops, on="stop_id")
        appeareance_stop_area = appearance_stop_id.groupby("parent_station").sum()["trip_id"]
        df_stop_area = self.stops[self.stops["stop_id"].str.contains("StopArea")][
            ["stop_name", "stop_lat", "stop_lon", "stop_id"]
        ].set_index("stop_id")
        df_stop_area = df_stop_area.assign(number_of_appearance=appeareance_stop_area)
        self.city_list = df_stop_area
        return df_stop_area
