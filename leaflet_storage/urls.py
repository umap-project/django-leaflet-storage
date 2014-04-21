from django.conf.urls import patterns, url
from django.contrib.auth.views import login
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache, cache_control

from . import views
from .decorators import jsonize_view, map_permissions_check,\
    login_required_if_not_anonymous_allowed
from .utils import decorated_patterns

urlpatterns = patterns('',
    url(r'^login/$', jsonize_view(login), name='login'),
    url(r'^login/popup/end/$', views.LoginPopupEnd.as_view(), name='login_popup_end'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^map/(?P<pk>\d+)/geojson/$', views.MapViewGeoJSON.as_view(), name='map_geojson'),
    url(r'^map/(?P<username>[-_\w]+)/(?P<slug>[-_\w]+)/$', views.MapOldUrl.as_view(), name='map_old_url'),
    url(r'^map/anonymous-edit/(?P<signature>.+)$', views.MapAnonymousEditUrl.as_view(), name='map_anonymous_edit_url'),
    url(r'^m/(?P<pk>\d+)/$', views.MapShortUrl.as_view(), name='map_short_url'),
    url(r'^pictogram/json/$', views.PictogramJSONList.as_view(), name='pictogram_list_json'),
)
urlpatterns += decorated_patterns('', [cache_control(must_revalidate=True), ],
    url(r'^datalayer/(?P<pk>[\d]+)/$', views.DataLayerView.as_view(), name='datalayer_view'),
)
urlpatterns += decorated_patterns('', [ensure_csrf_cookie, ],
    url(r'^map/(?P<slug>[-_\w]+)_(?P<pk>\d+)$', views.MapView.as_view(), name='map'),
    url(r'^map/new/$', views.MapNew.as_view(), name='map_new'),
)
urlpatterns += decorated_patterns('', [login_required_if_not_anonymous_allowed, never_cache, ],
    url(r'^map/create/$', views.MapCreate.as_view(), name='map_create'),
)
urlpatterns += decorated_patterns('', [map_permissions_check, never_cache, ],
    url(r'^map/(?P<map_id>[\d]+)/update/settings/$', views.MapUpdate.as_view(), name='map_update'),
    url(r'^map/(?P<map_id>[\d]+)/update/permissions/$', views.UpdateMapPermissions.as_view(), name='map_update_permissions'),
    url(r'^map/(?P<map_id>[\d]+)/update/delete/$', views.MapDelete.as_view(), name='map_delete'),
    url(r'^map/(?P<map_id>[\d]+)/update/clone/$', views.MapClone.as_view(), name='map_clone'),
    url(r'^map/(?P<map_id>[\d]+)/datalayer/create/$', views.DataLayerCreate.as_view(), name='datalayer_create'),
    url(r'^map/(?P<map_id>[\d]+)/datalayer/update/(?P<pk>\d+)/$', views.DataLayerUpdate.as_view(), name='datalayer_update'),
    url(r'^map/(?P<map_id>[\d]+)/datalayer/delete/(?P<pk>\d+)/$', views.DataLayerDelete.as_view(), name='datalayer_delete'),
)
