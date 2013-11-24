# -*- coding: utf-8 -*-

import simplejson
import os

from itertools import chain

from django.contrib.gis.db import models
from django.db.models import get_model as dj_get_model
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.signing import Signer
from django.contrib import messages
from django.template.defaultfilters import slugify
from django.core.files.base import File

from .fields import DictField


class NamedModel(models.Model):
    name = models.CharField(max_length=200, verbose_name=_("name"))

    class Meta:
        abstract = True
        ordering = ('name', )

    def __unicode__(self):
        return self.name


class Licence(NamedModel):
    """
    The licence one map is published on.
    """
    details = models.URLField(
        verbose_name=_('details'),
        help_text=_('Link to a page where the licence is detailed.')
    )

    @classmethod
    def get_default(cls):
        """
        Returns a default Licence, creates it if it doesn't exist.
        Needed to prevent a licence deletion from deleting all the linked
        maps.
        """
        return cls.objects.get_or_create(
            # can't use ugettext_lazy for database storage, see #13965
            name=getattr(settings, "LEAFLET_STORAGE_DEFAULT_LICENCE_NAME", ugettext('No licence set'))
        )[0]

    @property
    def json(self):
        return {
            'name': self.name,
            'url': self.details
        }


class TileLayer(NamedModel):
    url_template = models.CharField(
        max_length=200,
        help_text=_("URL template using OSM tile format")
    )
    minZoom = models.IntegerField(default=0)
    maxZoom = models.IntegerField(default=18)
    attribution = models.CharField(max_length=300)
    rank = models.SmallIntegerField(
        blank=True,
        null=True,
        help_text=_('Order of the tilelayers in the edit box')
    )

    @property
    def json(self):
        return dict((field.name, getattr(self, field.name)) for field in self._meta.fields)

    @classmethod
    def get_default(cls):
        """
        Returns the default tile layer (used for a map when no layer is set).
        """
        return cls.objects.order_by('rank')[0]  # FIXME, make it administrable

    @classmethod
    def get_list(cls, selected=None):
        l = []
        for t in cls.objects.all():
            fields = t.json
            if selected and selected.pk == t.pk:
                fields['selected'] = True
            l.append(fields)
        return l

    class Meta:
        ordering = ('rank', 'name', )


class Map(NamedModel):
    """
    A single thematical map.
    """
    ANONYMOUS = 1
    EDITORS = 2
    OWNER = 3
    EDIT_STATUS = (
        (ANONYMOUS, _('Everyone can edit')),
        (EDITORS, _('Only editors can edit')),
        (OWNER, _('Only owner can edit')),
    )
    slug = models.SlugField(db_index=True)
    description = models.TextField(blank=True, null=True, verbose_name=_("description"))
    center = models.PointField(geography=True, verbose_name=_("center"))
    zoom = models.IntegerField(default=7, verbose_name=_("zoom"))
    locate = models.BooleanField(default=False, verbose_name=_("locate"), help_text=_("Locate user on load?"))
    licence = models.ForeignKey(
        Licence,
        help_text=_("Choose the map licence."),
        verbose_name=_('licence'),
        on_delete=models.SET_DEFAULT,
        default=Licence.get_default
    )
    modified_at = models.DateTimeField(auto_now=True)
    tilelayer = models.ForeignKey(TileLayer, blank=True, null=True, related_name="maps",  verbose_name=_("background"))
    owner = models.ForeignKey(User, blank=True, null=True, related_name="owned_maps", verbose_name=_("owner"))
    editors = models.ManyToManyField(User, blank=True, verbose_name=_("editors"))
    edit_status = models.SmallIntegerField(choices=EDIT_STATUS, default=OWNER, verbose_name=_("edit status"))
    settings = DictField(blank=True, null=True, verbose_name=_("settings"))

    objects = models.GeoManager()

    @property
    def geojson(self):
        #transitional
        settings = self.settings
        if not "properties" in settings:
            settings["properties"] = dict(self.settings)
            settings['properties']['zoom'] = self.zoom
            settings['properties']['name'] = self.name
            settings['properties']['description'] = self.description
            if self.tilelayer:
                settings['properties']['tilelayer'] = self.tilelayer.json
            if self.licence:
                settings['properties']['licence'] = self.licence.json
        if not "geometry" in settings:
            settings["geometry"] = simplejson.loads(self.center.geojson)
        return settings

    def get_absolute_url(self):
        return reverse("map", kwargs={'slug': self.slug, 'pk': self.pk})

    def get_anonymous_edit_url(self):
        signer = Signer()
        signature = signer.sign(self.pk)
        return reverse('map_anonymous_edit_url', kwargs={'signature': signature})

    def is_anonymous_owner(self, request):
        if self.owner:
            # edit cookies are only valid while map hasn't owner
            return False
        key, value = self.signed_cookie_elements
        try:
            has_anonymous_cookie = int(request.get_signed_cookie(key, False)) == value
        except ValueError:
            has_anonymous_cookie = False
        return has_anonymous_cookie

    def can_edit(self, user=None, request=None):
        """
        Define if a user can edit or not the instance, according to his account
        or the request.
        """
        can = False
        if request and not self.owner:
            if (getattr(settings, "LEAFLET_STORAGE_ALLOW_ANONYMOUS", False)
                    and self.is_anonymous_owner(request)):
                can = True
                if user and user.is_authenticated():
                    # if user is authenticated, attach as owner
                    self.owner = user
                    self.save()
                    msg = _("Your anonymous map has been attached to your account %s" % user)
                    messages.info(request, msg)
        elif self.edit_status == self.ANONYMOUS:
            can = True
        elif not user.is_authenticated():
            pass
        elif user == self.owner:
            can = True
        elif self.edit_status == self.EDITORS and user in self.editors.all():
            can = True
        return can

    @property
    def signed_cookie_elements(self):
        return ('anonymous_owner|%s' % self.pk, self.pk)

    def get_tilelayer(self):
        return self.tilelayer or TileLayer.get_default()

    def clone(self, **kwargs):
        new = self.__class__.objects.get(pk=self.pk)
        new.pk = None
        new.name = u"%s %s" % (_("Clone of"), self.name)
        if "owner" in kwargs:
            # can be None in case of anonymous cloning
            new.owner = kwargs["owner"]
        new.save()
        for editor in self.editors.all():
            new.editors.add(editor)
        for datalayer in self.datalayer_set.all():
            datalayer.clone(map_inst=new)
        return new


class Pictogram(NamedModel):
    """
    An image added to an icon of the map.
    """
    attribution = models.CharField(max_length=300)
    pictogram = models.ImageField(upload_to="pictogram")

    @property
    def json(self):
        return {
            "id": self.pk,
            "attribution": self.attribution,
            "name": self.name,
            "src": self.pictogram.url
        }


class IconConfigMixin(models.Model):

    ICON_CLASS = (
        ('Default', 'Default'),
        ('Circle', 'Circle'),
        ('Drop', 'Drop'),
        ('Ball', 'Ball'),
    )
    pictogram = models.ForeignKey(
        Pictogram,
        null=True,
        blank=True,
        verbose_name=_("pictogram")
    )
    icon_class = models.CharField(
        null=True,
        blank=True,
        choices=ICON_CLASS,
        max_length=32,
        verbose_name=_("icon type"),
        help_text=_("Choose the style of the marker.")
    )

    class Meta:
        abstract = True

    @property
    def icon(self):
        # All the features are processed the same way by vectoformats
        # so they need to share all exported properties
        return {
            "iconClass": self.icon_class,
            "iconUrl": self.pictogram.pictogram.url if self.pictogram else None
        }


class DataLayer(NamedModel, IconConfigMixin):
    """
    Layer to store Features in.
    """
    def upload_to(instance, filename):
        path = ["datalayer", str(instance.map.pk)[-1]]
        if len(str(instance.map.pk)) > 1:
            path.append(str(instance.map.pk)[-2])
        path.append(str(instance.map.pk))
        path.append("%s.geojson" % (slugify(instance.name) or "untitled"))
        return os.path.join(*path)
    map = models.ForeignKey(Map)
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("description")
    )
    options = DictField(blank=True, null=True, verbose_name=_("options"))
    geojson = models.FileField(upload_to=upload_to, blank=True, null=True)
    display_on_load = models.BooleanField(
        default=False,
        verbose_name=_("display on load"),
        help_text=_("Display this layer on load.")
    )

    @property
    def metadata(self):
        return {
            "name": self.name,
            "id": self.pk,
            "displayOnLoad": self.display_on_load
        }

    def to_geojson(self):
        # this method is transitional
        data = self.options
        data['id'] = self.pk
        data['name'] = self.name
        data['description'] = self.description
        data.update(self.icon)
        return {
            'type': 'FeatureCollection',
            'features': [f.to_geojson() for f in self.features],
            '_storage': data
        }

    @property
    def features(self):
        if not hasattr(self, "_features"):
            filters = {
                "datalayer": self
            }
            markers = get_model("Marker").objects.filter(**filters)
            polylines = get_model("Polyline").objects.filter(**filters)
            polygons = get_model("Polygon").objects.filter(**filters)
            self._features = sorted(chain(markers, polylines, polygons), key=lambda i: i.name)
        return self._features

    @classmethod
    def create_default(cls, map_inst):
        return DataLayer.objects.create(
            map=map_inst,
            name=getattr(settings, "LEAFLET_STORAGE_DEFAULT_LAYER_NAME", _("Layer 1")),
            display_on_load=True
        )

    def clone(self, map_inst=None):
        new = self.__class__.objects.get(pk=self.pk)
        new.pk = None
        if map_inst:
            new.map = map_inst
        new.geojson = File(new.geojson.file.file)
        new.save()
        return new


class BaseFeature(NamedModel):

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("description")
    )
    datalayer = models.ForeignKey(DataLayer, verbose_name=_("layer"))
    options = DictField(blank=True, null=True, verbose_name=_("options"))

    objects = models.GeoManager()

    @property
    def icon(self):
        # All the features are processed the same way by vectoformats
        # so they need to share all exported properties
        return {}

    @property
    def color(self):
        return self.options['color'] if 'color' in self.options else None

    def clone(self, datalayer=None):
        new = self.__class__.objects.get(pk=self.pk)
        new.pk = None
        if datalayer:
            new.datalayer = datalayer
        new.save()
        return new

    def to_geojson(self):
        # transitional method
        properties = {'_storage_options': self.options}
        properties['_storage_options'].update(self.icon)
        properties.update({
            'name': self.name,
            'description': self.description,
        })
        return {
            'type': 'Feature',
            'geometry': {
                'type': self.latlng.geom_type,
                'coordinates': self.latlng.coords
            },
            'properties': properties
        }

    class Meta:
        abstract = True


class AbstractMarker(IconConfigMixin, BaseFeature):
    """
    Point of interest.
    """
    latlng = models.PointField(geography=True)

    class Meta:
        abstract = True
        ordering = ('name', )


class AbstractPolyline(BaseFeature):
    latlng = models.LineStringField(geography=True)

    class Meta:
        abstract = True
        ordering = ('name', )


class AbstractPolygon(BaseFeature):
    latlng = models.PolygonField(geography=True)

    class Meta:
        abstract = True
        ordering = ('name', )


# ############## #
# Default Models #
# ############## #

class Marker(AbstractMarker):
    pass


class Polyline(AbstractPolyline):
    pass


class Polygon(AbstractPolygon):
    pass


# ###### #
# Getter #
# ###### #


def get_model(name):
    """
    Example of settings:
    LEAFLET_STORAGE_MODELS = {
        "Marker": ('app_name', 'ModelName'),
    }
    """
    LEAFLET_STORAGE_MODELS = getattr(settings, "LEAFLET_STORAGE_MODELS", {})
    if not name in LEAFLET_STORAGE_MODELS:
        model = globals()[name]
    else:
        model = dj_get_model(*LEAFLET_STORAGE_MODELS[name])
    return model
