from datetime import datetime

import pandas as pd
import pytest

import app.analyzerCalendarDates as Ana
from app.models import Coords


@pytest.fixture
def analyzer() -> Ana:
    return Ana.AnalyzerCalendarDates("TEST/AnalyzerCalendarDates")


# Testing of analyzer.find_nearby_stops


def test_nearby_stops(analyzer) -> None:
    coords = Coords(lat=42.0, lon=2.0, max_distance=0.5)
    stops = analyzer.find_nearby_stops(coords)
    assert stops.shape[0] == 1
    assert stops["stop_name"].values[0] == "Laval"


def test_nearby_no_stop(analyzer) -> None:
    coords = Coords(lat=0, lon=0, max_distance=0.5)
    stops = analyzer.find_nearby_stops(coords)
    assert stops.shape[0] == 0


def test_nearby_multiple_stops(analyzer) -> None:
    coords = Coords(lat=45.0, lon=5.0, max_distance=0.5)
    stops = analyzer.find_nearby_stops(coords)
    assert stops.shape[0] == 2
    assert "Paris001" in stops["stop_id"].values
    assert "Paris2001" in stops["stop_id"].values


# Testing of analyzer.get_trips_nearby_location


def test_trips_nearby_no_stops(analyzer) -> None:
    coords = Coords(lat=0, lon=0, max_distance=0.5)
    trips = analyzer.get_trips_nearby_location(coords)
    assert trips.shape[0] == 0


def test_trips_nearby_one_stop(analyzer) -> None:
    coords = Coords(lat=50.0, lon=10.0, max_distance=0.5)
    trips = analyzer.get_trips_nearby_location(coords)
    assert trips.shape[0] == 1
    assert trips.values[0] == "TRIP001"
    assert analyzer.unique_departures.shape[0] == 1
    assert analyzer.unique_departures["stop_id"].values[0] == "Marseille001"


def test_trips_nearby_one_stop_multiple_trips(analyzer) -> None:
    coords = Coords(lat=100.0, lon=15.0, max_distance=0.5)
    trips = analyzer.get_trips_nearby_location(coords)
    assert trips.shape[0] == 2
    assert "TRIP002" in trips.values
    assert "TRIP003" in trips.values
    assert analyzer.unique_departures.shape[0] == 2
    assert pd.Timedelta("17:56:00") in analyzer.unique_departures["departure_time"].values
    assert pd.Timedelta("18:56:00") in analyzer.unique_departures["departure_time"].values


def test_trips_nearby_multiple_stops_multiple_trips_not_same_trips(analyzer) -> None:
    coords = Coords(lat=45.0, lon=0.0, max_distance=0.5)
    trips = analyzer.get_trips_nearby_location(coords)
    assert "TRIP004" in trips.values
    assert "TRIP005" in trips.values
    assert "TRIP006" in trips.values
    assert trips.shape[0] == 3
    assert analyzer.unique_departures.shape[0] == 3
    assert "Nantes001" in analyzer.unique_departures["stop_id"].values
    assert "Nantes2001" in analyzer.unique_departures["stop_id"].values


def test_trips_nearby_multiple_stops_multiple_trips_same_trips(analyzer) -> None:
    coords = Coords(lat=45.0, lon=5.0, max_distance=0.5)
    trips = analyzer.get_trips_nearby_location(coords)
    assert "TRIP007" in trips.values
    assert "TRIP008" in trips.values
    assert "TRIP009" in trips.values
    assert trips.shape[0] == 3
    assert analyzer.unique_departures.shape[0] == 3
    assert "Paris001" in analyzer.unique_departures["stop_id"].values
    assert "Paris2001" in analyzer.unique_departures["stop_id"].values


# Testing of analyzer.filter_trips_within_period


def test_filter_trips_period_no_stop(analyzer) -> None:
    coords = Coords(lat=0.0, lon=0.0, max_distance=0.5)
    trips = analyzer.filter_trips_within_period(coords, datetime(2024, 7, 1), datetime(2024, 7, 1))
    assert trips.shape[0] == 0


def test_filter_trips_period_lower_than_real(analyzer) -> None:
    coords = Coords(lat=50.0, lon=10.0, max_distance=0.5)
    trips = analyzer.filter_trips_within_period(coords, datetime(2024, 1, 1), datetime(2024, 1, 1))
    assert trips.shape[0] == 0


def test_filter_trips_period_of_one_day(analyzer) -> None:
    coords = Coords(lat=50.0, lon=10.0, max_distance=0.5)
    trips = analyzer.filter_trips_within_period(coords, datetime(2024, 7, 1), datetime(2024, 7, 1))
    assert trips.shape[0] == 1
    assert trips.values[0] == "TRIP001"


def test_filter_trips_period_multiple_services(analyzer) -> None:
    coords = Coords(lat=100.0, lon=15.0, max_distance=0.5)
    trips = analyzer.filter_trips_within_period(coords, datetime(2024, 7, 1), datetime(2024, 7, 6))
    assert trips.shape[0] == 2
    assert "TRIP002" in trips.values
    assert "TRIP003" in trips.values


def test_filter_trips_period_multiple_trips_to_one_service(analyzer) -> None:
    coords = Coords(lat=45.0, lon=0.0, max_distance=0.5)
    trips = analyzer.filter_trips_within_period(coords, datetime(2024, 7, 1), datetime(2024, 8, 1))
    assert trips.shape[0] == 3
    assert "TRIP004" in trips.values
    assert "TRIP005" in trips.values
    assert "TRIP006" in trips.values


# Testing of analyzer.find_destinations_from_location


def test_find_destinations_no_stop(analyzer) -> None:
    coords = Coords(lat=0.0, lon=0.0, max_distance=0.5)
    destinations = analyzer.find_destinations_from_location(coords, datetime(2024, 7, 1), datetime(2024, 8, 1))
    assert destinations.shape[0] == 0


def test_find_destinations_dates_outside_of_period(analyzer) -> None:
    coords = Coords(lat=45.0, lon=0.0, max_distance=0.5)
    destinations = analyzer.find_destinations_from_location(coords, datetime(2023, 7, 1), datetime(2023, 8, 1))
    assert destinations.shape[0] == 0


def test_find_destinations_one_single_trip(analyzer) -> None:
    coords = Coords(lat=50.0, lon=10.0, max_distance=0.5)
    destinations = analyzer.find_destinations_from_location(coords, datetime(2024, 7, 1), datetime(2024, 7, 1))
    assert destinations.shape[0] == 1
    assert destinations["stop_name"].values[0] == "Perpignan"


def test_find_destinations_one_single_trip_multiple_destinations(analyzer) -> None:
    coords = Coords(lat=40.0, lon=0.0, max_distance=0.5)
    destinations = analyzer.find_destinations_from_location(coords, datetime(2024, 8, 10), datetime(2024, 8, 20))
    assert destinations.shape[0] == 2
    assert "Laval" in destinations["stop_name"].values
    assert "Strasbourg" in destinations["stop_name"].values


def test_find_destinations_same_city_in_one_trip(analyzer) -> None:
    coords = Coords(lat=45.0, lon=5.0, max_distance=0.5)
    destinations = analyzer.find_destinations_from_location(coords, datetime(2024, 7, 1), datetime(2024, 8, 1))
    assert destinations.shape[0] == 3
    assert "Laval001" in destinations["stop_id"].values
    assert "Vannes001" in destinations["stop_id"].values
    assert "Strasbourg001" in destinations["stop_id"].values
    assert "Paris2001" not in destinations["stop_id"].values


# Testing of analyzer.find_trips_between_locations


def test_find_trips_stops_not_found(analyzer) -> None:
    dep_coords = Coords(lat=0.0, lon=0.0, max_distance=0.5)
    arr_coords = Coords(lat=0.0, lon=0.0, max_distance=0.5)
    trips = analyzer.find_trips_between_locations(
        dep_coords, arr_coords, datetime(2024, 7, 1), datetime(2024, 9, 1), pd.Timedelta("08:00:00")
    )
    assert trips.shape[0] == 0


def test_find_trips_hours_too_late(analyzer) -> None:
    dep_coords = Coords(lat=50.0, lon=10.0, max_distance=0.5)
    arr_coords = Coords(lat=48.0, lon=5.0, max_distance=0.5)
    trips = analyzer.find_trips_between_locations(
        dep_coords, arr_coords, datetime(2024, 7, 1), datetime(2024, 7, 1), pd.Timedelta("20:00:00")
    )
    assert trips.shape[0] == 0


def test_find_trips_one(analyzer) -> None:
    dep_coords = Coords(lat=50.0, lon=10.0, max_distance=0.5)
    arr_coords = Coords(lat=48.0, lon=5.0, max_distance=0.5)
    trips = analyzer.find_trips_between_locations(
        dep_coords, arr_coords, datetime(2024, 7, 1), datetime(2024, 7, 1), pd.Timedelta("08:00:00")
    )
    assert trips.shape[0] == 1
    assert "TRIP001" in trips["trip_id"].values


def test_find_trips_multiple(analyzer) -> None:
    dep_coords = Coords(lat=100.0, lon=15.0, max_distance=0.5)
    arr_coords = Coords(lat=48.0, lon=5.0, max_distance=0.5)
    trips = analyzer.find_trips_between_locations(
        dep_coords, arr_coords, datetime(2024, 7, 1), datetime(2024, 8, 1), pd.Timedelta("08:00:00")
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
