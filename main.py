import threading, asyncio
from math import pi
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
            """
            Alterna el tema de la página entre modo claro y oscuro
            """
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

        # Tiempo real - Formato numérico personalizado
        def formato(n): return "{:.1f}".format(n)

        # Carga asíncrona y en paralelo de los tres orígenes de datos
        async def cargar_datos():
            """
            Carga los datos de los tres orígenes de datos en paralelo.
            """
            async def cargar_contaminacion():
                med_cont, cal_cont, act_cont = await asyncio.to_thread(DataProvider.get_res_contamin, page)
                columna_1.actualizar(act_cont)
                columna_1.controls[2].actualizar(formato(med_cont["no2"]))
                columna_1.controls[3].actualizar(formato(med_cont["o3"]))
                columna_1.controls[4].actualizar(formato(med_cont["pm10"]))
                page.update()

            async def cargar_precipitaciones():
                med_prec, int_prec, dir_viento, act_prec = await asyncio.to_thread(DataProvider.get_res_precipit, page)
                columna_2.actualizar(act_prec)
                columna_2.controls[2].actualizar(formato(med_prec["Precipitación acumulada día (mm)"]))
                columna_2.controls[3].actualizar("-" if int_prec == "" else int_prec)
                columna_2.controls[4].actualizar(formato(med_prec["Velocidad del viento (km/h)"]), dir_viento)
                page.update()

            async def cargar_trafico():
                med_traf, est_traf, trm_traf, act_traf = await asyncio.to_thread(DataProvider.get_res_trafico, page)
                columna_3.actualizar(act_traf)
                columna_3.controls[2].actualizar(formato(med_traf))
                columna_3.controls[3].actualizar(est_traf)
                columna_3.controls[4].actualizar(trm_traf)
                page.update()

            # Mostrar spinner de carga
            spinner_carga.visible = True
            # Deshabilitar botón de refrescar
            btn_refrescar.disabled = True
            # Rotar el botón de refrescar
            btn_refrescar.rotate.angle += pi
            page.update()

            # Los tres orígenes de datos se cargan en paralelo
            await asyncio.gather(
                cargar_contaminacion(),
                cargar_precipitaciones(),
                cargar_trafico(),
            )

            # Históricos
            await tabla_historicos.actualizar()

            # Ocultar el spinner cuando todos hayan terminado
            spinner_carga.visible = False
            # Habilitar botón de refrescar
            btn_refrescar.disabled = False
            # Devolver el botón de refrescar a su estado original
            btn_refrescar.rotate.angle += pi
            page.update()

            # Mostrar snackbar de éxito
            page.show_dialog(ft.SnackBar(ft.Text("Datos cargados correctamente", color=ft.Colors.ON_PRIMARY_CONTAINER), bgcolor=ft.Colors.PRIMARY_CONTAINER))

        # Botón de refrescar
        btn_refrescar = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Refrescar datos",
            on_click=lambda _: page.run_task(cargar_datos),
            rotate=ft.Rotate(angle=0, alignment=ft.Alignment.CENTER),
            animate_rotation=ft.Animation(duration=500, curve=ft.AnimationCurve.EASE_IN_OUT),
        )

        # Barra de navegación
        page.appbar = ft.AppBar(
            leading=ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, margin=10),
            leading_width=30,
            title=ft.Text("Dashboard Valéncia"),
            center_title=False,
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            actions=[
                btn_refrescar,
                btn_alternar_tema,
            ],
        )

        # Crear columnas con datos placeholder (se actualizan cuando terminan de cargar)
        columna_1 = MyColumn(
            "Calidad del aire",
            ft.Icons.AIR,
            [
                MyCard("NO2", "-", "µg/m³"),
                MyCard("O3", "-", "µg/m³"),
                MyCard("PM10", "-", "µg/m³"),
            ],
            "-",
            DataProvider.CONTAMINACION
        )

        columna_2 = MyColumn(
            "Precipitaciones",
            ft.Icons.UMBRELLA,
            [
                MyCard("Acumulado hoy", "-", "mm/m²"),
                MyCard("Intensidad", "-", ""),
                MyCard("Viento", "-", "Km/h"),
            ],
            "-",
            DataProvider.PRECIPITACIONES
        )

        columna_3 = MyColumn(
            "Tráfico",
            ft.Icons.TRAFFIC,
            [
                MyCard("Índice medio de vehículos", "-", "vehículos"),
                MyCard("Estado general", "-", ""),
                MyCard("Tramo con más vehículos", "-", "")
            ],
            "-",
            DataProvider.TRAFICO
        )

        # Spinner de carga inicial para el área de datos en tiempo real
        spinner_carga = ft.Container(
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
                            ft.Text("Cargando datos...", size=16),
                        ]
                    )
                ]
            ),
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

        hist_exp_dialog = ExportDialog(tabla_historicos)

        btn_exportar_hist = ft.Button(
            content=ft.Text("Exportar"),
            icon=ft.Icons.FILE_DOWNLOAD_ROUNDED,
            on_click=lambda _: page.show_dialog(hist_exp_dialog),
        )

        # Mapa
        mi_mapa = MyMap()

        # Selector de capas para el mapa
        selector_capas = ft.Container(
            top=10,
            left=10,
            bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.SURFACE_CONTAINER),
            padding=10,
            border_radius=8,
            shadow=ft.BoxShadow(
                blur_radius=5,
                color=ft.Colors.with_opacity(0.3, ft.Colors.SHADOW),
            ),
            content=ft.Column(
                tight=True,
                spacing=5,
                controls=[
                    ft.Text("Capas del Mapa", weight=ft.FontWeight.BOLD),
                    ft.Checkbox(
                        label="Contaminación", 
                        value=mi_mapa.contaminacion_visible, 
                        on_change=lambda e: mi_mapa.set_contaminacion_visible(e.control.value)
                    ),
                    ft.Checkbox(
                        label="Precipitaciones", 
                        value=mi_mapa.precipitaciones_visible, 
                        on_change=lambda e: mi_mapa.set_precipitaciones_visible(e.control.value)
                    ),
                    ft.Checkbox(
                        label="Tráfico", 
                        value=mi_mapa.trafico_visible, 
                        on_change=lambda e: mi_mapa.set_trafico_visible(e.control.value)
                    ),
                ]
            )
        )

        # Leyenda del mapa
        def item_leyenda(color, texto):
            return ft.Row(
                controls=[
                    ft.Container(width=12, height=12, bgcolor=color, border_radius=3),
                    ft.Text(texto, size=11)
                ],
                spacing=5,
                tight=True
            )

        contenedor_leyenda = ft.Container(
            bottom=60,
            left=10,
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.SURFACE_CONTAINER),
            padding=15,
            border_radius=10,
            visible=False,
            width=210,
            shadow=ft.BoxShadow(
                blur_radius=10,
                color=ft.Colors.with_opacity(0.3, ft.Colors.SHADOW),
            ),
            content=ft.Column(
                tight=True,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Text("Leyenda", weight=ft.FontWeight.BOLD, size=14),
                    ft.Divider(height=1),
                    ft.Text("Contaminación", weight=ft.FontWeight.W_600, size=12),
                    item_leyenda(ft.Colors.GREEN, "Buena"),
                    item_leyenda(ft.Colors.BLUE, "Razonablemente Buena"),
                    item_leyenda(ft.Colors.ORANGE, "Regular"),
                    item_leyenda(ft.Colors.RED, "Mala"),
                    item_leyenda(ft.Colors.DEEP_PURPLE, "Muy Mala / Extrema"),
                    ft.Text("Precipitaciones", weight=ft.FontWeight.W_600, size=12),
                    item_leyenda(ft.Colors.LIGHT_BLUE, "0 mm (Sin lluvia)"),
                    item_leyenda(ft.Colors.CYAN, "< 1 mm (Muy ligera)"),
                    item_leyenda(ft.Colors.BLUE, "1 - 5 mm (Ligera)"),
                    item_leyenda(ft.Colors.INDIGO, "5 - 20 mm (Moderada)"),
                    item_leyenda(ft.Colors.DEEP_PURPLE, "> 20 mm (Intensa)"),
                    ft.Text("Tráfico", weight=ft.FontWeight.W_600, size=12),
                    item_leyenda(ft.Colors.GREEN, "Fluido"),
                    item_leyenda(ft.Colors.AMBER, "Denso"),
                    item_leyenda(ft.Colors.RED, "Congestionado"),
                    item_leyenda(ft.Colors.BLACK, "Cortado / Sin Datos"),
                ]
            )
        )

        def toggle_leyenda(e):
            contenedor_leyenda.visible = not contenedor_leyenda.visible
            btn_leyenda.icon = ft.Icons.CLOSE if contenedor_leyenda.visible else ft.Icons.INFO_OUTLINE
            btn_leyenda.update()
            contenedor_leyenda.update()

        btn_leyenda = ft.FloatingActionButton(
            icon=ft.Icons.INFO_OUTLINE,
            mini=True,
            bottom=10,
            left=10,
            on_click=toggle_leyenda,
            tooltip="Ver leyenda",
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.SURFACE_CONTAINER),
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
                                # Tab "Tiempo real": Stack para mostrar el spinner encima de las columnas
                                ft.Stack(
                                    expand=True,
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                columna_1,
                                                columna_2,
                                                columna_3,
                                            ]
                                        ),
                                        spinner_carga,
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
                                # Tab "Mapa": Stack con el mapa y el selector de capas encima
                                ft.Stack(
                                    expand=True,
                                    controls=[
                                        mi_mapa,
                                        selector_capas,
                                        contenedor_leyenda,
                                        btn_leyenda
                                    ]
                                )
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

        # Arrancar la carga inicial en paralelo una vez la página está construida
        page.run_task(cargar_datos)


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
