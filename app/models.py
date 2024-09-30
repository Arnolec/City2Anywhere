from pydantic import BaseModel


class Periode(BaseModel):
    start: str
    end: str


class Coords(BaseModel):
    lat: float
    lon: float
    max_distance: float


class Destinations(BaseModel):
    coords: Coords
    start: str
    end: str
    transport: list[str] = []


class DestinationsCreate(Destinations):
    pass


class Trips(BaseModel):
    dep_coords: Coords
    arr_coords: Coords
    periode: Periode
    dep_time: str
    transport: list[str]


class TripsCreate(Trips):
    pass
