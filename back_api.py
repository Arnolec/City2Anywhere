from datetime import datetime

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.backend.back_methods as back
import app.backend.models as models

app = FastAPI()

# Nécessite une V2 pour régler probablement les requêtes et ce qui est retourné


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

back.update_data()
analyzers = back.load_analyzers()
list_cities: pd.DataFrame = back.get_cities(analyzers)


@app.get("/", response_model=models.HealthCheck(), summary="Default route, ensure the API is running")
def default_route():
    return models.HealthCheck(status="OK")


@app.get("/v1/transports/", tags=["v1"], summary="Get the list of transports")
def get_transports() -> dict:
    keys = [*analyzers.keys()]
    if len(keys) == 0:
        return JSONResponse(None, 404)
    result = {"transport_types": keys}
    return result


@app.get("/v1/list_cities/", tags=["v1"], summary="Get the list of cities")
def get_list_cities() -> dict:
    cities = list_cities.to_dict()
    if len(cities) == 0:
        return JSONResponse(None, 404)
    return JSONResponse(cities, 200)


@app.get("/v1/center/", tags=["v1"], summary="Get the center of the cities")
def get_center() -> tuple[float, float]:
    centroid = back.get_center(list_cities)
    if centroid is None:
        return JSONResponse(None, 404)
    result = {"x": centroid.x, "y": centroid.y}
    return JSONResponse(result, 200)


@app.patch("/v1/destinations/", tags=["v1"], summary="Get the destinations from the departure city at a given time")
def get_destinations(params: models.DestinationsCreate):
    try:
        start = datetime.strptime(params.periode.start, "%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(params.periode.end, "%Y-%m-%dT%H:%M:%S")
        if end < start:
            return JSONResponse("Erreur : la fin est inférieure au début", 422)
    except ValueError as e:
        return JSONResponse("Erreur sur les paramètres liés au temps" + e, 422)
    try:
        coords = back.get_city_max_distance(params.coords, list_cities)
        if coords is None:
            return JSONResponse("Aucune ville trouvée avec ces coordonnées", 422)
    except ValueError:
        return JSONResponse("Erreur sur les paramètres liés aux coordonnées", 404)
    destinations = back.get_destinations(coords, [start, end], params.transport, analyzers, list_cities)
    return destinations


@app.patch("/v1/trips/", tags=["v1"], summary="Get the trips beetween chosen cities at a given time")
def get_trips(params: models.TripsCreate):
    try:
        start = datetime.strptime(params.periode.start, "%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(params.periode.end, "%Y-%m-%dT%H:%M:%S")
        if end < start:
            return JSONResponse("Erreur : la fin est inférieure au début", 422)
        dep_time = datetime.strptime("2000-10-10T" + params.dep_time, "%Y-%m-%dT%H:%M:%S")
    except ValueError as e:
        return JSONResponse("Erreur sur les paramètres liés au temps" + e, 422)
    try:
        dep_coords = back.get_city_max_distance(params.dep_coords, list_cities)
        arr_coords = back.get_city_max_distance(params.arr_coords, list_cities)
        if dep_coords is None or arr_coords is None:
            return JSONResponse("Aucune ville de départ ou d'arrivée trouvée avec ces coordonnées", 404)
    except ValueError:
        return JSONResponse("Erreur sur les paramètres liés aux coordonnées", 422)
    trips = back.get_trips_to_city(dep_coords, arr_coords, [start, end], analyzers, params.transport, dep_time)
    return trips
