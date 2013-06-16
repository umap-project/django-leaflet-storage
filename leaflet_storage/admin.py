from django.contrib.gis import admin
from .models import Map, Marker, DataLayer, Pictogram, TileLayer, Polyline,\
                    Licence


admin.site.register(Map, admin.OSMGeoAdmin)
admin.site.register(Marker, admin.OSMGeoAdmin)
admin.site.register(Polyline, admin.OSMGeoAdmin)
admin.site.register(DataLayer)
admin.site.register(Pictogram)
admin.site.register(TileLayer)
admin.site.register(Licence)
