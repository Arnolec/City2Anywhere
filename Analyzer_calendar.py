import pandas as pd
from datetime import datetime
import os
import numpy as np
from Analyzer import Analyzer

MARGE_DISTANCE: float = 0.03


class Analyzer_calendar(Analyzer):
    arrets_depart: pd.DataFrame = pd.DataFrame()
    list_cities: pd.DataFrame = pd.DataFrame()
    stops: pd.DataFrame = pd.DataFrame()
    calendar_dates: pd.DataFrame = pd.DataFrame()
    calendar: pd.DataFrame = pd.DataFrame()
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
        return destinations

    def get_trajets(
        self,
        departure_lat: float,
        departure_lon: float,
        arrival_lat: float,
        arrival_lon: float,
        date_min: datetime,
        date_max: datetime,
        departure_time: pd.Timedelta,
    ) -> pd.DataFrame:
        stops_depart: pd.DataFrame = self.stops[
            (self.stops["stop_lat"] > departure_lat - MARGE_DISTANCE)
            & (self.stops["stop_lat"] < departure_lat + MARGE_DISTANCE)
            & (self.stops["stop_lon"] > departure_lon - MARGE_DISTANCE)
            & (self.stops["stop_lon"] < departure_lon + MARGE_DISTANCE)
        ]
        stops_arrivee: pd.DataFrame = self.stops[
            (self.stops["stop_lat"] > arrival_lat - MARGE_DISTANCE / 2)
            & (self.stops["stop_lat"] < arrival_lat + MARGE_DISTANCE / 2)
            & (self.stops["stop_lon"] > arrival_lon - MARGE_DISTANCE / 2)
            & (self.stops["stop_lon"] < arrival_lon + MARGE_DISTANCE / 2)
        ]
        trajets_avec_depart: pd.DataFrame = self.stop_times[
            self.stop_times["stop_id"].isin(stops_depart["stop_id"])
        ]
        trajets_avec_depart = trajets_avec_depart[
            trajets_avec_depart["departure_time"] > departure_time
        ]
        trajets_avec_arrivee: pd.DataFrame = self.stop_times[
            self.stop_times["stop_id"].isin(stops_arrivee["stop_id"])
        ]
        trips_avec_depart_arrivee: pd.DataFrame = pd.merge(
            trajets_avec_depart, trajets_avec_arrivee, on="trip_id"
        )
        trips_heure: pd.DataFrame = trips_avec_depart_arrivee[
            trips_avec_depart_arrivee["departure_time_x"] < trips_avec_depart_arrivee["departure_time_y"]
        ]
        trips: pd.DataFrame = pd.merge(trips_heure, self.trips, on="trip_id")
        trips_dates = self.dates_from_trips(trips, date_min, date_max)
        return trips_dates

    def dates_from_trips(self, trips : pd.DataFrame, date_min : datetime, date_max : datetime) -> pd.Series:
        #print(trips)
        date_min = pd.to_datetime(date_min)
        date_max = pd.to_datetime(date_max)
        services: pd.DataFrame = self.calendar[self.calendar["service_id"].isin(trips["service_id"])]
        services_dans_periode: pd.DataFrame = services[
            ((services["start_date"] >= date_min) & (services["start_date"] <= date_max))
            | ((services["end_date"] >= date_min) & (services["end_date"] <= date_max))
        ]
        services_dans_periode = services_dans_periode.assign(
            days_ok_start=np.vectorize(lambda x: date_min if (date_min >= pd.to_datetime(x)) else x)(
                services_dans_periode["start_date"]
            ),
            days_ok_end=np.vectorize(lambda x: date_max if (date_max <= pd.to_datetime(x)) else x)(services_dans_periode["end_date"]),
        )
        dataframe_concat = pd.DataFrame()
        for _, row in services_dans_periode.iterrows():
            df = pd.DataFrame({'date': pd.date_range(start=row.days_ok_start,end=row.days_ok_end), 'service_id': row.service_id, 'monday' : row.monday, 'tuesday' : row.tuesday, 'wednesday' : row.wednesday, 'thursday' : row.thursday, 'friday' : row.friday, 'saturday' : row.saturday, 'sunday' : row.sunday})
            monday_index = df.columns.get_loc("monday")
            df = df[df.apply(lambda x: True if x.iloc[monday_index + x.date.weekday()] == 1 else False, axis=1)]
            dataframe_concat = pd.concat([dataframe_concat, df])
        dataframe_valid_dates = pd.merge(trips, dataframe_concat, on="service_id")
        dataframe_valid_dates["horaire_depart"] = dataframe_valid_dates["date"] + dataframe_valid_dates["departure_time_x"]
        dataframe_valid_dates["horaire_arrivee"] = dataframe_valid_dates["date"] + dataframe_valid_dates["departure_time_y"]
        return dataframe_valid_dates

    def list_of_cities(self) -> pd.DataFrame:
        appearance_count = self.stop_times.groupby("stop_id").count()["trip_id"]
        stop_cities = self.stops.set_index("stop_id")
        stop_cities = stop_cities.assign(number_of_appearance=appearance_count)
        self.list_cities = stop_cities
        return stop_cities
