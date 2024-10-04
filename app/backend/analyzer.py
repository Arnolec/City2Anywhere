from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from app.backend.models import Coords


# Interface for the different analyzers
class Analyzer(ABC):
    @abstractmethod
    def find_trips_between_locations(
        self,
        dep_coords: Coords,
        arr_coords: Coords,
        start_date: datetime,
        end_date: datetime,
        departure_time: pd.Timedelta,
    ) -> pd.DataFrame:
        pass

    @abstractmethod
    def find_destinations_from_location(
        self,
        city_coords: Coords,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_list_of_cities(self) -> pd.DataFrame:
        pass
