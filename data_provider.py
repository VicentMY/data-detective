import os, datetime, requests, csv
from bs4 import BeautifulSoup
import pandas as pd

class DataProvider():

    WORK_DIR = os.path.dirname(__file__)
    CACHE_DIR = os.path.join(WORK_DIR, "hist_cache")

    CONTAMINACION = "Contaminación"
    PRECIPITACIONES = "Precipitaciones"
    TRAFICO = "Tráfico"

    # RESUMENES DE LOS DATOS
    @staticmethod
    def get_res_contamin():
        url = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estacions-contaminacio-atmosferiques-estaciones-contaminacion-atmosfericas/records?select=objectid%2Cnombre%2Cso2%2Cno2%2Co3%2Cco%2Cpm10%2Cpm25%2Ctipoemisio%2Cfecha_carg%2Ccalidad_am&limit=20"
        data = pd.read_json(url, encoding="utf-8")

        estaciones = [estacion for estacion in data["results"]]
        df = pd.DataFrame(estaciones)
        
        media = df[["so2", "no2", "o3", "co", "pm10", "pm25"]].mean()
        
        calidad = df["calidad_am"].mode()[0]
        
        actualizado = df["fecha_carg"].mode()[0]
        
        return media, calidad, actualizado
    
    @staticmethod
    def get_res_precipit():
        url = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estacions-atmosferiques-estaciones-atmosfericas/records?select=objectid%2Cnombre%2Cfecha_carg%2Cviento_dir%2Cviento_vel%2Ctemperatur%2Chumedad_re%2Cpresion_ba%2Cprecipitac&limit=20"
        data = pd.read_json(url, encoding="utf-8")

        estaciones = [estacion for estacion in data["results"]]
        df = pd.DataFrame(estaciones)

        media = df[["viento_dir", "viento_vel", "temperatur", "humedad_re", "presion_ba", "precipitac"]].mean()

        actualizado = df["fecha_carg"].mode()[0]

        return media, actualizado

    # TODO: Lo mismo para tráfico
    @staticmethod
    def get_res_trafico():
        pass

    # HISTORICOS
    @staticmethod
    def get_hist_contaminacion():

        # TODO: Cambiar fuente de datos a https://dadesobertes.gva.es/va/dataset?q=Mesuraments+diaris+de+contaminants+atmosf%C3%A8rics+i+oz%C3%B3+de+la+Comunitat+Valenciana&frequency=Datos+hist%C3%B3ricos&groups=medio-ambiente&tags=Contaminaci%C3%B3n&sort=title_string+asc&page=1

        dfs = []
        csv_folder = f"{DataProvider.CACHE_DIR}/contaminacion"

        if not os.path.exists(csv_folder):
            os.makedirs(csv_folder, exist_ok=True)

            r = requests.get("https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estacions-contaminacio-atmosferiques-estaciones-contaminacion-atmosfericas/records?select=mediciones")
            data = r.json()

            for estacion in data["results"]:
                csv_url = estacion["mediciones"]

                if csv_url != None:
                    csv_file = csv_url.split("/")[-1:][0]
                    csv_text = requests.get(csv_url).text

                    csv.DictWriter(csv_text, delimiter=";")

                    with open(os.path.join(csv_folder, csv_file), "w", encoding="utf-8") as f:
                        f.write()

        return dfs
    
    @staticmethod
    def get_hist_precipiaciones(fecha: str):
        filas = []

        csv_path = f"{DataProvider.CACHE_DIR}/precipitaciones/{fecha}.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        if not os.path.exists(csv_path):

            url = f"https://www.avamet.org/mx-meteoxarxa.php?data={fecha}&territori=c15"
            html = requests.get(url).text

            soup = BeautifulSoup(html, "html.parser")
            tablas = soup.find_all("table")

            encabezados = ["Estación", "Temperatura mínima (°C)", "Temperatura media (°C)", "Temperatura màxima (°C)", "Humedad relativa media (%)", "Precipitación media (mm)", "Viento medio (km/h)", "Viento dirección", "Viento màximo (km/h)"]

            filas.append(encabezados)

            if not tablas:
                print("No se encontraron tablas")
            else:
                tabla = tablas[0]

                i = 0
                for tr in tabla.find_all("tr"):
                    if i > 3:
                        celdas = []
                        for td in tr.find_all("td"):
                            celdas.append(td.get_text(strip=True))

                        filas.append(celdas)

                    i += 1

            with open(csv_path, "w", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(filas)

            print("DESCARGADO")

        else:
            with open(csv_path, "r", encoding="utf-8") as file:
                filas = list(csv.reader(file))

            print("LEÍDO")

        return filas
