from django.contrib.auth.models import AnonymousUser

from leaflet_storage.models import Marker, Map, DataLayer
from .base import BaseTest, UserFactory, MarkerFactory, DataLayerFactory,\
                  PolygonFactory, PolylineFactory, MapFactory


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

    def test_clone_should_return_new_instance(self):
        clone = self.map.clone()
        self.assertNotEqual(self.map.pk, clone.pk)
        self.assertEqual(self.map.name, clone.name)
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
        marker = MarkerFactory(datalayer=self.datalayer)
        clone = self.map.clone()
        self.assertNotEqual(self.map.pk, clone.pk)
        self.assertEqual(self.map.datalayer_set.count(), 1)
        datalayer = clone.datalayer_set.all()[0]
        self.assertIn(self.datalayer, self.map.datalayer_set.all())
        self.assertNotEqual(self.datalayer.pk, datalayer.pk)
        self.assertEqual(self.datalayer.name, datalayer.name)
        self.assertEqual(len(datalayer.features), 1)
        new_marker = datalayer.features[0]
        self.assertNotEqual(marker.pk, new_marker.pk)
        self.assertEqual(marker.name, new_marker.name)
        self.assertEqual(marker.options, new_marker.options)


class LicenceModel(BaseTest):

    def test_licence_delete_should_not_remove_linked_maps(self):
        marker = MarkerFactory(datalayer=self.datalayer)
        self.assertEqual(marker.datalayer.map.licence, self.licence)
        self.licence.delete()
        self.assertEqual(Map.objects.filter(pk=self.map.pk).count(), 1)
        self.assertEqual(DataLayer.objects.filter(pk=self.datalayer.pk).count(), 1)
        self.assertEqual(Marker.objects.filter(pk=marker.pk).count(), 1)


class DataLayerModel(BaseTest):

    def test_features_should_be_locally_cached(self):
        MarkerFactory(datalayer=self.datalayer)
        MarkerFactory(datalayer=self.datalayer)
        MarkerFactory(datalayer=self.datalayer)
        self.datalayer.features
        with self.assertNumQueries(0):
            self.datalayer.features

    def test_datalayers_should_be_ordered_by_name(self):
        c4 = DataLayerFactory(map=self.map, name="eeeeeee")
        c1 = DataLayerFactory(map=self.map, name="1111111")
        c3 = DataLayerFactory(map=self.map, name="ccccccc")
        c2 = DataLayerFactory(map=self.map, name="aaaaaaa")
        self.assertEqual(
            list(self.map.datalayer_set.all()),
            [c1, c2, c3, c4, self.datalayer]
        )

    def test_features_should_be_mixed_and_ordered_by_name(self):
        f4 = MarkerFactory(datalayer=self.datalayer, name="eeee")
        f1 = PolygonFactory(datalayer=self.datalayer, name="1111")
        f3 = PolylineFactory(datalayer=self.datalayer, name="cccc")
        f2 = MarkerFactory(datalayer=self.datalayer, name="aaaa")
        self.assertEqual(
            list(self.datalayer.features),
            [f1, f2, f3, f4]
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

    def test_clone_should_clone_features_too(self):
        marker = MarkerFactory(datalayer=self.datalayer)
        clone = self.datalayer.clone()
        self.assertNotEqual(self.datalayer.pk, clone.pk)
        self.assertEqual(len(clone.features), 1)
        cloned_marker = clone.features[0]
        self.assertNotEqual(marker.pk, cloned_marker.pk)
        self.assertEqual(marker.name, cloned_marker.name)


class MarkerModel(BaseTest):

    def test_clone_should_return_new_instance(self):
        original = MarkerFactory(datalayer=self.datalayer)
        clone = original.clone()
        self.assertNotEqual(original.pk, clone.pk)
        self.assertEqual(original.name, clone.name)
        self.assertEqual(original.datalayer, clone.datalayer)
        self.assertEqual(original.latlng, clone.latlng)

    def test_clone_should_update_datalayer_if_passed(self):
        datalayer = DataLayerFactory(map=self.map)
        original = MarkerFactory(datalayer=self.datalayer)
        clone = original.clone(datalayer=datalayer)
        self.assertNotEqual(original.pk, clone.pk)
        self.assertNotEqual(original.datalayer, clone.datalayer)
        self.assertEqual(datalayer, clone.datalayer)
        self.assertEqual(original.name, clone.name)
        self.assertEqual(original.latlng, clone.latlng)
