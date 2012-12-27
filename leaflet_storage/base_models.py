# -*- coding: utf-8 -*-

from django.contrib.gis.db import models
from django.db.models import get_model as dj_get_model
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _


class NamedModel(models.Model):
    name = models.CharField(max_length=200, verbose_name=_("name"))

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name


class Licence(NamedModel):
    """
    The licence one map is published on.
    """
    pass


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
    licence = models.ForeignKey(Licence, help_text=_("Choose the map licence."), verbose_name=_('licence'))
    modified_at = models.DateTimeField(auto_now=True)
    tilelayers = models.ManyToManyField(TileLayer, through="MapToTileLayer")
    owner = models.ForeignKey(User, related_name="owned_maps", verbose_name=_("owner"))
    editors = models.ManyToManyField(User, blank=True, verbose_name=_("editors"))
    edit_status = models.SmallIntegerField(choices=EDIT_STATUS, default=OWNER, verbose_name=_("edit status"))

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
        return reverse("map", kwargs={'slug': self.slug, 'username': self.owner.username})

    def can_edit(self, user):
        """
        Define if an already authenticated user can edit or not the instance.
        """
        if user == self.owner or self.edit_status == self.ANONYMOUS:
            can = True
        elif self.edit_status == self.EDITORS and user in self.editors.all():
            can = True
        else:
            can = False
        return can


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


class Category(NamedModel):
    """
    Category of a Marker.
    """
    ICON_CLASS = (
        ('Default', 'Default'),
        ('Circle', 'Circle'),
        ('Drop', 'Drop'),
        ('Ball', 'Ball'),
    )
    map = models.ForeignKey(Map)
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("description")
    )
    color = models.CharField(
        max_length=32,
        default="DarkBlue",
        help_text=_("Must be a CSS valid name (eg.: DarkBlue or #123456)"),
        verbose_name=_("color")
    )
    pictogram = models.ForeignKey(
        Pictogram,
        null=True,
        blank=True,
        verbose_name=_("pictogram")
    )
    icon_class = models.CharField(
        choices=ICON_CLASS,
        max_length=32,
        default="Default",
        verbose_name="icon type"
    )
    preset = models.BooleanField(
        default=False,
        verbose_name=_("preset"),
        help_text=_("Display this category on load.")
    )
    rank = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Rank to order the categories"),
        verbose_name=_("rank")
    )

    @property
    def json(self):
        return {
            "name": self.name,
            "pk": self.pk,
            "color": self.color,
            "pictogram_url": self.pictogram.pictogram.url if self.pictogram else None,
            "icon_class": self.icon_class,
            "preset": self.preset,
        }

    @property
    def features(self):
        filters = {
            "category": self
        }
        markers = Marker.objects.filter(**filters)
        polylines = Polyline.objects.filter(**filters)
        polygons = Polygon.objects.filter(**filters)
        return list(markers) + list(polylines) + list(polygons)

    class Meta:
        ordering = ["rank"]


class BaseFeature(NamedModel):
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("description")
    )
    color = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name=_("color")
    )
    category = models.ForeignKey(Category, verbose_name=_("category"))

    objects = models.GeoManager()

    class Meta:
        abstract = True


class AbstractMarker(BaseFeature):
    """
    Point of interest.
    """
    latlng = models.PointField(geography=True)

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
