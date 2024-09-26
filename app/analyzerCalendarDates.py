import os
from datetime import datetime

import numpy as np
import pandas as pd
import pytz

from app.analyzer import Analyzer

DISTANCE_MARGIN: float = 0.05


class AnalyzerCalendarDates(Analyzer):
    unique_departures: pd.DataFrame = pd.DataFrame()
    city_list: pd.DataFrame = pd.DataFrame()
    stops: pd.DataFrame = pd.DataFrame()
    calendar_dates: pd.DataFrame = pd.DataFrame()
    routes: pd.DataFrame = pd.DataFrame()
    stop_times: pd.DataFrame = pd.DataFrame()
    trips: pd.DataFrame = pd.DataFrame()
    nearby_stops: pd.DataFrame = pd.DataFrame()
    timezone: str = "UTC"

    def __init__(self, transport_type="TER"):
        self.calendar_dates = pd.read_csv(os.path.join("Data", transport_type, "calendar_dates.txt"))
        self.stop_times = pd.read_csv(os.path.join("Data", transport_type, "stop_times.txt"))[
            ["trip_id", "stop_id", "departure_time"]
        ]
        agency = pd.read_csv(os.path.join("Data", transport_type, "agency.txt"))
        self.timezone = agency["agency_timezone"].iloc[0]
        stops = pd.read_csv(os.path.join("Data", transport_type, "stops.txt"))
        if "stop_timezone" not in stops.columns:
            stops = stops.assign(stop_timezone=self.timezone)
            self.stops = stops[["stop_id", "stop_name", "stop_lat", "stop_lon", "stop_timezone"]]
        else:
            if stops["stop_timezone"].iloc[0] == "":
                stops["stop_timezone"] = self.timezone
                self.stops = stops[["stop_id", "stop_name", "stop_lat", "stop_lon", "stop_timezone"]]
            else:
                self.stops = stops[["stop_id", "stop_name", "stop_lat", "stop_lon", "stop_timezone"]]
        self.trips = pd.read_csv(os.path.join("Data", transport_type, "trips.txt"))[
            ["service_id", "trip_id", "route_id"]
        ]
        self.calendar_dates.date = pd.to_datetime(self.calendar_dates["date"], format="%Y%m%d")
        self.stop_times["departure_time"] = pd.to_timedelta(self.stop_times["departure_time"])

    # Retourne les StopPoints proche du point de départ
    def find_nearby_stops(
        self, lat: float, lon: float, max_distance: float
    ):  # Stop ID pour Global, parent_station pour SNCF
        return self.stops[
            np.sqrt((self.stops["stop_lat"] - lat) ** 2 + (self.stops["stop_lon"] - lon) ** 2) < 1.05 * max_distance
        ]

    def get_trips_nearby_location(self, lat: float, lon: float, max_distance: float) -> pd.Series:
        self.nearby_stops: pd.DataFrame = self.find_nearby_stops(lat, lon, max_distance)
        trips_containing_departure: pd.DataFrame = self.stop_times[
            self.stop_times["stop_id"].isin(self.nearby_stops["stop_id"])
        ]
        self.unique_departures = trips_containing_departure.drop_duplicates(subset="trip_id")
        trip_ids: pd.Series = self.unique_departures["trip_id"]
        return trip_ids

    def filter_trips_within_period(
        self,
        lat: float,
        lon: float,
        start_date: datetime,
        end_date: datetime,
        max_distance: float,
    ) -> pd.Series:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        trip_ids: pd.Series = self.get_trips_nearby_location(lat, lon, max_distance)
        relevant_trips: pd.DataFrame = self.trips[self.trips["trip_id"].isin(trip_ids)]
        relevant_services: pd.DataFrame = self.calendar_dates[
            self.calendar_dates["service_id"].isin(relevant_trips["service_id"])
        ]
        services_within_period: pd.DataFrame = relevant_services[
            (relevant_services["date"] >= start_date) & (relevant_services["date"] <= end_date)
        ]
        services_within_period.drop_duplicates(subset="service_id")
        trips_within_period: pd.DataFrame = relevant_trips[
            relevant_trips["service_id"].isin(services_within_period["service_id"])
        ]
        return trips_within_period["trip_id"]

    def find_destinations_from_location(
        self,
        lat: float,
        lon: float,
        start_date: datetime,
        end_date: datetime,
        max_distance: float,
    ) -> pd.DataFrame:
        trip_ids_within_period: pd.Series = self.filter_trips_within_period(
            lat, lon, start_date, end_date, max_distance
        )
        stop_times_right_stops: pd.DataFrame = self.stop_times[self.stop_times["trip_id"].isin(trip_ids_within_period)]
        cities_after_inital_departure: pd.DataFrame = stop_times_right_stops.assign(
            city_departure_time="", stop_id_ville=""
        )

        departure_stop_ids: pd.Series = self.unique_departures["stop_id"]
        departure_stop_ids.index = self.unique_departures["trip_id"]
        departure_id = departure_stop_ids.loc[cities_after_inital_departure["trip_id"]]
        cities_after_inital_departure["stop_id_ville"] = departure_id.array

        departure_time: pd.Series = self.unique_departures["departure_time"]  # StopTime trip
        departure_time.index = self.unique_departures["trip_id"]
        column_departure_time = departure_time.loc[cities_after_inital_departure["trip_id"]]
        cities_after_inital_departure["city_departure_time"] = column_departure_time.array

        duplicate_destinations_stop_points: pd.DataFrame = cities_after_inital_departure[
            cities_after_inital_departure["departure_time"] > cities_after_inital_departure["city_departure_time"]
        ]
        duplicate_destinations_stop_points = self.stops[
            self.stops["stop_id"].isin(duplicate_destinations_stop_points["stop_id"])
        ]
        destinations_stop_area = duplicate_destinations_stop_points.drop_duplicates(subset="stop_id")
        destinations: pd.DataFrame = destinations_stop_area[
            ~destinations_stop_area["stop_id"].isin(self.nearby_stops["stop_id"])
        ]
        return destinations

    def find_trips_between_locations(
        self,
        departure_lat,
        departure_lon,
        arrival_lat: float,
        arrival_lon: float,
        start_date: datetime,
        end_date: datetime,
        departure_time: pd.Timedelta,
        max_distance: float,
    ) -> pd.DataFrame:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        departure_stops: pd.DataFrame = self.find_nearby_stops(departure_lat, departure_lon, max_distance)
        arrival_stops: pd.DataFrame = self.find_nearby_stops(arrival_lat, arrival_lon, max_distance)
        trips_containing_departure: pd.DataFrame = pd.merge(self.stop_times, departure_stops, on="stop_id")
        trips_containing_departure = trips_containing_departure[
            trips_containing_departure["departure_time"] > departure_time
        ]
        trips_containing_arrival: pd.DataFrame = pd.merge(self.stop_times, arrival_stops, on="stop_id")
        trips_containing_both: pd.DataFrame = pd.merge(
            trips_containing_departure, trips_containing_arrival, on="trip_id"
        )
        if trips_containing_both.empty:
            return pd.DataFrame()
        trips_in_right_direction: pd.DataFrame = trips_containing_both[
            trips_containing_both["departure_time_x"] < trips_containing_both["departure_time_y"]
        ]
        trips: pd.DataFrame = pd.merge(trips_in_right_direction, self.trips, on="trip_id")
        trips_and_calendar_dates: pd.DataFrame = pd.merge(trips, self.calendar_dates, on="service_id")
        valid_trips: pd.DataFrame = trips_and_calendar_dates[
            (trips_and_calendar_dates["date"] >= start_date) & (trips_and_calendar_dates["date"] <= end_date)
        ].assign(
            dep_time=trips_and_calendar_dates["date"] + trips_and_calendar_dates["departure_time_x"],
            arr_time=trips_and_calendar_dates["date"] + trips_and_calendar_dates["departure_time_y"],
        )
        trips = valid_trips
        trips["dep_time"] = pd.to_datetime(trips["dep_time"], utc=False).dt.tz_localize(pytz.timezone(self.timezone))
        trips["arr_time"] = pd.to_datetime(trips["arr_time"], utc=False).dt.tz_localize(pytz.timezone(self.timezone))
        trips = trips.assign(stop_timezone_x=self.timezone, stop_timezone_y=self.timezone)
        return trips

    def get_list_of_cities(self) -> pd.DataFrame:
        appearance_count = self.stop_times.groupby("stop_id").count()["trip_id"]
        stop_cities = self.stops.set_index("stop_id")
        stop_cities = stop_cities.assign(number_of_appearance=appearance_count)
        return stop_cities
