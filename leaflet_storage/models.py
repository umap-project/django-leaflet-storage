# -*- coding: utf-8 -*-

from .base_models import (DataLayer, Map, TileLayer, Pictogram, Licence,
                                  MapToTileLayer, get_model)

# Marker is the only model configurable for now
Marker = get_model("Marker")
Polyline = get_model("Polyline")
Polygon = get_model("Polygon")
