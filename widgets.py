import os, datetime, requests, csv
import pandas as pd
import flet as ft
import flet_map as ftm
import flet_datatable2 as ft2
from bs4 import BeautifulSoup

from data_provider import DataProvider

class MyCard(ft.Card):
    def __init__(self, titulo: str, valor: str, unidad: str):
        super().__init__()

        self.shadow_color = ft.Colors.ON_SURFACE_VARIANT
        self.content = ft.Container(
            padding=10,
            content=ft.Column(
                controls=[
                    ft.Text(titulo, size=14, weight=ft.FontWeight.W_600),
                    ft.Row(
                        controls=[
                            ft.Text(valor, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                            ft.Text(unidad),
                        ]
                    )
                ]
            )
        )


class MyColumn(ft.Column):
    def __init__(self, titulo: str, icono: ft.IconData, widgets: list[ft.Control]):
        super().__init__()

        self.expand = 1
        self.controls = [
            ft.Row(
                controls=[
                    ft.Icon(icono, color=ft.Colors.PRIMARY),
                    ft.Text(titulo, weight=ft.FontWeight.BOLD),
                ]
            ),
            ft.Divider(color=ft.Colors.PRIMARY, radius=50),
            widgets[0],
            widgets[1],
            widgets[2],
        ]


class MyMap(ftm.Map):
    def __init__(self):
        super().__init__(layers=[], expand=True)

        self.expand = 1
        self.initial_center = ftm.MapLatitudeLongitude(39.47, -0.37)
        self.max_zoom = 18
        self.initial_zoom = 13
        self.min_zoom = 12

        self.layers = [
            ftm.TileLayer(
                url_template="http://localhost:5000/tiles/{z}/{x}/{y}.png",
                user_agent_package_name="valencia.dashboard.local",
                on_image_error=lambda e: print("TileLayer Error"),
                max_zoom=18,
                min_zoom=12,
            ),
            ftm.RichAttribution(
                attributions=[
                    ftm.TextSourceAttribution(
                        text="OpenStreetMap Contributors",
                        on_click=lambda e: e.page.launch_url(
                            "https://www.openstreetmap.org/copyright"
                        ),
                    ),
                    ftm.TextSourceAttribution(
                        text="Flet",
                        on_click=lambda e: e.page.launch_url(
                            "https://flet.dev"),
                    ),
                ]
            ),
            ftm.SimpleAttribution(
                text="Flet",
                alignment=ft.Alignment.TOP_RIGHT,
                on_click=lambda e: print("Clicked SimpleAttribution"),
            ),
            ftm.MarkerLayer(
                markers=MyMap.get_marcadores()
            )
        ]
    
    @staticmethod
    def get_marcadores():
               
        # CONTAMINACIÓN
        url = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estacions-contaminacio-atmosferiques-estaciones-contaminacion-atmosfericas/records?select=objectid%2Cnombre%2Cdireccion%2Ctipozona%2Cso2%2Cno2%2Co3%2Cco%2Cpm10%2Cpm25%2Ctipoemisio%2Cfecha_carg%2Ccalidad_am%2Cgeo_point_2d&limit=20"
        data = pd.read_json(url, encoding="utf-8")

        estaciones = [e for e in data["results"]]
        df = pd.DataFrame(estaciones)

        # Extraer latitud y longitud de geo_point_2d
        df["lon"] = df["geo_point_2d"].apply(lambda x: x["lon"] if isinstance(x, dict) and "lon" in x else None)
        df["lat"] = df["geo_point_2d"].apply(lambda x: x["lat"] if isinstance(x, dict) and "lat" in x else None)

        # Eliminar la columna geo_point_2d para evitar confusiones
        df = df.drop(columns="geo_point_2d")
        
        # TODO: Hacer marcadores interactivos con el nombre de la estación y su calidad del aire
        marcadores = [
            ftm.Marker(
                content=ft.Icon(ft.Icons.AIR, color=ft.Colors.RED),
                coordinates=ftm.MapLatitudeLongitude(lat, lon),
            ) for nombre, calidad, lat, lon in zip(df["nombre"], df["calidad_am"], df["lat"], df["lon"])
        ]

        return marcadores


class MyDropdown(ft.DropdownM2):
    def __init__(self):
        super().__init__()

        self.width = 200
        self.value = DataProvider.CONTAMINACION
        self.options = [
            ft.dropdownm2.Option(DataProvider.CONTAMINACION),
            ft.dropdownm2.Option(DataProvider.PRECIPITACIONES),
            ft.dropdownm2.Option(DataProvider.TRAFICO)
        ]

class MyTable(ft2.DataTable2):
    def __init__(self):
        super().__init__(columns=[])

        self.crear = True

        self.heading_row_color = ft.Colors.SECONDARY_CONTAINER
        self.sort_ascending = True
        self.expand = True
        self.heading_row_height = 50
        self.data_row_height = 50
        self.column_spacing = 12
        self.horizontal_margin = 12

        self.actualizar()

    def actualizar(self, categoria: str = DataProvider.PRECIPITACIONES, fecha: str = ""):

        datos = self.obtener_datos(categoria, fecha)

        encabezados = datos[0]
        filas = datos[1:]

        self.columns = [
            ft2.DataColumn2(
                label=ft.Text(enc, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                size=ft2.DataColumnSize.M,
            ) for enc in encabezados
        ]

        self.rows = [
            ft2.DataRow2(
                expand=True,
                cells=[
                    ft.DataCell(ft.Text(celda, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)) for celda in fila
                ]
            ) for fila in filas
        ]

        if self.crear:
            self.crear = False
        else:
            self.update()

    def obtener_datos(self, categoria: str, fecha: str):
        if fecha == "":
            hoy = datetime.datetime.now()
            fecha = (hoy - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
       
        if categoria == DataProvider.CONTAMINACION:
            return DataProvider.get_hist_contaminacion()
        elif categoria == DataProvider.PRECIPITACIONES:
            return DataProvider.get_hist_precipiaciones(fecha)
        else:
            pass


class MyDatepicker(ft.DatePicker):
    def __init__(self, tabla: MyTable):
        super().__init__()

        hoy = datetime.datetime.now()
        
        self.last_date = hoy - datetime.timedelta(days=1)
        self.on_change = lambda e: self.on_fecha_seleccionada(e, tabla)
        self.on_dismiss = lambda: print("Dissmissed")

    def on_fecha_seleccionada(self, e: ft.Event[ft.DatePicker], tabla: MyTable):
        fecha = (e.control.value + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        tabla.actualizar(fecha=fecha)
