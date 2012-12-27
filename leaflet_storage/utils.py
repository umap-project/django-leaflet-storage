from django.core.urlresolvers import get_resolver
from django.core.urlresolvers import RegexURLPattern, RegexURLResolver
from django.conf.urls.defaults import patterns

from VectorFormats.Formats import Django, GeoJSON


def get_uri_template(urlname, args=None, prefix=""):
    '''
    Utility function to return an URI Template from a named URL in django
    Copied from django-digitalpaper.

    Restrictions:
    - Only supports named urls! i.e. url(... name="toto")
    - Only support one namespace level
    - Only returns the first URL possibility.
    - Supports multiple pattern possibilities (i.e., patterns with
      non-capturing parenthesis in them) by trying to find a pattern
      whose optional parameters match those you specified (a parameter
      is considered optional if it doesn't appear in every pattern possibility)
    '''
    def _convert(template, args=None):
        """URI template converter"""
        if not args:
            args = []
        paths = template % dict([p, "{%s}" % p] for p in args)
        return u'%s/%s' % (prefix, paths)

    resolver = get_resolver(None)
    parts = urlname.split(':')
    if len(parts) > 1 and resolver.namespace_dict.has_key(parts[0]):
        namespace = parts[0]
        urlname = parts[1]
        nprefix, resolver = resolver.namespace_dict[namespace]
        prefix = prefix + '/' + nprefix.rstrip('/')
    possibilities = resolver.reverse_dict.getlist(urlname)
    for tmp in possibilities:
        possibility, pattern = tmp[:2]
        if not args:
            # If not args are specified, we only consider the first pattern
            # django gives us
            result, params = possibility[0]
            return _convert(result, params)
        else:
            # If there are optionnal arguments passed, use them to try to find
            # the correct pattern.
            # First, we need to build a list with all the arguments
            seen_params = []
            for result, params in possibility:
                seen_params.append(params)
            # Then build a set to find the common ones, and use it to build the
            # list of all the expected params
            common_params = reduce(lambda x, y: set(x) & set(y), seen_params)
            expected_params = sorted(common_params.union(args))
            # Then loop again over the pattern possibilities and return
            # the first one that strictly match expected params
            for result, params in possibility:
                if sorted(params) == expected_params:
                    return _convert(result, params)
    return None


def instances_to_geojson(instances, geo_field, properties):
    """
    Return a FeatureCollection from Geo instances.
    """
    djf = Django.Django(geodjango=geo_field, properties=properties)
    geoj = GeoJSON.GeoJSON()
    return geoj.encode(djf.decode(instances))


class DecoratedURLPattern(RegexURLPattern):
    def resolve(self, *args, **kwargs):
        result = RegexURLPattern.resolve(self, *args, **kwargs)
        if result:
            result.func = self._decorate_with(result.func)
        return result


def decorated_patterns(prefix, func, *args):
    """
    Utility function to decorate a group of url in urls.py

    Taken from http://djangosnippets.org/snippets/532/ + comments
    See also http://friendpaste.com/6afByRiBB9CMwPft3a6lym

    Example:
    urlpatterns = patterns('',
        url(r'^language/(?P<lang_code>[a-z]+)$', 'ops.common.views.change_language', name='change_language'),

        ) + decorated_patterns('', login_required, url(r'^', include('cms.urls')),
    )
    """
    result = patterns(prefix, *args)
    if func:
        for p in result:
            if isinstance(p, RegexURLPattern):
                p.__class__ = DecoratedURLPattern
                p._decorate_with = func
            elif isinstance(p, RegexURLResolver):
                for pp in p.url_patterns:
                    if isinstance(pp, RegexURLPattern):
                        pp.__class__ = DecoratedURLPattern
                        pp._decorate_with = func

    return result
