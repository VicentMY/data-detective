import threading, time
import datetime as dt

import flet as ft
import flet_datatable2 as ft2

from tile_server import arrancar_proxy_tiles

from widgets import MyCard, MyColumn, MyMap, MyDatepicker, MyTable

class MyApp:
    def __init__(self, page: ft.Page):
        # Propiedades de la página
        page.title = "Dashboard Valéncia"
        page.padding = 10

        # Tema de la página
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(color_scheme_seed="indigo", use_material3=True)

        def alternar_tema(e: ft.Event[ft.IconButton]):
            en_modo_claro = page.theme_mode == ft.ThemeMode.LIGHT

            # Cambiar el tema de la página
            page.theme_mode = ft.ThemeMode.DARK if en_modo_claro else ft.ThemeMode.LIGHT
            # Cambiar el icono del botón
            btn_alternar_tema.icon = ft.Icons.DARK_MODE if en_modo_claro else ft.Icons.LIGHT_MODE
            # Cambiar el tooltip del botón
            btn_alternar_tema.tooltip = f"Cambiar a modo {"claro" if en_modo_claro else "oscuro"}"

            page.update()

        # Botón cambiar de tema
        btn_alternar_tema = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.DARK_MODE,
            on_click=alternar_tema,
            tooltip=f"Cambiar a modo {"claro" if page.theme_mode == ft.ThemeMode.DARK else "oscuro"}",
        )

        # Barra de navegación
        page.appbar = ft.AppBar(
            leading=ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, margin=10),
            leading_width=30,
            title=ft.Text("Dashboard Valéncia"),
            center_title=False,
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            actions=[
                btn_alternar_tema,
            ],
        )

        columna_1 = MyColumn(
            "Calidad del aire",
            ft.Icons.AIR,
            [MyCard("NO2", 18.8, "µg/m³"), MyCard("O3", 4.1, "µg/m³"), MyCard("PM10", 24.8, "µg/m³")]
        )

        columna_2 = MyColumn(
            "Precipitaciones",
            ft.Icons.UMBRELLA,
            [MyCard("Acumulado hoy", 0.00, "mm/m²"), MyCard("Intensidad", 0.0, "L/h"), MyCard("Probabilidad en 1h", 5, "%")]
        )
        
        columna_3 = MyColumn(
            "Tráfico",
            ft.Icons.TRAFFIC,
            [MyCard("Índice de congestión", 68, "%"), MyCard("Accidentes activos", 4, ""), MyCard("Velocidad media de flujo", 42, "km/h")]
        )

        tabla = MyTable()
        dialog_fecha = MyDatepicker(tabla)

        btn_elegir_fecha = ft.Button(
            content=ft.Text("Elegir fecha"),
            icon=ft.Icons.DATE_RANGE,
            on_click=lambda: page.show_dialog(dialog_fecha),
        )

        page.add(
            ft.Tabs(
                selected_index=0,
                length=3,
                expand=True,
                content=ft.Column(
                    # expand=True,
                    controls=[
                        ft.TabBarView(
                            expand=True,
                            controls=[
                                ft.Row(
                                    controls=[
                                        columna_1,
                                        columna_2,
                                        columna_3,
                                    ]
                                ),
                                ft.Column(
                                    expand=True,
                                    controls=[
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            controls=[
                                                btn_elegir_fecha,
                                            ]
                                        ),
                                        ft.Row(
                                            expand=3,
                                            controls=[
                                                tabla,
                                            ]
                                        )
                                    ]
                                ),
                                MyMap([]),
                            ]
                        ),
                        ft.TabBar(
                            divider_height=0.1,
                            tab_alignment=ft.TabAlignment.CENTER,
                            tabs=[
                                ft.Tab(label="Tiempo real", icon=ft.Icons.AV_TIMER),
                                ft.Tab(label="Histórico", icon=ft.Icons.HISTORY),
                                ft.Tab(label="Mapa", icon=ft.Icons.MAP)
                            ]
                        )
                    ]
                )
            )
        )




if __name__ == "__main__":
    # Crear un hilo para arrancar el seudo-servidor Proxy de fondo
    # hilo_tiles = threading.Thread(
    #     target=arrancar_proxy_tiles,
    #     daemon=True
    # )
    # Iniciar el hilo
    # hilo_tiles.start()

    # Espera para asegurar que el proxy está listo
    # time.sleep(1)

    # Arrancar la app
    ft.run(MyApp)
