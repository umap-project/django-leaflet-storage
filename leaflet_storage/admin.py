from django.contrib.gis import admin
from .models import Map, Marker, DataLayer, Pictogram, TileLayer, Polyline,\
                    Licence


class TileLayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'rank', )
    list_editable =('rank', )

admin.site.register(Map, admin.OSMGeoAdmin)
admin.site.register(Marker, admin.OSMGeoAdmin)
admin.site.register(Polyline, admin.OSMGeoAdmin)
admin.site.register(DataLayer)
admin.site.register(Pictogram)
admin.site.register(TileLayer, TileLayerAdmin)
admin.site.register(Licence)
