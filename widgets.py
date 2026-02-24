import os, datetime, requests, csv
import flet as ft
import flet_map as ftm
import flet_datatable2 as ft2
from bs4 import BeautifulSoup

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
    def __init__(self, markers: list[ftm.Marker]):
        super().__init__(layers=[], expand=True)

        self.expand = 1
        self.initial_center = ftm.MapLatitudeLongitude(39.47, -0.37)
        self.max_zoom = 18
        self.initial_zoom = 13
        self.min_zoom = 12

        self.layers = [
            ftm.TileLayer(
                url_template="http://localhost:5000/tiles/{z}/{x}/{y}.png",
                user_agent_package_name="valencia.dashboard.local",  # TODO: Cambiar al personal
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
            # ftm.MarkerLayer(

            # )
        ]


class MyTable(ft2.DataTable2):
    def __init__(self):
        super().__init__(columns=[])

        self.WORK_DIR = os.path.dirname(__file__)
        self.CACHE_DIR = os.path.join(self.WORK_DIR, "hist_cache")

        self.crear = True

        self.disabled = True

        self.heading_row_color = ft.Colors.SECONDARY_CONTAINER
        self.sort_ascending = True
        self.expand = True
        self.heading_row_height = 50
        self.data_row_height = 50
        self.column_spacing = 12
        self.horizontal_margin = 12

        self.actualizar()

    def actualizar(self, fecha: str = ""):

        datos = self.obtener_datos(fecha)

        encabezados = datos[0]
        filas = datos[1:]

        self.columns = [
            ft2.DataColumn2(
                label=ft.Text(enc),
                size=ft2.DataColumnSize.M,
            ) for enc in encabezados
        ]

        self.rows = [
            ft2.DataRow2(
                expand=True,
                cells=[
                    ft.DataCell(ft.Text(celda)) for celda in fila
                ]
            ) for fila in filas
        ]

        if self.crear:
            self.crear = False
        else:
            self.update()

    def obtener_datos(self, fecha: str):
        if fecha == "":
            hoy = datetime.datetime.now()
            fecha = (hoy - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        csv_path = f"{self.CACHE_DIR}/{fecha}.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        filas = []

        if not os.path.exists(csv_path):

            url = f"https://www.avamet.org/mx-meteoxarxa.php?data={fecha}&territori=c15"
            html = requests.get(url).text

            soup = BeautifulSoup(html, "html.parser")
            tablas = soup.find_all("table")

            encabezados = ["Estació", "Temp mín (°C)", "Temp mit (°C)", "Temp màx (°C)", "HR mit (%)", "Prec mit (mm)", "Vent mit", "Vent dir", "Vent màx"]

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


class MyDatepicker(ft.DatePicker):
    def __init__(self, tabla: MyTable):
        super().__init__()

        hoy = datetime.datetime.now()
        
        self.last_date = hoy - datetime.timedelta(days=1)
        self.on_change = lambda e: self.on_fecha_seleccionada(e, tabla)
        self.on_dismiss = lambda: print("Dissmissed")

    def on_fecha_seleccionada(self, e: ft.Event[ft.DatePicker], tabla: MyTable):
        fecha = (e.control.value + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        tabla.actualizar(fecha)
