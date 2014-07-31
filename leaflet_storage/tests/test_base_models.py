from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse

from leaflet_storage.models import Map, DataLayer
from .base import BaseTest, UserFactory, DataLayerFactory, MapFactory


class MapModel(BaseTest):

    def test_anonymous_can_edit_if_status_anonymous(self):
        anonymous = AnonymousUser()
        self.map.edit_status = self.map.ANONYMOUS
        self.map.save()
        self.assertTrue(self.map.can_edit(anonymous))

    def test_anonymous_cannot_edit_if_not_status_anonymous(self):
        anonymous = AnonymousUser()
        self.map.edit_status = self.map.OWNER
        self.map.save()
        self.assertFalse(self.map.can_edit(anonymous))

    def test_non_editors_can_edit_if_status_anonymous(self):
        lambda_user = UserFactory(username="John", password="123123")
        self.map.edit_status = self.map.ANONYMOUS
        self.map.save()
        self.assertTrue(self.map.can_edit(lambda_user))

    def test_non_editors_cannot_edit_if_not_status_anonymous(self):
        lambda_user = UserFactory(username="John", password="123123")
        self.map.edit_status = self.map.OWNER
        self.map.save()
        self.assertFalse(self.map.can_edit(lambda_user))

    def test_editors_cannot_edit_if_status_owner(self):
        editor = UserFactory(username="John", password="123123")
        self.map.edit_status = self.map.OWNER
        self.map.save()
        self.assertFalse(self.map.can_edit(editor))

    def test_editors_can_edit_if_status_editors(self):
        editor = UserFactory(username="John", password="123123")
        self.map.edit_status = self.map.EDITORS
        self.map.editors.add(editor)
        self.map.save()
        self.assertTrue(self.map.can_edit(editor))

    def test_logged_in_user_should_be_allowed_for_anonymous_map_with_anonymous_edit_status(self):
        self.map.owner = None
        self.map.edit_status = self.map.ANONYMOUS
        self.map.save()
        editor = UserFactory(username="John", password="123123")
        url = reverse('map_update', kwargs={'map_id': self.map.pk})
        request = self.request_factory.get(url)
        request.user = editor
        self.assertTrue(self.map.can_edit(editor, request))

    def test_clone_should_return_new_instance(self):
        clone = self.map.clone()
        self.assertNotEqual(self.map.pk, clone.pk)
        self.assertEqual(u"Clone of " + self.map.name, clone.name)
        self.assertEqual(self.map.settings, clone.settings)
        self.assertEqual(self.map.center, clone.center)
        self.assertEqual(self.map.zoom, clone.zoom)
        self.assertEqual(self.map.licence, clone.licence)
        self.assertEqual(self.map.tilelayer, clone.tilelayer)

    def test_clone_should_keep_editors(self):
        editor = UserFactory(username="Mark")
        self.map.editors.add(editor)
        clone = self.map.clone()
        self.assertNotEqual(self.map.pk, clone.pk)
        self.assertIn(editor, self.map.editors.all())
        self.assertIn(editor, clone.editors.all())

    def test_clone_should_update_owner_if_passer(self):
        new_owner = UserFactory(username="Mark")
        clone = self.map.clone(owner=new_owner)
        self.assertNotEqual(self.map.pk, clone.pk)
        self.assertNotEqual(self.map.owner, clone.owner)
        self.assertEqual(new_owner, clone.owner)

    def test_clone_should_clone_datalayers_and_features_too(self):
        clone = self.map.clone()
        self.assertNotEqual(self.map.pk, clone.pk)
        self.assertEqual(self.map.datalayer_set.count(), 1)
        datalayer = clone.datalayer_set.all()[0]
        self.assertIn(self.datalayer, self.map.datalayer_set.all())
        self.assertNotEqual(self.datalayer.pk, datalayer.pk)
        self.assertEqual(self.datalayer.name, datalayer.name)
        self.assertIsNotNone(datalayer.geojson)
        self.assertNotEqual(datalayer.geojson.path, self.datalayer.geojson.path)

    def test_publicmanager_should_get_only_public_maps(self):
        self.map.share_status = self.map.PUBLIC
        open_map = MapFactory(owner=self.user, licence=self.licence, share_status=Map.OPEN)
        private_map = MapFactory(owner=self.user, licence=self.licence, share_status=Map.PRIVATE)
        self.assertIn(self.map, Map.public.all())
        self.assertNotIn(open_map, Map.public.all())
        self.assertNotIn(private_map, Map.public.all())


class LicenceModel(BaseTest):

    def test_licence_delete_should_not_remove_linked_maps(self):
        self.licence.delete()
        self.assertEqual(Map.objects.filter(pk=self.map.pk).count(), 1)
        self.assertEqual(DataLayer.objects.filter(pk=self.datalayer.pk).count(), 1)


class DataLayerModel(BaseTest):

    def test_datalayers_should_be_ordered_by_name(self):
        c4 = DataLayerFactory(map=self.map, name="eeeeeee")
        c1 = DataLayerFactory(map=self.map, name="1111111")
        c3 = DataLayerFactory(map=self.map, name="ccccccc")
        c2 = DataLayerFactory(map=self.map, name="aaaaaaa")
        self.assertEqual(
            list(self.map.datalayer_set.all()),
            [c1, c2, c3, c4, self.datalayer]
        )

    def test_clone_should_return_new_instance(self):
        clone = self.datalayer.clone()
        self.assertNotEqual(self.datalayer.pk, clone.pk)
        self.assertEqual(self.datalayer.name, clone.name)
        self.assertEqual(self.datalayer.map, clone.map)

    def test_clone_should_update_map_if_passed(self):
        new_map = MapFactory(owner=self.user, licence=self.licence)
        clone = self.datalayer.clone(map_inst=new_map)
        self.assertNotEqual(self.datalayer.pk, clone.pk)
        self.assertEqual(self.datalayer.name, clone.name)
        self.assertNotEqual(self.datalayer.map, clone.map)
        self.assertEqual(new_map, clone.map)

    def test_clone_should_clone_geojson_too(self):
        clone = self.datalayer.clone()
        self.assertNotEqual(self.datalayer.pk, clone.pk)
        self.assertIsNotNone(clone.geojson)
        self.assertNotEqual(clone.geojson.path, self.datalayer.geojson.path)

    def test_upload_to_should_split_map_id(self):
        self.map.pk = 302
        self.datalayer.name = "a name"
        self.assertEqual(
            DataLayer.upload_to(self.datalayer, None),
            "datalayer/2/0/302/a-name.geojson"
        )

    def test_upload_to_should_never_has_empty_name(self):
        self.map.pk = 1
        self.datalayer.name = ""
        self.assertEqual(
            DataLayer.upload_to(self.datalayer, None),
            "datalayer/1/1/untitled.geojson"
        )

    def test_upload_to_should_cut_too_long_name(self):
        self.map.pk = 1
        self.datalayer.name = "name" * 20
        self.assertEqual(
            DataLayer.upload_to(self.datalayer, None),
            "datalayer/1/1/namenamenamenamenamenamenamenamenamenamenamenamena.geojson"
        )
