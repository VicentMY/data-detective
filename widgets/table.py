import datetime, asyncio
import flet as ft
import flet_datatable2 as ft2
import pandas as pd

from data_provider import DataProvider


class MyTable(ft2.DataTable2):
    """
    Tabla para mostrar los datos historicos de contaminación, precipitaciones y tráfico.
    """
    def __init__(self):
        super().__init__(columns=[])

        self.datos = pd.DataFrame()

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
        self._spinner = ft.Container(
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.SURFACE),
            content=ft.Column(
                visible=True,
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
            ),
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
        # asyncio.create_task(self.actualizar())

    def did_mount(self):
        self.page.run_task(self.actualizar)

    async def actualizar(self):
        """
        Actualiza la tabla con los datos de la categoría y fecha seleccionadas.
        """

        # Mostrar el spinner
        self._spinner.visible = True
        self.page.update()

        try:
            # Obtener los datos en un hilo separado para no bloquear el event loop
            # (las llamadas a DataProvider son síncronas/bloqueantes)
            self.datos = await asyncio.to_thread(self._obtener_datos_sync, self.categoria, self.fecha)

            # Separar encabezados y filas
            encabezados = self.datos.columns
            filas = self.datos.itertuples(index=False)

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
                        ft.DataCell(ft.Text(str(celda), max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)) for celda in fila
                    ]
                ) for fila in filas
            ]

        except Exception as e:
            print(f"[MyTable] No se ha podido obtener los datos históricos: {e}")
            self.page.show_dialog(ft.SnackBar(ft.Text("No se ha podido obtener los datos históricos", color=ft.Colors.ON_ERROR_CONTAINER), bgcolor=ft.Colors.ERROR_CONTAINER))

        # Ocultar el spinner
        self._spinner.visible = False
        self.page.update()

    def _obtener_datos_sync(self, categoria: str, fecha: str):
        """
        Versión síncrona de la obtención de datos. Diseñada para ejecutarse en
        un hilo separado mediante asyncio.to_thread() y no bloquear el event loop.

        Args:
            categoria (str): Categoría de los datos.
            fecha (str): Fecha de los datos.

        Returns:
            pd.DataFrame: Dataframe con los datos.
        """
        hoy = datetime.date.today()

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
            if fecha == "":
                fecha = (hoy - datetime.timedelta(days=365)).strftime("%Y-%m-%d")

            datos = DataProvider.get_hist_trafico(fecha)

        # Asigna la fecha a la tabla
        self.fecha = fecha

        return datos

    async def exportar_datos(self, tipo: str):
        """
        Exporta los datos de la tabla al formato seleccionado.

        Args:
            tipo (str): Formato de exportación.
        """
        # Si no hay datos, no se puede exportar
        if self.datos.empty:
            print("[MyTable] No hay datos para exportar")
            self.page.show_dialog(ft.SnackBar(ft.Text("No hay datos para exportar", color=ft.Colors.ON_ERROR_CONTAINER), bgcolor=ft.Colors.ERROR_CONTAINER))
            return

        # Nombre sugerido para el archivo
        nombre_sugerido = f"{self.categoria.replace(' ', '_')}_{self.fecha}.{tipo.lower()}"

        # Abre el selector de archivos del sistema
        path = await ft.FilePicker().save_file(
            dialog_title="Exportar datos como...",
            file_name=nombre_sugerido,
            allowed_extensions=["csv", "json", "parquet"]
        )

        # Si se selecciona una ruta, se exportan los datos
        if path:
            if tipo.lower() == "csv":
                self.datos.to_csv(path, index=False)

            elif tipo.lower() == "json":
                self.datos.to_json(path, orient="records", indent=4)

            elif tipo.lower() == "parquet":
                self.datos.to_parquet(path, index=False)
            
            print("[MyTable] Exportado en:", path)
            self.page.show_dialog(ft.SnackBar(ft.Text("Datos exportados correctamente", color=ft.Colors.ON_PRIMARY_CONTAINER), bgcolor=ft.Colors.PRIMARY_CONTAINER))


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

        # Actualiza la fecha de la tabla
        tabla.fecha = fecha

        # Si la categoría es contaminación, se le resta un año a la fecha
        if tabla.categoria == DataProvider.CONTAMINACION:
            fecha = (datetime.datetime.strptime(fecha, "%Y-%m-%d") - datetime.timedelta(days=365)).strftime("%Y-%m-%d")

        # Actualiza el título
        titulo.value = f"Histórico - {fecha}:"
        titulo.update()
        
        # Actualiza la tabla y el stack
        await tabla.actualizar()
        tabla.contenedor.update()


class MyDropdown(ft.DropdownM2):
    """
    Selector de categoría para seleccionar la categoría de los datos.

    Args:
        tabla (MyTable): Tabla para actualizar.
    """
    def __init__(self, tabla: MyTable):
        super().__init__()

        # Ancho del dropdown
        self.width = 200

        # Valor inicial
        self.value = tabla.categoria

        # Opciones del dropdown
        self.options = [
            ft.dropdownm2.Option(DataProvider.CONTAMINACION),
            ft.dropdownm2.Option(DataProvider.PRECIPITACIONES),
            ft.dropdownm2.Option(DataProvider.TRAFICO)
        ]

        async def _on_change(e):
            await self.on_seleccionar_categoria(e, tabla=tabla)

        # Callback que se ejecuta cuando se selecciona una categoría
        self.on_change = _on_change

    async def on_seleccionar_categoria(self, e: ft.Event[ft.DropdownM2], tabla: MyTable):
        """
        Callback que se ejecuta cuando se selecciona una categoría.

        Args:
            e (ft.Event[ft.DropdownM2]): Evento de selección de categoría.
            tabla (MyTable): Tabla para actualizar.
        """
        # Actualiza la categoría de la tabla
        tabla.categoria = e.control.value
        
        # Actualiza la tabla y el stack
        await tabla.actualizar()
        tabla.contenedor.update()
