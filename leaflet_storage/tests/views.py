import os

from django.test import TransactionTestCase
from django.utils import simplejson
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.core.signing import get_cookie_signer

from leaflet_storage.models import Map, DataLayer, Marker, Polygon, Polyline

from .base import (MapFactory, DataLayerFactory, MarkerFactory,
                   UserFactory, BaseTest)


@override_settings(LEAFLET_STORAGE_ALLOW_ANONYMOUS=False)
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
        # A datalayer must have been created automatically
        self.assertEqual(DataLayer.objects.filter(map=created_map).count(), 1)
        # Default tilelayer must have been linked to the map
        self.assertEqual(created_map.tilelayers.count(), 1)
        self.assertEqual(created_map.tilelayers.all()[0], self.tilelayer)

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
        marker1 = MarkerFactory(datalayer=self.datalayer)
        marker2 = MarkerFactory(datalayer=self.datalayer)
        marker3 = MarkerFactory(datalayer=self.datalayer)
        url = reverse('map_delete', args=(self.map.pk, ))
        post_data = {
            'confirm': "yes",
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Map.objects.filter(pk=self.map.pk).count(), 0)
        self.assertEqual(DataLayer.objects.filter(pk=self.datalayer.pk).count(), 0)
        # Check that features have been delete
        self.assertEqual(Marker.objects.filter(pk=marker1.pk).count(), 0)
        self.assertEqual(Marker.objects.filter(pk=marker2.pk).count(), 0)
        self.assertEqual(Marker.objects.filter(pk=marker3.pk).count(), 0)
        # Check that user has not been impacted
        self.assertEqual(User.objects.filter(pk=self.user.pk).count(), 1)
        # Test response is a json
        json = simplejson.loads(response.content)
        self.assertIn("redirect", json)

    def test_short_url_should_redirect_to_canonical(self):
        url = reverse('map_short_url', kwargs={'pk': self.map.pk})
        canonical = reverse('map', kwargs={'pk': self.map.pk, 'slug': self.map.slug})
        response = self.client.get(url)
        self.assertRedirects(response, canonical, status_code=301)

    def test_old_url_should_redirect_to_canonical(self):
        url = reverse(
            'map_old_url',
            kwargs={'username': self.map.owner.username, 'slug': self.map.slug}
        )
        canonical = reverse('map', kwargs={'pk': self.map.pk, 'slug': self.map.slug})
        response = self.client.get(url)
        self.assertRedirects(response, canonical, status_code=301)


@override_settings(LEAFLET_STORAGE_ALLOW_ANONYMOUS=True)
class AnonymousMapViews(BaseTest):

    def setUp(self):
        super(AnonymousMapViews, self).setUp()
        self.anonymous_map = MapFactory(
            name="an-anonymous-map",
            owner=None,
            licence=self.licence
        )
        key, value = self.anonymous_map.signed_cookie_elements
        self.anonymous_cookie_key = key
        self.anonymous_cookie_value = get_cookie_signer(salt=key).sign(value)

    def test_quick_create_GET(self):
        url = reverse('map_add')
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
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        created_map = Map.objects.latest('pk')
        self.assertEqual(json['redirect'], created_map.get_absolute_url())
        self.assertEqual(created_map.name, name)
        key, value = created_map.signed_cookie_elements
        self.assertIn(key, self.client.cookies)

    def test_quick_update_no_cookie_GET(self):
        url = reverse('map_update', kwargs={'map_id': self.anonymous_map.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertNotIn("html", json)
        self.assertIn("login_required", json)

    def test_quick_update_no_cookie_POST(self):
        url = reverse('map_update', kwargs={'map_id': self.anonymous_map.pk})
        # POST only mendatory fields
        new_name = 'new map name'
        post_data = {
            'name': new_name,
            'licence': self.anonymous_map.licence.pk
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertNotIn("html", json)
        self.assertIn("login_required", json)

    def test_quick_update_with_cookie_GET(self):
        url = reverse('map_update', kwargs={'map_id': self.anonymous_map.pk})
        self.client.cookies[self.anonymous_cookie_key] = self.anonymous_cookie_value
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("html", json)

    def test_quick_update_with_cookie_POST(self):
        url = reverse('map_update', kwargs={'map_id': self.anonymous_map.pk})
        self.client.cookies[self.anonymous_cookie_key] = self.anonymous_cookie_value
        # POST only mendatory fields
        new_name = 'new map name'
        post_data = {
            'name': new_name,
            'licence': self.anonymous_map.licence.pk
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        updated_map = Map.objects.get(pk=self.anonymous_map.pk)
        self.assertEqual(json['redirect'], updated_map.get_absolute_url())

    def test_anonymous_edit_url(self):
        url = self.anonymous_map.get_anonymous_edit_url()
        canonical = reverse(
            'map',
            kwargs={'pk': self.anonymous_map.pk, 'slug': self.anonymous_map.slug}
        )
        response = self.client.get(url)
        self.assertRedirects(response, canonical, status_code=302)
        key, value = self.anonymous_map.signed_cookie_elements
        self.assertIn(key, self.client.cookies)

    def test_bad_anonymous_edit_url_should_return_403(self):
        url = self.anonymous_map.get_anonymous_edit_url()
        url = reverse(
            'map_anonymous_edit_url',
            kwargs={'signature': "%s:badsignature" % self.anonymous_map.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_with_cookie_is_attached_as_owner(self):
        url = reverse('map_update', kwargs={'map_id': self.anonymous_map.pk})
        self.client.cookies[self.anonymous_cookie_key] = self.anonymous_cookie_value
        self.client.login(username=self.user.username, password="123123")
        self.assertEqual(self.anonymous_map.owner, None)
        # POST only mendatory fields
        new_name = 'new map name for authenticated user'
        post_data = {
            'name': new_name,
            'licence': self.anonymous_map.licence.pk
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        updated_map = Map.objects.get(pk=self.anonymous_map.pk)
        self.assertEqual(json['redirect'], updated_map.get_absolute_url())
        self.assertEqual(updated_map.owner.pk, self.user.pk)


@override_settings(LEAFLET_STORAGE_ALLOW_ANONYMOUS=False)
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


@override_settings(LEAFLET_STORAGE_ALLOW_ANONYMOUS=False)
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


@override_settings(LEAFLET_STORAGE_ALLOW_ANONYMOUS=False)
class MarkerViewsPermissions(ViewsPermissionsTest):

    def test_marker_add(self):
        url = reverse('marker_add', kwargs={'map_id': self.map.pk})
        self.check_url_permissions(url)

    def test_marker_update(self):
        marker = MarkerFactory(datalayer=self.datalayer)
        url = reverse('marker_update', kwargs={'map_id': self.map.pk, 'pk': marker.pk})
        self.check_url_permissions(url)

    def test_marker_delete(self):
        marker = MarkerFactory(datalayer=self.datalayer)
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
            'datalayer': self.datalayer.pk,
            'latlng': '{"type": "Point","coordinates": [-0.1318359375,51.474540439419755]}'
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        created_marker = Marker.objects.latest('pk')
        self.assertEqual(created_marker.name, name)
        # Test response is a json
        json = simplejson.loads(response.content)
        self.assertIn("geometry", json)

    def test_delete_GET(self):
        marker = MarkerFactory(datalayer=self.datalayer)
        url = reverse('marker_delete', args=(self.map.pk, marker.pk))
        self.client.login(username=self.user.username, password="123123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("html", json)
        self.assertIn("form", json['html'])

    def test_delete_POST(self):
        marker = MarkerFactory(datalayer=self.datalayer)
        url = reverse('marker_delete', args=(self.map.pk, marker.pk))
        post_data = {
            'confirm': "yes",
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Marker.objects.filter(pk=marker.pk).count(), 0)
        # Check that datalayer and map have not been impacted
        self.assertEqual(Map.objects.filter(pk=self.map.pk).count(), 1)
        self.assertEqual(DataLayer.objects.filter(pk=self.datalayer.pk).count(), 1)
        # Test response is a json
        json = simplejson.loads(response.content)
        self.assertIn("info", json)


class UploadData(TransactionTestCase):

    def setUp(self):
        self.user = UserFactory(password="123123")
        self.map = MapFactory(owner=self.user)
        self.datalayer = DataLayerFactory(map=self.map)

    def tearDown(self):
        self.user.delete()

    def process_file(self, filename, content_type):
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
            'datalayer': self.datalayer.pk,
            'data_file': f,
            'content_type': content_type
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data)
        return response

    def test_GeoJSON_generic(self):
        # Contains tow Point, two Polygons and one Polyline
        response = self.process_file("test_upload_data.json", "geojson")
        self.client.login(username=self.user.username, password="123123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer).count(), 2)
        self.assertEqual(Polygon.objects.filter(datalayer=self.datalayer).count(), 2)
        self.assertEqual(Polyline.objects.filter(datalayer=self.datalayer).count(), 1)
        # Check properties population
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer, name="London").count(), 1)
        marker = Marker.objects.get(datalayer=self.datalayer, name="London")
        self.assertEqual(marker.description, "London description")
        self.assertEqual(marker.options["color"], "Pink")
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer, name="Antwerpen").count(), 1)
        marker = Marker.objects.get(datalayer=self.datalayer, name="Antwerpen")
        self.assertEqual(marker.description, None)
        self.assertFalse("color" in marker.options)

    def test_GeoJSON_empty_coordinates_should_not_be_imported(self):
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer).count(), 0)
        self.assertEqual(Polyline.objects.filter(datalayer=self.datalayer).count(), 0)
        self.assertEqual(Polygon.objects.filter(datalayer=self.datalayer).count(), 0)
        response = self.process_file("test_upload_empty_coordinates.json", "geojson")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer).count(), 0)
        self.assertEqual(Polyline.objects.filter(datalayer=self.datalayer).count(), 0)
        self.assertEqual(Polygon.objects.filter(datalayer=self.datalayer).count(), 0)

    def test_GeoJSON_non_linear_ring_should_not_be_imported(self):
        response = self.process_file("test_upload_non_linear_ring.json", "geojson")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Polygon.objects.filter(datalayer=self.datalayer).count(), 0)

    def test_GeoJSON_missing_name_should_be_set_with_datalayer_name(self):
        # One feature is missing a name
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer).count(), 0)
        response = self.process_file("test_upload_missing_name.json", "geojson")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer).count(), 2)
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer, name=self.datalayer.name).count(), 1)
        self.assertEqual(Polyline.objects.filter(datalayer=self.datalayer).count(), 1)
        self.assertEqual(Polygon.objects.filter(datalayer=self.datalayer).count(), 1)

    def test_import_data_from_url(self):
        url = reverse('upload_data', kwargs={'map_id': self.map.pk})
        current_path = os.path.dirname(os.path.realpath(__file__))
        fixture_path = os.path.join(
            current_path,
            'fixtures',
            "test_upload_data.json"
        )
        post_data = {
            'datalayer': self.datalayer.pk,
            'data_url': "file://%s" % fixture_path,
            'content_type': 'geojson'
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data)
        response = self.process_file("test_upload_data.json", "geojson")
        self.client.login(username=self.user.username, password="123123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer).count(), 2)
        self.assertEqual(Polygon.objects.filter(datalayer=self.datalayer).count(), 2)
        self.assertEqual(Polyline.objects.filter(datalayer=self.datalayer).count(), 1)

    def test_KML_generic(self):
        response = self.process_file("test_upload_data.kml", "kml")
        self.client.login(username=self.user.username, password="123123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Polyline.objects.filter(datalayer=self.datalayer).count(), 1)
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer).count(), 1)
        self.assertEqual(Polygon.objects.filter(datalayer=self.datalayer).count(), 1)

    def test_GPX_generic(self):
        response = self.process_file("test_upload_data.gpx", "gpx")
        self.client.login(username=self.user.username, password="123123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Polyline.objects.filter(datalayer=self.datalayer).count(), 1)
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer).count(), 1)

    def test_CSV_generic(self):
        response = self.process_file("test_upload_data.csv", "csv")
        self.client.login(username=self.user.username, password="123123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer).count(), 1)
        marker = Marker.objects.get(datalayer=self.datalayer)
        self.assertEqual(marker.name, "a point somewhere")

    def test_import_data_from_textarea(self):
        url = reverse('upload_data', kwargs={'map_id': self.map.pk})
        data_raw = """latitude,longitude,name\n41.1,118,my title"""
        post_data = {
            'datalayer': self.datalayer.pk,
            'data_raw': data_raw,
            'content_type': 'csv'
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Marker.objects.filter(datalayer=self.datalayer).count(), 1)


class DownloadDataViews(BaseTest):

    def test_geojson_download(self):
        url = reverse('download_data', kwargs={'map_id': self.map.pk})
        marker = MarkerFactory(
            datalayer=self.datalayer,
            description="this is a description",
            options={'color': '#123456'})
        response = self.client.get(url)
        self.assertEqual(response['Content-Type'], 'application/json')
        json = simplejson.loads(response.content)
        self.assertIn("features", json)
        feature = json['features'][0]
        self.assertEqual(feature['properties']['description'], marker.description)
        self.assertEqual(feature['properties']['color'], marker.options['color'])


class DataLayerViews(BaseTest):

    def test_delete_GET(self):
        url = reverse('datalayer_delete', args=(self.map.pk, self.datalayer.pk))
        self.client.login(username=self.user.username, password="123123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertIn("html", json)
        self.assertIn("form", json['html'])

    def test_delete_POST(self):
        # create some features
        marker1 = MarkerFactory(datalayer=self.datalayer)
        marker2 = MarkerFactory(datalayer=self.datalayer)
        marker3 = MarkerFactory(datalayer=self.datalayer)
        url = reverse('datalayer_delete', args=(self.map.pk, self.datalayer.pk))
        post_data = {
            'confirm': "yes",
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DataLayer.objects.filter(pk=self.datalayer.pk).count(), 0)
        # Check that features have been delete
        self.assertEqual(Marker.objects.filter(pk=marker1.pk).count(), 0)
        self.assertEqual(Marker.objects.filter(pk=marker2.pk).count(), 0)
        self.assertEqual(Marker.objects.filter(pk=marker3.pk).count(), 0)
        # Check that map has not been impacted
        self.assertEqual(Map.objects.filter(pk=self.map.pk).count(), 1)
        # Test response is a json
        json = simplejson.loads(response.content)
        self.assertIn("info", json)
