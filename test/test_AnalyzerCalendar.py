import pytest
import pandas as pd
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from AnalyzerCalendar import AnalyzerCalendar as Analyzer

@pytest.fixture
def analyzer() -> Analyzer:
    return Analyzer("TEST/AnalyzerCalendar")

# Testing of analyzer.find_nearby_stops

def test_nearby_stops_none(analyzer) -> None:
    stops = analyzer.find_nearby_stops(0 , 0)
    assert stops.shape[0] == 0

def test_nearby_stops_one(analyzer) -> None:
    stops = analyzer.find_nearby_stops(1.0 , 1.0)
    assert stops.shape[0] == 1
    assert stops["stop_name"].values[0] == "Laval"

def test_nearby_stops_multiple_stops(analyzer) -> None:
    stops = analyzer.find_nearby_stops(8.0 , 8.0)
    assert stops.shape[0] == 2
    assert "Avignon1" in stops["stop_name"].values
    assert "Avignon2" in stops["stop_name"].values

# Testing of analyzer.get_trips_nearby_location

def test_trips_nearby_no_stops(analyzer) -> None:
    trips = analyzer.get_trips_nearby_location(0, 0)
    assert trips.shape[0] == 0

def test_trips_nearby_one_stop(analyzer) -> None:
    trips = analyzer.get_trips_nearby_location(1.0, 1.0)
    assert trips.shape[0] == 1
    assert trips.values[0] == "TRIP001"
    assert analyzer.unique_departures.shape[0] == 1
    assert analyzer.unique_departures["stop_id"].values[0] == "Laval_id"

def test_trips_nearby_one_stop_multiple_trips(analyzer) -> None:
    trips = analyzer.get_trips_nearby_location(2.0, 2.0)
    assert trips.shape[0] == 2
    assert "TRIP001" in trips.values
    assert "TRIP002" in trips.values
    assert analyzer.unique_departures.shape[0] == 2
    assert "Nantes_id" in analyzer.unique_departures["stop_id"].values

def test_trips_nearby_multiple_stops_multiple_trips_not_same_trips(analyzer) -> None:
    trips = analyzer.get_trips_nearby_location(15.0 , 15.0)
    assert "TRIP003" in trips.values
    assert "TRIP004" in trips.values
    assert trips.shape[0] == 2
    assert analyzer.unique_departures.shape[0] == 2
    assert "Strasbourg1_id" in analyzer.unique_departures["stop_id"].values
    assert "Strasbourg2_id" in analyzer.unique_departures["stop_id"].values

def test_trips_nearby_multiple_stops_multiple_trips_same_trips(analyzer) -> None:
    trips = analyzer.get_trips_nearby_location(15.0 , 15.0)
    assert "TRIP003" in trips.values
    assert "TRIP004" in trips.values
    assert trips.shape[0] == 2
    assert analyzer.unique_departures.shape[0] == 2
    assert "Strasbourg1_id" in analyzer.unique_departures["stop_id"].values
    assert "Strasbourg2_id" in analyzer.unique_departures["stop_id"].values

def test_trips_nearby_multiple_stops_multiple_trips_same_trips(analyzer) -> None:
    trips = analyzer.get_trips_nearby_location(8.0 , 8.0)
    assert "TRIP005" in trips.values
    assert "TRIP006" in trips.values
    assert "TRIP007" in trips.values
    assert trips.shape[0] == 3
    assert analyzer.unique_departures.shape[0] == 3
    assert "Avignon1_id" in analyzer.unique_departures["stop_id"].values
    assert "Avignon2_id" in analyzer.unique_departures["stop_id"].values

# Testing of analyzer.filter_trips_within_period

def test_filter_trips_within_period_no_trips(analyzer) -> None:
    trips = analyzer.filter_trips_within_period(0, 0, datetime(2024, 7, 1), datetime(2024, 7, 1))
    assert trips.shape[0] == 0

def test_filter_trips_within_period_one_trip_outside_period(analyzer) -> None:
    trips = analyzer.filter_trips_within_period(1.0, 1.0, datetime(2023, 7, 1), datetime(2023, 7, 1))
    assert trips.shape[0] == 0

def test_filter_trips_within_period_one_trip_in_period(analyzer) -> None:
    trips = analyzer.filter_trips_within_period(1.0, 1.0, datetime(2024, 7, 1), datetime(2024, 7, 1))
    assert trips.shape[0] == 1
    assert trips.values[0] == "TRIP001"

def test_filter_trips_within_period_trips_in_period_but_no_days(analyzer) -> None:
    trips = analyzer.filter_trips_within_period(2.0, 2.0, datetime(2024, 6, 20), datetime(2024, 7, 3))
    assert trips.shape[0] == 1
    assert trips.values[0] == "TRIP001"

def test_filter_trips_within_period_trips_in_period_and_days(analyzer) -> None:
    trips = analyzer.filter_trips_within_period(2.0, 2.0, datetime(2024, 7, 3), datetime(2024, 7, 8))
    assert trips.shape[0] == 1
    assert "TRIP002" in trips.values

def test_filter_trips_within_period_multiple_trips_in_period_and_days(analyzer) -> None:
    trips = analyzer.filter_trips_within_period(15.0, 15.0, datetime(2024, 7, 3), datetime(2024, 7, 10))
    assert trips.shape[0] == 2
    assert "TRIP003" in trips.values
    assert "TRIP004" in trips.values

# Testing of analyzer.find_destinations_from_location

def test_find_destinations_no_stop(analyzer) -> None:
    destinations = analyzer.find_destinations_from_location(0, 0, datetime(2024, 7, 1), datetime(2024, 8, 1))
    assert destinations.shape[0] == 0

def test_find_destinations_dates_outside_of_period(analyzer) -> None:
    destinations = analyzer.find_destinations_from_location(15.0, 15.0, datetime(2023, 7, 1), datetime(2023, 8, 1))
    assert destinations.shape[0] == 0

def test_find_destinations_one_single_trip(analyzer) -> None:
    destinations = analyzer.find_destinations_from_location(1.0, 1.0, datetime(2024, 7, 1), datetime(2024, 7, 1))
    assert destinations.shape[0] == 1
    assert destinations["stop_name"].values[0] == "Nantes"

def test_find_destinations_one_single_trip_multiple_destinations(analyzer) -> None:
    destinations = analyzer.find_destinations_from_location(15.0, 15.0, datetime(2024, 7, 1), datetime(2024, 7, 7))
    assert destinations.shape[0] == 2
    assert "Vannes" in destinations["stop_name"].values
    assert "SaintMalo" in destinations["stop_name"].values

def test_find_destinations_same_city_in_one_trip(analyzer) -> None:
    destinations = analyzer.find_destinations_from_location(8.0 , 8.0, datetime(2024, 7, 1), datetime(2024, 8, 1))
    assert destinations.shape[0] == 5
    assert "Avignon2" not in destinations["stop_name"].values
    assert "Marseille" in destinations["stop_name"].values
    assert "Lyon" in destinations["stop_name"].values
    assert "Brest" in destinations["stop_name"].values
    assert "Bordeaux" in destinations["stop_name"].values
    assert "Nimes" in destinations["stop_name"].values

# Testing of analyzer.find_trips_beetween_locations

def test_find_trips_no_stop(analyzer) -> None:
    destinations = analyzer.find_trips_between_locations(0.0, 0.0, 1.0, 1.0, datetime(2024, 7, 1), datetime(2024, 8, 1), pd.Timedelta(hours=6))
    assert destinations.shape[0] == 0

def test_find_trips_hours_too_late(analyzer) -> None:
    destinations = analyzer.find_trips_between_locations(1.0, 1.0, 2.0, 2.0, datetime(2024, 7, 1), datetime(2024, 8, 1), pd.Timedelta(hours=20))
    assert destinations.shape[0] == 0

def test_find_trips_one_single_trip(analyzer) -> None:
    destinations = analyzer.find_trips_between_locations(1.0, 1.0, 2.0, 2.0, datetime(2024, 7, 1), datetime(2024, 8, 1), pd.Timedelta(hours=6))
    assert destinations.shape[0] == 1
    assert destinations["arr_time"].values[0] == pd.to_datetime(datetime(2024, 7, 1)) + pd.Timedelta("12:45:00")

def test_find_trips_two_same_stops_same_trip_multiple_dates(analyzer) -> None:
    destinations = analyzer.find_trips_between_locations(8.0, 8.0, 9.0, 9.0, datetime(2024, 7, 1), datetime(2024, 8, 1), pd.Timedelta(hours=6))
    assert destinations.shape[0] == 15

def test_find_trips_one_trip_multiple_dates(analyzer) -> None:
    destinations = analyzer.find_trips_between_locations(15.0, 15.0, 5.0, 5.0, datetime(2024, 7, 1), datetime(2024, 8, 1), pd.Timedelta(hours=6))
    assert destinations.shape[0] == 4

def test_find_trips_one_trip_multiple_dates(analyzer) -> None:
    destinations = analyzer.find_trips_between_locations(15.0, 15.0, 5.0, 5.0, datetime(2024, 7, 1), datetime(2024, 8, 1), pd.Timedelta(hours=6))
    assert destinations.shape[0] == 4

def test_find_trips_one_trip_multiple_dates2(analyzer) -> None:
    destinations = analyzer.find_trips_between_locations(15.0, 15.0, 4.0, 4.0, datetime(2024, 7, 4), datetime(2024, 8, 5), pd.Timedelta(hours=6))
    assert destinations.shape[0] == 1

# Testing of analyzer.get_list_of_cities

def test_list_of_cities(analyzer) -> None:
    cities = analyzer.get_list_of_cities()
    assert cities.shape[0] == 17
    assert "Laval" in cities["stop_name"].values
    assert "Vannes" in cities["stop_name"].values
    assert "Strasbourg1" in cities["stop_name"].values
    assert "number_of_appearance" in cities.columns