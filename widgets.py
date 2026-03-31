from flet.controls import padding
import os, datetime, requests, csv, threading, asyncio, time
import pandas as pd
import flet as ft
import flet_map as ftm
import flet_datatable2 as ft2

from data_provider import DataProvider

class MyCard(ft.Card):
    """
    Tarjeta para mostrar un valor con su unidad.

    Args:
        titulo (str): Título de la tarjeta
        valor (str): Valor a mostrar
        unidad (str): Unidad del valor
    """
    def __init__(self, titulo: str, valor: str, unidad: str):
        super().__init__()

        self.shadow_color = ft.Colors.ON_SURFACE_VARIANT
        self.content = ft.Container(
            padding=10,
            content=ft.Column(
                controls=[
                    ft.Text(titulo, size=14, weight=ft.FontWeight.W_600), # Título de la tarjeta
                    ft.Row(
                        controls=[
                            ft.Text(valor, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY), # Valor a mostrar
                            ft.Text(unidad), # Unidad del valor
                        ]
                    )
                ]
            )
        )


class MyColumn(ft.Column):
    """
    Columna para mostrar un título, un icono y tres widgets.

    Args:
        titulo (str): Título de la columna
        icono (ft.IconData): Icono de la columna
        widgets (list[ft.Control]): Lista de widgets a mostrar
    """
    def __init__(self, titulo: str, icono: ft.IconData, widgets: list[ft.Control]):
        super().__init__()

        self.expand = 1
        self.controls = [
            ft.Row(
                controls=[
                    ft.Icon(icono, color=ft.Colors.PRIMARY), # Icono de la columna
                    ft.Text(titulo, weight=ft.FontWeight.BOLD), # Título de la columna
                ]
            ),
            ft.Divider(color=ft.Colors.PRIMARY, radius=50), # Divisor
            # Widgets
            widgets[0],
            widgets[1],
            widgets[2],

            # TODO: Terminar el pie de columna
            ft.Button(
                content=ft.Text("Exportar"),
                icon=ft.Icons.FILE_DOWNLOAD_ROUNDED,
                on_click=lambda: print("EXPORTAR"),
            )
        ]


class MyMap(ftm.Map):
    """
    Mapa para mostrar la posición de las estaciones de contaminación, precipitaciones y tráfico en la ciudad de Valencia.
    """
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
        try:
            url = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estacions-contaminacio-atmosferiques-estaciones-contaminacion-atmosfericas/records?select=objectid%2Cnombre%2Cdireccion%2Ctipozona%2Cso2%2Cno2%2Co3%2Cco%2Cpm10%2Cpm25%2Ctipoemisio%2Cfecha_carg%2Ccalidad_am%2Cgeo_point_2d&limit=20"
            data = pd.read_json(url, encoding="utf-8")

            estaciones = [e for e in data["results"]]
            df = pd.DataFrame(estaciones)
        
        except Exception as e:
            print(f"Error al obtener los marcadores de las estaciones de contaminación: {e}")
            return []

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


class MyTable(ft2.DataTable2):
    """
    Tabla para mostrar los datos historicos de contaminación, precipitaciones y tráfico.
    """
    def __init__(self):
        super().__init__(columns=[])

        self.datos = []

        self.fecha = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d") # Fecha por defecto
        self.categoria = DataProvider.CONTAMINACION # Categoría por defecto

        # Formato de la tabla
        self.heading_row_color = ft.Colors.SECONDARY_CONTAINER
        self.sort_ascending = True
        self.expand = True
        self.heading_row_height = 50
        self.data_row_height = 50
        self.column_spacing = 12
        self.horizontal_margin = 12

        # Añadir una columna vacía para que no se queje
        self.columns = [
            ft2.DataColumn2(
                label=ft.Text("", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                size=ft2.DataColumnSize.M,
            )
        ]

        # Spinner para indicar que se están cargando los datos
        self._spinner = ft.Column(
            visible=False,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.ProgressRing(),
                        ft.Text("Cargando..."),
                    ]
                )
            ]
        )

        # Stack para mostrar el spinner sobre la tabla
        self.contenedor = ft.Stack(
            expand=True,
            controls=[
                self, # La tabla
                self._spinner,
            ]
        )

        # Carga inicial de los datos
        asyncio.create_task(self.actualizar())

    async def actualizar(self):
        """
        Actualiza la tabla con los datos de la categoría y fecha seleccionadas.
        """

        # Mostrar el spinner y ocultar la tabla
        self._spinner.visible = True
        self.visible = False

        # Actualizar la tabla y el spinner
        self.update()
        self._spinner.update()
    
        try:
            # Obtener los datos (puede tardar) de forma asíncrona
            self.datos = await self.obtener_datos(self.categoria, self.fecha)

            # Separar encabezados y filas
            encabezados = self.datos[0]
            filas = self.datos[1:]

            # Actualizar las columnas
            self.columns = [
                ft2.DataColumn2(
                    label=ft.Text(enc, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    size=ft2.DataColumnSize.M,
                ) for enc in encabezados
            ]

            # Actualizar las filas
            self.rows = [
                ft2.DataRow2(
                    expand=True,
                    cells=[
                        ft.DataCell(ft.Text(celda, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)) for celda in fila
                    ]
                ) for fila in filas
            ]
        
        except Exception as e:
            print("Error al obtener los datos")

        # Ocultar el spinner y mostrar la tabla
        self._spinner.visible = False
        self.visible = True

        # Actualizar la tabla y el spinner
        self.update()
        self._spinner.update()
        
    async def obtener_datos(self, categoria: str, fecha: str):
        """
        Obtiene los datos de la categoría y fecha seleccionadas.

        Args:
            categoria (str): Categoría de los datos.
            fecha (str): Fecha de los datos.

        Returns:
            list: Lista de filas con los datos para la tabla.
        """
        hoy = datetime.date.today()
        datos = []

        # Obtener los datos según la categoría
        if categoria == DataProvider.CONTAMINACION:
            if fecha == "":
                # Si no se selecciona fecha, se selecciona hoy hace un año
                fecha = (hoy - datetime.timedelta(days=365)).strftime("%Y-%m-%d")

            if datetime.datetime.strptime(fecha, "%Y-%m-%d").year >= hoy.year:
                # Si se selecciona una fecha del año actual, se selecciona la de hace un año
                fecha = (datetime.datetime.strptime(fecha, "%Y-%m-%d") - datetime.timedelta(days=365)).strftime("%Y-%m-%d")

            datos = DataProvider.get_hist_contaminacion(fecha)
        
        elif categoria == DataProvider.PRECIPITACIONES:
            if fecha == "":
                # Si no se selecciona fecha, se selecciona la fecha de ayer
                fecha = (hoy - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
            datos = DataProvider.get_hist_precipiaciones(fecha)
        
        else:
            # TODO: Implementar tráfico
            pass
        
        self.fecha = fecha # Asigna la fecha a la tabla

        return datos

    # TODO: Terminar implementación de exportación de datos
    async def exportar_datos(self, tipo: str):
        """
        Inicia el proceso de exportación de datos abriendo el selector de archivos.
        """
        if not self.datos:
            print("No hay datos para exportar")
            return

        print(tipo)
        print(tipo.lower())
        nombre_sugerido = f"{self.categoria.replace(' ', '_')}_{self.fecha}.{tipo.lower()}"

        path = await ft.FilePicker().save_file(
            dialog_title="Exportar datos como...",
            file_name=nombre_sugerido,
            allowed_extensions=["csv", "json", "parquet"]
        )
        print(path)

        if path:
            print("Guardando en:", path)

            # TODO: Manejar diferentes tipos de archivo (JSON, Parquet)
            with open(path, "w", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(self.datos)


class MyDatepicker(ft.DatePicker):
    """
    Selector de fecha para seleccionar la fecha de los datos.

    Args:
        tabla (MyTable): Tabla para actualizar.
        titulo (ft.Text): Título para actualizar.
    """
    def __init__(self, tabla: MyTable, titulo: ft.Text):
        super().__init__()

        hoy = datetime.datetime.now()
        
        self.last_date = hoy - datetime.timedelta(days=1) # Fecha máxima seleccionable
        
        async def _on_change(e):
            await self.on_fecha_seleccionada(e, tabla=tabla, titulo=titulo)
        
        self.on_change = _on_change
        self.on_dismiss = lambda: print("Dissmissed")

    async def on_fecha_seleccionada(self, e: ft.Event[ft.DatePicker], tabla: MyTable, titulo: ft.Text):
        """
        Callback que se ejecuta cuando se selecciona una fecha.

        Args:
            e (ft.Event[ft.DatePicker]): Evento de selección de fecha.
            tabla (MyTable): Tabla para actualizar.
            titulo (ft.Text): Título para actualizar.
        """
        # Se le suma un día porque el datepicker devuelve la fecha de hoy como "ayer" debido a un bug de Flet con la zona horaria
        fecha = (e.control.value + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        # TODO: Hacer que el datapicker tenga la fecha de la tabla como valor inicial
        self.value = datetime.datetime.strptime(tabla.fecha, "%Y-%m-%d") + datetime.timedelta(days=1)

        tabla.fecha = fecha # Actualiza la fecha de la tabla

        # Si la categoría es contaminación, se le resta un año a la fecha
        if tabla.categoria == DataProvider.CONTAMINACION:
            fecha = (datetime.datetime.strptime(fecha, "%Y-%m-%d") - datetime.timedelta(days=365)).strftime("%Y-%m-%d")

        titulo.value = f"Histórico - {fecha}:" # Actualiza el título
        titulo.update()
        await tabla.actualizar() # Actualiza la tabla
        tabla.contenedor.update() # Actualiza el stack


class MyDropdown(ft.DropdownM2):
    """
    Selector de categoría para seleccionar la categoría de los datos.

    Args:
        tabla (MyTable): Tabla para actualizar.
    """
    def __init__(self, tabla: MyTable):
        super().__init__()

        self.width = 200 # Ancho del dropdown
        self.value = tabla.categoria # Valor inicial
        self.options = [
            ft.dropdownm2.Option(DataProvider.CONTAMINACION),
            ft.dropdownm2.Option(DataProvider.PRECIPITACIONES),
            ft.dropdownm2.Option(DataProvider.TRAFICO)
        ] # Opciones del dropdown

        async def _on_change(e):
            await self.on_seleccionar_categoria(e, tabla=tabla)

        self.on_change = _on_change
    
    async def on_seleccionar_categoria(self, e: ft.Event[ft.DropdownM2], tabla: MyTable):
        """
        Callback que se ejecuta cuando se selecciona una categoría.

        Args:
            e (ft.Event[ft.DropdownM2]): Evento de selección de categoría.
            tabla (MyTable): Tabla para actualizar.
        """
        tabla.categoria = e.control.value # Actualiza la categoría de la tabla
        await tabla.actualizar() # Actualiza la tabla
        tabla.contenedor.update() # Actualiza el stack


class ExportDialog(ft.AlertDialog):
    def __init__(self, tabla: MyTable):
        super().__init__()

        self.tabla = tabla
        self.tipo = "CSV"

        def _on_change(e):
            self.tipo = e.control.value

        self.title = ft.Text("Exportar datos")
        self.content = ft.Column(
            tight=True,
            controls=[
                ft.Text("Selecciona el formato de exportación:"),
                ft.DropdownM2(
                    options=[
                        ft.dropdownm2.Option("CSV"),
                        ft.dropdownm2.Option("JSON"),
                        ft.dropdownm2.Option("Parquet")
                    ],
                    value="CSV",
                    on_change=_on_change
                )
            ]
        )
        self.actions = [
            ft.TextButton("Cancelar", on_click=lambda _: self.page.pop_dialog()),
            ft.TextButton("Exportar", on_click=self.exportar)
        ]

    async def exportar(self, e):
        self.page.pop_dialog()
        print("Exportar", self.tipo)
        await self.tabla.exportar_datos(self.tipo)