# -*- coding:utf-8 -*-

import os
import hashlib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as do_logout
from django.contrib.auth import get_user_model
from django.core.signing import Signer, BadSignature
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseRedirect, CompatibleStreamingHttpResponse,
                         HttpResponsePermanentRedirect)
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.views.generic import View
from django.views.generic import DetailView
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import ListView
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils.http import http_date
from django.middleware.gzip import re_accepts_gzip
from django.utils.translation import to_locale

from .models import Map, DataLayer, TileLayer, Pictogram, Licence
from .utils import get_uri_template, gzip_file
from .forms import (DataLayerForm, UpdateMapPermissionsForm, MapSettingsForm,
                    AnonymousMapPermissionsForm, DEFAULT_LATITUDE,
                    DEFAULT_LONGITUDE, FlatErrorList)

User = get_user_model()
ANONYMOUS_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # One month


# ############## #
#     Utils      #
# ############## #

def _urls_for_js(urls=None):
    """
    Return templated URLs prepared for javascript.
    """
    if urls is None:
        # prevent circular import
        from .urls import urlpatterns
        urls = [url.name for url in urlpatterns if getattr(url, 'name', None)]
    urls = dict(zip(urls, [get_uri_template(url) for url in urls]))
    urls.update(getattr(settings, 'LEAFLET_STORAGE_EXTRA_URLS', {}))
    return urls


def render_to_json(templates, response_kwargs, context, request):
    """
    Generate a JSON HttpResponse with rendered template HTML.
    """
    html = render_to_string(
        templates,
        response_kwargs,
        RequestContext(request, context)
    )
    _json = simplejson.dumps({
        "html": html
    })
    return HttpResponse(_json)


def simple_json_response(**kwargs):
    return HttpResponse(simplejson.dumps(kwargs))


# ############## #
#      Map       #
# ############## #


class FormLessEditMixin(object):
    http_method_names = [u'post', ]

    def form_invalid(self, form):
        return simple_json_response(errors=form.errors, error=unicode(form.errors))

    def get_form(self, form_class):
        kwargs = self.get_form_kwargs()
        kwargs['error_class'] = FlatErrorList
        return form_class(**kwargs)


class MapDetailMixin(object):

    model = Map

    def get_context_data(self, **kwargs):
        context = super(MapDetailMixin, self).get_context_data(**kwargs)
        properties = {}
        properties['datalayers'] = self.get_datalayers()
        properties['urls'] = _urls_for_js()
        properties['tilelayers'] = self.get_tilelayers()
        if self.get_short_url():
            properties['shortUrl'] = self.get_short_url()

        if settings.USE_I18N:
            locale = settings.LANGUAGE_CODE
            # Check attr in case the middleware is not active
            if hasattr(self.request, "LANGUAGE_CODE"):
                locale = self.request.LANGUAGE_CODE
            locale = to_locale(locale)
            properties['locale'] = locale
            context['locale'] = locale
        properties['allowEdit'] = self.is_edit_allowed()
        properties["default_iconUrl"] = "%sstorage/src/img/marker.png" % settings.STATIC_URL
        properties['storage_id'] = self.get_storage_id()
        properties['licences'] = dict((l.name, l.json) for l in Licence.objects.all())
        # if properties['locateOnLoad']:
        #     properties['locate'] = {
        #         'setView': True,
        #         'enableHighAccuracy': True,
        #         'timeout': 3000
        #     }
        map_settings = self.get_geojson()
        if not "properties" in map_settings:
            map_settings['properties'] = {}
        map_settings['properties'].update(properties)
        context['map_settings'] = simplejson.dumps(map_settings, indent=settings.DEBUG)
        return context

    def get_tilelayers(self):
        return TileLayer.get_list(selected=TileLayer.get_default())

    def get_datalayers(self):
        return []

    def is_edit_allowed(self):
        return True

    def get_storage_id(self):
        return None

    def get_geojson(self):
        return {
            "geometry": {
                "coordinates": [DEFAULT_LONGITUDE, DEFAULT_LATITUDE],
                "type": "Point"
            },
            "properties": {
                "zoom": getattr(settings, 'LEAFLET_ZOOM', 6)
            }
        }

    def get_short_url(self):
        return None


class MapView(MapDetailMixin, DetailView):

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        canonical = self.get_canonical_url()
        if not request.path == canonical:
            canonical = "?".join([canonical, request.META['QUERY_STRING']])
            return HttpResponsePermanentRedirect(canonical)
        if not self.object.can_view(request):
            return HttpResponseForbidden('Forbidden')
        return super(MapView, self).get(request, *args, **kwargs)

    def get_canonical_url(self):
        return self.object.get_absolute_url()

    def get_datalayers(self):
        datalayers = DataLayer.objects.filter(map=self.object)  # TODO manage state
        return [l.metadata for l in datalayers]

    def get_tilelayers(self):
        return TileLayer.get_list(selected=self.object.get_tilelayer())

    def is_edit_allowed(self):
        return self.object.can_edit(self.request.user, self.request)

    def get_storage_id(self):
        return self.object.pk

    def get_short_url(self):
        shortUrl = None
        if hasattr(settings, 'SHORT_SITE_URL'):
            short_url_name = getattr(settings, 'MAP_SHORT_URL_NAME', 'map_short_url')
            short_path = reverse_lazy(short_url_name, kwargs={'pk': self.object.pk})
            shortUrl = "%s%s" % (settings.SHORT_SITE_URL, short_path)
        return shortUrl

    def get_geojson(self):
        settings = self.object.settings
        if not "properties" in settings:
            settings['properties'] = {}
        if self.object.owner:
            settings['properties']['author'] = {
                'name': self.object.owner.get_username(),
                'link': reverse('user_maps', args=(self.object.owner.get_username(), ))
            }
        return settings


class MapViewGeoJSON(MapView):

    def get_canonical_url(self):
        return reverse('map_geojson', args=(self.object.pk, ))

    def render_to_response(self, context, *args, **kwargs):
        return HttpResponse(context['map_settings'])


class MapNew(MapDetailMixin, TemplateView):
    template_name = "leaflet_storage/map_detail.html"


class MapCreate(FormLessEditMixin, CreateView):
    model = Map
    form_class = MapSettingsForm

    def form_valid(self, form):
        if self.request.user.is_authenticated():
            form.instance.owner = self.request.user
        self.object = form.save()
        if not self.request.user.is_authenticated():
            anonymous_url = "%s%s" % (
                settings.SITE_URL,
                self.object.get_anonymous_edit_url()
            )
            msg = _(
                "Your map has been created! If you want to edit this map from "
                "another computer, please use this link: %(anonymous_url)s"
                % {"anonymous_url": anonymous_url}
            )
        else:
            msg = _("Congratulations, your map has been created!")
        response = simple_json_response(
            id=self.object.pk,
            url=self.object.get_absolute_url(),
            info=msg
        )
        if not self.request.user.is_authenticated():
            key, value = self.object.signed_cookie_elements
            response.set_signed_cookie(
                key=key,
                value=value,
                max_age=ANONYMOUS_COOKIE_MAX_AGE
            )
        return response


class MapUpdate(FormLessEditMixin, UpdateView):
    model = Map
    form_class = MapSettingsForm
    pk_url_kwarg = 'map_id'

    def form_valid(self, form):
        self.object.settings = form.cleaned_data["settings"]
        self.object.save()
        return simple_json_response(
            id=self.object.pk,
            url=self.object.get_absolute_url(),
            info=_("Map has been updated!")
        )


class UpdateMapPermissions(UpdateView):
    template_name = "leaflet_storage/map_update_permissions.html"
    model = Map
    pk_url_kwarg = 'map_id'

    def get_form_class(self):
        if self.object.owner:
            return UpdateMapPermissionsForm
        else:
            return AnonymousMapPermissionsForm

    def get_form(self, form_class):
        form = super(UpdateMapPermissions, self).get_form(form_class)
        user = self.request.user
        if self.object.owner and not user == self.object.owner:
            del form.fields['edit_status']
            del form.fields['share_status']
            del form.fields['owner']
        return form

    def form_valid(self, form):
        self.object = form.save()
        return simple_json_response(info=_("Map editors updated with success!"))

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)


class MapDelete(DeleteView):
    model = Map
    pk_url_kwarg = "map_id"

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        if self.object.owner and self.request.user != self.object.owner:
            return HttpResponseForbidden(_('Only its owner can delete the map.'))
        if not self.object.owner and not self.object.is_anonymous_owner(self.request):
            return HttpResponseForbidden('Forbidden.')
        self.object.delete()
        return simple_json_response(redirect="/")


class MapClone(View):

    def post(self, *args, **kwargs):
        if not getattr(settings, "LEAFLET_STORAGE_ALLOW_ANONYMOUS", False) \
           and not self.request.user.is_authenticated():
            return HttpResponseForbidden('Forbidden')
        owner = self.request.user if self.request.user.is_authenticated() else None
        self.object = kwargs['map_inst'].clone(owner=owner)
        response = simple_json_response(redirect=self.object.get_absolute_url())
        if not self.request.user.is_authenticated():
            key, value = self.object.signed_cookie_elements
            response.set_signed_cookie(
                key=key,
                value=value,
                max_age=ANONYMOUS_COOKIE_MAX_AGE
            )
            anonymous_url = "%s%s" % (
                settings.SITE_URL,
                self.object.get_anonymous_edit_url()
            )
            msg = _(
                "Your map has been cloned! If you want to edit this map from "
                "another computer, please use this link: %(anonymous_url)s"
                % {"anonymous_url": anonymous_url}
            )
        else:
            msg = _("Congratulations, your map has been cloned!")
        messages.info(self.request, msg)
        return response


class MapShortUrl(RedirectView):
    query_string = True

    def get_redirect_url(self, **kwargs):
        map_inst = get_object_or_404(Map, pk=kwargs['pk'])
        url = map_inst.get_absolute_url()
        if self.query_string:
            args = self.request.META.get('QUERY_STRING', '')
            if args:
                url = "%s?%s" % (url, args)
        return url


class MapOldUrl(RedirectView):
    """
    Handle map URLs from before anonymous allowing.
    """
    query_string = True

    def get_redirect_url(self, **kwargs):
        owner = get_object_or_404(User, username=self.kwargs['username'])
        map_inst = get_object_or_404(Map, slug=self.kwargs['slug'], owner=owner)
        url = map_inst.get_absolute_url()
        if self.query_string:
            args = self.request.META.get('QUERY_STRING', '')
            if args:
                url = "%s?%s" % (url, args)
        return url


class MapAnonymousEditUrl(RedirectView):

    def get(self, request, *args, **kwargs):
        signer = Signer()
        try:
            pk = signer.unsign(self.kwargs['signature'])
        except BadSignature:
            return HttpResponseForbidden('Bad Signature')
        else:
            map_inst = get_object_or_404(Map, pk=pk)
            url = map_inst.get_absolute_url()
            response = HttpResponseRedirect(url)
            if not map_inst.owner:
                key, value = map_inst.signed_cookie_elements
                response.set_signed_cookie(
                    key=key,
                    value=value,
                    max_age=ANONYMOUS_COOKIE_MAX_AGE
                )
            return response


# ############## #
#    DataLayer   #
# ############## #


class GZipMixin(object):

    EXT = '.gz'

    def path(self):
        """
        Serve gzip file if client accept it.
        Generate or update the gzip file if needed.
        """
        path = self.object.geojson.path
        statobj = os.stat(path)
        ae = self.request.META.get('HTTP_ACCEPT_ENCODING', '')
        if re_accepts_gzip.search(ae) and getattr(settings, 'LEAFLET_STORAGE_GZIP', True):
            gzip_path = "{path}{ext}".format(path=path, ext=self.EXT)
            up_to_date = True
            if not os.path.exists(gzip_path):
                up_to_date = False
            else:
                gzip_statobj = os.stat(gzip_path)
                if statobj.st_mtime > gzip_statobj.st_mtime:
                    up_to_date = False
            if not up_to_date:
                gzip_file(path, gzip_path)
            path = gzip_path
        return path

    def etag(self):
        path = self.path()
        with open(path) as f:
            return hashlib.md5(f.read()).hexdigest()


class DataLayerView(GZipMixin, BaseDetailView):
    model = DataLayer

    def render_to_response(self, context, **response_kwargs):
        response = None
        path = self.path()

        if getattr(settings, 'LEAFLET_STORAGE_XSENDFILE_HEADER', None):
            response = HttpResponse()
            response[settings.LEAFLET_STORAGE_XSENDFILE_HEADER] = path
        else:
            # TODO IMS
            statobj = os.stat(path)
            response = CompatibleStreamingHttpResponse(
                open(path, 'rb'),
                content_type='application/json'
            )
            response["Last-Modified"] = http_date(statobj.st_mtime)
            response['ETag'] = '%s' % hashlib.md5(response.content).hexdigest()
            response['Content-Length'] = str(len(response.content))
        if path.endswith(self.EXT):
            response['Content-Encoding'] = 'gzip'
        return response


class DataLayerCreate(FormLessEditMixin, GZipMixin, CreateView):
    model = DataLayer
    form_class = DataLayerForm

    def form_valid(self, form):
        form.instance.map = self.kwargs['map_inst']
        self.object = form.save()
        response = simple_json_response(**self.object.metadata)
        response['ETag'] = self.etag()
        return response


class DataLayerUpdate(FormLessEditMixin, GZipMixin, UpdateView):
    model = DataLayer
    form_class = DataLayerForm

    def form_valid(self, form):
        self.object = form.save()
        response = simple_json_response(**self.object.metadata)
        response['ETag'] = self.etag()
        return response

    def if_match(self):
        """Optimistic concurrency control."""
        match = True
        if_match = self.request.META.get('HTTP_IF_MATCH')
        if if_match:
                etag = self.etag()
                if etag != if_match:
                    match = False
        return match

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.map != self.kwargs['map_inst']:
            return HttpResponseForbidden('Route to nowhere')
        if not self.if_match():
            return HttpResponse(status=412)
        return super(DataLayerUpdate, self).post(request, *args, **kwargs)


class DataLayerDelete(DeleteView):
    model = DataLayer

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        if self.object.map != self.kwargs['map_inst']:
            return HttpResponseForbidden('Route to nowhere')
        self.object.delete()
        return simple_json_response(info=_("Layer successfully deleted."))


# ############## #
#     Picto      #
# ############## #

class PictogramJSONList(ListView):
    model = Pictogram

    def render_to_response(self, context, **response_kwargs):
        content = [p.json for p in Pictogram.objects.all()]
        return simple_json_response(pictogram_list=content)


# ############## #
#     Generic    #
# ############## #

def logout(request):
    do_logout(request)
    return simple_json_response(redirect="/")


class LoginPopupEnd(TemplateView):
    """
    End of a loggin process in popup.
    Basically close the popup.
    """
    template_name = "leaflet_storage/login_popup_end.html"
