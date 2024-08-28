import pandas as pd
from datetime import datetime
import os
import numpy as np
from Analyzer import Analyzer

MARGE_DISTANCE: float = 0.03


class AnalyzerFlixbus(Analyzer):
    arrets_depart: pd.DataFrame = pd.DataFrame()
    list_cities: pd.DataFrame = pd.DataFrame()
    stops: pd.DataFrame = pd.DataFrame()
    calendar_dates: pd.DataFrame = pd.DataFrame()
    calendar: pd.DataFrame = pd.DataFrame
    routes: pd.DataFrame = pd.DataFrame()
    stop_times: pd.DataFrame = pd.DataFrame()
    trips: pd.DataFrame = pd.DataFrame()
    lat: float = 0.0
    lon: float = 0.0
    stop_times_trips: pd.DataFrame = pd.DataFrame()
    nearby_stops: pd.DataFrame = pd.DataFrame()
    days: dict[int, str] = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "saturday",
        6: "sunday",
    }
    monday_integer_index: int = 0

    def __init__(self, transport_type="FLIXBUS"):
        self.calendar_dates = pd.read_csv(os.path.join("Data", transport_type, "calendar_dates.txt"))
        self.calendar = pd.read_csv(os.path.join("Data", transport_type, "calendar.txt"))
        self.stop_times = pd.read_csv(os.path.join("Data", transport_type, "stop_times.txt"))[
            ["trip_id", "stop_id", "departure_time"]
        ]
        self.stops = pd.read_csv(os.path.join("Data", transport_type, "stops.txt"))[
            ["stop_id", "stop_name", "stop_lat", "stop_lon"]
        ]
        self.trips = pd.read_csv(os.path.join("Data", transport_type, "trips.txt"))[
            ["service_id", "trip_id", "route_id"]
        ]
        self.calendar_dates.date = pd.to_datetime(self.calendar_dates["date"], format="%Y%m%d")
        self.calendar.start_date = pd.to_datetime(self.calendar["start_date"], format="%Y%m%d")
        self.calendar.end_date = pd.to_datetime(self.calendar["end_date"], format="%Y%m%d")
        self.stop_times["departure_time"] = pd.to_timedelta(self.stop_times["departure_time"])
        self.monday_integer_index = self.calendar.columns.get_loc("monday")

    def stops_proches(self, lat: float, lon: float):  # Stop ID pour Global, parent_station pour SNCF
        return self.stops[
            (self.stops["stop_lat"] > lat - MARGE_DISTANCE)
            & (self.stops["stop_lat"] < lat + MARGE_DISTANCE)
            & (self.stops["stop_lon"] > lon - MARGE_DISTANCE)
            & (self.stops["stop_lon"] < lon + MARGE_DISTANCE)
        ]

    def trips_stops_proches(self, lat: float, lon: float) -> pd.Series:
        self.nearby_stops: pd.DataFrame = self.stops_proches(lat, lon)
        trips: pd.DataFrame = self.stop_times[self.stop_times["stop_id"].isin(self.nearby_stops["stop_id"])]
        self.arrets_depart = trips.drop_duplicates(subset="trip_id")
        trips_ids: pd.Series = self.arrets_depart["trip_id"]
        return trips_ids

    # All trips that fits calendar
    # @profile
    def trips_dans_periode(self, lat: float, lon: float, date_min: datetime, date_max: datetime) -> pd.Series:
        date_min = pd.to_datetime(date_min)
        date_max = pd.to_datetime(date_max)
        trips_ids: pd.Series = self.trips_stops_proches(lat, lon)
        trips: pd.DataFrame = self.trips[self.trips["trip_id"].isin(trips_ids)]
        services: pd.DataFrame = self.calendar[self.calendar["service_id"].isin(trips["service_id"])]
        services_dans_periode: pd.DataFrame = services[
            ((services["start_date"] >= date_min) & (services["start_date"] <= date_max))
            | ((services["end_date"] >= date_min) & (services["end_date"] <= date_max))
        ]
        services_dans_periode = services_dans_periode.assign(
            days_ok_start=np.vectorize(lambda x: date_min if (date_min >= x) else x)(
                services_dans_periode["start_date"]
            ),
            days_ok_end=np.vectorize(lambda x: date_max if (date_max <= x) else x)(services_dans_periode["end_date"]),
        )
        services_dans_periode["days_ok"] = services_dans_periode["days_ok_end"] - services_dans_periode["days_ok_start"]
        # Optimisation de la ligne suivante à faire
        services_in_dates = services_dans_periode[services_dans_periode.apply(self.service_in_dates, axis=1)]
        services_in_dates.drop_duplicates(subset="service_id")
        trips_dans_periode: pd.DataFrame = trips[trips["service_id"].isin(services_in_dates["service_id"])]
        return trips_dans_periode["trip_id"]

    # All trips that fits calendar_date cancels

    def service_in_dates(self, services: pd.Series):
        if services.days_ok >= pd.Timedelta(days=6):
            return True
        i = 0
        while i <= services.days_ok.days:
            day = (services.days_ok_start + pd.Timedelta(days=i)).weekday()
            if services.iloc[self.monday_integer_index + day] == 1:
                return True
            i += 1
        return False

    # @profile
    def get_set_destinations(self, lat: float, lon: float, date_min: datetime, date_max: datetime) -> pd.DataFrame:
        trips_ids_dans_periode: pd.Series = self.trips_dans_periode(lat, lon, date_min, date_max)
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

        destinations_doublons_stops: pd.DataFrame = stop_times_temps_superieur[
            stop_times_temps_superieur["departure_time"] > stop_times_temps_superieur["temps_ville"]
        ]
        destinations_doublons_stops = self.stops[self.stops["stop_id"].isin(destinations_doublons_stops["stop_id"])]
        destinations = destinations_doublons_stops.drop_duplicates(subset="stop_id")
        print(destinations["stop_name"])
        return destinations


a = AnalyzerFlixbus()
a.get_set_destinations(48.8566, 2.3522, datetime(2024, 8, 1), datetime(2024, 8, 31))
