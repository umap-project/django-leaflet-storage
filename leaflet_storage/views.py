# -*- coding:utf-8 -*-


from django.conf import settings
from django.db import transaction
from django.contrib import messages
from django.utils import simplejson
from django.core.signing import Signer
from django.db.utils import DatabaseError
from django.template import RequestContext
from django.contrib.auth.models import User
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from django.contrib.gis.geos import GEOSGeometry
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic.list import BaseListView, ListView
from django.contrib.auth import logout as do_logout
from django.template.loader import render_to_string
from django.views.generic.detail import BaseDetailView
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import CreateView, UpdateView, FormView, DeleteView
from django.http import HttpResponse, HttpResponseNotAllowed, Http404, HttpResponseRedirect

from vectorformats.formats import django, geojson

from .models import (Map, Marker, Category, Polyline, TileLayer,
                     MapToTileLayer, Polygon, Pictogram)
from .utils import get_uri_template
from .forms import (QuickMapCreateForm, UpdateMapExtentForm, CategoryForm,
                    UploadDataForm, UpdateMapPermissionsForm, MapSettingsForm,
                    MarkerForm, PolygonForm, PolylineForm, AnonymousMapPermissionsForm,
                    DownloadDataForm)


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
    return dict(zip(urls, [get_uri_template(url) for url in urls]))


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

class GeoJSONMixin(object):

    def geojson(self, context):
        qs = self.get_queryset()
        djf = django.Django(geodjango="latlng", properties=['name', 'category_id', 'options', 'icon'])
        geoj = geojson.GeoJSON()
        return geoj.encode(djf.decode(qs), to_string=False)


class MapView(DetailView):

    model = Map

    def get_int_from_request(self, key, fallback):
        try:
            output = int(self.request.GET[key])
        except (ValueError, KeyError):
            output = fallback
        return output

    def get_context_data(self, **kwargs):
        context = super(MapView, self).get_context_data(**kwargs)
        map_settings = {}
        categories = Category.objects.filter(map=self.object)  # TODO manage state
        category_data = [c.json for c in categories]
        map_settings['categories'] = category_data
        map_settings['urls'] = _urls_for_js()
        tilelayers_data = self.object.tilelayers_data
        map_settings['tilelayers'] = tilelayers_data
        if settings.USE_I18N:
            locale = settings.LANGUAGE_CODE
            # Check attr in case the middleware is not active
            if hasattr(self.request, "LANGUAGE_CODE"):
                locale = self.request.LANGUAGE_CODE
            map_settings['locale'] = locale
        if self.request.user.is_authenticated():
            allow_edit = int(self.object.can_edit(self.request.user, self.request))
        else:
            # Default to 1: display buttons for anonymous, they can
            # login from action process
            allow_edit = 1
        # Precedence to GET param
        allow_edit = self.get_int_from_request("allowEdit", allow_edit)
        map_settings['allowEdit'] = allow_edit
        for name, label, default in MapSettingsForm.SETTINGS:
            value = self.get_int_from_request(name, self.object.settings.get(name, default))
            try:
                value = int(value)
            except ValueError:
                value = default
            map_settings[name] = value
        map_settings["default_iconUrl"] = "%sstorage/src/img/marker.png" % settings.STATIC_URL
        map_settings['center'] = simplejson.loads(self.object.center.geojson)
        map_settings['storage_id'] = self.object.pk
        map_settings['zoom'] = self.object.zoom
        if map_settings['locateOnLoad']:
            map_settings['locate'] = {
                'setView': True,
                'enableHighAccuracy': True,
                'timeout': 3000
            }
        context['map_settings'] = simplejson.dumps(map_settings)
        return context


class MapInfos(DetailView):
    model = Map
    template_name = "leaflet_storage/map_infos.html"
    pk_url_kwarg = 'map_id'

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)


class QuickMapCreate(CreateView):
    model = Map
    form_class = QuickMapCreateForm

    def form_valid(self, form):
        """
        Provide default values, to keep form simple.
        """
        if self.request.user.is_authenticated():
            form.instance.owner = self.request.user
        self.object = form.save()
        layer = TileLayer.get_default()
        MapToTileLayer.objects.create(map=self.object, tilelayer=layer, rank=1)
        Category.create_default(self.object)
        response = simple_json_response(redirect=self.get_success_url())
        if not self.request.user.is_authenticated():
            key, value = self.object.signed_cookie_elements
            response.set_signed_cookie(key, value)
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
            msg = _("Congratulations, your map has been created! To start editing, click on the pen icon.")
        messages.info(self.request, msg)
        return response

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)

    def get_context_data(self, **kwargs):
        kwargs.update({
            'action_url': reverse_lazy('map_add')
        })
        return super(QuickMapCreate, self).get_context_data(**kwargs)


# TODO: factorize with QuickCreate!
class QuickMapUpdate(UpdateView):
    model = Map
    form_class = QuickMapCreateForm
    pk_url_kwarg = 'map_id'

    def form_valid(self, form):
        self.object = form.save()
        return simple_json_response(redirect=self.get_success_url())

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)

    def get_context_data(self, **kwargs):
        kwargs.update({
            'action_url': reverse_lazy('map_update', args=[self.object.pk]),
            'delete_url': reverse_lazy('map_delete', args=[self.object.pk])
        })
        return super(QuickMapUpdate, self).get_context_data(**kwargs)


class UpdateMapExtent(UpdateView):
    model = Map
    form_class = UpdateMapExtentForm
    pk_url_kwarg = 'map_id'

    def form_invalid(self, form):
        return simple_json_response(info=form.errors)

    def form_valid(self, form):
        self.object = form.save()
        return simple_json_response(info=_("Zoom and center updated with success!"))


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
        return form

    def form_valid(self, form):
        self.object = form.save()
        return simple_json_response(info=_("Map editors updated with success!"))

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)


class UpdateMapSettings(UpdateView):
    template_name = "leaflet_storage/map_update_settings.html"
    model = Map
    form_class = MapSettingsForm
    pk_url_kwarg = 'map_id'

    def form_valid(self, form):
        self.object.settings = form.cleaned_data
        self.object.save()
        # We need to reload the page, to make the UI take into account the new
        # settings
        return simple_json_response(redirect=self.object.get_absolute_url())

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)


class UpdateMapTileLayers(TemplateView):
    template_name = "leaflet_storage/map_update_tilelayers.html"
    pk_url_kwarg = 'map_id'

    def get_context_data(self, **kwargs):
        return {
            "tilelayers": TileLayer.objects.all(),
            'map': kwargs['map_inst']
        }

    def post(self, request, *args, **kwargs):
        # TODO: manage with a proper form
        map_inst = kwargs['map_inst']
        # Empty relations (we don't keep trace of unchecked box for now)
        MapToTileLayer.objects.filter(map=map_inst).delete()
        try:
            layer_id = int(request.POST['tilelayer'])
        except (KeyError, ValueError):
            # Don't let a map without tilelayer
            layer = TileLayer.get_default()
            layer_id = layer.pk
        finally:
            # TODO manage rank and multiselection
            MapToTileLayer.objects.create(map=map_inst, tilelayer_id=layer_id)
        return simple_json_response(tilelayers=map_inst.tilelayers_data)

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)


class UploadData(FormView):
    template_name = "leaflet_storage/upload_form.html"
    form_class = UploadDataForm
    pk_url_kwarg = 'map_id'

    def get_form(self, form_class):
        form = super(UploadData, self).get_form(form_class)
        map_inst = self.kwargs['map_inst']
        form.fields['category'].queryset = Category.objects.filter(map=map_inst)
        return form

    def get_context_data(self, **kwargs):
        kwargs.update({
            'action_url': reverse_lazy('upload_data', kwargs={'map_id': self.kwargs['map_id']})
        })
        return super(UploadData, self).get_context_data(**kwargs)

    @transaction.commit_manually
    def form_valid(self, form):
        FEATURE_TO_MODEL = {
            'Point': Marker,
            'LineString': Polyline,
            'Polygon': Polygon
        }
        # Use a tuple to add more sources possible
        # first item is field name
        FIELDS = [
            ('name', 'title'),
            ('description', 'desc'),
            'color'
        ]
        features = (form.cleaned_data.get('data_file')
                   or form.cleaned_data.get('data_url')
                   or form.cleaned_data.get('data_raw'))
        category = form.cleaned_data.get('category')
        counter = 0
        for feature in features:
            sid = transaction.savepoint()
            klass = FEATURE_TO_MODEL.get(feature.geometry['type'], None)
            if not klass:
                continue  # TODO notify user
            # Remove altitude, if there
            try:
                if feature.geometry['type'] == "LineString":
                    feature.geometry['coordinates'] = map(
                        lambda x: x[:2],
                        feature.geometry['coordinates']
                    )
                elif feature.geometry['type'] == "Point":
                    feature.geometry['coordinates'] = feature.geometry['coordinates'][:2]
                elif feature.geometry['type'] == "Polygon":
                    feature.geometry['coordinates'] = map(
                        lambda x: map(lambda y: y[:2], x),
                        feature.geometry['coordinates']
                    )
            except Exception, e:
                print e
                continue
            try:
                latlng = GEOSGeometry(repr(feature.geometry))
            except Exception, e:
                print e
                continue  # TODO notify user
            if latlng.empty:
                continue  # TODO notify user
            kwargs = {
                'latlng': latlng,
                'category': category,
                'name': category.name  # Default
            }
            for field in FIELDS:
                if isinstance(field, tuple):
                    name = field[0]
                    candidates = field
                else:
                    name = field
                    candidates = [field]
                for candidate in candidates:
                    if candidate in feature.properties:
                        value = feature.properties[candidate]
                        if not value:
                            continue
                        if name in klass._meta.get_all_field_names():
                            kwargs[name] = value
                        else:
                            # it's an option
                            if not "options" in kwargs:
                                kwargs['options'] = {}
                            kwargs['options'][name] = value
                        break
            try:
                klass.objects.create(**kwargs)
            except DatabaseError:
                transaction.savepoint_rollback(sid)
                continue  # TODO notify user
            else:
                transaction.savepoint_commit(sid)
            counter += 1
        transaction.commit()
        kwargs = {
            'category': category.json,
            'info': "%d features created!" % counter,
        }
        return simple_json_response(**kwargs)

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)


class DownloadData(GeoJSONMixin, DetailView):

    model = Map
    pk_url_kwarg = 'map_id'

    def get_queryset(self):
        features = []
        for category in self.object.category_set.all():
            features += category.features
        return features

    def get_object(self):
        return get_object_or_404(Map, pk=self.kwargs[self.pk_url_kwarg])

    def render_to_response(self, context):
        response = simple_json_response(**self.geojson(context))
        response['Content-Type'] = "application/json"
        response['Content-Disposition'] = 'attachment; filename="features.json"'
        return response


class EmbedMap(DetailView):
    model = Map
    template_name = "leaflet_storage/map_embed.html"
    pk_url_kwarg = 'map_id'

    def get_context_data(self, **kwargs):
        site_url = (settings.SHORT_SITE_URL if hasattr(settings, 'SHORT_SITE_URL')
                   else settings.SITE_URL if hasattr(settings, 'SITE_URL')
                   else 'http://%s' % self.request.META['HTTP_HOST'])
        iframe_url = map_url = '%s%s' % (site_url, self.object.get_absolute_url())
        qs_kwargs = {
            'allowEdit': 0,
            'embedControl': 0,
            'homeControl': 0,
            'locateControl': 0,
            'jumpToLocationControl': 0,
            'editInOSMControl': 0,
            'scaleControl': 0,
            'miniMap': 0,
        }
        query_string = "&".join("%s=%s" % (k, v) for k, v in qs_kwargs.iteritems())
        iframe_url = "%s?%s" % (iframe_url, query_string)
        map_short_url = "%s%s" % (site_url, reverse_lazy('map_short_url', kwargs={'pk': self.object.pk}))
        kwargs.update({
            'map_url': map_url,
            'iframe_url': iframe_url,
            'map_short_url': map_short_url,
            'download_form': DownloadDataForm()
        })
        return super(EmbedMap, self).get_context_data(**kwargs)

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)


class MapDelete(DeleteView):
    model = Map
    pk_url_kwarg = "map_id"

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        if not self.request.user == self.object.owner:
            return HttpResponseNotAllowed(_('Only its owner can delete the map.'))
        self.object.delete()
        return simple_json_response(redirect="/")

    def get_context_data(self, **kwargs):
        kwargs.update({
            'action_url': reverse_lazy('map_delete', kwargs={'map_id': self.kwargs['map_id']})
        })
        return super(MapDelete, self).get_context_data(**kwargs)


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
        pk = signer.unsign(self.kwargs['signature'])
        map_inst = get_object_or_404(Map, pk=pk)
        url = map_inst.get_absolute_url()
        response = HttpResponseRedirect(url)
        key, value = map_inst.signed_cookie_elements
        response.set_signed_cookie(key, value)
        return response


# ############## #
#    Features    #
# ############## #


class FeatureGeoJSONListView(BaseListView, GeoJSONMixin):

    def get_queryset(self):
        category = get_object_or_404(Category, pk=self.kwargs['category_id'])
        return category.features

    def render_to_response(self, context, **response_kwargs):
        geoj = self.geojson(context)
        return HttpResponse(simplejson.dumps(geoj))


class FeatureView(DetailView):
    context_object_name = "feature"

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)

    def get_template_names(self):
        """
        Add a fallback, but keep the default templates to make it easily
        extendable.
        """
        templates = super(FeatureView, self).get_template_names()
        templates.append("leaflet_storage/feature_detail.html")
        return templates


class FeatureAdd(CreateView):

    def get_success_url(self):
        return reverse_lazy(self.geojson_url, kwargs={"pk": self.object.pk})

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)

    def get_form(self, form_class):
        form = super(FeatureAdd, self).get_form(form_class)
        map_inst = self.kwargs['map_inst']
        categories = Category.objects.filter(map=map_inst)
        form.fields['category'].queryset = categories
        if categories:
            form.fields['category'].initial = categories[0]
        return form

    def get_template_names(self):
        """
        Add a fallback, but keep the default templates to make it easily
        extendable.
        """
        templates = super(FeatureAdd, self).get_template_names()
        templates.append("leaflet_storage/feature_form.html")
        return templates


class FeatureUpdate(UpdateView):

    def get_success_url(self):
        return reverse_lazy(self.geojson_url, kwargs={"pk": self.object.pk})

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)

    def get_context_data(self, **kwargs):
        kwargs.update({
            'delete_url': reverse_lazy(self.delete_url, kwargs={'map_id': self.kwargs['map_id'], 'pk': self.object.pk})
        })
        return super(FeatureUpdate, self).get_context_data(**kwargs)

    # TODO: factorize with FeatureAdd!
    def get_form(self, form_class):
        form = super(FeatureUpdate, self).get_form(form_class)
        map_inst = self.kwargs['map_inst']
        form.fields['category'].queryset = Category.objects.filter(map=map_inst)
        return form

    def get_template_names(self):
        """
        Add a fallback, but keep the default templates to make it easily
        extendable.
        """
        templates = super(FeatureUpdate, self).get_template_names()
        templates.append("leaflet_storage/feature_form.html")
        return templates


class FeatureDelete(DeleteView):
    context_object_name = "feature"
    template_name = "leaflet_storage/feature_confirm_delete.html"

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return simple_json_response(
            #Translators: "feature" is a feature type: Marker, Polyline, Polygon
            info=_("%(feature)s successfully deleted." % {"feature": self.model._meta.verbose_name})
        )


class FeatureGeoJSON(BaseDetailView, GeoJSONMixin):

    def get_queryset(self):
        return self.model.objects.filter(pk=self.kwargs['pk'])

    def render_to_response(self, context):
        collection = self.geojson(context)
        try:
            geoj = collection['features'][0]
        except KeyError:
            return Http404()
        return HttpResponse(simplejson.dumps(geoj))


class MarkerGeoJSON(FeatureGeoJSON):
    model = Marker


class MarkerDelete(FeatureDelete):
    model = Marker


class MarkerView(FeatureView):
    model = Marker


class MarkerUpdate(FeatureUpdate):
    model = Marker
    geojson_url = 'marker_geojson'
    delete_url = "marker_delete"
    form_class = MarkerForm


class MarkerAdd(FeatureAdd):
    model = Marker
    geojson_url = 'marker_geojson'
    form_class = MarkerForm


class PolylineView(FeatureView):
    model = Polyline


class PolylineAdd(FeatureAdd):
    model = Polyline
    geojson_url = 'polyline_geojson'
    form_class = PolylineForm


class PolylineUpdate(FeatureUpdate):
    model = Polyline
    geojson_url = 'polyline_geojson'
    delete_url = "polyline_delete"
    form_class = PolylineForm


class PolylineDelete(FeatureDelete):
    model = Polyline


class PolylineGeoJSON(FeatureGeoJSON):
    model = Polyline


class PolygonView(FeatureView):
    model = Polygon


class PolygonAdd(FeatureAdd):
    model = Polygon
    geojson_url = 'polygon_geojson'
    form_class = PolygonForm


class PolygonUpdate(FeatureUpdate):
    model = Polygon
    geojson_url = 'polygon_geojson'
    delete_url = "polygon_delete"
    form_class = PolygonForm


class PolygonDelete(FeatureDelete):
    model = Polygon


class PolygonGeoJSON(FeatureGeoJSON):
    model = Polygon


# ############## #
#    Category    #
# ############## #

class CategoryCreate(CreateView):
    model = Category
    form_class = CategoryForm

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)

    def get_context_data(self, **kwargs):
        kwargs.update({
            'action_url': reverse_lazy('category_add', kwargs={'map_id': self.kwargs['map_id']})
        })
        return super(CategoryCreate, self).get_context_data(**kwargs)

    def get_initial(self):
        initial = super(CategoryCreate, self).get_initial()
        map_inst = self.kwargs['map_inst']
        initial.update({
            "map": map_inst
        })
        return initial

    def form_valid(self, form):
        self.object = form.save()
        return simple_json_response(category=self.object.json)


class CategoryUpdate(UpdateView):
    model = Category
    form_class = CategoryForm

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)

    def get_context_data(self, **kwargs):
        kwargs.update({
            'action_url': reverse_lazy('category_update', kwargs={'map_id': self.kwargs['map_id'], 'pk': self.object.pk}),
            'delete_url': reverse_lazy('category_delete', kwargs={'map_id': self.kwargs['map_id'], 'pk': self.object.pk})
        })
        return super(CategoryUpdate, self).get_context_data(**kwargs)

    def form_valid(self, form):
        self.object = form.save()
        return simple_json_response(category=self.object.json)


class CategoryDelete(DeleteView):
    model = Category

    def render_to_response(self, context, **response_kwargs):
        return render_to_json(self.get_template_names(), response_kwargs, context, self.request)

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return simple_json_response(info=_("Category successfully deleted."))


# ############## #
#     Picto      #
# ############## #

class PictogramJsonList(ListView):
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
