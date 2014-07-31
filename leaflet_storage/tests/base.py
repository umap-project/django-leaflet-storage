from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import simplejson
from django.core.urlresolvers import reverse
from django.core.files import temp
from django.test.client import RequestFactory

import factory

from leaflet_storage.models import Map, TileLayer, Licence, DataLayer
from leaflet_storage.forms import DEFAULT_CENTER

User = get_user_model()


class LicenceFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Licence
    name = "WTFPL"


class TileLayerFactory(factory.DjangoModelFactory):
    FACTORY_FOR = TileLayer
    name = "Test zoom layer"
    url_template = "http://{s}.test.org/{z}/{x}/{y}.png"
    attribution = "Test layer attribution"


class UserFactory(factory.DjangoModelFactory):
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


class MapFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Map
    name = "test map"
    slug = "test-map"
    center = DEFAULT_CENTER
    settings = {
        'geometry': {
            'coordinates': [13.447265624999998, 48.94415123418794],
            'type': 'Point'
        },
        'properties': {
            'datalayersControl': True,
            'description': 'Which is just the Danube, at the end, I mean, JUST THE DANUBE',
            'displayCaptionOnLoad': False,
            'displayDataBrowserOnLoad': False,
            'displayPopupFooter': False,
            'licence': '',
            'miniMap': False,
            'moreControl': True,
            'name': 'Cruising on the Donau',
            'scaleControl': True,
            'tilelayer': {
                'attribution': u'\xa9 OSM Contributors - tiles OpenRiverboatMap',
                'maxZoom': 18,
                'minZoom': 0,
                'url_template': 'http://{s}.layers.openstreetmap.fr/openriverboatmap/{z}/{x}/{y}.png'
            },
            'tilelayersControl': True,
            'zoom': 7,
            'zoomControl': True
        },
        'type': 'Feature'
    }

    licence = factory.SubFactory(LicenceFactory)
    owner = factory.SubFactory(UserFactory)


class DataLayerFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DataLayer
    map = factory.SubFactory(MapFactory)
    name = "test datalayer"
    description = "test description"
    display_on_load = True
    geojson = factory.django.FileField(data="""{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[13.68896484375,48.55297816440071]},"properties":{"_storage_options":{"color":"DarkCyan","iconClass":"Ball"},"name":"Here","description":"Da place anonymous again 755"}}],"_storage":{"displayOnLoad":true,"name":"Donau","id":926}}""")


class BaseFeatureFactory(factory.DjangoModelFactory):
    ABSTRACT_FACTORY = True
    name = "test feature"
    description = "test description"
    datalayer = factory.SubFactory(DataLayerFactory)


class BaseTest(TestCase):
    """
    Provide miminal data need in tests.
    """

    def setUp(self):
        self.user = UserFactory(password="123123")
        self.licence = LicenceFactory()
        self.map = MapFactory(owner=self.user, licence=self.licence)
        self.datalayer = DataLayerFactory(map=self.map)
        self.tilelayer = TileLayerFactory()
        self.request_factory = RequestFactory()

    def tearDown(self):
        self.user.delete()
        self.map.delete()
        self.datalayer.delete()

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

    def temp_file(self, content):
        tdir = temp.gettempdir()
        f = temp.NamedTemporaryFile(dir=tdir)
        f.write(content)
        f.seek(0)
        return f
