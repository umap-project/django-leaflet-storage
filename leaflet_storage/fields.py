import simplejson

from django.db import models
from django.conf import settings


class DictField(models.TextField):
    """
    A very simple field to store JSON in db.
    """

    __metaclass__ = models.SubfieldBase

    def get_prep_value(self, value):
        return simplejson.dumps(value)

    def to_python(self, value):
        if not value:
            value = {}
        if isinstance(value, basestring):
            return simplejson.loads(value)
        else:
            return value

if "south" in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^leaflet_storage\.fields\.DictField"])
