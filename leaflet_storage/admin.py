from django.contrib.gis import admin
from .models import Map, Marker, DataLayer, Pictogram, TileLayer, Polyline,\
                    Licence


class MapToTileLayerAdmin(admin.TabularInline):
    model = Map.tilelayers.through


class MapAdmin(admin.OSMGeoAdmin):
    inlines = [
        MapToTileLayerAdmin,
    ]

admin.site.register(Map, MapAdmin)
admin.site.register(Marker, admin.OSMGeoAdmin)
admin.site.register(Polyline, admin.OSMGeoAdmin)
admin.site.register(DataLayer)
admin.site.register(Pictogram)
admin.site.register(TileLayer)
admin.site.register(Licence)
