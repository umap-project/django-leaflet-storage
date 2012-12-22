from django.utils import simplejson
from django import template
from django.conf import settings

from ..models import Category
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
    tilelayer_data = {
        'tilelayer': map_instance.tilelayers.all()[0].json,
        "rank": 1
    }
    categories = Category.objects.filter(map=map_instance, preset=True)
    category_data = [c.json for c in categories]
    return {
        'map': map_instance,
        'tilelayer': simplejson.dumps(tilelayer_data),
        'categories': simplejson.dumps(category_data),
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
