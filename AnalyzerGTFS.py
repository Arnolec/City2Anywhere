# Version Stable de l'AnalyzerGTFS
import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta
import re

SEUIL_DISTANCE = 0.03

def date_to_timestamp(date):
    pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2})')
    if pattern.match(date) is None:
        return None
    else:
        match = pattern.search(date)
        return int(match[1])*3600 + int(match[2])*60 + int(match[3])

# Exemple de ville : StopArea:OCE87586545

class AnalyzerGTFS:
    stop_time_trip = [] # Contient StopPoints, Trajets et horaires des trajets
    trip = [] # Contient les trip_id, route_id et les services_id
    stops_trip_id = [] # Contient tous les stops des trajets corrects
    date = [] # Contient tous les services et toutes les dates comprises entre date_min et date_max, (Utile pour afficher à l'utilisateur toutes les dates possibles pour le trajet)
    destinations = [] # Contient les stops après la ville (StopSequence > StopSequence de la ville)
    stops = []
    calendar_dates = []
    routes = []
    stop_times = []
    trips = []
    lat = 0
    lon = 0
    date_min = None
    date_max = None

    def __init__(self, path ='TER'):
        self.calendar_dates = pd.read_csv('Data/'+ path +'/calendar_dates.txt')
        self.stop_times = pd.read_csv('Data/'+ path +'/stop_times.txt')[['trip_id', 'stop_id', 'departure_time']]
        self.stops = pd.read_csv('Data/'+ path +'/stops.txt')[['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'parent_station']]
        self.trips = pd.read_csv('Data/'+ path +'/trips.txt')[['service_id', 'trip_id', 'route_id']]
        self.calendar_dates.date = pd.to_datetime(self.calendar_dates["date"], format='%Y%m%d').dt.date
        self.calendar_dates = self.calendar_dates.drop_duplicates(subset='service_id')
        self.stop_times.departure_time = self.stop_times.apply(lambda x : date_to_timestamp(x['departure_time']), axis=1)
        self.stops['parent_station'] = self.stops['parent_station'].fillna('')
    
    # Etape 1 : Récupérer les stops de la ville / StopArea
    def get_stops(self):
        self.id_ville = self.villes_proches(self.lat, self.lon)
        ville_Set = set(self.id_ville['stop_id'].array)
        return self.stops[[set([l]).issubset(ville_Set) for l in self.stops.parent_station.values.tolist()]]['stop_id']
    
    # Etape 2 : Récupérer tous les trajets des différents StopPoints, peut importe la date
    def get_trips(self):
        stops_ids = self.get_stops()
        self.stop_time_trip = pd.merge(self.stop_times, stops_ids, on='stop_id')
        self.stop_time_trip = self.stop_time_trip.drop_duplicates(subset='trip_id') #Doublons possibles si deux StopPoints différents sont sur un même trajet
        return self.stop_time_trip['trip_id']

    # Etape 3 : Récupérer les services_id des Trajets
    def get_service_id(self):
        trip_ids = self.get_trips()
        self.trip = pd.merge(trip_ids, self.trips, on='trip_id')
        return self.trip['service_id']
    
    # Etape 4 : Récupérer les services fonctionnant sur les dates données
    def get_dates(self):
        service_id = self.get_service_id()
        dates = pd.merge(service_id, self.calendar_dates, on='service_id')
        return dates[(dates['date'] >= self.date_min) & (dates['date'] <= self.date_max)]
    
    # Etape 5 : Récupérer les trajets des services fonctionnant sur les dates données
    def get_trajets(self):
        services_uniques = self.get_dates().drop_duplicates(subset='service_id')
        return pd.merge(services_uniques, self.trip, on='service_id')
    
    # Etape 6 : Récupérer les stops des trajets corrects
    def get_stops_trajets(self):
        trajets = self.get_trajets()
        return pd.merge(trajets, self.stop_times, on='trip_id')
    
    # Etape 7 : Récupérer les ids des destinations, c'est à dire les stops après la ville (StopSequence > StopSequence de la ville)
    def get_stops_destinations(self):
        stops_trip_id = self.get_stops_trajets().assign(temps_ville = "", stop_id_ville = "")

        stop_ids_ville = self.stop_time_trip['stop_id']
        stop_ids_ville.index = self.stop_time_trip['trip_id']
        stop_id_ville_origine = stop_ids_ville.loc[stops_trip_id['trip_id']]

        stops_trip_id['stop_id_ville'] = stop_id_ville_origine.array
        time = self.stop_time_trip['departure_time'] #StopTime trip
        time.index = self.stop_time_trip['trip_id']
        value = time.loc[stops_trip_id['trip_id']]
        stops_trip_id['temps_ville'] = value.array
        self.destinations = stops_trip_id[stops_trip_id['departure_time'] > stops_trip_id['temps_ville']]
        return self.destinations['stop_id']
    
    # Etape 8 : Récupérer les destinations
    def get_destinations(self, lat, lon, date_min = datetime.today, date_max = datetime.today):
        self.load_search(lat, lon, date_min, date_max)
        destinations_uniques = self.get_stops_destinations()
        destinations_StopPoint = pd.merge(destinations_uniques, self.stops, on='stop_id')
        destinationSet = set(destinations_StopPoint['parent_station'].array)
        destinations_StopArea = self.stops[[set([l]).issubset(destinationSet) for l in self.stops.stop_id.values.tolist()]]
        destinations_StopArea.drop_duplicates(subset='stop_id')
        return destinations_StopArea
    
    # Retourne les stopArea proche du point de départ
    def villes_proches(self,lat,long):
        return self.stops[(self.stops['stop_lat'] > lat-SEUIL_DISTANCE) & (self.stops['stop_lat'] < lat+SEUIL_DISTANCE) & (self.stops['stop_lon'] > long-SEUIL_DISTANCE) & (self.stops['stop_lon'] < long+SEUIL_DISTANCE) & self.stops['stop_id'].str.contains('StopArea')]
    
    # Pas très efficace, à améliorer
    def trajet_destination(self,villeDestination):
        destinationsParentStation = pd.merge(self.destinations, self.stops, on='stop_id') # Merge entre les destinations et les stops pour récupérer les parent_station
        StopPoints = destinationsParentStation[villeDestination == destinationsParentStation['parent_station']] # Récupérer les StopPoints de la ville de destination
        trajets = pd.merge(StopPoints, self.destinations, on=['stop_id','service_id','temps_ville','departure_time','trip_id','stop_id_ville','route_id']) # Merge entre StopPoints de la ville et les destinations pour récupérer les trajets faisant le lien entre les deux
        trajets_services = pd.merge(trajets.drop_duplicates(subset='service_id'), self.get_dates(), on='service_id') 
        trajets_services.assign(jour_suivant_depart = 0, jour_suivant_arrivee = 0)
        # Rectification des temps de trajet si > 24h
        trajets_services['jour_suivant_depart'] = trajets_services.apply(lambda x : x['temps_ville'] > 24*3600, axis=1)
        trajets_services['temps_ville'] = trajets_services.apply(lambda x : x['temps_ville']-24*3600 if x['jour_suivant_depart'] else x['temps_ville'] , axis=1)
        trajets_services['jour_suivant_arrivee'] = trajets_services.apply(lambda x : x['departure_time'] > 24*3600, axis=1)
        trajets_services['departure_time'] = trajets_services.apply(lambda x : x['departure_time'] - 24*3600 if x['jour_suivant_arrivee'] else x['departure_time'], axis=1)
        return trajets_services # Retourne tous les trajets faisant le lien entre la ville et la destination marchant sur les critères sélectionnés

    @staticmethod
    def list_of_cities(path):
        stops = pd.read_csv('Data/'+ path +'/stops.txt')[['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'parent_station']]
        return stops[stops['stop_id'].str.contains('StopArea')][['stop_name','stop_lat','stop_lon','stop_id']]
    
    def load_search(self, lat, lon ,date_min= datetime.today,date_max = datetime.today):
        self.lat = lat
        self.lon = lon
        self.date_min = datetime.strptime(date_min, '%Y%m%d').date()
        self.date_max = datetime.strptime(date_max, '%Y%m%d').date()