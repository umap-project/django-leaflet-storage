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

    def test_can_set_item(self):
        d = {'locateControl': True}
        self.map.settings = d
        self.map.save()
        map_inst = Map.objects.get(pk=self.map.pk)
        map_inst.settings['color'] = 'DarkGreen'
        self.assertEqual(
            map_inst.settings['locateControl'],
            True
        )

    def test_should_return_a_dict_if_none(self):
        self.map.settings = None
        self.map.save()
        self.assertEqual(
            Map.objects.get(pk=self.map.pk).settings,
            {}
        )
