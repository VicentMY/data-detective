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

        async def actualizar_todo(e):
            """
            Actualiza todos los datos de la aplicación.
            Las llamadas a DataProvider son bloqueantes, por lo que se ejecutan
            en hilos separados con asyncio.to_thread() para no congelar la UI.
            """
            # Deshabilitar botón y rotar
            btn_refrescar.disabled = True
            btn_refrescar.rotate.angle += pi
            btn_refrescar.update()
            page.update()

            def formato(n): return "{:.1f}".format(n)

            # Contaminación (hilo separado para no bloquear el event loop)
            med_cont, cal_cont, act_cont = await asyncio.to_thread(DataProvider.get_res_contamin, page)
            columna_1.actualizar(act_cont)
            columna_1.controls[2].actualizar(formato(med_cont["no2"]))
            columna_1.controls[3].actualizar(formato(med_cont["o3"]))
            columna_1.controls[4].actualizar(formato(med_cont["pm10"]))
            page.update()

            # Precipitaciones
            med_prec, int_prec, dir_viento, act_prec = await asyncio.to_thread(DataProvider.get_res_precipit, page)
            columna_2.actualizar(act_prec)
            columna_2.controls[2].actualizar(formato(med_prec["Precipitación acumulada día (mm)"]))
            columna_2.controls[3].actualizar("-" if int_prec == "" else int_prec)
            columna_2.controls[4].actualizar(formato(med_prec["Velocidad del viento (km/h)"]), dir_viento)
            page.update()

            # Tráfico
            med_traf, est_traf, trm_traf, act_traf = await asyncio.to_thread(DataProvider.get_res_trafico, page)
            columna_3.actualizar(act_traf)
            columna_3.controls[2].actualizar(formato(med_traf))
            columna_3.controls[3].actualizar(est_traf)
            columna_3.controls[4].actualizar(trm_traf)
            page.update()

            # Históricos (ya gestiona internamente su propio hilo)
            await tabla_historicos.actualizar()

            # Restaurar botón
            btn_refrescar.disabled = False
            btn_refrescar.rotate.angle += pi
            btn_refrescar.update()
            page.update()

            # Mostrar snackbar de éxito
            page.show_dialog(ft.SnackBar(ft.Text("Datos actualizados correctamente", color=ft.Colors.ON_PRIMARY_CONTAINER), bgcolor=ft.Colors.PRIMARY_CONTAINER))

        # Botón de refrescar
        btn_refrescar = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Refrescar datos",
            on_click=actualizar_todo,
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

        # Tiempo real - Formato numérico personalizado
        def formato(n): return "{:.1f}".format(n)

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
        spinner_inicio = ft.Column(
            visible=True,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.ProgressRing(),
                        ft.Text("Cargando datos en tiempo real...", size=16),
                    ]
                )
            ]
        )

        # Carga asíncrona y en paralelo de los tres orígenes de datos
        async def cargar_datos_iniciales():
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

            # Los tres orígenes de datos se cargan en paralelo
            await asyncio.gather(
                cargar_contaminacion(),
                cargar_precipitaciones(),
                cargar_trafico(),
            )

            # Ocultar el spinner cuando todos hayan terminado
            spinner_inicio.visible = False
            page.update()

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
                                        spinner_inicio,
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

        # Arrancar la carga inicial en paralelo una vez la página está construida
        page.run_task(cargar_datos_iniciales)


if __name__ == "__main__":
    # # Crear un hilo para arrancar el seudo-servidor Proxy de fondo
    # hilo_tiles = threading.Thread(
    #     target=arrancar_proxy_tiles,
    #     daemon=True
    # )
    # # Iniciar el hilo
    # hilo_tiles.start()

    # Arrancar la app
    ft.run(MyApp)
