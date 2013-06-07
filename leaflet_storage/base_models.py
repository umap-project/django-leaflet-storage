# -*- coding: utf-8 -*-

from django.contrib.gis.db import models
from django.db.models import get_model as dj_get_model
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.signing import Signer
from django.contrib import messages

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


class TileLayer(NamedModel):
    url_template = models.CharField(
        max_length=200,
        help_text=_("URL template using OSM tile format")
    )
    minZoom = models.IntegerField(default=0)
    maxZoom = models.IntegerField(default=18)
    attribution = models.CharField(max_length=300)

    @property
    def json(self):
        return dict((field.name, getattr(self, field.name)) for field in self._meta.fields)

    @classmethod
    def get_default(cls):
        """
        Returns the default tile layer (used for a map when no layer is set).
        """
        return cls.objects.order_by('pk')[0]  # FIXME, make it administrable


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
    tilelayers = models.ManyToManyField(TileLayer, through="MapToTileLayer")
    owner = models.ForeignKey(User, blank=True, null=True, related_name="owned_maps", verbose_name=_("owner"))
    editors = models.ManyToManyField(User, blank=True, verbose_name=_("editors"))
    edit_status = models.SmallIntegerField(choices=EDIT_STATUS, default=OWNER, verbose_name=_("edit status"))
    settings = DictField(blank=True, null=True, verbose_name=_("settings"))

    objects = models.GeoManager()

    @property
    def tilelayers_data(self):
        tilelayers_data = []
        for rank, m2t in enumerate(MapToTileLayer.objects.filter(map=self), start=1):
            tilelayers_data.append({
                "tilelayer": m2t.tilelayer.json,
                "rank": rank
            })
        return tilelayers_data

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


class MapToTileLayer(models.Model):
    tilelayer = models.ForeignKey(TileLayer)
    map = models.ForeignKey(Map)
    rank = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['rank', 'tilelayer__name']


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


class Category(NamedModel, IconConfigMixin):
    """
    Category of a Feature.
    """
    map = models.ForeignKey(Map)
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("description")
    )
    options = DictField(blank=True, null=True, verbose_name=_("options"))
    display_on_load = models.BooleanField(
        default=False,
        verbose_name=_("display on load"),
        help_text=_("Display this category on load.")
    )

    @property
    def json(self):
        return {
            "name": self.name,
            "pk": self.pk,
            "pictogram_url": self.pictogram.pictogram.url if self.pictogram else None,
            "icon_class": self.icon_class,
            "display_on_load": self.display_on_load,
            "options": self.options,
        }

    @property
    def features(self):
        if not hasattr(self, "_features"):
            filters = {
                "category": self
            }
            markers = get_model("Marker").objects.filter(**filters)
            polylines = get_model("Polyline").objects.filter(**filters)
            polygons = get_model("Polygon").objects.filter(**filters)
            self._features = list(markers) + list(polylines) + list(polygons)
        return self._features

    @classmethod
    def create_default(cls, map_inst):
        return Category.objects.create(
            map=map_inst,
            name=getattr(settings, "LEAFLET_STORAGE_DEFAULT_CATEGORY_NAME", _("My data")),
            display_on_load=True
        )


class BaseFeature(NamedModel):

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("description")
    )
    category = models.ForeignKey(Category, verbose_name=_("category"))
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

    class Meta:
        abstract = True


class AbstractMarker(BaseFeature, IconConfigMixin):
    """
    Point of interest.
    """
    latlng = models.PointField(geography=True)

    @property
    def icon(self):
        # All the features are processed the same way by vectoformats
        # so they need to share all exported properties
        return {
            "class": self.icon_class,
            "url": self.pictogram.pictogram.url if self.pictogram else None
        }

    class Meta:
        abstract = True


class AbstractPolyline(BaseFeature):
    latlng = models.LineStringField(geography=True)

    class Meta:
        abstract = True


class AbstractPolygon(BaseFeature):
    latlng = models.PolygonField(geography=True)

    class Meta:
        abstract = True


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
