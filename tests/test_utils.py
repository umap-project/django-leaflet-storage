# -*- coding:utf-8 -*-

from django.test import TestCase
from django.utils import six

from leaflet_storage.utils import smart_decode


class SmartDecodeTests(TestCase):

    def test_should_return_unicode(self):
        self.assertTrue(isinstance(smart_decode('test'), six.string_types))
        self.assertTrue(isinstance(smart_decode(u'test'), six.string_types))

    def test_should_convert_utf8(self):
        self.assertEqual(smart_decode('é'), u"é")
