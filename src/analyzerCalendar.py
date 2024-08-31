import pandas as pd
from datetime import datetime
import os
import numpy as np
from analyzer import Analyzer
import pytz

DISTANCE_MARGIN: float = 0.05


class AnalyzerCalendar(Analyzer):
    unique_departures: pd.DataFrame = pd.DataFrame()
    city_list: pd.DataFrame = pd.DataFrame()
    stops: pd.DataFrame = pd.DataFrame()
    calendar_dates: pd.DataFrame = pd.DataFrame()
    calendar: pd.DataFrame = pd.DataFrame()
    routes: pd.DataFrame = pd.DataFrame()
    stop_times: pd.DataFrame = pd.DataFrame()
    trips: pd.DataFrame = pd.DataFrame()
    lat: float = 0.0
    lon: float = 0.0
    nearby_stops: pd.DataFrame = pd.DataFrame()
    monday_integer_index: int = 0
    timezone: str = "UTC"

    def __init__(self, transport_type="FLIXBUS"):
        self.calendar_dates = pd.read_csv(os.path.join("Data", transport_type, "calendar_dates.txt"))
        self.calendar = pd.read_csv(os.path.join("Data", transport_type, "calendar.txt"))
        self.stop_times = pd.read_csv(os.path.join("Data", transport_type, "stop_times.txt"))[
            ["trip_id", "stop_id", "departure_time"]
        ]
        agency = pd.read_csv(os.path.join("Data", transport_type, "agency.txt"))
        self.timezone = agency["agency_timezone"].iloc[0]
        stops = pd.read_csv(os.path.join("Data", transport_type, "stops.txt"))
        if "stop_timezone" in stops.columns:
            self.stops = stops[["stop_id", "stop_name", "stop_lat", "stop_lon", "stop_timezone"]]
        else:
            self.stops = stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]]
            self.stops["stop_timezone"] = self.timezone
        self.trips = pd.read_csv(os.path.join("Data", transport_type, "trips.txt"))[
            ["service_id", "trip_id", "route_id"]
        ]
        self.calendar_dates.date = pd.to_datetime(self.calendar_dates["date"], format="%Y%m%d")
        self.calendar.start_date = pd.to_datetime(self.calendar["start_date"], format="%Y%m%d")
        self.calendar.end_date = pd.to_datetime(self.calendar["end_date"], format="%Y%m%d")
        self.stop_times["departure_time"] = pd.to_timedelta(self.stop_times["departure_time"])
        self.monday_integer_index = self.calendar.columns.get_loc("monday")

    # All stops near the location, Step 1 of find_destinations_from_location
    def find_nearby_stops(self, lat: float, lon: float):
        return self.stops[
            (self.stops["stop_lat"] > lat - DISTANCE_MARGIN / 2)
            & (self.stops["stop_lat"] < lat + DISTANCE_MARGIN / 2)
            & (self.stops["stop_lon"] > lon - DISTANCE_MARGIN / 2)
            & (self.stops["stop_lon"] < lon + DISTANCE_MARGIN / 2)
        ]

    # All trips that fits location, Step 2 of find_destinations_from_location
    def get_trips_nearby_location(self, lat: float, lon: float) -> pd.Series:
        self.nearby_stops: pd.DataFrame = self.find_nearby_stops(lat, lon)
        relevant_trips: pd.DataFrame = self.stop_times[self.stop_times["stop_id"].isin(self.nearby_stops["stop_id"])]
        self.unique_departures = relevant_trips.drop_duplicates(subset="trip_id")
        trip_ids: pd.Series = self.unique_departures["trip_id"]
        return trip_ids

    # All trips that fits calendar, Step 3 of find_destinations_from_location
    def filter_trips_within_period(self, lat: float, lon: float, start_date: datetime, end_date: datetime) -> pd.Series:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        trip_ids: pd.Series = self.get_trips_nearby_location(lat, lon)
        relevant_trips: pd.DataFrame = self.trips[self.trips["trip_id"].isin(trip_ids)]
        relevant_services: pd.DataFrame = self.calendar[self.calendar["service_id"].isin(relevant_trips["service_id"])]
        services_within_period: pd.DataFrame = relevant_services[
            ((relevant_services["start_date"] >= start_date) & (relevant_services["start_date"] <= end_date))
            | ((relevant_services["end_date"] >= start_date) & (relevant_services["end_date"] <= end_date))
            | ((relevant_services["start_date"] <= start_date) & (relevant_services["end_date"] >= end_date))
        ]
        if services_within_period.empty:
            return pd.Series()
        services_within_period = services_within_period.assign(
            days_ok_start=np.vectorize(lambda x: start_date if (start_date >= x) else x)(
                services_within_period["start_date"]
            ),
            days_ok_end=np.vectorize(lambda x: end_date if (end_date <= x) else x)(services_within_period["end_date"]),
        )
        services_within_period["days_ok"] = (
            services_within_period["days_ok_end"] - services_within_period["days_ok_start"]
        )
        # Optimisation de la ligne suivante à faire
        services_in_dates = services_within_period[services_within_period.apply(self.is_service_in_dates, axis=1)]
        services_in_dates.drop_duplicates(subset="service_id")
        trips_dans_periode: pd.DataFrame = relevant_trips[
            relevant_trips["service_id"].isin(services_in_dates["service_id"])
        ]
        return trips_dans_periode["trip_id"]

    # Function to check if a service is within the date range
    def is_service_in_dates(self, services: pd.Series) -> bool:
        if services.days_ok >= pd.Timedelta(days=6):
            return True
        day_offset = 0
        while day_offset <= services.days_ok.days:
            current_day_index = (services.days_ok_start + pd.Timedelta(days=day_offset)).weekday()
            if services.iloc[self.monday_integer_index + current_day_index] == 1:
                return True
            day_offset += 1
        return False

    # Find all destinations from a location and a period
    def find_destinations_from_location(
        self, lat: float, lon: float, date_min: datetime, date_max: datetime
    ) -> pd.DataFrame:
        trip_ids_within_period: pd.Series = self.filter_trips_within_period(lat, lon, date_min, date_max)
        stop_times_right_stops: pd.DataFrame = self.stop_times[self.stop_times["trip_id"].isin(trip_ids_within_period)]
        cities_after_inital_departure: pd.DataFrame = stop_times_right_stops.assign(
            city_departure_time="", city_stop_id=""
        )

        departure_stop_ids: pd.Series = self.unique_departures["stop_id"]
        departure_stop_ids.index = self.unique_departures["trip_id"]
        departure_id = departure_stop_ids.loc[cities_after_inital_departure["trip_id"]]
        cities_after_inital_departure["departure_stop_id"] = departure_id.array

        departure_time: pd.Series = self.unique_departures["departure_time"]  # StopTime trip
        departure_time.index = self.unique_departures["trip_id"]
        column_departure_time = departure_time.loc[cities_after_inital_departure["trip_id"]]
        cities_after_inital_departure["city_departure_time"] = column_departure_time.array

        duplicate_destinations_stop_times: pd.DataFrame = cities_after_inital_departure[
            cities_after_inital_departure["departure_time"] > cities_after_inital_departure["city_departure_time"]
        ]
        duplicate_destinations_stops = self.stops[
            self.stops["stop_id"].isin(duplicate_destinations_stop_times["stop_id"])
        ]
        destinations = duplicate_destinations_stops.drop_duplicates(subset="stop_id")
        destinations = destinations[~destinations["stop_id"].isin(self.nearby_stops["stop_id"])]
        return destinations

    def find_trips_between_locations(
        self,
        departure_lat: float,
        departure_lon: float,
        arrival_lat: float,
        arrival_lon: float,
        start_date: datetime,
        end_date: datetime,
        departure_time: pd.Timedelta,
    ) -> pd.DataFrame:
        departure_stops: pd.DataFrame = self.stops[
            (self.stops["stop_lat"] > departure_lat - DISTANCE_MARGIN / 2)
            & (self.stops["stop_lat"] < departure_lat + DISTANCE_MARGIN / 2)
            & (self.stops["stop_lon"] > departure_lon - DISTANCE_MARGIN / 2)
            & (self.stops["stop_lon"] < departure_lon + DISTANCE_MARGIN / 2)
        ]
        arrival_stops: pd.DataFrame = self.stops[
            (self.stops["stop_lat"] > arrival_lat - DISTANCE_MARGIN / 2)
            & (self.stops["stop_lat"] < arrival_lat + DISTANCE_MARGIN / 2)
            & (self.stops["stop_lon"] > arrival_lon - DISTANCE_MARGIN / 2)
            & (self.stops["stop_lon"] < arrival_lon + DISTANCE_MARGIN / 2)
        ]
        trips_containing_departure: pd.DataFrame = pd.merge(departure_stops, self.stop_times, on="stop_id")
        trips_containing_departure = trips_containing_departure[
            trips_containing_departure["departure_time"] > departure_time
        ]
        trips_containing_departure = trips_containing_departure.drop_duplicates(subset="trip_id")
        trips_containing_arrival: pd.DataFrame = pd.merge(arrival_stops, self.stop_times, on="stop_id")
        trips_containing_both: pd.DataFrame = pd.merge(
            trips_containing_departure, trips_containing_arrival, on="trip_id"
        )
        trips_in_right_direction: pd.DataFrame = trips_containing_both[
            trips_containing_both["departure_time_x"] < trips_containing_both["departure_time_y"]
        ]
        relevant_trips: pd.DataFrame = pd.merge(trips_in_right_direction, self.trips, on="trip_id")
        trips_in_dates = self.dates_from_trips(relevant_trips, start_date, end_date)
        return trips_in_dates

    def dates_from_trips(self, trips: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        services: pd.DataFrame = self.calendar[self.calendar["service_id"].isin(trips["service_id"])]
        services_within_period: pd.DataFrame = services[
            ((services["start_date"] >= start_date) & (services["start_date"] <= end_date))
            | ((services["end_date"] >= start_date) & (services["end_date"] <= end_date))
            | ((services["start_date"] <= start_date) & (services["end_date"] >= end_date))
        ]
        if services_within_period.empty:
            return pd.DataFrame()
        services_within_period = services_within_period.assign(
            days_ok_start=np.vectorize(lambda x: start_date if (start_date >= pd.to_datetime(x)) else x)(
                services_within_period["start_date"]
            ),
            days_ok_end=np.vectorize(lambda x: end_date if (end_date <= pd.to_datetime(x)) else x)(
                services_within_period["end_date"]
            ),
        )
        dataframe_concat = pd.DataFrame()
        for _, row in services_within_period.iterrows():
            df = pd.DataFrame(
                {
                    "date": pd.date_range(start=row.days_ok_start, end=row.days_ok_end),
                    "service_id": row.service_id,
                    "monday": row.monday,
                    "tuesday": row.tuesday,
                    "wednesday": row.wednesday,
                    "thursday": row.thursday,
                    "friday": row.friday,
                    "saturday": row.saturday,
                    "sunday": row.sunday,
                }
            )
            monday_index = df.columns.get_loc("monday")
            df = df[df.apply(lambda x: True if x.iloc[monday_index + x.date.weekday()] == 1 else False, axis=1)]
            dataframe_concat = pd.concat([dataframe_concat, df])
        dataframe_valid_calendar = pd.merge(trips, dataframe_concat, on="service_id")
        dataframe_valid_calendar = dataframe_valid_calendar.assign(idx = dataframe_valid_calendar.index)

        trips_to_check_if_cancel = dataframe_valid_calendar[["trip_id", "date", "idx"]]
        trips_to_check_if_cancel = pd.merge(trips_to_check_if_cancel, self.trips, on="trip_id")
        trips_canceled = pd.merge(trips_to_check_if_cancel, self.calendar_dates, on=["service_id", "date"])
        dataframe_valid_dates = dataframe_valid_calendar[
            ~dataframe_valid_calendar["idx"].isin(trips_canceled["idx"])
        ]
        dataframe_valid_dates.loc[:,"dep_time"] = dataframe_valid_dates["date"] + dataframe_valid_dates["departure_time_x"]
        dataframe_valid_dates.loc[:,"arr_time"] = dataframe_valid_dates["date"] + dataframe_valid_dates["departure_time_y"]
        dataframe_valid_dates.loc[:,"dep_time"] = dataframe_valid_dates.apply(
            lambda x: x["dep_time"].replace(tzinfo=pytz.timezone(self.timezone)).astimezone(tz=x["stop_timezone_x"]),
            axis=1,
        )
        dataframe_valid_dates.loc[:,"arr_time"] = dataframe_valid_dates.apply(
            lambda x: x["arr_time"].replace(tzinfo=pytz.timezone(self.timezone)).astimezone(tz=x["stop_timezone_y"]),
            axis=1,
        )
        return dataframe_valid_dates

    def get_list_of_cities(self) -> pd.DataFrame:
        appearance_count = self.stop_times.groupby("stop_id").count()["trip_id"]
        stop_cities = self.stops.set_index("stop_id")
        stop_cities = stop_cities.assign(number_of_appearance=appearance_count)
        return stop_cities
