from django.utils import simplejson
from django import template
from django.conf import settings

from ..models import DataLayer, TileLayer
from ..views import _urls_for_js

register = template.Library()


@register.inclusion_tag('leaflet_storage/css.html')
def leaflet_storage_css():
    return {
        "STATIC_URL": settings.STATIC_URL
    }


@register.inclusion_tag('leaflet_storage/js.html')
def leaflet_storage_js(locale=None):
    return {
        "STATIC_URL": settings.STATIC_URL,
        "locale": locale
    }


@register.inclusion_tag('leaflet_storage/map_fragment.html')
def map_fragment(map_instance, **kwargs):
    layers = DataLayer.objects.filter(map=map_instance)
    datalayer_data = [c.metadata for c in layers]
    tilelayers = TileLayer.get_list()  # TODO: no need to all
    map_settings = map_instance.settings
    if not "properties" in map_settings:
        map_settings['properties'] = {}
    map_settings['properties'].update({
        'tilelayers': tilelayers,
        'datalayers': datalayer_data,
        'urls': _urls_for_js(),
        'STATIC_URL': settings.STATIC_URL,
        "allowEdit": False,
        'hash': False,
        'attributionControl': False,
        'scrollWheelZoom': False,
        'datalayersControl': False,
        'zoomControl': False,
        'storageAttributionControl': False,
        'moreControl': False,
        'scaleControl': False,
        'miniMap': False,
        'storage_id': map_instance.pk,
        'onLoadPanel': "none",
        'captionBar': False,
        'default_iconUrl': "%sstorage/src/img/marker.png" % settings.STATIC_URL,
        'slideshow': {}
    })
    map_settings['properties'].update(kwargs)
    return {
        "map_settings": simplejson.dumps(map_settings),
        "map": map_instance
    }


@register.simple_tag
def tilelayer_preview(tilelayer):
    """
    Return an <img> tag with a tile of the tilelayer.
    """
    output = '<img src="{src}" alt="{alt}" title="{title}" />'
    url = tilelayer.url_template.format(s="a", z=9, x=265, y=181)
    output = output.format(src=url, alt=tilelayer.name, title=tilelayer.name)
    return output


@register.filter
def notag(s):
    return s.replace('<', '&lt;')
