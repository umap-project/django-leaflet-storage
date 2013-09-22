from django.utils import simplejson
from django import template
from django.conf import settings

from ..models import DataLayer
from ..views import _urls_for_js

register = template.Library()


@register.inclusion_tag('leaflet_storage/css.html')
def leaflet_storage_css():
    return {
        "STATIC_URL": settings.STATIC_URL
    }


@register.inclusion_tag('leaflet_storage/js.html')
def leaflet_storage_js():
    return {
        "STATIC_URL": settings.STATIC_URL
    }


@register.inclusion_tag('leaflet_storage/map_fragment.html')
def map_fragment(map_instance):
    layers = DataLayer.objects.filter(map=map_instance)
    datalayer_data = [c.json for c in layers]
    tilelayer = map_instance.get_tilelayer().json
    tilelayer['selected'] = True
    return {
        'map': map_instance,
        'tilelayer': simplejson.dumps(tilelayer),
        'datalayers': simplejson.dumps(datalayer_data),
        'urls': simplejson.dumps(_urls_for_js()),
        'STATIC_URL': settings.STATIC_URL,
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
