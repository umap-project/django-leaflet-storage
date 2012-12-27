from django.test import TestCase
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User
from django.utils import simplejson
from django.core.urlresolvers import reverse

import factory

from leaflet_storage.models import Map, TileLayer, Licence, Category, Marker


class LicenceFactory(factory.Factory):
    FACTORY_FOR = Licence
    name = "WTFPL"


class TileLayerFactory(factory.Factory):
    FACTORY_FOR = TileLayer
    name = "Test zoom layer"
    url_template = "http://{s}.test.org/{z}/{x}/{y}.png"
    attribution = "Test layer attribution"


class UserFactory(factory.Factory):
    FACTORY_FOR = User
    username = 'Joe'
    email = factory.LazyAttribute(lambda a: '{0}@example.com'.format(a.username).lower())

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserFactory, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user


class MapFactory(factory.Factory):
    FACTORY_FOR = Map
    name = "test map"
    slug = "test-map"
    center = Point(2, 51)
    licence = factory.SubFactory(LicenceFactory)
    owner = factory.SubFactory(UserFactory)


class CategoryFactory(factory.Factory):
    FACTORY_FOR = Category
    map = factory.SubFactory(MapFactory)
    name = "test category"
    description = "test description"
    color = "DarkRed"
    display_on_load = True
    rank = 1


class BaseFeatureFactory(factory.Factory):
    ABSTRACT_FACTORY = True
    name = "test feature"
    description = "test description"
    color = None  # Having a color on a feature is not the normal case
    category = factory.SubFactory(CategoryFactory)


class MarkerFactory(BaseFeatureFactory):
    FACTORY_FOR = Marker
    latlng = '{"type": "Point","coordinates": [-0.1318359375,51.474540439419755]}'


class BaseTest(TestCase):
    """
    Provide miminal data need in tests.
    """

    def setUp(self):
        self.user = UserFactory(password="123123")
        self.map = MapFactory(owner=self.user)
        self.category = CategoryFactory(map=self.map)
        self.tilelayer = TileLayerFactory()
        self.licence = LicenceFactory()

    def tearDown(self):
        self.user.delete()
        self.map.delete()
        self.category.delete()

    def assertLoginRequired(self, response):
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("login_required", json)
        redirect_url = reverse('login')
        self.assertEqual(json['login_required'], redirect_url)

    def assertHasForm(self, response):
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("html", json)
        self.assertIn("form", json['html'])
