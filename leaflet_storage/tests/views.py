# -*- coding: utf-8 -*-
from django.utils import simplejson
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.core.signing import get_cookie_signer

from leaflet_storage.models import Map, DataLayer

from .base import (MapFactory, UserFactory, BaseTest)


@override_settings(LEAFLET_STORAGE_ALLOW_ANONYMOUS=False)
class MapViews(BaseTest):

    def test_create(self):
        url = reverse('map_create')
        # POST only mendatory fields
        name = 'test-map-with-new-name'
        post_data = {
            'name': name,
            'center': '{"type":"Point","coordinates":[13.447265624999998,48.94415123418794]}',
            'settings': '{"type":"Feature","geometry":{"type":"Point","coordinates":[5.0592041015625,52.05924589011585]},"properties":{"tilelayer":{"maxZoom":20,"url_template":"http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png","minZoom":0,"attribution":"HOT and friends"},"licence":"","description":"","name":"test enrhûmé","tilelayersControl":true,"displayDataBrowserOnLoad":false,"displayPopupFooter":true,"displayCaptionOnLoad":false,"miniMap":true,"moreControl":true,"scaleControl":true,"zoomControl":true,"datalayersControl":true,"zoom":8}}'
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        created_map = Map.objects.latest('pk')
        self.assertEqual(json['id'], created_map.pk)
        self.assertEqual(created_map.name, name)

    def test_update(self):
        url = reverse('map_update', kwargs={'map_id': self.map.pk})
        # POST only mendatory fields
        new_name = 'new map name'
        post_data = {
            'name': new_name,
            'center': '{"type":"Point","coordinates":[13.447265624999998,48.94415123418794]}',
            'settings': '{"type":"Feature","geometry":{"type":"Point","coordinates":[5.0592041015625,52.05924589011585]},"properties":{"tilelayer":{"maxZoom":20,"url_template":"http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png","minZoom":0,"attribution":"HOT and friends"},"licence":"","description":"","name":"test enrhûmé","tilelayersControl":true,"displayDataBrowserOnLoad":false,"displayPopupFooter":true,"displayCaptionOnLoad":false,"miniMap":true,"moreControl":true,"scaleControl":true,"zoomControl":true,"datalayersControl":true,"zoom":8}}'
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertNotIn("html", json)
        updated_map = Map.objects.get(pk=self.map.pk)
        self.assertEqual(json['id'], updated_map.pk)
        self.assertEqual(updated_map.name, new_name)

    def test_delete(self):
        url = reverse('map_delete', args=(self.map.pk, ))
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, {}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Map.objects.filter(pk=self.map.pk).count(), 0)
        self.assertEqual(DataLayer.objects.filter(pk=self.datalayer.pk).count(), 0)
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

    def test_clone_map_should_create_a_new_instance(self):
        self.assertEqual(Map.objects.count(), 1)
        url = reverse('map_clone', kwargs={'map_id': self.map.pk})
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Map.objects.count(), 2)
        clone = Map.objects.latest('pk')
        self.assertNotEqual(clone.pk, self.map.pk)
        self.assertEqual(clone.name, u"Clone of " + self.map.name)

    def test_clone_map_should_not_be_possible_if_user_is_not_allowed(self):
        self.assertEqual(Map.objects.count(), 1)
        url = reverse('map_clone', kwargs={'map_id': self.map.pk})
        self.map.edit_status = self.map.OWNER
        self.map.save()
        response = self.client.post(url)
        self.assertLoginRequired(response)
        other_user = UserFactory(username="Bob", password="123123")
        self.client.login(username=other_user.username, password="123123")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.map.edit_status = self.map.ANONYMOUS
        self.map.save()
        self.client.logout()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Map.objects.count(), 1)

    def test_clone_should_set_cloner_as_owner(self):
        url = reverse('map_clone', kwargs={'map_id': self.map.pk})
        other_user = UserFactory(username="Bob", password="123123")
        self.map.edit_status = self.map.EDITORS
        self.map.editors.add(other_user)
        self.map.save()
        self.client.login(username=other_user.username, password="123123")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Map.objects.count(), 2)
        clone = Map.objects.latest('pk')
        self.assertNotEqual(clone.pk, self.map.pk)
        self.assertEqual(clone.name, u"Clone of " + self.map.name)
        self.assertEqual(clone.owner, other_user)

    def test_map_creation_should_allow_unicode_names(self):
        url = reverse('map_create')
        # POST only mendatory fields
        name = u'Академический'
        post_data = {
            'name': name,
            'center': '{"type":"Point","coordinates":[13.447265624999998,48.94415123418794]}',
            'settings': '{"type":"Feature","geometry":{"type":"Point","coordinates":[5.0592041015625,52.05924589011585]},"properties":{"tilelayer":{"maxZoom":20,"url_template":"http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png","minZoom":0,"attribution":"HOT and friends"},"licence":"","description":"","name":"test enrhûmé","tilelayersControl":true,"displayDataBrowserOnLoad":false,"displayPopupFooter":true,"displayCaptionOnLoad":false,"miniMap":true,"moreControl":true,"scaleControl":true,"zoomControl":true,"datalayersControl":true,"zoom":8}}'
        }
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        created_map = Map.objects.latest('pk')
        self.assertEqual(json['id'], created_map.pk)
        self.assertEqual(created_map.name, name)
        # Lower case of the russian original name
        # self.assertEqual(created_map.slug, u"академический")
        # for now we fallback to "map", see unicode_name branch
        self.assertEqual(created_map.slug, u"map")


@override_settings(LEAFLET_STORAGE_ALLOW_ANONYMOUS=True)
class AnonymousMapViews(BaseTest):

    def setUp(self):
        super(AnonymousMapViews, self).setUp()
        self.anonymous_map = MapFactory(
            name="an-anonymous-map",
            owner=None,
        )
        key, value = self.anonymous_map.signed_cookie_elements
        self.anonymous_cookie_key = key
        self.anonymous_cookie_value = get_cookie_signer(salt=key).sign(value)

    def test_create(self):
        url = reverse('map_create')
        # POST only mendatory fields
        name = 'test-map-with-new-name'
        post_data = {
            'name': name,
            'center': '{"type":"Point","coordinates":[13.447265624999998,48.94415123418794]}',
            'settings': '{"type":"Feature","geometry":{"type":"Point","coordinates":[5.0592041015625,52.05924589011585]},"properties":{"tilelayer":{"maxZoom":20,"url_template":"http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png","minZoom":0,"attribution":"HOT and friends"},"licence":"","description":"","name":"test enrhûmé","tilelayersControl":true,"displayDataBrowserOnLoad":false,"displayPopupFooter":true,"displayCaptionOnLoad":false,"miniMap":true,"moreControl":true,"scaleControl":true,"zoomControl":true,"datalayersControl":true,"zoom":8}}'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        created_map = Map.objects.latest('pk')
        self.assertEqual(json['id'], created_map.pk)
        self.assertEqual(created_map.name, name)
        key, value = created_map.signed_cookie_elements
        self.assertIn(key, self.client.cookies)

    def test_update_no_cookie(self):
        url = reverse('map_update', kwargs={'map_id': self.anonymous_map.pk})
        # POST only mendatory fields
        new_name = 'new map name'
        post_data = {
            'name': new_name,
            'center': '{"type":"Point","coordinates":[13.447265624999998,48.94415123418794]}',
            'settings': '{"type":"Feature","geometry":{"type":"Point","coordinates":[5.0592041015625,52.05924589011585]},"properties":{"tilelayer":{"maxZoom":20,"url_template":"http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png","minZoom":0,"attribution":"HOT and friends"},"licence":"","description":"","name":"test enrhûmé","tilelayersControl":true,"displayDataBrowserOnLoad":false,"displayPopupFooter":true,"displayCaptionOnLoad":false,"miniMap":true,"moreControl":true,"scaleControl":true,"zoomControl":true,"datalayersControl":true,"zoom":8}}'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertNotIn("id", json)
        self.assertIn("login_required", json)

    def test_update_with_cookie(self):
        url = reverse('map_update', kwargs={'map_id': self.anonymous_map.pk})
        self.client.cookies[self.anonymous_cookie_key] = self.anonymous_cookie_value
        # POST only mendatory fields
        new_name = 'new map name'
        post_data = {
            'name': new_name,
            'center': '{"type":"Point","coordinates":[13.447265624999998,48.94415123418794]}',
            'settings': '{"type":"Feature","geometry":{"type":"Point","coordinates":[5.0592041015625,52.05924589011585]},"properties":{"tilelayer":{"maxZoom":20,"url_template":"http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png","minZoom":0,"attribution":"HOT and friends"},"licence":"","description":"","name":"test enrhûmé","tilelayersControl":true,"displayDataBrowserOnLoad":false,"displayPopupFooter":true,"displayCaptionOnLoad":false,"miniMap":true,"moreControl":true,"scaleControl":true,"zoomControl":true,"datalayersControl":true,"zoom":8}}'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        updated_map = Map.objects.get(pk=self.anonymous_map.pk)
        self.assertEqual(json['id'], updated_map.pk)

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
            'center': '{"type":"Point","coordinates":[13.447265624999998,48.94415123418794]}',
            'settings': '{"type":"Feature","geometry":{"type":"Point","coordinates":[5.0592041015625,52.05924589011585]},"properties":{"tilelayer":{"maxZoom":20,"url_template":"http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png","minZoom":0,"attribution":"HOT and friends"},"licence":"","description":"","name":"test enrhûmé","tilelayersControl":true,"displayDataBrowserOnLoad":false,"displayPopupFooter":true,"displayCaptionOnLoad":false,"miniMap":true,"moreControl":true,"scaleControl":true,"zoomControl":true,"datalayersControl":true,"zoom":8}}'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        updated_map = Map.objects.get(pk=self.anonymous_map.pk)
        self.assertEqual(json['id'], updated_map.pk)
        self.assertEqual(updated_map.owner.pk, self.user.pk)

    def test_clone_map_should_not_be_possible_if_user_is_not_allowed(self):
        self.assertEqual(Map.objects.count(), 2)
        url = reverse('map_clone', kwargs={'map_id': self.map.pk})
        self.map.edit_status = self.map.OWNER
        self.map.save()
        response = self.client.get(url)
        self.assertLoginRequired(response)
        other_user = UserFactory(username="Bob", password="123123")
        self.client.login(username=other_user.username, password="123123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Map.objects.count(), 2)

    def test_clone_map_should_be_possible_if_edit_status_is_anonymous(self):
        self.assertEqual(Map.objects.count(), 2)
        url = reverse('map_clone', kwargs={'map_id': self.map.pk})
        self.map.edit_status = self.map.ANONYMOUS
        self.map.save()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Map.objects.count(), 3)
        clone = Map.objects.latest('pk')
        self.assertNotEqual(clone.pk, self.map.pk)
        self.assertEqual(clone.name, u"Clone of " + self.map.name)
        self.assertEqual(clone.owner, None)


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

    def test_map_create_permissions(self):
        url = reverse('map_create')
        # POST anonymous
        response = self.client.post(url, {})
        self.assertLoginRequired(response)

    def test_map_update_permissions(self):
        url = reverse('map_update', kwargs={'map_id': self.map.pk})
        self.check_url_permissions(url)

    def test_only_owner_can_delete(self):
        self.map.editors.add(self.other_user)
        url = reverse('map_delete', kwargs={'map_id': self.map.pk})
        self.client.login(username=self.other_user.username, password="123123")
        response = self.client.post(url, {}, follow=True)
        self.assertEqual(response.status_code, 403)


class DataLayerViews(BaseTest):

    def test_get(self):
        url = reverse('datalayer_view', args=(self.datalayer.pk, ))
        response = self.client.get(url)
        self.assertIsNotNone(response['Etag'])
        self.assertIsNotNone(response['Last-Modified'])
        self.assertIsNotNone(response['Cache-Control'])
        json = simplejson.loads(response.content)
        self.assertIn('_storage', json)
        self.assertIn('features', json)
        self.assertEquals(json['type'], 'FeatureCollection')

    def test_update(self):
        url = reverse('datalayer_update', args=(self.map.pk, self.datalayer.pk))
        self.client.login(username=self.user.username, password="123123")
        name = "new name"
        post_data = {
            "name": name,
            "display_on_load": True,
            "geojson": '{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[-3.1640625,53.014783245859235],[-3.1640625,51.86292391360244],[-0.50537109375,51.385495069223204],[1.16455078125,52.38901106223456],[-0.41748046875,53.91728101547621],[-2.109375,53.85252660044951],[-3.1640625,53.014783245859235]]]},"properties":{"_storage_options":{},"name":"Ho god, sounds like a polygouine"}},{"type":"Feature","geometry":{"type":"LineString","coordinates":[[1.8017578124999998,51.16556659836182],[-0.48339843749999994,49.710272582105695],[-3.1640625,50.0923932109388],[-5.60302734375,51.998410382390325]]},"properties":{"_storage_options":{},"name":"Light line"}},{"type":"Feature","geometry":{"type":"Point","coordinates":[0.63720703125,51.15178610143037]},"properties":{"_storage_options":{},"name":"marker he"}}],"_storage":{"displayOnLoad":true,"name":"new name","id":1668,"remoteData":{},"color":"LightSeaGreen","description":"test"}}'
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        modified_datalayer = DataLayer.objects.get(pk=self.datalayer.pk)
        self.assertEqual(modified_datalayer.name, name)
        # Test response is a json
        json = simplejson.loads(response.content)
        self.assertIn("id", json)
        self.assertEqual(self.datalayer.pk, json['id'])

    def test_should_not_be_possible_to_update_with_wrong_map_id_in_url(self):
        other_map = MapFactory(owner=self.user)
        url = reverse('datalayer_update', args=(other_map.pk, self.datalayer.pk))
        self.client.login(username=self.user.username, password="123123")
        name = "new name"
        post_data = {
            "name": name,
            "display_on_load": True,
            "geojson": '{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[-3.1640625,53.014783245859235],[-3.1640625,51.86292391360244],[-0.50537109375,51.385495069223204],[1.16455078125,52.38901106223456],[-0.41748046875,53.91728101547621],[-2.109375,53.85252660044951],[-3.1640625,53.014783245859235]]]},"properties":{"_storage_options":{},"name":"Ho god, sounds like a polygouine"}},{"type":"Feature","geometry":{"type":"LineString","coordinates":[[1.8017578124999998,51.16556659836182],[-0.48339843749999994,49.710272582105695],[-3.1640625,50.0923932109388],[-5.60302734375,51.998410382390325]]},"properties":{"_storage_options":{},"name":"Light line"}},{"type":"Feature","geometry":{"type":"Point","coordinates":[0.63720703125,51.15178610143037]},"properties":{"_storage_options":{},"name":"marker he"}}],"_storage":{"displayOnLoad":true,"name":"new name","id":1668,"remoteData":{},"color":"LightSeaGreen","description":"test"}}'
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 403)
        modified_datalayer = DataLayer.objects.get(pk=self.datalayer.pk)
        self.assertEqual(modified_datalayer.name, self.datalayer.name)

    def test_delete(self):
        url = reverse('datalayer_delete', args=(self.map.pk, self.datalayer.pk))
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, {}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DataLayer.objects.filter(pk=self.datalayer.pk).count(), 0)
        # Check that map has not been impacted
        self.assertEqual(Map.objects.filter(pk=self.map.pk).count(), 1)
        # Test response is a json
        json = simplejson.loads(response.content)
        self.assertIn("info", json)

    def test_should_not_be_possible_to_delete_with_wrong_map_id_in_url(self):
        other_map = MapFactory(owner=self.user)
        url = reverse('datalayer_delete', args=(other_map.pk, self.datalayer.pk))
        self.client.login(username=self.user.username, password="123123")
        response = self.client.post(url, {}, follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(DataLayer.objects.filter(pk=self.datalayer.pk).count(), 1)
