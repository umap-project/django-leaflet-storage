from leaflet_storage.models import Map
from .base import BaseTest


class DictFieldTest(BaseTest):

    def test_can_use_dict(self):
        d = {'locateControl': True}
        self.map.settings = d
        self.map.save()
        self.assertEqual(
            Map.objects.get(pk=self.map.pk).settings,
            d
        )

    def test_should_return_a_dict_if_none(self):
        self.map.settings = None
        self.map.save()
        self.assertEqual(
            Map.objects.get(pk=self.map.pk).settings,
            {}
        )
