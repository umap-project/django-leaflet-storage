import os

from django.test import TransactionTestCase
from django.utils import simplejson
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from leaflet_storage.models import Map, Category, Marker, Polygon, Polyline

from .base import (MapFactory, CategoryFactory, MarkerFactory,
                   UserFactory, BaseTest)


class MapViews(BaseTest):

    def test_quick_create_GET(self):
        url = reverse('map_add')
        self.client.login(username=self.user.username, password="123123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("html", json)
        self.assertIn("form", json['html'])

    def test_quick_create_POST(self):
        url = reverse('map_add')
        # POST only mendatory fields
        name = 'test-map-with-new-name'
        post_data = {
            'name': name,
            'licence': self.licence.pk
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        created_map = Map.objects.latest('pk')
        self.assertEqual(json['redirect'], created_map.get_absolute_url())
        self.assertEqual(created_map.name, name)
        # A category must have been created automatically
        self.assertEqual(Category.objects.filter(map=created_map).count(), 1)
        # Default tilelayer must have been linked to the map
        self.assertEqual(created_map.tilelayers.count(), 1)
        self.assertEqual(created_map.tilelayers.all()[0], self.tilelayer)

    def test_quick_create_with_existing_name_should_not_succeed(self):
        url = reverse('map_add')
        # POST only mendatory fields
        post_data = {
            'name': self.map.name,
            'licence': self.licence.pk
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn('html', json)
        self.assertEqual(Map.objects.filter(name=self.map.name, owner=self.map.owner).count(), 1)

    def test_quick_update_GET(self):
        url = reverse('map_update', kwargs={'map_id': self.map.pk})
        self.client.login(username=self.user.username, password="123123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("html", json)
        self.assertIn(self.map.name, json['html'])

    def test_quick_update_POST(self):
        url = reverse('map_update', kwargs={'map_id': self.map.pk})
        # POST only mendatory fields
        new_name = 'new map name'
        post_data = {
            'name': new_name,
            'licence': self.map.licence.pk
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertNotIn("html", json)
        updated_map = Map.objects.get(pk=self.map.pk)
        self.assertEqual(json['redirect'], updated_map.get_absolute_url())
        self.assertEqual(updated_map.name, new_name)

    def test_quick_update_with_existing_name_should_no_succeed(self):
        url = reverse('map_update', kwargs={'map_id': self.map.pk})
        other_map = MapFactory(name="existing name", slug="existing-name", owner=self.user)
        # POST only mendatory fields
        post_data = {
            'name': other_map.name,
            'licence': self.map.licence.pk
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("html", json)
        self.assertEqual(Map.objects.filter(name=other_map.name, owner=self.map.owner).count(), 1)

    def test_delete_GET(self):
        url = reverse('map_delete', args=(self.map.pk, ))
        self.client.login(username=self.user.username, password="123123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("html", json)
        self.assertIn("form", json['html'])

    def test_delete_POST(self):
        # create some features
        marker1 = MarkerFactory(category=self.category)
        marker2 = MarkerFactory(category=self.category)
        marker3 = MarkerFactory(category=self.category)
        url = reverse('map_delete', args=(self.map.pk, ))
        post_data = {
            'confirm': "yes",
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Map.objects.filter(pk=self.map.pk).count(), 0)
        self.assertEqual(Category.objects.filter(pk=self.category.pk).count(), 0)
        # Check that features have been delete
        self.assertEqual(Marker.objects.filter(pk=marker1.pk).count(), 0)
        self.assertEqual(Marker.objects.filter(pk=marker2.pk).count(), 0)
        self.assertEqual(Marker.objects.filter(pk=marker3.pk).count(), 0)
        # Check that user has not been impacted
        self.assertEqual(User.objects.filter(pk=self.user.pk).count(), 1)
        # Test response is a json
        json = simplejson.loads(response.content)
        self.assertIn("redirect", json)


class ViewsPermissionsTest(BaseTest):

    def setUp(self):
        super(ViewsPermissionsTest, self).setUp()
        self.other_user = UserFactory(username="Bob", password="123123")

    def check_url_permissions(self, url):
        # GET anonymous
        response = self.client.get(url)
        self.assertLoginRequired(response)
        # POST anonymous
        response = self.client.post(url, {})
        self.assertLoginRequired(response)
        # GET with wrong permissions
        self.client.login(username=self.other_user.username, password="123123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        # POST with wrong permissions
        self.client.login(username=self.other_user.username, password="123123")
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 403)


class MapViewsPermissions(ViewsPermissionsTest):

    def test_map_add_permissions(self):
        url = reverse('map_add')
        # GET anonymous
        response = self.client.get(url)
        self.assertLoginRequired(response)
        # POST anonymous
        response = self.client.post(url, {})
        self.assertLoginRequired(response)

    def test_map_update_permissions(self):
        url = reverse('map_update', kwargs={'map_id': self.map.pk})
        self.check_url_permissions(url)

    def test_upload_data_permissions(self):
        url = reverse('upload_data', kwargs={'map_id': self.map.pk})
        self.check_url_permissions(url)

    def test_map_update_extend_permissions(self):
        # only POST is available for this view
        url = reverse('map_update_extent', kwargs={'map_id': self.map.pk})
        # POST anonymous
        response = self.client.post(url, {})
        self.assertLoginRequired(response)
        # POST with wrong permissions
        self.client.login(username=self.other_user.username, password="123123")
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 403)

    def test_embed_view_should_be_open_bar(self):
        url = reverse('map_embed', kwargs={'map_id': self.map.pk})
        # HTTP_HOST is needed by the view for now
        response = self.client.get(url, HTTP_HOST="local.local")
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("html", json)
        self.assertIn("iframe", json['html'])

    def test_only_owner_can_delete(self):
        self.map.editors.add(self.other_user)
        url = reverse('map_delete', kwargs={'map_id': self.map.pk})
        post_data = {
            'confirm': "yes",
        }
        self.client.login(username=self.other_user.username, password="123123")
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 403)


class MarkerViewsPermissions(ViewsPermissionsTest):

    def test_marker_add(self):
        url = reverse('marker_add', kwargs={'map_id': self.map.pk})
        self.check_url_permissions(url)

    def test_marker_update(self):
        marker = MarkerFactory(category=self.category)
        url = reverse('marker_update', kwargs={'map_id': self.map.pk, 'pk': marker.pk})
        self.check_url_permissions(url)

    def test_marker_delete(self):
        marker = MarkerFactory(category=self.category)
        url = reverse('marker_delete', kwargs={'map_id': self.map.pk, 'pk': marker.pk})
        self.check_url_permissions(url)


class MarkerViews(BaseTest):

    def test_add_GET(self):
        url = reverse('marker_add', args=(self.map.pk, ))
        self.client.login(username=self.user.username, password="123123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("html", json)
        self.assertIn("form", json['html'])

    def test_add_POST(self):
        url = reverse('marker_add', args=(self.map.pk, ))
        name = 'test-marker'
        post_data = {
            'name': name,
            'category': self.category.pk,
            'latlng': '{"type": "Point","coordinates": [-0.1318359375,51.474540439419755]}'
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        created_marker = Marker.objects.latest('pk')
        self.assertEqual(created_marker.name, name)
        # Test response is a json
        json = simplejson.loads(response.content)
        self.assertIn("features", json)

    def test_delete_GET(self):
        marker = MarkerFactory(category=self.category)
        url = reverse('marker_delete', args=(self.map.pk, marker.pk))
        self.client.login(username=self.user.username, password="123123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("html", json)
        self.assertIn("form", json['html'])

    def test_delete_POST(self):
        marker = MarkerFactory(category=self.category)
        url = reverse('marker_delete', args=(self.map.pk, marker.pk))
        post_data = {
            'confirm': "yes",
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Marker.objects.filter(pk=marker.pk).count(), 0)
        # Check that category and map have not been impacted
        self.assertEqual(Map.objects.filter(pk=self.map.pk).count(), 1)
        self.assertEqual(Category.objects.filter(pk=self.category.pk).count(), 1)
        # Test response is a json
        json = simplejson.loads(response.content)
        self.assertIn("info", json)


class UploadData(TransactionTestCase):

    def setUp(self):
        self.user = UserFactory(password="123123")
        self.map = MapFactory(owner=self.user)
        self.category = CategoryFactory(map=self.map)

    def tearDown(self):
        self.user.delete()

    def process_file(self, filename):
        """
        Process a file stored in tests/fixtures/
        """
        url = reverse('upload_data', kwargs={'map_id': self.map.pk})
        current_path = os.path.dirname(os.path.realpath(__file__))
        fixture_path = os.path.join(
            current_path,
            'fixtures',
            filename
        )
        f = open(fixture_path)
        post_data = {
            'category': self.category.pk,
            'data_file': f
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data)
        return response

    def test_GeoJSON_generic(self):
        # Contains tow Point, two Polygons and one Polyline
        response = self.process_file("test_upload_data.json")
        self.client.login(username=self.user.username, password="123123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Marker.objects.filter(category=self.category).count(), 2)
        self.assertEqual(Polygon.objects.filter(category=self.category).count(), 2)
        self.assertEqual(Polyline.objects.filter(category=self.category).count(), 1)
        # Check properties population
        self.assertEqual(Marker.objects.filter(category=self.category, name="London").count(), 1)
        marker = Marker.objects.get(category=self.category, name="London")
        self.assertEqual(marker.description, "London description")
        self.assertEqual(marker.color, "Pink")
        self.assertEqual(Marker.objects.filter(category=self.category, name="Antwerpen").count(), 1)
        marker = Marker.objects.get(category=self.category, name="Antwerpen")
        self.assertEqual(marker.description, "")
        self.assertEqual(marker.color, None)

    def test_GeoJSON_empty_coordinates_should_not_be_imported(self):
        self.assertEqual(Marker.objects.filter(category=self.category).count(), 0)
        self.assertEqual(Polyline.objects.filter(category=self.category).count(), 0)
        self.assertEqual(Polygon.objects.filter(category=self.category).count(), 0)
        response = self.process_file("test_upload_empty_coordinates.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Marker.objects.filter(category=self.category).count(), 0)
        self.assertEqual(Polyline.objects.filter(category=self.category).count(), 0)
        self.assertEqual(Polygon.objects.filter(category=self.category).count(), 0)

    def test_GeoJSON_non_linear_ring_should_not_be_imported(self):
        response = self.process_file("test_upload_non_linear_ring.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Polygon.objects.filter(category=self.category).count(), 0)

    def test_GeoJSON_missing_name_should_not_stop_import(self):
        # One feature is missing a name
        # We have to make sure that the other feature are imported
        self.assertEqual(Marker.objects.filter(category=self.category).count(), 0)
        response = self.process_file("test_upload_missing_name.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Marker.objects.filter(category=self.category).count(), 1)
        self.assertEqual(Polyline.objects.filter(category=self.category).count(), 1)
        self.assertEqual(Polygon.objects.filter(category=self.category).count(), 1)

    def test_import_data_from_url(self):
        url = reverse('upload_data', kwargs={'map_id': self.map.pk})
        current_path = os.path.dirname(os.path.realpath(__file__))
        fixture_path = os.path.join(
            current_path,
            'fixtures',
            "test_upload_data.json"
        )
        post_data = {
            'category': self.category.pk,
            'data_file': "file://%s" % fixture_path
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data)
        response = self.process_file("test_upload_data.json")
        self.client.login(username=self.user.username, password="123123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Marker.objects.filter(category=self.category).count(), 2)
        self.assertEqual(Polygon.objects.filter(category=self.category).count(), 2)
        self.assertEqual(Polyline.objects.filter(category=self.category).count(), 1)

    def test_KML_generic(self):
        # Contains one Polyline
        response = self.process_file("test_upload_data.kml")
        self.client.login(username=self.user.username, password="123123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Polyline.objects.filter(category=self.category).count(), 1)
        self.assertEqual(Marker.objects.filter(category=self.category).count(), 1)
        self.assertEqual(Polygon.objects.filter(category=self.category).count(), 1)


class CategoryViews(BaseTest):

    def test_delete_GET(self):
        url = reverse('category_delete', args=(self.map.pk, self.category.pk))
        self.client.login(username=self.user.username, password="123123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("html", json)
        self.assertIn("form", json['html'])

    def test_delete_POST(self):
        # create some features
        marker1 = MarkerFactory(category=self.category)
        marker2 = MarkerFactory(category=self.category)
        marker3 = MarkerFactory(category=self.category)
        url = reverse('category_delete', args=(self.map.pk, self.category.pk))
        post_data = {
            'confirm': "yes",
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.filter(pk=self.category.pk).count(), 0)
        # Check that features have been delete
        self.assertEqual(Marker.objects.filter(pk=marker1.pk).count(), 0)
        self.assertEqual(Marker.objects.filter(pk=marker2.pk).count(), 0)
        self.assertEqual(Marker.objects.filter(pk=marker3.pk).count(), 0)
        # Check that map has not been impacted
        self.assertEqual(Map.objects.filter(pk=self.map.pk).count(), 1)
        # Test response is a json
        json = simplejson.loads(response.content)
        self.assertIn("info", json)
