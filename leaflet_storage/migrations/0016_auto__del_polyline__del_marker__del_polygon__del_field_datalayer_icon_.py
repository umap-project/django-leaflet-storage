# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Polyline'
        db.delete_table(u'leaflet_storage_polyline')

        # Deleting model 'Marker'
        db.delete_table(u'leaflet_storage_marker')

        # Deleting model 'Polygon'
        db.delete_table(u'leaflet_storage_polygon')

        # Deleting field 'DataLayer.icon_class'
        db.delete_column(u'leaflet_storage_datalayer', 'icon_class')

        # Deleting field 'DataLayer.pictogram'
        db.delete_column(u'leaflet_storage_datalayer', 'pictogram_id')


    def backwards(self, orm):
        # Adding model 'Polyline'
        db.create_table(u'leaflet_storage_polyline', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('datalayer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.DataLayer'])),
            ('latlng', self.gf('django.contrib.gis.db.models.fields.LineStringField')(geography=True)),
            ('options', self.gf('leaflet_storage.fields.DictField')(null=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'leaflet_storage', ['Polyline'])

        # Adding model 'Marker'
        db.create_table(u'leaflet_storage_marker', (
            ('icon_class', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('datalayer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.DataLayer'])),
            ('pictogram', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.Pictogram'], null=True, blank=True)),
            ('latlng', self.gf('django.contrib.gis.db.models.fields.PointField')(geography=True)),
            ('options', self.gf('leaflet_storage.fields.DictField')(null=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'leaflet_storage', ['Marker'])

        # Adding model 'Polygon'
        db.create_table(u'leaflet_storage_polygon', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('datalayer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.DataLayer'])),
            ('latlng', self.gf('django.contrib.gis.db.models.fields.PolygonField')(geography=True)),
            ('options', self.gf('leaflet_storage.fields.DictField')(null=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'leaflet_storage', ['Polygon'])

        # Adding field 'DataLayer.icon_class'
        db.add_column(u'leaflet_storage_datalayer', 'icon_class',
                      self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True),
                      keep_default=False)

        # Adding field 'DataLayer.pictogram'
        db.add_column(u'leaflet_storage_datalayer', 'pictogram',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.Pictogram'], null=True, blank=True),
                      keep_default=False)


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'leaflet_storage.datalayer': {
            'Meta': {'ordering': "('name',)", 'object_name': 'DataLayer'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'display_on_load': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'geojson': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'map': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['leaflet_storage.Map']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'options': ('leaflet_storage.fields.DictField', [], {'null': 'True', 'blank': 'True'})
        },
        u'leaflet_storage.licence': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Licence'},
            'details': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'leaflet_storage.map': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Map'},
            'center': ('django.contrib.gis.db.models.fields.PointField', [], {'geography': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'edit_status': ('django.db.models.fields.SmallIntegerField', [], {'default': '3'}),
            'editors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'licence': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['leaflet_storage.Licence']", 'on_delete': 'models.SET_DEFAULT'}),
            'locate': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_maps'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'settings': ('leaflet_storage.fields.DictField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'tilelayer': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'maps'", 'null': 'True', 'to': u"orm['leaflet_storage.TileLayer']"}),
            'zoom': ('django.db.models.fields.IntegerField', [], {'default': '7'})
        },
        u'leaflet_storage.pictogram': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Pictogram'},
            'attribution': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'pictogram': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'})
        },
        u'leaflet_storage.tilelayer': {
            'Meta': {'ordering': "('rank', 'name')", 'object_name': 'TileLayer'},
            'attribution': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'maxZoom': ('django.db.models.fields.IntegerField', [], {'default': '18'}),
            'minZoom': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'rank': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'url_template': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['leaflet_storage']