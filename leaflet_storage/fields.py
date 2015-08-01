import json

from django.db import models


class DictField(models.TextField):
    """
    A very simple field to store JSON in db.
    """

    __metaclass__ = models.SubfieldBase

    def get_prep_value(self, value):
        return json.dumps(value)

    def to_python(self, value):
        if not value:
            value = {}
        if isinstance(value, basestring):
            return json.loads(value)
        else:
            return value
