from django.contrib.gis.db import models


class PublicManager(models.GeoManager):

    def get_query_set(self):
        return super(PublicManager, self).get_query_set().filter(share_status=self.model.PUBLIC)
