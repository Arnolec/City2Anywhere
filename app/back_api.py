from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd

import app.back_methods as back
import app.models as models

app = FastAPI()

# Nécessite une V2 pour régler probablement les requêtes et ce qui est retourné

origins = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://localhost",
    "http://localhost:8080" "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

back.update_data()
analyzers = back.load_analyzers()
list_cities: dict = back.get_cities(analyzers)


@app.get("/", response_model=str)
def default_route():
    return "Hello, default route"


@app.get("/list_cities/")
def get_list_cities() -> dict:
    if len(list_cities) == 0:
        return JSONResponse(None, 404)
    return JSONResponse(list_cities, 200)


@app.get("/center/")
def get_center() -> tuple[float, float]:
    cities = pd.DataFrame(list_cities)
    centroid = back.get_center(cities)
    if centroid is None:
        return JSONResponse(None, 404)
    result = {"x": centroid.x, "y": centroid.y}
    return JSONResponse(result, 200)


@app.patch("/destinations/")
def get_destinations(params: models.DestinationsCreate):
    try:
        start = datetime.strptime(params.start, "%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(params.end, "%Y-%m-%dT%H:%M:%S")
    except ValueError as e:
        return JSONResponse("Erreur sur les paramètres liés au temps" + e, 422)
    destinations = back.get_destinations(
        params.coords, [start, end], params.transport, analyzers, pd.DataFrame(list_cities)
    )
    return destinations


@app.patch("/trips/")
def get_trips(params: models.TripsCreate):
    try:
        start = datetime.strptime(params.periode.start, "%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(params.periode.end, "%Y-%m-%dT%H:%M:%S")
        dep_time = datetime.strptime("2000-10-10T" + params.dep_time, "%Y-%m-%dT%H:%M:%S")
    except ValueError as e:
        return JSONResponse("Erreur sur les paramètres liés au temps" + e, 422)
    trips = back.get_trips_to_city(
        params.dep_coords, params.arr_coords, [start, end], analyzers, params.transport, dep_time
    )
    return trips
