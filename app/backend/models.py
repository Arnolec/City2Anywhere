from pydantic import BaseModel


class HealthCheck(BaseModel):
    status: str = "OK"


class Periode(BaseModel):
    start: str = "2024-10-10T00:00:00"
    end: str = "2024-10-11T00:00:00"


class Coords(BaseModel):
    lat: float = 48.8566
    lon: float = 2.3522


class CoordsDistance(Coords):
    max_distance: float = 0.1


class Destinations(BaseModel):
    coords: Coords = Coords()
    periode: Periode = Periode()
    transport: list[str] = [
        "BLABLABUS",
        "FLIXBUS",
        "TER",
        "TGV",
        "INTERCITE",
        "INTERCITE",
        "DB-LONG",
        "DB-REGIONAL",
        "EUROSTAR",
    ]


class DestinationsCreate(Destinations):
    pass


class Trips(BaseModel):
    dep_coords: Coords = Coords()
    arr_coords: Coords = Coords()
    periode: Periode = Periode()
    dep_time: str = "06:00:00"
    transport: list[str] = [
        "BLABLABUS",
        "FLIXBUS",
        "TER",
        "TGV",
        "INTERCITE",
        "INTERCITE",
        "DB-LONG",
        "DB-REGIONAL",
        "EUROSTAR",
    ]


class TripsCreate(Trips):
    pass
