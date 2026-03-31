import threading
import flet as ft

from tile_server import arrancar_proxy_tiles

from data_provider import DataProvider
from widgets import MyCard, MyColumn, MyMap, MyDatepicker, MyTable, MyDropdown, ExportDialog


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

        # Tiempo real
        med_cont, cal_cont, act_cont = DataProvider.get_res_contamin()  # Datos de contaminación
        med_prec, act_prec = DataProvider.get_res_precipit()  # Datos de precipitaciones

        def formato(n): return "{:.1f}".format(n)  # Formato de los números

        columna_1 = MyColumn(
            "Calidad del aire",
            ft.Icons.AIR,
            [MyCard("NO2", formato(med_cont["no2"]), "µg/m³"), MyCard("O3", formato(
                med_cont["o3"]), "µg/m³"), MyCard("PM10", formato(med_cont["pm10"]), "µg/m³")]
        )
        # TODO: Añadir una flecha con la dirección del viento
        columna_2 = MyColumn(
            "Precipitaciones",
            ft.Icons.UMBRELLA,
            [MyCard("Precipitación actual", formato(med_prec["precipitac"]), "mm/m²"), MyCard("Viento", formato(
                med_prec["viento_vel"]), "Km/h"), MyCard("Humedad", formato(med_prec["humedad_re"]), "%")]
        )

        # TODO: Obtener datos del tráfico
        columna_3 = MyColumn(
            "Tráfico",
            ft.Icons.TRAFFIC,
            [MyCard("Índice de congestión", 0, "%"), MyCard(
                "Accidentes activos", 0, ""), MyCard("Velocidad media de flujo", 0, "km/h")]
        )

        # Históricos
        tabla_historicos = MyTable()

        titulo_historico = ft.Text(
            f"Histórico - {tabla_historicos.fecha}:", weight=ft.FontWeight.BOLD, size=20)

        dd_elegir_datos = MyDropdown(tabla_historicos)

        btn_elegir_fecha = ft.Button(
            content=ft.Text("Elegir fecha"),
            icon=ft.Icons.DATE_RANGE,
            on_click=lambda _: page.show_dialog(MyDatepicker(
                tabla=tabla_historicos, titulo=titulo_historico)),
        )

        exp_dialog = ExportDialog(tabla_historicos)

        btn_exportar_hist = ft.Button(
            content=ft.Text("Exportar"),
            icon=ft.Icons.FILE_DOWNLOAD_ROUNDED,
            on_click=lambda _: page.show_dialog(exp_dialog),
        )

        page.add(
            ft.Tabs(
                selected_index=0,
                length=3,
                expand=True,
                content=ft.Column(
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
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                            controls=[
                                                titulo_historico,
                                                dd_elegir_datos,
                                                btn_elegir_fecha,
                                                btn_exportar_hist,
                                            ]
                                        ),
                                        ft.Row(
                                            expand=3,
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            controls=[
                                                # Utilizar el stack para mostrar el spinner sobre la tabla
                                                tabla_historicos.contenedor,
                                            ]
                                        )
                                    ]
                                ),
                                MyMap(),
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
    hilo_tiles = threading.Thread(
        target=arrancar_proxy_tiles,
        daemon=True
    )
    # Iniciar el hilo
    hilo_tiles.start()

    # Arrancar la app
    ft.run(MyApp)
