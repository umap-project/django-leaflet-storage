from django.conf.urls import patterns, url
from django.contrib.auth.views import login
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache

from . import views
from .decorators import jsonize_view, map_permissions_check,\
    login_required_if_not_anonymous_allowed
from .utils import decorated_patterns

urlpatterns = patterns('',
    url(r'^login/$', jsonize_view(login), name='login'),
    url(r'^login/popup/end/$', views.LoginPopupEnd.as_view(), name='login_popup_end'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^map/(?P<slug>[-_\w]+)_(?P<pk>\d+)$', views.MapView.as_view(), name='map'),
    url(r'^map/(?P<username>[-_\w]+)/(?P<slug>[-_\w]+)/$', views.MapOldUrl.as_view(), name='map_old_url'),
    url(r'^map/anonymous-edit/(?P<signature>.+)$', views.MapAnonymousEditUrl.as_view(), name='map_anonymous_edit_url'),
    url(r'^m/(?P<pk>\d+)/$', views.MapShortUrl.as_view(), name='map_short_url'),
    url(r'^feature/json/datalayer/(?P<datalayer_id>[\d]+)/$', views.FeatureGeoJSONListView.as_view(), name='feature_geojson_list'),
    url(r'^datalayer/(?P<pk>[\d]+)/$', views.DataLayerView.as_view(), name='datalayer_view'),
    url(r'^marker/json/(?P<pk>[\d]+)/$', views.MarkerGeoJSON.as_view(), name='marker_geojson'),
    url(r'^marker/(?P<pk>\d+)/$', views.MarkerView.as_view(), name='marker'),
    url(r'^polyline/(?P<pk>\d+)/$', views.PolylineView.as_view(), name='polyline'),
    url(r'^polyline/json/(?P<pk>[\d]+)/$', views.PolylineGeoJSON.as_view(), name='polyline_geojson'),
    url(r'^polygon/(?P<pk>\d+)/$', views.PolygonView.as_view(), name='polygon'),
    url(r'^polygon/json/(?P<pk>[\d]+)/$', views.PolygonGeoJSON.as_view(), name='polygon_geojson'),
    url(r'^map/(?P<map_id>[\d]+)/export/iframe/$', views.EmbedMap.as_view(), name='map_embed'),
    url(r'^map/(?P<map_id>[\d]+)/infos/caption/$', views.MapInfos.as_view(), name='map_infos'),
    url(r'^pictogram/json/$', views.PictogramJSONList.as_view(), name='pictogram_list_json'),
    url(r'^map/(?P<map_id>[\d]+)/export/data/$', views.DownloadData.as_view(), name='download_data'),
)
urlpatterns += decorated_patterns('', [login_required_if_not_anonymous_allowed, never_cache, ],
    url(r'^map/add/$', views.QuickMapCreate.as_view(), name='map_add'),
)
urlpatterns += decorated_patterns('', [map_permissions_check, never_cache, ],
    url(r'^map/(?P<map_id>[\d]+)/update/metadata/$', views.QuickMapUpdate.as_view(), name='map_update'),
    url(r'^map/(?P<map_id>[\d]+)/update/settings/$', views.UpdateMapSettings.as_view(), name='map_update_settings'),
    url(r'^map/(?P<map_id>[\d]+)/update/extent/$', csrf_exempt(views.UpdateMapExtent.as_view()), name='map_update_extent'),
    url(r'^map/(?P<map_id>[\d]+)/update/tilelayer/$', csrf_exempt(views.UpdateMapTileLayer.as_view()), name='map_update_tilelayer'),
    url(r'^map/(?P<map_id>[\d]+)/update/permissions/$', views.UpdateMapPermissions.as_view(), name='map_update_permissions'),
    url(r'^map/(?P<map_id>[\d]+)/update/delete/$', views.MapDelete.as_view(), name='map_delete'),
    url(r'^map/(?P<map_id>[\d]+)/update/clone/$', views.MapClone.as_view(), name='map_clone'),
    url(r'^map/(?P<map_id>[\d]+)/import/data/$', views.UploadData.as_view(), name='upload_data'),
    url(r'^map/(?P<map_id>[\d]+)/datalayer/create/$', views.DataLayerCreate.as_view(), name='datalayer_create'),
    url(r'^map/(?P<map_id>[\d]+)/datalayer/update/(?P<pk>\d+)/$', views.DataLayerUpdate.as_view(), name='datalayer_update'),
    url(r'^map/(?P<map_id>[\d]+)/datalayer/delete/(?P<pk>\d+)/$', views.DataLayerDelete.as_view(), name='datalayer_delete'),
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
