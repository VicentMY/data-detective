import math
import requests
import flet as ft
import flet_map as ftm


# ---------------------------------------------------------------------------
# Helpers de conversión de coordenadas
# ---------------------------------------------------------------------------

def utm_a_latlon(easting: float, northing: float, zona: int = 30, hemisferio: str = "N") -> tuple[float, float]:
    """
    Convierte coordenadas UTM (EPSG:25830 → ETRS89 / UTM zona 30N) a WGS84 (lat, lon).
    Implementación matemática directa, sin dependencias externas.

    Args:
        easting: Coordenada X en metros.
        northing: Coordenada Y en metros.
        zona: Zona UTM (30 para España peninsular).
        hemisferio: 'N' (norte) o 'S' (sur).

    Returns:
        tuple: (latitud, longitud) en grados decimales WGS84.
    """
    # Parámetros del elipsoide GRS80 (≈ WGS84 a efectos prácticos)
    a = 6_378_137.0          # semieje mayor
    f = 1 / 298.257222101   # achatamiento
    b = a * (1 - f)          # semieje menor
    e2 = 1 - (b / a) ** 2   # excentricidad al cuadrado

    k0 = 0.9996              # factor de escala UTM
    lon0 = math.radians((zona - 1) * 6 - 180 + 3)  # meridiano central
    false_easting = 500_000.0
    false_northing = 0.0 if hemisferio == "N" else 10_000_000.0

    x = easting - false_easting
    y = northing - false_northing

    ep2 = e2 / (1 - e2)
    M = y / k0
    mu = M / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))

    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    phi1 = (mu
            + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
            + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
            + (151 * e1 ** 3 / 96) * math.sin(6 * mu)
            + (1097 * e1 ** 4 / 512) * math.sin(8 * mu))

    N1 = a / math.sqrt(1 - e2 * math.sin(phi1) ** 2)
    T1 = math.tan(phi1) ** 2
    C1 = ep2 * math.cos(phi1) ** 2
    R1 = a * (1 - e2) / (1 - e2 * math.sin(phi1) ** 2) ** 1.5
    D = x / (N1 * k0)

    lat = phi1 - (N1 * math.tan(phi1) / R1) * (
        D ** 2 / 2
        - (5 + 3 * T1 + 10 * C1 - 4 * C1 ** 2 - 9 * ep2) * D ** 4 / 24
        + (61 + 90 * T1 + 298 * C1 + 45 * T1 ** 2 - 252 * ep2 - 3 * C1 ** 2) * D ** 6 / 720
    )
    lon = lon0 + (
        D
        - (1 + 2 * T1 + C1) * D ** 3 / 6
        + (5 - 2 * C1 + 28 * T1 - 3 * C1 ** 2 + 8 * ep2 + 24 * T1 ** 2) * D ** 5 / 120
    ) / math.cos(phi1)

    return math.degrees(lat), math.degrees(lon)


# ---------------------------------------------------------------------------
# Colores según calidad del aire (contaminación)
# ---------------------------------------------------------------------------

# Mapa de calidad del aire → color del marcador
_COLORES_CALIDAD = {
    "Buena":                  ft.Colors.GREEN,
    "Razonablemente Buena":   ft.Colors.BLUE,
    "Regular":                ft.Colors.ORANGE,
    "Mala":                   ft.Colors.RED,
    "Muy Mala":               ft.Colors.DEEP_PURPLE,
    "Extremadamente Mala":    ft.Colors.PURPLE,
}
_COLOR_DEFAULT = ft.Colors.GREY


# ---------------------------------------------------------------------------
# Colores según nivel de precipitación (mm)
# ---------------------------------------------------------------------------

def _color_precipitacion(mm: float | None) -> str:
    """
    Devuelve un color según los mm de precipitación acumulada.

    Escala:
        sin datos / null → gris
        0 mm            → azul claro  (sin lluvia)
        0-1 mm          → cyan        (muy ligera)
        1-5 mm          → azul        (ligera)
        5-20 mm         → azul oscuro (moderada)
        > 20 mm         → violeta     (intensa)
    """
    if mm is None:
        return ft.Colors.GREY
    if mm == 0:
        return ft.Colors.LIGHT_BLUE
    if mm < 1:
        return ft.Colors.CYAN
    if mm < 5:
        return ft.Colors.BLUE
    if mm < 20:
        return ft.Colors.INDIGO
    return ft.Colors.DEEP_PURPLE


# ---------------------------------------------------------------------------
# Colores y nombres para el estado del tráfico
# ---------------------------------------------------------------------------

def _color_trafico(estado: int | None) -> str:
    """Devuelve el color correspondiente al estado del tráfico."""
    color_map = {
        0: ft.Colors.GREEN,
        1: ft.Colors.AMBER, # Dens
        2: ft.Colors.RED, # Congestionat
        3: ft.Colors.BLACK, # Tallat
        4: ft.Colors.GREY, # Sense dades
        5: ft.Colors.GREEN_300,
        6: ft.Colors.AMBER_300,
        7: ft.Colors.RED_300,
        8: ft.Colors.BLUE_GREY,
        9: ft.Colors.GREY_400
    }
    return color_map.get(estado, ft.Colors.GREY)

def _nombre_estado_trafico(estado: int | None) -> str:
    """Devuelve el nombre amigable del estado del tráfico."""
    estados = {
        0: "Fluido",
        1: "Denso",
        2: "Congestionado",
        3: "Cortado",
        4: "Sin datos",
        5: "Subterráneo Fluido",
        6: "Subterráneo Denso",
        7: "Subterráneo Congestionado",
        8: "Subterráneo Cortado",
        9: "Subterráneo Sin datos"
    }
    return estados.get(estado, "Desconocido")


# ---------------------------------------------------------------------------
# Widget principal del mapa
# ---------------------------------------------------------------------------

class MyMap(ftm.Map):
    """
    Mapa para mostrar la posición de las estaciones de contaminación,
    precipitaciones y tráfico en la ciudad de Valencia.
    """

    def __init__(self):
        super().__init__(layers=[], expand=True)

        self.expand = 1
        self.initial_center = ftm.MapLatitudeLongitude(39.47, -0.37)
        self.max_zoom = 18
        self.initial_zoom = 13
        self.min_zoom = 12

        # Capa de marcadores de contaminación (en su propio MarkerLayer para poder ocultarla)
        self._layer_contaminacion = ftm.MarkerLayer(
            markers=MyMap.get_marcadores_contaminacion()
        )

        # Capa de marcadores de precipitaciones (independiente para poder ocultarla)
        self._layer_precipitaciones = ftm.MarkerLayer(
            markers=MyMap.get_marcadores_precipitaciones()
        )

        polilineas_trafico, tooltips_trafico = MyMap.get_marcadores_trafico()

        # Capa de polilineas de tráfico (independiente para poder ocultarla)
        self._layer_trafico = ftm.PolylineLayer(
            polylines=polilineas_trafico
        )
        
        # Capa de anclajes (marcadores invisibles/sutiles) para los tooltips de tráfico
        self._layer_trafico_tooltips = ftm.MarkerLayer(
            markers=tooltips_trafico
        )

        self.layers = [
            ftm.TileLayer(
                url_template="http://localhost:5000/tiles/{z}/{x}/{y}.png",
                user_agent_package_name="valencia.dashboard.local",
                on_image_error=lambda e: print("[MyMap] Error al cargar los tiles"),
                max_zoom=18,
                min_zoom=12,
            ),
            ftm.RichAttribution(
                attributions=[
                    ftm.TextSourceAttribution(
                        text="© OpenStreetMap contributors, © CARTO",
                        on_click=lambda e: e.page.launch_url("https://carto.com/attributions"),
                    ),
                    ftm.TextSourceAttribution(
                        text="Flet",
                        on_click=lambda e: e.page.launch_url("https://flet.dev"),
                    ),
                ]
            ),
            ftm.SimpleAttribution(
                text="Flet",
                alignment=ft.Alignment.TOP_RIGHT,
            ),
            # Capas exclusivas
            self._layer_contaminacion,
            self._layer_precipitaciones,
            self._layer_trafico,
            self._layer_trafico_tooltips,
        ]

    # ------------------------------------------------------------------
    # Control de visibilidad de la capa de contaminación
    # ------------------------------------------------------------------

    @property
    def contaminacion_visible(self) -> bool:
        """Indica si la capa de contaminación está visible."""
        return self._layer_contaminacion.visible if self._layer_contaminacion.visible is not None else True

    def toggle_contaminacion(self):
        """Alterna la visibilidad de la capa de marcadores de contaminación."""
        self._layer_contaminacion.visible = not self.contaminacion_visible
        self._layer_contaminacion.update()

    def set_contaminacion_visible(self, visible: bool):
        """Establece explícitamente la visibilidad de la capa de contaminación."""
        self._layer_contaminacion.visible = visible
        self._layer_contaminacion.update()

    # ------------------------------------------------------------------
    # Control de visibilidad de la capa de precipitaciones
    # ------------------------------------------------------------------

    @property
    def precipitaciones_visible(self) -> bool:
        """Indica si la capa de precipitaciones está visible."""
        return self._layer_precipitaciones.visible if self._layer_precipitaciones.visible is not None else True

    def toggle_precipitaciones(self):
        """Alterna la visibilidad de la capa de marcadores de precipitaciones."""
        self._layer_precipitaciones.visible = not self.precipitaciones_visible
        self._layer_precipitaciones.update()

    def set_precipitaciones_visible(self, visible: bool):
        """Establece explícitamente la visibilidad de la capa de precipitaciones."""
        self._layer_precipitaciones.visible = visible
        self._layer_precipitaciones.update()

    # ------------------------------------------------------------------
    # Control de visibilidad de la capa de tráfico
    # ------------------------------------------------------------------

    @property
    def trafico_visible(self) -> bool:
        """Indica si la capa de tráfico está visible."""
        return self._layer_trafico.visible if self._layer_trafico.visible is not None else True

    def toggle_trafico(self):
        """Alterna la visibilidad de la capa de polilineas de tráfico."""
        nuevo_visible = not self.trafico_visible
        self._layer_trafico.visible = nuevo_visible
        self._layer_trafico_tooltips.visible = nuevo_visible
        self._layer_trafico.update()
        self._layer_trafico_tooltips.update()

    def set_trafico_visible(self, visible: bool):
        """Establece explícitamente la visibilidad de la capa de tráfico."""
        self._layer_trafico.visible = visible
        self._layer_trafico_tooltips.visible = visible
        self._layer_trafico.update()
        self._layer_trafico_tooltips.update()

    # ------------------------------------------------------------------
    # Obtención de marcadores
    # ------------------------------------------------------------------

    @staticmethod
    def get_marcadores_contaminacion() -> list:
        """
        Obtiene los marcadores de las estaciones de contaminación atmosférica
        de la ciudad de Valencia desde el geoportal municipal.

        Las coordenadas de la API vienen en EPSG:25830 (UTM ETRS89 zona 30N)
        y se convierten a WGS84 (lat/lon) para posicionarlas en el mapa.
        El color del icono refleja la calidad del aire de cada estación.

        Returns:
            list[ftm.Marker]: Lista de marcadores listos para añadir a un MarkerLayer.
        """
        try:
            url = (
                "https://geoportal.valencia.es/server/rest/services/OPENDATA/"
                "MedioAmbiente/MapServer/156/query?where=1=1"
                "&outFields=objectid%2Cnombre%2Cso2%2Cno2%2Co3%2Cco%2Cpm10%2Cpm25"
                "%2Ctipoemisio%2Cfecha_carg%2Ccalidad_am&f=json"
            )
            data = requests.get(url, timeout=10).json()
            features = data["features"]

        except Exception as ex:
            print(f"[MyMap] Error al obtener marcadores de contaminación: {ex}")
            return []

        marcadores = []
        for feature in features:
            attrs = feature.get("attributes", {})
            geom  = feature.get("geometry", {})

            x = geom.get("x")
            y = geom.get("y")
            if x is None or y is None:
                continue

            # Convertir UTM EPSG:25830 → WGS84
            lat, lon = utm_a_latlon(x, y, zona=30, hemisferio="N")

            nombre   = attrs.get("nombre", "Desconocida")
            calidad  = attrs.get("calidad_am") or "Desconocida"
            color    = _COLORES_CALIDAD.get(calidad, _COLOR_DEFAULT)

            marcadores.append(
                ftm.Marker(
                    coordinates=ftm.MapLatitudeLongitude(lat, lon),
                    content=ft.Icon(
                        ft.Icons.AIR,
                        color=color,
                        size=24,
                        tooltip=f"{nombre}\nCalidad: {calidad}",
                    ),
                )
            )

        print(f"[MyMap] {len(marcadores)} marcadores de contaminación cargados.")
        return marcadores

    @staticmethod
    def get_marcadores_precipitaciones() -> list:
        """
        Obtiene los marcadores de las estaciones meteorológicas (precipitaciones)
        de la ciudad de Valencia desde el geoportal municipal.

        Las coordenadas de la API vienen en EPSG:25830 (UTM ETRS89 zona 30N)
        y se convierten a WGS84 (lat/lon). El color del icono refleja el nivel
        de precipitación acumulada de cada estación.

        Returns:
            list[ftm.Marker]: Lista de marcadores listos para añadir a un MarkerLayer.
        """
        try:
            url = (
                "https://geoportal.valencia.es/server/rest/services/OPENDATA/"
                "MedioAmbiente/MapServer/157/query?where=1=1"
                "&outFields=*&f=json"
            )
            data = requests.get(url, timeout=10).json()
            features = data["features"]

        except Exception as ex:
            print(f"[MyMap] Error al obtener marcadores de precipitaciones: {ex}")
            return []

        marcadores = []
        for feature in features:
            attrs = feature.get("attributes", {})
            geom  = feature.get("geometry", {})

            x = geom.get("x")
            y = geom.get("y")
            if x is None or y is None:
                continue

            # Convertir UTM EPSG:25830 → WGS84
            lat, lon = utm_a_latlon(x, y, zona=30, hemisferio="N")

            nombre    = attrs.get("nombre", "Desconocida")
            precip    = attrs.get("precipitac")        # mm acumulados
            temp      = attrs.get("temperatur")        # ºC
            humedad   = attrs.get("humedad_re")        # %
            color     = _color_precipitacion(precip)

            # Tooltip con los datos disponibles
            lineas = [nombre]
            if precip  is not None: lineas.append(f"Precipitación: {precip} mm")
            if temp    is not None: lineas.append(f"Temperatura: {temp} ºC")
            if humedad is not None: lineas.append(f"Humedad: {humedad} %")
            tooltip = "\n".join(lineas)

            marcadores.append(
                ftm.Marker(
                    coordinates=ftm.MapLatitudeLongitude(lat, lon),
                    content=ft.Icon(
                        ft.Icons.WATER_DROP,
                        color=color,
                        size=24,
                        tooltip=tooltip,
                    ),
                )
            )

        print(f"[MyMap] {len(marcadores)} marcadores de precipitaciones cargados.")
        return marcadores


    @staticmethod
    def get_marcadores_trafico() -> tuple[list, list]:
        """
        Obtiene los tramos de tráfico de la ciudad de Valencia
        desde el geoportal municipal y devuelve polilineas para el mapa
        y marcadores de ayuda (sutiles) para los tooltips (hover).

        Las coordenadas de la API vienen en EPSG:25830 y se convierten a WGS84.

        Returns:
            tuple: (lista_recorrido_polilinea, lista_marcadores_tooltips)
        """
        try:
            url = (
                "https://geoportal.valencia.es/server/rest/services/OPENDATA/"
                "Trafico/MapServer/192/query?where=1=1"
                "&outFields=*&f=json"
            )
            data = requests.get(url, timeout=10).json()
            features = data["features"]

        except Exception as ex:
            print(f"[MyMap] Error al obtener datos de tráfico: {ex}")
            return [], []

        polilineas = []
        marcadores_tooltips = []
        
        for feature in features:
            attrs = feature.get("attributes", {})
            geom  = feature.get("geometry", {})

            paths = geom.get("paths", [])
            if not paths:
                continue

            nombre    = attrs.get("denominacion") or "Desconocida"
            estado    = attrs.get("estado")
            color     = _color_trafico(estado)
            lbl_est   = _nombre_estado_trafico(estado)
            tooltip   = f"{nombre}\nEstado: {lbl_est}"

            # Un 'feature' puede tener varias lineas desconectadas (paths)
            for path in paths:
                puntos_wgs84 = []
                for x, y in path:
                    lat, lon = utm_a_latlon(x, y, zona=30, hemisferio="N")
                    puntos_wgs84.append(ftm.MapLatitudeLongitude(lat, lon))
                
                if puntos_wgs84:
                    # Trazo de la autopista/calle (no pilla el hover instintivamente en flet_map)
                    polilineas.append(
                        ftm.PolylineMarker(
                            coordinates=puntos_wgs84,
                            color=color,
                            stroke_width=3.5,
                            tooltip=tooltip
                        )
                    )
                    
                    # Añadir un nodo central para facilitar el "hover" (un círculo pequeño sutil)
                    idx_central = len(puntos_wgs84) // 2
                    marcadores_tooltips.append(
                        ftm.Marker(
                            coordinates=puntos_wgs84[idx_central],
                            content=ft.Icon(
                                ft.Icons.CIRCLE, 
                                size=12, 
                                color=color, 
                                tooltip=tooltip
                            ),
                            alignment=ft.Alignment.CENTER
                        )
                    )

        print(f"[MyMap] {len(polilineas)} tramos de tráfico cargados.")
        return polilineas, marcadores_tooltips
