import flet as ft
from data_provider import DataProvider
from widgets.cards import MyCard
import datetime
import pandas as pd

class PollutionDialog(ft.AlertDialog):
    def __init__(self):
        super().__init__()

        # Obtener datos de contaminación
        self.df = DataProvider.get_tiempo_real(DataProvider.CONTAMINACION)
        
        # Estado de la UI
        if self.df.empty:
            self.selected_index = None
        else:
            self.selected_index = 0

        self.title = ft.Text("Información de Estaciones de Contaminación")
        
        self.stations_list = ft.ListView(expand=1, spacing=5, width=250)
        
        self.details_grid = ft.GridView(
            expand=1,
            runs_count=2,
            max_extent=320,
            child_aspect_ratio=2.1,
            spacing=10,
            run_spacing=10,
        )

        self.content = ft.Container(
            width=1000,
            height=600,
            content=ft.Row(
                expand=1,
                controls=[
                    ft.Container(
                        content=self.stations_list,
                        border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
                        padding=ft.Padding.only(right=10)
                    ),
                    ft.Container(
                        content=self.details_grid,
                        expand=1,
                        padding=ft.Padding.only(left=10)
                    )
                ]
            )
        )
        
        self.actions = [
            ft.TextButton("Cerrar", on_click=lambda e: e.page.pop_dialog())
        ]
        
        self.populate_stations()
        self.update_details()

    def populate_stations(self):
        if self.df.empty:
            return
            
        for i, row in self.df.iterrows():
            btn = ft.ListTile(
                title=ft.Text(row["nombre"], size=14, weight=ft.FontWeight.W_500),
                data=i,
                on_click=self.on_station_click,
                selected=i == self.selected_index,
                selected_color=ft.Colors.PRIMARY,
                selected_tile_color=ft.Colors.PRIMARY_CONTAINER,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
            self.stations_list.controls.append(btn)

    def on_station_click(self, e):
        self.selected_index = e.control.data
        for c in self.stations_list.controls:
            c.selected = c.data == self.selected_index
        self.update_details()
        self.update()

    def update_details(self):
        self.details_grid.controls.clear()
        if self.selected_index is None or self.df.empty:
            self.details_grid.controls.append(ft.Text("No hay datos disponibles."))
            return
            
        row = self.df.iloc[self.selected_index]
        
        # Formatear la fecha
        fecha = row["fecha_carg"]
        if fecha != "NULL" and pd.notna(fecha):
            fecha_str = datetime.datetime.fromtimestamp(int(fecha)/1000).strftime("%d/%m/%Y %H:%M")
        else:
            fecha_str = "-"
            
        def fmt(val):
            return str(val) if pd.notna(val) else "-"

        fields = [
            ("ID Estación", fmt(row["objectid"]), ""),
            ("SO2", fmt(row["so2"]), "µg/m³"),
            ("NO2", fmt(row["no2"]), "µg/m³"),
            ("O3", fmt(row["o3"]), "µg/m³"),
            ("CO", fmt(row["co"]), "mg/m³"),
            ("PM10", fmt(row["pm10"]), "µg/m³"),
            ("PM2.5", fmt(row["pm25"]), "µg/m³"),
            ("Calidad", fmt(row["calidad_am"]).replace(" ", "\n"), ""),
            ("Actualizado", fecha_str, ""),
        ]
        
        for titulo, valor, unidad in fields:
            self.details_grid.controls.append(
                MyCard(titulo=titulo, valor=valor, unidad=unidad)
            )

class PrecipitationsDialog(ft.AlertDialog):
    def __init__(self):
        super().__init__()

        # Obtener datos de precipitaciones
        self.df = DataProvider.get_tiempo_real(DataProvider.PRECIPITACIONES)
        
        # Estado de la UI
        if self.df.empty:
            self.selected_index = None
        else:
            self.selected_index = 0

        self.title = ft.Text("Información de Estaciones de Precipitaciones")
        
        self.stations_list = ft.ListView(expand=1, spacing=5, width=280)
        
        self.details_grid = ft.GridView(
            expand=1,
            runs_count=2,
            max_extent=320,
            child_aspect_ratio=2.1,
            spacing=10,
            run_spacing=10,
        )

        self.content = ft.Container(
            width=1000,
            height=650,
            content=ft.Row(
                expand=1,
                controls=[
                    ft.Container(
                        content=self.stations_list,
                        border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
                        padding=ft.Padding.only(right=10)
                    ),
                    ft.Container(
                        content=self.details_grid,
                        expand=1,
                        padding=ft.Padding.only(left=10)
                    )
                ]
            )
        )
        
        self.actions = [
            ft.TextButton("Cerrar", on_click=lambda e: e.page.pop_dialog())
        ]
        
        self.populate_stations()
        self.update_details()

    def populate_stations(self):
        if self.df.empty:
            return
            
        for i, row in self.df.iterrows():
            btn = ft.ListTile(
                title=ft.Text(row["Estación"], size=14, weight=ft.FontWeight.W_500),
                data=i,
                on_click=self.on_station_click,
                selected=i == self.selected_index,
                selected_color=ft.Colors.PRIMARY,
                selected_tile_color=ft.Colors.PRIMARY_CONTAINER,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
            self.stations_list.controls.append(btn)

    def on_station_click(self, e):
        self.selected_index = e.control.data
        for c in self.stations_list.controls:
            c.selected = c.data == self.selected_index
        self.update_details()
        self.update()

    def update_details(self):
        self.details_grid.controls.clear()
        if self.selected_index is None or self.df.empty:
            self.details_grid.controls.append(ft.Text("No hay datos disponibles."))
            return
            
        row = self.df.iloc[self.selected_index]
            
        def fmt(val):
            return str(val) if pd.notna(val) and val != "" else "-"

        fields = [
            ("Temp. actual", fmt(row["Temperatura actual (ºC)"]), "ºC"),
            ("Temp. mínima", fmt(row["Temperatura mínima (ºC)"]), "ºC"),
            ("Temp. máxima", fmt(row["Temperatura máxima (ºC)"]), "ºC"),
            ("Punto rocío", fmt(row["Punto de rocío (ºC)"]), "ºC"),
            ("Humedad", fmt(row["Humedad relativa (%)"]), "%"),
            ("Acum. día", fmt(row["Precipitación acumulada día (mm)"]), "mm"),
            ("Intensidad", fmt(row["Intensidad de precipitación"]), ""),
            ("Vel. viento", fmt(row["Velocidad del viento (km/h)"]), "km/h"),
            ("Dir. viento", fmt(row["Dirección del viento"]), ""),
            ("Vel. máx. viento", fmt(row["Velocidad máxima del viento (km/h)"]), "km/h"),
            ("Actualizado", fmt(row["Actualizado"]), ""),
        ]
        
        for titulo, valor, unidad in fields:
            self.details_grid.controls.append(
                MyCard(titulo=titulo, valor=valor, unidad=unidad)
            )

class TrafficDialog(ft.AlertDialog):
    def __init__(self):
        super().__init__()

        # Obtener datos de tráfico
        self.df = DataProvider.get_tiempo_real(DataProvider.TRAFICO)
        
        # Estado de la UI
        if self.df.empty:
            self.selected_index = None
        else:
            self.selected_index = 0

        self.title = ft.Text("Información de Tramos de Tráfico")
        
        self.stations_list = ft.ListView(expand=1, spacing=5, width=350)
        
        self.details_grid = ft.GridView(
            expand=1,
            runs_count=2,
            max_extent=320,
            child_aspect_ratio=2.1,
            spacing=10,
            run_spacing=10,
        )

        self.content = ft.Container(
            width=1100,
            height=650,
            content=ft.Row(
                expand=1,
                controls=[
                    ft.Container(
                        content=self.stations_list,
                        border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
                        padding=ft.Padding.only(right=10)
                    ),
                    ft.Container(
                        content=self.details_grid,
                        expand=1,
                        padding=ft.Padding.only(left=10)
                    )
                ]
            )
        )
        
        self.actions = [
            ft.TextButton("Cerrar", on_click=lambda e: e.page.pop_dialog())
        ]
        
        self.populate_stations()
        self.update_details()

    def populate_stations(self):
        if self.df.empty:
            return
            
        for i, row in self.df.iterrows():
            # Usar denominación si existe, si no des_tramo
            nombre = row["denominacion"] if pd.notna(row["denominacion"]) and row["denominacion"] != "" else row["des_tramo"]
            btn = ft.ListTile(
                title=ft.Text(nombre, size=12, weight=ft.FontWeight.W_500, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                data=i,
                on_click=self.on_station_click,
                selected=i == self.selected_index,
                selected_color=ft.Colors.PRIMARY,
                selected_tile_color=ft.Colors.PRIMARY_CONTAINER,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
            self.stations_list.controls.append(btn)

    def on_station_click(self, e):
        self.selected_index = e.control.data
        for c in self.stations_list.controls:
            c.selected = c.data == self.selected_index
        self.update_details()
        self.update()

    def update_details(self):
        self.details_grid.controls.clear()
        if self.selected_index is None or self.df.empty:
            self.details_grid.controls.append(ft.Text("No hay datos disponibles."))
            return
            
        row = self.df.iloc[self.selected_index]
            
        def fmt(val, limit=None):
            if pd.isna(val) or val == "":
                return "-"
            s = str(val)
            if limit and len(s) > limit:
                return s[:limit] + "..."
            return s
        
        # Formatear el estado del tráfico
        estado_raw = row["estado_est"]
        estado_str = "-"
        if pd.notna(estado_raw):
            try:
                estado_str = DataProvider.ESTADOS_TRAFICO.get(int(estado_raw), str(estado_raw))
            except:
                estado_str = str(estado_raw)

        fields = [
            ("ID Fiware", fmt(row["fiwareid"]), ""),
            ("IMV (Intensidad)", fmt(row["imv"]), "veh/h"),
            ("Estado (Int.)", fmt(row["estado_int"]), ""),
            ("Tráfico (Estimado)", estado_str.replace(" / ", "\n"), ""),
            ("Tramo", fmt(row["des_tramo"], limit=14), ""),
            ("Actualizado", fmt(row["Actualizado"]), ""),
        ]
        
        for titulo, valor, unidad in fields:
            self.details_grid.controls.append(
                MyCard(titulo=titulo, valor=valor, unidad=unidad)
            )
