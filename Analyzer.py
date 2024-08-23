from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd


# Interface for the different analyzers
class Analyzer(ABC):
    @abstractmethod
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
        pass

    @abstractmethod
    def get_set_destinations(self, lat: float, lon: float, date_min: datetime, date_max: datetime) -> pd.DataFrame:
        pass

    @abstractmethod
    def list_of_cities(self) -> pd.DataFrame:
        pass
