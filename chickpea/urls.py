from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import login

from chickpea import views
from .decorators import login_required, jsonize_view, map_permissions_check
from .utils import decorated_patterns

urlpatterns = patterns('',
    url(r'^login/$', jsonize_view(login), name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^map/(?P<username>[-_\w]+)/(?P<slug>[-_\w]+)/$', views.MapView.as_view(), name='map'),
    url(r'^feature/json/category/(?P<category_id>[\d]+)/$', views.FeatureGeoJSONListView.as_view(), name='feature_geojson_list'),
    url(r'^marker/json/(?P<pk>[\d]+)/$', views.MarkerGeoJSONView.as_view(), name='marker_geojson'),
    url(r'^marker/(?P<pk>\d+)/$', views.MarkerView.as_view(), name='marker'),
    url(r'^polyline/(?P<pk>\d+)/$', views.PolylineView.as_view(), name='polyline'),
    url(r'^polyline/json/(?P<pk>[\d]+)/$', views.PolylineGeoJSONView.as_view(), name='polyline_geojson'),
    url(r'^polygon/(?P<pk>\d+)/$', views.PolygonView.as_view(), name='polygon'),
    url(r'^polygon/json/(?P<pk>[\d]+)/$', views.PolygonGeoJSONView.as_view(), name='polygon_geojson'),
    url(r'^map/(?P<map_id>[\d]+)/export/iframe/$', views.EmbedMap.as_view(), name='map_embed'),
    url(r'^map/(?P<map_id>[\d]+)/infos/caption/$', views.MapInfos.as_view(), name='map_infos'),
)
urlpatterns += decorated_patterns('', login_required,
    url(r'^map/add/$', views.QuickMapCreate.as_view(), name='map_add'),
)
urlpatterns += decorated_patterns('', map_permissions_check,
    url(r'^map/(?P<map_id>[\d]+)/update/metadata/$', views.QuickMapUpdate.as_view(), name='map_update'),
    url(r'^map/(?P<map_id>[\d]+)/update/extent/$', csrf_exempt(views.UpdateMapExtent.as_view()), name='map_update_extent'),
    url(r'^map/(?P<map_id>[\d]+)/update/tilelayers/$', views.UpdateMapTileLayers.as_view(), name='map_update_tilelayers'),
    url(r'^map/(?P<map_id>[\d]+)/update/permissions/$', views.UpdateMapPermissions.as_view(), name='map_update_permissions'),
    url(r'^map/(?P<map_id>[\d]+)/update/delete/$', views.MapDelete.as_view(), name='map_delete'),
    url(r'^map/(?P<map_id>[\d]+)/import/file/$', views.UploadData.as_view(), name='upload_data'),
    url(r'^map/(?P<map_id>[\d]+)/category/add/$', views.CategoryCreate.as_view(), name='category_add'),
    url(r'^map/(?P<map_id>[\d]+)/category/edit/(?P<pk>\d+)/$', views.CategoryUpdate.as_view(), name='category_update'),
    url(r'^map/(?P<map_id>[\d]+)/category/delete/(?P<pk>\d+)/$', views.CategoryDelete.as_view(), name='category_delete'),
    url(r'^map/(?P<map_id>[\d]+)/marker/add/$', views.MarkerAdd.as_view(), name='marker_add'),
    url(r'^map/(?P<map_id>[\d]+)/marker/edit/(?P<pk>\d+)/$', views.MarkerUpdate.as_view(), name='marker_update'),
    url(r'^map/(?P<map_id>[\d]+)/marker/delete/(?P<pk>\d+)/$', views.MarkerDelete.as_view(), name='marker_delete'),
    url(r'^map/(?P<map_id>[\d]+)/polyline/add/$', views.PolylineAdd.as_view(), name='polyline_add'),
    url(r'^map/(?P<map_id>[\d]+)/polyline/edit/(?P<pk>\d+)/$', views.PolylineUpdate.as_view(), name='polyline_update'),
    url(r'^map/(?P<map_id>[\d]+)/polyline/delete/(?P<pk>\d+)/$', views.PolylineDelete.as_view(), name='polyline_delete'),
    url(r'^map/(?P<map_id>[\d]+)/polygon/add/$', views.PolygonAdd.as_view(), name='polygon_add'),
    url(r'^map/(?P<map_id>[\d]+)/polygon/edit/(?P<pk>\d+)/$', views.PolygonUpdate.as_view(), name='polygon_update'),
    url(r'^map/(?P<map_id>[\d]+)/polygon/delete/(?P<pk>\d+)/$', views.PolygonDelete.as_view(), name='polygon_delete'),
)
