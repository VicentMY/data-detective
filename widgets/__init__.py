# Re-exporta todos los widgets para mantener compatibilidad con los imports existentes.
# En main.py se puede seguir usando: from widgets import MyCard, MyColumn, ...

from widgets.cards import MyCard, MyColumn
from widgets.map import MyMap
from widgets.table import MyTable, MyDatepicker, MyDropdown
from widgets.export_dialog import ExportDialog
from widgets.stations_dialog import PollutionDialog, PrecipitationsDialog, TrafficDialog

__all__ = [
    "MyCard",
    "MyColumn",
    "MyMap",
    "MyTable",
    "MyDatepicker",
    "MyDropdown",
    "ExportDialog",
    "PollutionDialog",
    "PrecipitationsDialog",
    "TrafficDialog",
]
