import pandas as pd
from datetime import datetime
import os
import requests
import zipfile


PERCENTAGE_NON_VALID_DATAS = 0.2


class DataUpdater:
    dict_update_url: dict[str, str] = {
        "TER": "https://eu.ftp.opendatasoft.com/sncf/gtfs/export-ter-gtfs-last.zip",
        "TGV": "https://eu.ftp.opendatasoft.com/sncf/gtfs/export_gtfs_voyages.zip",
        "INTERCITE": "https://eu.ftp.opendatasoft.com/sncf/gtfs/export-intercites-gtfs-last.zip",
        "FLIXBUS": "https://transport.data.gouv.fr/resources/11681/download",
    }

    def __init__(self, updatable_data: list[str] = ["FLIXBUS", "TER", "TGV", "INTERCITE"]):
        self.updatable_data = updatable_data

    def is_updatable_data(self, transport: str) -> bool:
        check_file = os.path.isfile(os.path.join("Data", transport, "calendar.txt"))
        dates: pd.DataFrame = pd.DataFrame()
        if check_file:
            dates = pd.read_csv(os.path.join("Data", transport, "calendar.txt"))["end_date"]
        else:
            dates = pd.read_csv(os.path.join("Data", transport, "calendar_dates.txt"))["date"]
        valid_datas = dates[dates > int(datetime.now().strftime("%Y%m%d"))].count()
        percentage_valid_datas = (valid_datas / len(dates))
        return percentage_valid_datas < 1 - PERCENTAGE_NON_VALID_DATAS

    def update_data(self):
        for transport in self.updatable_data:
            if not self.is_updatable_data(transport): continue 
            # Étape 1: Télécharger le fichier ZIP
            url = self.dict_update_url[transport]  # Remplacez par l'URL réelle
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Erreur lors du téléchargement du fichier ZIP pour {transport}")
                return None

            # Utiliser le répertoire courant (là où le script est exécuté)
            script_dir = os.getcwd()

            # Créer un sous-répertoire 'temp' pour stocker le fichier ZIP temporairement
            temp_dir = os.path.join(script_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)

            # Chemin pour enregistrer le fichier ZIP temporairement
            zip_temp_path = os.path.join(temp_dir, "temp_file.zip")

            # Étape 2: Enregistrer le fichier ZIP dans le dossier temp
            with open(zip_temp_path, "wb") as temp_zip_file:
                temp_zip_file.write(response.content)

            # Étape 3: Décompression du fichier ZIP dans le dossier test_data
            destination_directory = os.path.join(script_dir, "Data", transport)

            # Créer le répertoire test_data s'il n'existe pas
            os.makedirs(destination_directory, exist_ok=True)

            # Ouvrir et extraire le contenu du ZIP, en écrasant les fichiers existants
            with zipfile.ZipFile(zip_temp_path, "r") as zip_ref:
                zip_ref.extractall(destination_directory)

            # Suppression du fichier ZIP temporaire et du répertoire temp
            os.remove(zip_temp_path)
            os.rmdir(temp_dir)
