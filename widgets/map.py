import pandas as pd
import flet as ft
import flet_map as ftm


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
            raise Exception("DEBUG")
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
