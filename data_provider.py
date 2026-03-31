import os, datetime, requests, csv, io
from bs4 import BeautifulSoup
import pandas as pd


class DataProvider():
    """
    Clase que se encarga de obtener y proveer los datos de las diferentes fuentes.
    """

    # Constantes
    WORK_DIR = os.path.dirname(__file__)
    CACHE_DIR = os.path.join(WORK_DIR, "hist_cache")

    CONTAMINACION = "Contaminación"
    PRECIPITACIONES = "Precipitaciones"
    TRAFICO = "Tráfico"

    # FIXME: La API ya no existe, hay que buscar una nueva
    # RESUMENES DE LOS DATOS
    @staticmethod
    def get_res_contamin():
        """
        Obtiene los datos de los contaminantes atmosféricos de la ciudad de Valencia en tiempo real.

        Returns:
            tuple: (media, calidad, actualizado)
                - media: Media de los contaminantes atmosféricos.
                - calidad: Calidad del aire.
                - actualizado: Fecha de actualización.
        """
        try:
            url = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estacions-contaminacio-atmosferiques-estaciones-contaminacion-atmosfericas/records?select=objectid%2Cnombre%2Cso2%2Cno2%2Co3%2Cco%2Cpm10%2Cpm25%2Ctipoemisio%2Cfecha_carg%2Ccalidad_am&limit=20"
            data = pd.read_json(url, encoding="utf-8")

            estaciones = [estacion for estacion in data["results"]]
            df = pd.DataFrame(estaciones)

        except Exception as e:
            # En caso de no poder obtener los datos, se crea un dataframe con datos nulos
            print(f"No se ha podido obtener los datos de contaminación en tiempo real: {e}")
            df = pd.DataFrame([{
                "objectid": 0,
                "nombre": "NULL",
                "so2": 0.0,
                "no2": 0.0,
                "o3": 0.0,
                "co": 0.0,
                "pm10": 0.0,
                "pm25": 0.0,
                "tipoemisio": "NULL",
                "fecha_carg": "NULL",
                "calidad_am": "NULL"
            }])

        media = df[["so2", "no2", "o3", "co", "pm10", "pm25"]].mean() # Media de los contaminantes

        calidad = df["calidad_am"].mode()[0] # Calidad del aire (la que más se repite)

        actualizado = df["fecha_carg"].mode()[0] # Fecha de actualización (la que más se repite)

        return media, calidad, actualizado

    @staticmethod
    def get_res_precipit():
        """
        Obtiene los datos de las precipitaciones de la ciudad de Valencia en tiempo real.

        Returns:
            tuple: (media, actualizado)
                - media: Media de las precipitaciones.
                - actualizado: Fecha de actualización.
        """
        try:
            url = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estacions-atmosferiques-estaciones-atmosfericas/records?select=objectid%2Cnombre%2Cfecha_carg%2Cviento_dir%2Cviento_vel%2Ctemperatur%2Chumedad_re%2Cpresion_ba%2Cprecipitac&limit=20"
            data = pd.read_json(url, encoding="utf-8")

            estaciones = [estacion for estacion in data["results"]]
            df = pd.DataFrame(estaciones)

        except Exception as e:
            # En caso de no poder obtener los datos, se crea un dataframe con datos nulos
            print(f"No se ha podido obtener los datos de las precipitaciones en tiempo real: {e}")
            df = pd.DataFrame([{
                "objectid": 0,
                "nombre": "NULL",
                "fecha_carg": "NULL",
                "viento_dir": 0.0,
                "viento_vel": 0.0,
                "temperatur": 0.0,
                "humedad_re": 0.0,
                "presion_ba": 0.0,
                "precipitac": 0.0
            }])

        media = df[["viento_dir", "viento_vel", "temperatur", "humedad_re", "presion_ba", "precipitac"]].mean() # Media de las precipitaciones

        actualizado = df["fecha_carg"].mode()[0] # Fecha de actualización (la que más se repite)

        return media, actualizado

    # TODO: Lo mismo para tráfico
    @staticmethod
    def get_res_trafico():
        pass

    # HISTORICOS
    @staticmethod
    def get_anio_contaminacion(anio: int):
        """
        Obtiene los datos históricos de la contaminación atmosférica de la ciudad de Valencia en un año concreto y lo guarda en un .parquet para mejorar el rendimiento.

        Args:
            anio (int): Año del cual se quieren obtener los datos.
        """
        # Datos historicos diarios en la Comunidad Valenciana desde 1994 hasta la actualidad
        url = f"https://dadesobertes.gva.es/va/dataset/med-cont-atmos-md-{anio}"
        
        # Obtiene el HTML de la página
        html = requests.get(url).text

        # Parsea el HTML
        soup = BeautifulSoup(html, "html.parser")

        # Obtiene todas las urls de los archivos CSV
        urls = [a["href"] for a in soup.find_all("a", class_="resource-url-analytics")]

        # Crear un .parquet para el año con los datos de los csv sin necesidad de descargarlos
        parquet_path = f"{DataProvider.CACHE_DIR}/contaminacion/{anio}.parquet"
        parquet_df = pd.DataFrame()
        for url in urls:
            r = requests.get(url)
            # El sep=";" es porque los CSV de la GVA vienen separados por punto y coma
            df = pd.read_csv(io.StringIO(r.text), sep=";")
            
            # Filtrar a las estaciones de la ciudad de Valencia (estaciones cuyo código "COD_ESTACION" empieza en "46250")
            df = df[df["COD_ESTACION"].astype(str).str.startswith("46250")]

            # Añadir el dataframe al dataframe principal
            parquet_df = pd.concat([parquet_df, df])

        # Guardar en parquet
        parquet_df.to_parquet(parquet_path)

    @staticmethod
    def get_hist_contaminacion(fecha):
        """
        Obtiene los datos históricos de la contaminación atmosférica de la ciudad de Valencia en un día concreto.

        Args:
            fecha (str): Fecha del cual se quieren obtener los datos.
        
        Returns:
            list[list[str]]: Lista de filas con los datos históricos.
        """
        # Obtiene los datos de un día concreto
        fecha = datetime.datetime.strptime(fecha, "%Y-%m-%d")
        anio = fecha.year

        # Si no existe el .parquet, se crea
        if not os.path.exists(f"{DataProvider.CACHE_DIR}/contaminacion/{anio}.parquet"):
            DataProvider.get_anio_contaminacion(anio)

        df = pd.read_parquet(f"{DataProvider.CACHE_DIR}/contaminacion/{anio}.parquet")

        # Filtrar por fecha
        df = df.loc[df["FECHA"] == fecha.strftime("%Y-%m-%d")]
        
        # Quedarse solo con las columnas necesarias
        df = df[["COD_ESTACION", "FECHA", "NOM_ESTACION", "SO2", "NO2", "O3", "CO", "PM10", "PM2.5"]]

        # Convertir a lista de listas
        filas = [df.columns.tolist()] + df.values.tolist()

        return filas


    @staticmethod
    def get_hist_precipiaciones(fecha: str):
        """
        Obtiene los datos históricos de las precipitaciones de la ciudad de Valencia en un día concreto.

        Args:
            fecha (str): Fecha del cual se quieren obtener los datos.
        
        Returns:
            list[list[str]]: Lista de filas con los datos históricos.
        """
        filas = []

        csv_path = f"{DataProvider.CACHE_DIR}/precipitaciones/{fecha}.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True) # Si no existe la carpeta, se crea

        # Si no existe el csv, se obtiene de internet
        if not os.path.exists(csv_path):
            # Datos de precipitaciones de un día concreto en la ciudad de Valencia
            url = f"https://www.avamet.org/mx-meteoxarxa.php?data={fecha}&territori=c15"
            html = requests.get(url).text

            # Parsea el HTML
            soup = BeautifulSoup(html, "html.parser")

            # Obtiene todas las tablas
            tablas = soup.find_all("table")

            # Encabezados de la tabla limpios
            encabezados = ["Estación", "Temperatura mínima (°C)", "Temperatura media (°C)", "Temperatura màxima (°C)", "Humedad relativa media (%)",
                           "Precipitación media (mm)", "Viento medio (km/h)", "Viento dirección", "Viento màximo (km/h)"]

            # Añadir los encabezados a la lista de filas
            filas.append(encabezados)

            # Si no se encontraron tablas, se imprime un mensaje
            if not tablas:
                print("No se encontraron tablas")
            else:
                # Obtiene la tabla correcta
                tabla = tablas[0]

                for i, tr in enumerate(tabla.find_all("tr")):
                    # Saltar los primeros 4 filas que no contienen datos
                    if i > 3:
                        celdas = [td.get_text(strip=True) for td in tr.find_all("td")]

                        filas.append(celdas)

            # Guardar en csv
            with open(csv_path, "w", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(filas)

        else:
            # Leer del csv
            with open(csv_path, "r", encoding="utf-8") as file:
                filas = list(csv.reader(file))

        return filas
