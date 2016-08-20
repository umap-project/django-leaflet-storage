import pytest
from django.core.files.base import ContentFile

from .base import DataLayerFactory, MapFactory

pytestmark = pytest.mark.django_db


def test_datalayers_should_be_ordered_by_rank(map, datalayer):
    datalayer.rank = 5
    datalayer.save()
    c4 = DataLayerFactory(map=map, rank=4)
    c1 = DataLayerFactory(map=map, rank=1)
    c3 = DataLayerFactory(map=map, rank=3)
    c2 = DataLayerFactory(map=map, rank=2)
    assert list(map.datalayer_set.all()) == [c1, c2, c3, c4, datalayer]


def test_upload_to(map, datalayer):
    map.pk = 302
    datalayer.pk = 17
    assert datalayer.upload_to().startswith('datalayer/2/0/302/17_')


def test_save_should_use_pk_as_name(map, datalayer):
    assert "/{}_".format(datalayer.pk) in datalayer.geojson.name


def test_same_geojson_file_name_will_be_suffixed(map, datalayer):
    before = datalayer.geojson.name
    datalayer.geojson.save(before, ContentFile("{}"))
    assert datalayer.geojson.name != before
    assert "/{}_".format(datalayer.pk) in datalayer.geojson.name


def test_clone_should_return_new_instance(map, datalayer):
    clone = datalayer.clone()
    assert datalayer.pk != clone.pk
    assert datalayer.name == clone.name
    assert datalayer.map == clone.map


def test_clone_should_update_map_if_passed(datalayer, user, licence):
    map = MapFactory(owner=user, licence=licence)
    clone = datalayer.clone(map_inst=map)
    assert datalayer.pk != clone.pk
    assert datalayer.name == clone.name
    assert datalayer.map != clone.map
    assert map == clone.map


def test_clone_should_clone_geojson_too(datalayer):
    clone = datalayer.clone()
    assert datalayer.pk != clone.pk
    assert clone.geojson is not None
    assert clone.geojson.path != datalayer.geojson.path
