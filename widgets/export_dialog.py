import flet as ft

class ExportDialog(ft.AlertDialog):
    def __init__(self, widget: ft.Control):
        super().__init__()

        self.widget = widget
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
        # Cierra el diálogo
        self.page.pop_dialog()
        
        # Importar los widgets ahora para evitar causar una importación circular
        from widgets.table import MyTable
        from widgets.cards import MyColumn
        
        # Si el widget es una tabla, se exportan sus datos
        if isinstance(self.widget, MyTable):
            await self.widget.exportar_datos(self.tipo)
        
        # Si el widget es una columna, se exportan sus datos
        elif isinstance(self.widget, MyColumn):
            await self.widget.exportar_datos(self.tipo)