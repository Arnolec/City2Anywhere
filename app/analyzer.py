from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd


# Interface for the different analyzers
class Analyzer(ABC):
    @abstractmethod
    def find_trips_between_locations(
        self,
        departure_lat: float,
        departure_lon: float,
        arrival_lat: float,
        arrival_lon: float,
        start_date: datetime,
        end_date: datetime,
        departure_time: pd.Timedelta,
        max_distance: float,
    ) -> pd.DataFrame:
        pass

    @abstractmethod
    def find_destinations_from_location(
        self, lat: float, lon: float, start_date: datetime, end_date: datetime, max_distance: float
    ) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_list_of_cities(self) -> pd.DataFrame:
        pass
