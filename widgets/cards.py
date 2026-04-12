import datetime
import flet as ft

from data_provider import DataProvider
from widgets.export_dialog import ExportDialog

class MyCard(ft.Card):
    """
    Tarjeta para mostrar un valor con su unidad.

    Args:
        titulo (str): Título de la tarjeta
        valor (str): Valor a mostrar
        unidad (str): Unidad del valor
    """
    def __init__(self, titulo: str, valor: str, unidad: str, extra: str = None):
        super().__init__()

        self.shadow_color = ft.Colors.ON_SURFACE_VARIANT
        
        # Guardar como atributos los controles que se van a actualizar
        self.txt_valor = ft.Text(valor, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
        self.txt_unidad = ft.Text(unidad, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        self.txt_extra = ft.Text(extra if extra else "", weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY, size=20, margin=ft.Margin(right=10), max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)

        self.content = ft.Container(
            padding=10,
            content=ft.Column(
                controls=[
                    # Título de la tarjeta
                    ft.Text(titulo, size=14, weight=ft.FontWeight.W_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    # Valor y unidad
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row([
                                # Valor a mostrar
                                self.txt_valor,
                                # Unidad del valor,
                                self.txt_unidad,
                            ]),
                            # Extra
                            self.txt_extra,
                        ]
                    )
                ]
            )
        )

    def actualizar(self, valor: str, extra: str = None):
        """
        Actualiza el valor y el extra de la tarjeta.
        """
        self.txt_valor.value = valor
        self.txt_extra.value = extra if extra else ""
        self.update()


class MyColumn(ft.Column):
    """
    Columna para mostrar un título, un icono y tres widgets.

    Args:
        titulo (str): Título de la columna
        icono (ft.IconData): Icono de la columna
        widgets (list[ft.Control]): Lista de widgets a mostrar
    """
    def __init__(self, titulo: str, icono: ft.IconData, widgets: list[ft.Control], actualizado: str, categoria: str):
        super().__init__()

        self.columna = titulo
        self.categoria = categoria
        self.expand = 1
        self.padding = ft.Padding.only(top=10, bottom=20)

        self.txt_actualizado = ft.Text(f"Última actualización: {actualizado}", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)

        self.controls = [
            ft.Row(
                controls=[
                    # Icono de la columna
                    ft.Icon(icono, color=ft.Colors.PRIMARY),
                    # Título de la columna
                    ft.Text(titulo, weight=ft.FontWeight.BOLD, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ]
            ),
            ft.Divider(color=ft.Colors.PRIMARY, radius=50),  # Divisor
            # Widgets
            widgets[0],
            widgets[1],
            widgets[2],

            self.txt_actualizado,

            # TODO: Reemplazar por gráfico comparando entre las estaciones
            ft.Placeholder(expand=1),

            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                margin=ft.Margin(left=20, right=20),
                controls=[
                    ft.Button(
                        content=ft.Text("Ver más", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        icon=ft.Icons.MORE_HORIZ_OUTLINED,
                        on_click=self.ver_mas,
                        color=ft.Colors.ON_PRIMARY_CONTAINER,
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    ),
                    ft.Button(
                        content=ft.Text("Exportar", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        icon=ft.Icons.FILE_DOWNLOAD_ROUNDED,
                        on_click=lambda e: self.page.show_dialog(ExportDialog(self)),
                        color=ft.Colors.ON_PRIMARY_CONTAINER,
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    ),
                ]
            )
        ]

    def actualizar(self, actualizado: str):
        """
        Actualiza la fecha de actualización de la columna.
        """
        self.txt_actualizado.value = f"Última actualización: {actualizado}"
        self.update()

    def ver_mas(self, e):
        """
        Abre un diálogo con más información según la categoría de la columna.
        """
        from widgets import PollutionDialog, PrecipitationsDialog, TrafficDialog

        if self.categoria == DataProvider.CONTAMINACION:
            self.page.show_dialog(PollutionDialog())
        elif self.categoria == DataProvider.PRECIPITACIONES:
            self.page.show_dialog(PrecipitationsDialog())
        elif self.categoria == DataProvider.TRAFICO:
            self.page.show_dialog(TrafficDialog())
        else:
            self.page.show_dialog(ft.SnackBar(ft.Text(f"Diálogo de ver más no implementado para {self.categoria}", color=ft.Colors.ON_ERROR_CONTAINER), bgcolor=ft.Colors.ERROR_CONTAINER))
    
    async def exportar_datos(self, tipo: str):
        """
        Exporta los datos de la columna al formato seleccionado.

        Args:
            tipo (str): Formato de exportación.
        """
        # Obtener los datos desde DataProvider
        datos = DataProvider.get_tiempo_real(self.categoria)

        # Si no hay datos, no se puede exportar
        if datos.empty:
            print("[MyCard] No hay datos para exportar")
            self.page.show_dialog(ft.SnackBar(ft.Text("No hay datos para exportar", color=ft.Colors.ON_ERROR_CONTAINER), bgcolor=ft.Colors.ERROR_CONTAINER))
            return

        # Nombre sugerido para el archivo
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        nombre_sugerido = f"{self.categoria.replace(' ', '_')}_{fecha_actual}.{tipo.lower()}"

        # Abre el selector de archivos del sistema
        path = await ft.FilePicker().save_file(
            dialog_title="Exportar datos como...",
            file_name=nombre_sugerido,
            allowed_extensions=["csv", "json", "parquet"]
        )

        # Si se selecciona una ruta, se exportan los datos
        if path:
            if tipo.lower() == "csv":
                datos.to_csv(path, index=False)

            elif tipo.lower() == "json":
                datos.to_json(path, orient="records", indent=4)

            elif tipo.lower() == "parquet":
                datos.to_parquet(path, index=False)
            
            print("[MyCard] Exportado en:", path)
            self.page.show_dialog(ft.SnackBar(ft.Text("Datos exportados correctamente", color=ft.Colors.ON_PRIMARY_CONTAINER), bgcolor=ft.Colors.PRIMARY_CONTAINER))
