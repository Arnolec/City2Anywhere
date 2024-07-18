import pandas as pd
from datetime import datetime

SEUIL_DISTANCE = 0.03

# Nouvelle version de la classe AnalyzerGTFS, version qui est optimisée

class AnalyzerGTFS:
    arrets_depart = []
    stops = []
    calendar_dates = []
    routes = []
    stop_times = []
    trips = []
    lat = 0
    lon = 0
    date_min = pd.to_datetime('2024-07-01')
    date_max = pd.to_datetime('2024-08-31')

    def __init__(self, path ='TER'):
        self.calendar_dates = pd.read_csv('Data/'+ path +'/calendar_dates.txt')
        self.stop_times = pd.read_csv('Data/'+ path +'/stop_times.txt')[['trip_id', 'stop_id', 'departure_time']]
        self.stops = pd.read_csv('Data/'+ path +'/stops.txt')[['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'parent_station']]
        self.trips = pd.read_csv('Data/'+ path +'/trips.txt')[['service_id', 'trip_id', 'route_id']]
        self.calendar_dates.date = pd.to_datetime(self.calendar_dates["date"], format='%Y%m%d')
        self.stop_times['departure_time'] = pd.to_timedelta(self.stop_times['departure_time'])
        self.stops['parent_station'] = self.stops['parent_station'].fillna('')
    
    def load_search_destinations(self, lat : float, lon : float ,date_min : str,date_max : str) -> None:
        self.lat = lat
        self.lon = lon
        self.date_min = pd.to_datetime(date_min, format='%Y%m%d')
        self.date_max = pd.to_datetime(date_max, format='%Y%m%d')
    

    # Retourne les StopPoints proche du point de départ
    def stops_proches(self,lat : float,lon : float): # Stop ID pour Global, parent_station pour SNCF
        return self.stops[(self.stops['stop_lat'] > lat-SEUIL_DISTANCE) & (self.stops['stop_lat'] < lat+SEUIL_DISTANCE) & (self.stops['stop_lon'] > lon-SEUIL_DISTANCE) & (self.stops['stop_lon'] < lon+SEUIL_DISTANCE) & self.stops['parent_station'].str.contains('StopArea')]
    
    def trips_stops_proches(self) -> pd.Series:
        stops_proches = self.stops_proches(self.lat, self.lon)
        trips = self.stop_times[self.stop_times['stop_id'].isin(stops_proches['stop_id'])]
        self.arrets_depart = trips.drop_duplicates(subset='trip_id')
        trips_ids = self.arrets_depart['trip_id']
        return trips_ids
    
    def trips_dans_periode(self) -> pd.Series:
        trips_ids = self.trips_stops_proches()
        trips = self.trips[self.trips['trip_id'].isin(trips_ids)]
        services = self.calendar_dates[self.calendar_dates['service_id'].isin(trips['service_id'])]
        services_dans_periode = services[(services['date'] >= self.date_min) & (services['date'] <= self.date_max)]
        services_dans_periode.drop_duplicates(subset='service_id')
        trips_dans_periode = trips[trips['service_id'].isin(services_dans_periode['service_id'])]
        return trips_dans_periode['trip_id']
    
    def get_set_destinations(self, lat : float, lon : float, date_min : str, date_max : str) -> pd.DataFrame:
        self.load_search_destinations(lat,lon,date_min,date_max)
        trips_ids_dans_periode = self.trips_dans_periode()
        stop_times_arret_correct = self.stop_times[self.stop_times['trip_id'].isin(trips_ids_dans_periode)]
        stop_times_temps_superieur = stop_times_arret_correct.assign(temps_depart = "", stop_id_ville = "")

        stop_ids_depart = self.arrets_depart['stop_id']
        stop_ids_depart.index = self.arrets_depart['trip_id']
        stop_id_depart = stop_ids_depart.loc[stop_times_temps_superieur['trip_id']]
        stop_times_temps_superieur['stop_id_ville'] = stop_id_depart.array

        temps_depart = self.arrets_depart['departure_time'] #StopTime trip
        temps_depart.index = self.arrets_depart['trip_id']
        colonne_temps_depart = temps_depart.loc[stop_times_temps_superieur['trip_id']]
        stop_times_temps_superieur['temps_ville'] = colonne_temps_depart.array

        destinations_doublons_stop_points = stop_times_temps_superieur[stop_times_temps_superieur['departure_time'] > stop_times_temps_superieur['temps_ville']]
        destinations_doublons_stop_points = self.stops[self.stops['stop_id'].isin(destinations_doublons_stop_points['stop_id'])]
        destinations_doublons_stop_area = self.stops[self.stops['stop_id'].isin(destinations_doublons_stop_points['parent_station'])]
        destinations_stop_area = destinations_doublons_stop_area.drop_duplicates(subset='stop_id')
        destinations = destinations_stop_area[~destinations_stop_area['stop_id'].isin(self.stops_proches(lat,lon)['parent_station'])]
        return destinations
    
    def get_trajets(self, lat_arrivee : float, lon_arrivee : float) -> pd.DataFrame:
        stops_depart = self.stops[(self.stops['stop_lat'] > self.lat-SEUIL_DISTANCE) & (self.stops['stop_lat'] < self.lat+SEUIL_DISTANCE) & (self.stops['stop_lon'] > self.lon-SEUIL_DISTANCE) & (self.stops['stop_lon'] < self.lon+SEUIL_DISTANCE) & self.stops['parent_station'].str.contains('StopArea')]
        stops_arrivee = self.stops[(self.stops['stop_lat'] > lat_arrivee-SEUIL_DISTANCE/2) & (self.stops['stop_lat'] < lat_arrivee+SEUIL_DISTANCE/2) & (self.stops['stop_lon'] > lon_arrivee-SEUIL_DISTANCE/2) & (self.stops['stop_lon'] < lon_arrivee+SEUIL_DISTANCE/2) & self.stops['parent_station'].str.contains('StopArea')]
        trajets_avec_stops_depart = self.stop_times[self.stop_times['stop_id'].isin(stops_depart['stop_id'])]
        trajets_avec_stops_arrivee = self.stop_times[self.stop_times['stop_id'].isin(stops_arrivee['stop_id'])]
        trips_avec_depart_arrivee =  pd.merge(trajets_avec_stops_depart,trajets_avec_stops_arrivee, on = 'trip_id')
        trips_heure = trips_avec_depart_arrivee[trips_avec_depart_arrivee['departure_time_x'] < trips_avec_depart_arrivee['departure_time_y']]
        trips = pd.merge(trips_heure, self.trips, on = 'trip_id')
        trips_et_jours = pd.merge(trips, self.calendar_dates, on = 'service_id')
        trajets = trips_et_jours[(trips_et_jours['date'] >= self.date_min) & (trips_et_jours['date'] <= self.date_max)]
        trajets = trajets.assign(horaire_depart = "", horaire_arrivee = "")
        trajets['horaire_depart'] = trajets.apply(lambda x : x['departure_time_x']+x['date'], axis=1)
        trajets['horaire_arrivee'] = trajets.apply(lambda x : x['departure_time_y']+x['date'], axis=1)
        return trajets
    
    @staticmethod
    def list_of_cities(path : str) -> pd.DataFrame:
        stops = pd.read_csv('Data/'+ path +'/stops.txt')[['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'parent_station']]
        return stops[stops['stop_id'].str.contains('StopArea')][['stop_name','stop_lat','stop_lon','stop_id']]