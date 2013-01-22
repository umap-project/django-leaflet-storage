from django.contrib.auth.models import AnonymousUser

from leaflet_storage.models import Marker, Map, Category
from .base import BaseTest, UserFactory, MarkerFactory, CategoryFactory


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


class LicenceModel(BaseTest):

    def test_licence_delete_should_not_remove_linked_maps(self):
        marker = MarkerFactory(category=self.category)
        self.assertEqual(marker.category.map.licence, self.licence)
        self.licence.delete()
        self.assertEqual(Map.objects.filter(pk=self.map.pk).count(), 1)
        self.assertEqual(Category.objects.filter(pk=self.category.pk).count(), 1)
        self.assertEqual(Marker.objects.filter(pk=marker.pk).count(), 1)


class CategoryModel(BaseTest):

    def test_features_should_be_locally_cached(self):
        MarkerFactory(category=self.category)
        MarkerFactory(category=self.category)
        MarkerFactory(category=self.category)
        self.category.features
        with self.assertNumQueries(0):
            self.category.features

    def test_categories_should_be_ordered_by_name(self):
        c4 = CategoryFactory(map=self.map, name="eeeeeee")
        c1 = CategoryFactory(map=self.map, name="1111111")
        c3 = CategoryFactory(map=self.map, name="ccccccc")
        c2 = CategoryFactory(map=self.map, name="aaaaaaa")
        self.assertEqual(
            list(self.map.category_set.all()),
            [c1, c2, c3, c4, self.category]
        )
