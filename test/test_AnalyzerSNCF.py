import pytest
import pandas as pd
from datetime import datetime

import AnalyzerSNCF as Ana


@pytest.fixture
def analyzer() -> Ana:
    return Ana.AnalyzerCalendarDates("TEST/AnalyzerSNCF")


# Testing of analyzer.find_nearby_stops


def test_nearby_stops(analyzer) -> None:
    stops = analyzer.find_nearby_stops(42.0, 2.0)
    assert stops.shape[0] == 1
    assert stops["stop_name"].values[0] == "Laval"


def test_nearby_no_stop(analyzer) -> None:
    stops = analyzer.find_nearby_stops(0, 0)
    assert stops.shape[0] == 0


def test_nearby_multiple_stops(analyzer) -> None:
    stops = analyzer.find_nearby_stops(45.000, 5.000)
    assert stops.shape[0] == 2
    assert "Paris001" in stops["stop_id"].values
    assert "Paris2001" in stops["stop_id"].values


# Testing of analyzer.get_trips_nearby_location


def test_trips_nearby_no_stops(analyzer) -> None:
    trips = analyzer.get_trips_nearby_location(0, 0)
    assert trips.shape[0] == 0


def test_trips_nearby_one_stop(analyzer) -> None:
    trips = analyzer.get_trips_nearby_location(50.0, 10.0)
    assert trips.shape[0] == 1
    assert trips.values[0] == "TRIP001"
    assert analyzer.unique_departures.shape[0] == 1
    assert analyzer.unique_departures["stop_id"].values[0] == "Marseille001"


def test_trips_nearby_one_stop_multiple_trips(analyzer) -> None:
    trips = analyzer.get_trips_nearby_location(100.0, 15.0)
    assert trips.shape[0] == 2
    assert "TRIP002" in trips.values
    assert "TRIP003" in trips.values
    assert analyzer.unique_departures.shape[0] == 2
    assert pd.Timedelta("17:56:00") in analyzer.unique_departures["departure_time"].values
    assert pd.Timedelta("18:56:00") in analyzer.unique_departures["departure_time"].values


def test_trips_nearby_multiple_stops_multiple_trips_not_same_trips(analyzer) -> None:
    trips = analyzer.get_trips_nearby_location(45.000, 0.000)
    assert "TRIP004" in trips.values
    assert "TRIP005" in trips.values
    assert "TRIP006" in trips.values
    assert trips.shape[0] == 3
    assert analyzer.unique_departures.shape[0] == 3
    assert "Nantes001" in analyzer.unique_departures["stop_id"].values
    assert "Nantes2001" in analyzer.unique_departures["stop_id"].values


def test_trips_nearby_multiple_stops_multiple_trips_same_trips(analyzer) -> None:
    trips = analyzer.get_trips_nearby_location(45.000, 5.000)
    assert "TRIP007" in trips.values
    assert "TRIP008" in trips.values
    assert "TRIP009" in trips.values
    assert trips.shape[0] == 3
    assert analyzer.unique_departures.shape[0] == 3
    assert "Paris001" in analyzer.unique_departures["stop_id"].values
    assert "Paris2001" in analyzer.unique_departures["stop_id"].values


# Testing of analyzer.filter_trips_within_period


def test_filter_trips_period_no_stop(analyzer) -> None:
    trips = analyzer.filter_trips_within_period(0, 0, datetime(2024, 7, 1), datetime(2024, 7, 1))
    assert trips.shape[0] == 0


def test_filter_trips_period_lower_than_real(analyzer) -> None:
    trips = analyzer.filter_trips_within_period(50.0, 10.0, datetime(2024, 1, 1), datetime(2024, 1, 1))
    assert trips.shape[0] == 0


def test_filter_trips_period_of_one_day(analyzer) -> None:
    trips = analyzer.filter_trips_within_period(50.0, 10.0, datetime(2024, 7, 1), datetime(2024, 7, 1))
    assert trips.shape[0] == 1
    assert trips.values[0] == "TRIP001"


def test_filter_trips_period_multiple_services(analyzer) -> None:
    trips = analyzer.filter_trips_within_period(100.0, 15.0, datetime(2024, 7, 1), datetime(2024, 7, 6))
    assert trips.shape[0] == 2
    assert "TRIP002" in trips.values
    assert "TRIP003" in trips.values


def test_filter_trips_period_multiple_trips_to_one_service(analyzer) -> None:
    trips = analyzer.filter_trips_within_period(45.000, 0.000, datetime(2024, 7, 1), datetime(2024, 8, 1))
    assert trips.shape[0] == 3
    assert "TRIP004" in trips.values
    assert "TRIP005" in trips.values
    assert "TRIP006" in trips.values


# Testing of analyzer.find_destinations_from_location


def test_find_destinations_no_stop(analyzer) -> None:
    destinations = analyzer.find_destinations_from_location(0, 0, datetime(2024, 7, 1), datetime(2024, 8, 1))
    assert destinations.shape[0] == 0


def test_find_destinations_dates_outside_of_period(analyzer) -> None:
    destinations = analyzer.find_destinations_from_location(45, 0.0, datetime(2023, 7, 1), datetime(2023, 8, 1))
    assert destinations.shape[0] == 0


def test_find_destinations_one_single_trip(analyzer) -> None:
    destinations = analyzer.find_destinations_from_location(50.0, 10.0, datetime(2024, 7, 1), datetime(2024, 7, 1))
    assert destinations.shape[0] == 1
    assert destinations["stop_name"].values[0] == "Perpignan"


def test_find_destinations_one_single_trip_multiple_destinations(analyzer) -> None:
    destinations = analyzer.find_destinations_from_location(40.0, 0.0, datetime(2024, 8, 10), datetime(2024, 8, 20))
    assert destinations.shape[0] == 2
    assert "Laval" in destinations["stop_name"].values
    assert "Strasbourg" in destinations["stop_name"].values


def test_find_destinations_same_city_in_one_trip(analyzer) -> None:
    destinations = analyzer.find_destinations_from_location(45.000, 5.000, datetime(2024, 7, 1), datetime(2024, 8, 1))
    assert destinations.shape[0] == 3
    assert "Laval" in destinations["stop_id"].values
    assert "Vannes" in destinations["stop_id"].values
    assert "Strasbourg" in destinations["stop_id"].values
    assert "Paris2" not in destinations["stop_id"].values


# Testing of analyzer.find_trips_between_locations


def test_find_trips_stops_not_found(analyzer) -> None:
    trips = analyzer.find_trips_between_locations(
        0, 0, 0, 0, datetime(2024, 7, 1), datetime(2024, 9, 1), pd.Timedelta("08:00:00")
    )
    assert trips.shape[0] == 0


def test_find_trips_hours_too_late(analyzer) -> None:
    trips = analyzer.find_trips_between_locations(
        50.0, 10.0, 48.0, 5.0, datetime(2024, 7, 1), datetime(2024, 7, 1), pd.Timedelta("20:00:00")
    )
    assert trips.shape[0] == 0


def test_find_trips_one(analyzer) -> None:
    trips = analyzer.find_trips_between_locations(
        50.0, 10.0, 48.0, 5.0, datetime(2024, 7, 1), datetime(2024, 7, 1), pd.Timedelta("08:00:00")
    )
    assert trips.shape[0] == 1
    assert "TRIP001" in trips["trip_id"].values


def test_find_trips_multiple(analyzer) -> None:
    trips = analyzer.find_trips_between_locations(
        100.0, 15.0, 48.0, 5.0, datetime(2024, 7, 1), datetime(2024, 8, 1), pd.Timedelta("08:00:00")
    )
    assert trips.shape[0] == 5
    assert "TRIP002" in trips["trip_id"].values
    assert "TRIP003" in trips["trip_id"].values


# Testing of analyzer.get_list_of_cities


def test_list_of_cities(analyzer) -> None:
    cities = analyzer.get_list_of_cities()
    assert cities.shape[0] == 11
    assert "Laval" in cities["stop_name"].values
    assert "Vannes" in cities["stop_name"].values
    assert "Strasbourg" in cities["stop_name"].values
    assert "number_of_appearance" in cities.columns
