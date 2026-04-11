from datetime import datetime
from requests import request
import os, datetime, requests, csv, io
from bs4 import BeautifulSoup
import pandas as pd
import flet as ft


class DataProvider():
    """
    Clase que se encarga de obtener y proveer los datos de las diferentes fuentes.
    """

    # Constantes
    WORK_DIR = os.path.dirname(__file__)
    HIST_CACHE_DIR = os.path.join(WORK_DIR, "data/hist_cache")
    REAL_TIME_CACHE_DIR = os.path.join(WORK_DIR, "data/real_time_cache")

    CONTAMINACION = "Contaminación"
    PRECIPITACIONES = "Precipitaciones"
    TRAFICO = "Tráfico"

    # Diferentes estados del tráfico (url2):
    ESTADOS_TRAFICO = {
        0: "Fluid / Fluido",
        1: "Dens / Denso",
        2: "Congestionat /Congestionado",
        3: "Tallat / Cortado",
        4: "Sense dades / Sin datos",
        5: "Subterrànies fluid / Subterráneo Fluido",
        6: "Subterrànies dens / Subterráneo Denso",
        7: "Subterrànies congestionat / Subterráneo Congestionado",
        8: "Subterrànies tallat / Subterráneo Cortado",
        9: "Subterrànies sense dades / Subterráneo Sin datos"
    }

    # Crear directorios si no existen
    os.makedirs(HIST_CACHE_DIR, exist_ok=True)
    os.makedirs(REAL_TIME_CACHE_DIR, exist_ok=True)

    os.makedirs(f"{HIST_CACHE_DIR}/contaminacion", exist_ok=True)
    os.makedirs(f"{HIST_CACHE_DIR}/precipitaciones", exist_ok=True)
    os.makedirs(f"{HIST_CACHE_DIR}/trafico", exist_ok=True)

    # RESUMENES DE LOS DATOS
    @staticmethod
    def get_res_contamin(page: ft.Page):
        """
        Obtiene los datos de los contaminantes atmosféricos de la ciudad de Valencia en tiempo real.

        Returns:
            tuple: (media, calidad, actualizado)
                - media: Media de los contaminantes atmosféricos.
                - calidad: Calidad del aire.
                - actualizado: Fecha de actualización.
        """
        try:
            url = "https://geoportal.valencia.es/server/rest/services/OPENDATA/MedioAmbiente/MapServer/156/query?where=1=1&outFields=objectid%2Cnombre%2Cso2%2Cno2%2Co3%2Cco%2Cpm10%2Cpm25%2Ctipoemisio%2Cfecha_carg%2Ccalidad_am&f=json"
            data = requests.get(url).json()

            estaciones = [est["attributes"] for est in data["features"]]
            df = pd.DataFrame(estaciones)

            # Guardar los datos en un archivo parquet
            df.to_parquet(f"{DataProvider.REAL_TIME_CACHE_DIR}/contaminacion.parquet")

        except Exception as e:
            # En caso de no poder obtener los datos, se crea un dataframe con datos nulos
            print(f"ERROR: No se ha podido obtener los datos de contaminación en tiempo real: {e}")
            page.show_dialog(ft.SnackBar(ft.Text("No se ha podido obtener los datos de contaminación en tiempo real. Mostrando datos en caché", color=ft.Colors.ON_ERROR_CONTAINER), bgcolor=ft.Colors.ERROR_CONTAINER))
            
            if os.path.exists(f"{DataProvider.REAL_TIME_CACHE_DIR}/contaminacion.parquet"):
                df = pd.read_parquet(f"{DataProvider.REAL_TIME_CACHE_DIR}/contaminacion.parquet")
            else:
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

        # Convierte la fecha de timestamp a string
        actualizado = datetime.datetime.fromtimestamp(actualizado / 1000).strftime("%d-%m-%Y %H:%M") if actualizado != "NULL" else "-"

        return media, calidad, actualizado

    @staticmethod
    def get_res_precipit(page: ft.Page):
        """
        Obtiene los datos de las precipitaciones de la ciudad de Valencia en tiempo real.

        Returns:
            tuple: (media, actualizado)
                - media: Media de las precipitaciones.
                - actualizado: Fecha de actualización.
        """
        try:
            # Datos de precipitaciones en tiempo real en la ciudad de Valencia de la web de AVAMET
            url = "https://www.avamet.org/mxo-mxo.php?territori=c15"
            html = requests.get(url).text

            # Parsea el HTML
            soup = BeautifulSoup(html, "html.parser")

            # Obtiene todas las tablas
            tablas = soup.find_all("table")

            # Encabezados de las columnas
            encabezados = ["Estación", "Altitud (m)", "Temperatura actual (ºC)", "Temperatura mínima (ºC)", "Temperatura máxima (ºC)", "Punto de rocío (ºC)", "Sensación térmica (ºC)", "Humedad relativa (%)", "Precipitación acumulada día (mm)", "Intensidad de precipitación", "Velocidad del viento (km/h)", "Dirección del viento", "Velocidad máxima del viento (km/h)", "Webcam", "Actualizado"]

            # Columnas numéricas
            numericos = ["Temperatura actual (ºC)", "Temperatura mínima (ºC)", "Temperatura máxima (ºC)", "Punto de rocío (ºC)", "Sensación térmica (ºC)", "Humedad relativa (%)", "Precipitación acumulada día (mm)", "Velocidad del viento (km/h)", "Velocidad máxima del viento (km/h)"]

            filas = []
            # Añade los encabezados a la lista de filas
            filas.append(encabezados)

            # Si no se han encontrado tablas, se imprime un mensaje
            if not tablas:
                print("ERROR: No se han encontrado tablas de precipitaciones")
            else:
                # Obtiene la primera tabla
                tabla = tablas[0]

                for i, tr in enumerate(tabla.find_all("tr")):
                    # Si la fila no es un encabezado
                    if i > 2:
                        tds = tr.find_all("td")
                        # Si la fila tiene al menos 2 celdas
                        if len(tds) >= 2:
                            # Obtiene todas las celdas de la fila menos las dos últimas
                            celdas = [td.get_text(strip=True) for td in tds[:-2]]
                            
                            # Penúltima celda: Webcam (extraemos el href si existe el tag <a>)
                            a_tag = tds[-2].find("a")
                            celdas.append(a_tag.get("href") if a_tag else "")
                            
                            # Última celda: Actualizado (extraemos el atributo title del <td>)
                            celdas.append(tds[-1].get("title", ""))
                            
                            # Añade las celdas a la lista de filas
                            filas.append(celdas)
            
            # Crea un dataframe con los datos
            df = pd.DataFrame(filas[1:], columns=encabezados)

            # Reemplaza las comas por puntos en las columnas numéricas
            df = df.apply(lambda x: x.str.replace(",", ".") if x.name in numericos else x)

            # Parsea las columnas numéricas de string a float
            df = df.apply(lambda x: pd.to_numeric(x, errors="coerce") if x.name in numericos else x)
            
            # Guarda los datos en caché
            df.to_parquet(f"{DataProvider.REAL_TIME_CACHE_DIR}/precipitaciones.parquet")

        except Exception as e:
            # En caso de no poder obtener los datos, intenta usar los datos que hay en caché y si no existe, crea un dataframe con datos nulos
            print(f"ERROR: No se ha podido obtener los datos de las precipitaciones en tiempo real: {e}")
            page.show_dialog(ft.SnackBar(ft.Text("No se ha podido obtener los datos de las precipitaciones en tiempo real. Mostrando datos en caché", color=ft.Colors.ON_ERROR_CONTAINER), bgcolor=ft.Colors.ERROR_CONTAINER))
            
            if os.path.exists(f"{DataProvider.REAL_TIME_CACHE_DIR}/precipitaciones.parquet"):
                df = pd.read_parquet(f"{DataProvider.REAL_TIME_CACHE_DIR}/precipitaciones.parquet")
            else:
                df = pd.DataFrame([{
                    "Estación": "NULL", 
                    "Altitud (m)": "NULL", 
                    "Temperatura actual (ºC)": 0.0, 
                    "Temperatura mínima (ºC)": 0.0, 
                    "Temperatura máxima (ºC)": 0.0, 
                    "Punto de rocío (ºC)": 0.0, 
                    "Sensación térmica (ºC)": 0.0, 
                    "Humedad relativa (%)": 0.0, 
                    "Precipitación acumulada día (mm)": 0.0, 
                    "Intensidad de precipitación": 0.0, 
                    "Velocidad del viento (km/h)": 0.0, 
                    "Dirección del viento": "NULL", 
                    "Velocidad máxima del viento (km/h)": 0.0, 
                    "Webcam": "NULL", 
                    "Actualizado": "-"
                }])

        # Media de las precipitaciones
        media = df[["Precipitación acumulada día (mm)", "Velocidad del viento (km/h)"]].mean()

        # Moda de la intensidad de precipitación
        intensidad = df["Intensidad de precipitación"].mode()[0]

        # Dirección del viento
        dir_viento = df["Dirección del viento"].mode()[0]

        # Fecha de actualización (la que más se repite)
        actualizado = df["Actualizado"].mode()[0]

        return media, intensidad, dir_viento, actualizado

    @staticmethod
    def get_res_trafico(page: ft.Page = None):
        """
        Obtiene los datos históricos de la contaminación atmosférica de la ciudad de Valencia en un año concreto y lo guarda en un .parquet para mejorar el rendimiento.

        Returns:
            tuple: (media, estado, tramo, actualizado)
            - media: Media general de vehículos.
            - estado: Estado general del tráfico.
            - tramo: Tramo con más vehículos.
            - actualizado: Fecha de actualización.
        """

        def get_datos_trafico(url: str):
            # Actualizado
            actualizado = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")

            # Obtener los datos en json de la url
            datos = requests.get(url).json()

            # Parsear los datos de json a dataframe
            tramos = [tram["attributes"] for tram in datos["features"]]
            df = pd.DataFrame(tramos)

            # Añadir columna "Actualizado"
            df["Actualizado"] = actualizado

            return df

        try:
            # Datos de la intensidad del tráfico en tiempo real
            url_int = "https://geoportal.valencia.es/server/rest/services/OPENDATA/Trafico/MapServer/188/query?where=1=1&outFields=*&f=json"
            df_int = get_datos_trafico(url_int)

            # Seleccionar solo las columnas necesarias y renombrar la columna "estado"
            df_int = df_int[["des_tramo", "imv", "estado", "fiwareid"]]
            df_int = df_int.rename(columns={"estado": "estado_int"})

            # Quedarse solo con la parte numérica de "fiwareid"
            df_int["fiwareid"] = df_int["fiwareid"].str.split("_", expand=True)[1].str.strip("A").str.strip("B")

            # Convertir la columna "imv" a float para poder hacer la media
            df_int = df_int.apply(lambda x: pd.to_numeric(x, errors="coerce") if x.name == "imv" else x)


            # Datos del estado del tráfico en tiempo real
            url_est = "https://geoportal.valencia.es/server/rest/services/OPENDATA/Trafico/MapServer/192/query?where=1=1&outFields=*&f=json"
            df_est = get_datos_trafico(url_est)

            # Seleccionar solo las columnas necesarias y renombrar la columna "estado"
            df_est = df_est[["denominacion", "estado", "fiwareid", "Actualizado"]]
            df_est = df_est.rename(columns={"estado": "estado_est"})

            # Quedarse solo con la parte numérica de "fiwareid"
            df_est["fiwareid"] = df_est["fiwareid"].str.split("_", expand=True)[1]


            # Unir los dos dataframes
            df = pd.merge(df_int, df_est, on="fiwareid", how="inner")

            # Guardar los datos en un archivo parquet
            df.to_parquet(f"{DataProvider.REAL_TIME_CACHE_DIR}/trafico.parquet")

        except Exception as e:
            print(f"ERROR: No se ha podido obtener los datos del tráfico en tiempo real: {e}")
            page.show_dialog(ft.SnackBar(ft.Text("No se ha podido obtener los datos del tráfico en tiempo real. Mostrando datos en caché", color=ft.Colors.ON_ERROR_CONTAINER), bgcolor=ft.Colors.ERROR_CONTAINER))

            ruta_df = f"{DataProvider.REAL_TIME_CACHE_DIR}/trafico.parquet"
            if os.path.exists(ruta_df):
                df = pd.read_parquet(ruta_df)
            else:
                df = pd.DataFrame([{
                    "des_tramo": "NULL",
                    "imv": 0.0,
                    "estado_int": "NULL",
                    "fiwareid": "NULL",
                    "denominacion": "NULL",
                    "estado_est": 0.0,
                    "Actualizado": "-"
                }])

        # Media de la intensidad de tráfico
        media = df["imv"].mean()

        # Estado del tráfico
        estado = DataProvider.ESTADOS_TRAFICO[df["estado_est"].mode()[0]]

        # Tramo con más vehículos
        df_ordenado = df.sort_values(by="imv", ascending=False)
        tramo = df_ordenado.iloc[0]["des_tramo"]

        # Fecha de actualización (la que más se repite)
        actualizado = df["Actualizado"].mode()[0]

        return media, estado, tramo, actualizado
            

    # HISTORICOS
    @staticmethod
    def get_hist_contaminacion(fecha):
        """
        Obtiene los datos históricos de la contaminación atmosférica de la ciudad de Valencia en un día concreto.

        Args:
            fecha (str): Fecha del cual se quieren obtener los datos.
        
        Returns:
            pd.DataFrame: Dataframe con los datos históricos.
        """
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
            parquet_path = f"{DataProvider.HIST_CACHE_DIR}/contaminacion/{anio}.parquet"
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


        # Obtiene el año
        anio = datetime.datetime.strptime(fecha, "%Y-%m-%d").year

        # Ruta del .parquet
        parquet_path = f"{DataProvider.HIST_CACHE_DIR}/contaminacion/{anio}.parquet"

        # Si no existe el .parquet, se crea
        if not os.path.exists(parquet_path):
            get_anio_contaminacion(anio)

        # Cargar el .parquet
        df = pd.read_parquet(parquet_path)

        # Filtrar por fecha
        df = df.loc[df["FECHA"] == fecha]
        
        # Quedarse solo con las columnas necesarias
        df = df[["COD_ESTACION", "FECHA", "NOM_ESTACION", "SO2", "NO2", "O3", "CO", "PM10", "PM2.5"]]

        return df


    @staticmethod
    def get_hist_precipiaciones(fecha: str):
        """
        Obtiene los datos históricos de las precipitaciones de la ciudad de Valencia en un día concreto.

        Args:
            fecha (str): Fecha del cual se quieren obtener los datos.
        
        Returns:
            pd.DataFrame: Dataframe con los datos históricos.
        """
        filas = []

        parquet_path = f"{DataProvider.HIST_CACHE_DIR}/precipitaciones/{fecha}.parquet"

        # Si no existe el parquet, se obtiene de internet
        if not os.path.exists(parquet_path):
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

            # Guardar en .parquet
            pd.DataFrame(filas[1:], columns=filas[0]).to_parquet(parquet_path)

        # Cargar el .parquet
        df = pd.read_parquet(parquet_path)

        return df

    @staticmethod
    def get_hist_trafico(fecha):
        """
        Obtiene los datos históricos del tráfico de la ciudad de Valencia.

        Args:
            fecha (str): Fecha en formato "dd-mm-yyyy"
        
        Returns:
            pd.DataFrame: Dataframe con los datos históricos.
        """
        def get_url_descarga(anio):
            """
            Obtiene la url de descarga del archivo .ods.

            Args:
                anio (int): Año del cual se quiere obtener la url de descarga.
            
            Returns:
                str: Url de descarga del archivo .ods.
            """
            # Texto a buscar como contenido de etiqueta <a>
            text = f"Imds vehículos motorizados año {anio} (formato: ods)"

            # Obtiene el HTML de la página
            html = requests.get("https://www.valencia.es/cas/movilidad/otras-descargas").text

            # Parsea el HTML
            soup = BeautifulSoup(html, "html.parser")

            # Obtiene todas las etiquetas <a>
            a_tags = soup.find_all("a")

            # Obtiene la url de la etiqueta <a> que contenga el texto buscado
            url = [a["href"] for a in a_tags if a.get_text(strip=True) == text][0]

            return url

        # Obtener el año
        anio = datetime.datetime.strptime(fecha, "%Y-%m-%d").year
        anio_actual = datetime.date.today().year

        if not os.path.exists(f"{DataProvider.HIST_CACHE_DIR}/trafico/{anio}.parquet") or anio == anio_actual:
            # Datos de IMD por año desde 2016 hasta la actualidad en la ciudad de Valencia
            url = get_url_descarga(anio)

            # Descargar el archivo .ods
            r = requests.get(url)
            ods = pd.read_excel(io.BytesIO(r.content), engine="odf", sheet_name=None)

            dfs = []

            if 2016 <= anio <= 2018:
                sheet_name = list(ods.keys())[0]
                df = ods[sheet_name].copy()
                df.rename(columns={'ATA': 'Id Tramo', 'DESCRIPCION': 'Tramo'}, inplace=True)

                # Encontrar columnas IMD
                imd_cols = [c for c in df.columns if 'IMD' in c and c not in ['Id Tramo', 'Tramo']]

                # Melt dataframe para tener columnas 'Mes' y 'IMD'
                df = df.melt(id_vars=['Id Tramo', 'Tramo'], value_vars=imd_cols, var_name='Mes_raw', value_name='IMD')

                # Extraer el número del mes de 'tramos_imd 2016-01.IMD'
                df['Mes'] = df['Mes_raw'].str.extract(r'-(\d\d)').astype(int)
                df['Sentido'] = pd.NA
                df = df[['Id Tramo', 'Tramo', 'Sentido', 'Mes', 'IMD']]
                dfs.append(df)

            else:
                mes_idx = 1
                for sname in ods:
                    df = ods[sname].copy()

                    # Saltar filas de resumen o descripción
                    if 'resumen' in sname.lower() or 'descripc' in sname.lower() or 'informe' in sname.lower():
                        continue
                    
                    # Limpiar filas y columnas vacías
                    df = df.dropna(axis=1, how='all')
                    df = df.dropna(how='all').reset_index(drop=True)

                    if len(df.columns) < 2:
                        continue
                    
                    # Si los encabezados están en la primera fila en lugar de columnas reales (problemas de 2022)
                    if 'unnamed' in str(df.columns[0]).lower():
                        df.columns = df.iloc[0]
                        df = df[1:].reset_index(drop=True)

                    # Estandarizar cadenas de columnas
                    df.columns = [str(c).strip().lower() for c in df.columns]

                    # Mapear dinámicamente las columnas a las estándar
                    col_map = {}
                    for c in df.columns:
                        if 'ata' in c or 'nombre' == c:
                            col_map[c] = 'Id Tramo'
                        elif 'descripc' in c:
                            col_map[c] = 'Tramo'
                        elif 'sentido' == c:
                            col_map[c] = 'Sentido'
                        elif 'imd' in c or 'lab.' in c or 'laborables' in c or 'laborales' in c:
                            col_map[c] = 'IMD'

                    df = df.rename(columns=col_map)

                    # A veces un año no tiene 'Sentido'
                    if 'Sentido' not in df.columns:
                        df['Sentido'] = pd.NA

                    if 'Tramo' not in df.columns:
                        df['Tramo'] = pd.NA

                    if 'IMD' not in df.columns:
                        # Try fallback
                        if len(df.columns) >= 4:
                            df = df.rename(columns={df.columns[3]: 'IMD'})
                        else:
                            continue

                    if 'Id Tramo' not in df.columns:
                        if len(df.columns) >= 1:
                            df = df.rename(columns={df.columns[0]: 'Id Tramo'})

                    # Keep strictly needed columns and add 'Mes'
                    df = df[['Id Tramo', 'Tramo', 'Sentido', 'IMD']].copy()
                    df['Mes'] = mes_idx
                    dfs.append(df)
                    mes_idx += 1

            # Concat all sheets (or months)
            df = pd.concat(dfs, ignore_index=True)

            # Asegurar que IMD es float
            df['IMD'] = pd.to_numeric(df['IMD'], errors='coerce')

            # Guardar en parquet
            df.to_parquet(f"{DataProvider.HIST_CACHE_DIR}/trafico/{anio}.parquet")
        
        # Cargar el parquet
        df = pd.read_parquet(f"{DataProvider.HIST_CACHE_DIR}/trafico/{anio}.parquet")
        
        # Filtrar por fecha
        df = df.loc[df["Mes"] == datetime.datetime.strptime(fecha, "%Y-%m-%d").month]

        # Convertir mes de número a nombre
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        df['Mes'] = df['Mes'].apply(lambda x: meses[x-1])
        
        return df


    @staticmethod
    def get_real_time_data(categoria: str):
        """
        Obtiene los datos de tiempo real de la categoría seleccionada desde la caché.

        Args:
            categoria (str): Categoría de los datos.

        Returns:
            pd.DataFrame: Dataframe con los datos de tiempo real.
        """
        if categoria == DataProvider.CONTAMINACION:
            path = f"{DataProvider.REAL_TIME_CACHE_DIR}/contaminacion.parquet"
        elif categoria == DataProvider.PRECIPITACIONES:
            path = f"{DataProvider.REAL_TIME_CACHE_DIR}/precipitaciones.parquet"
        elif categoria == DataProvider.TRAFICO:
            path = f"{DataProvider.REAL_TIME_CACHE_DIR}/trafico1.parquet"
        else:
            return pd.DataFrame()

        if os.path.exists(path):
            return pd.read_parquet(path)
        else:
            return pd.DataFrame()

if __name__ == "__main__":
    
    DataProvider.get_hist_trafico("2016-01-01")
