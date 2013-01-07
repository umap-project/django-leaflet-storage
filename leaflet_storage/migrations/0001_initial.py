# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Licence'
        db.create_table('leaflet_storage_licence', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('details', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('leaflet_storage', ['Licence'])

        # Adding model 'TileLayer'
        db.create_table('leaflet_storage_tilelayer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('url_template', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('minZoom', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('maxZoom', self.gf('django.db.models.fields.IntegerField')(default=18)),
            ('attribution', self.gf('django.db.models.fields.CharField')(max_length=300)),
        ))
        db.send_create_signal('leaflet_storage', ['TileLayer'])

        # Adding model 'Map'
        db.create_table('leaflet_storage_map', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('center', self.gf('django.contrib.gis.db.models.fields.PointField')(geography=True)),
            ('zoom', self.gf('django.db.models.fields.IntegerField')(default=7)),
            ('locate', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('licence', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.Licence'], on_delete=models.SET_DEFAULT)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='owned_maps', to=orm['auth.User'])),
            ('edit_status', self.gf('django.db.models.fields.SmallIntegerField')(default=3)),
        ))
        db.send_create_signal('leaflet_storage', ['Map'])

        # Adding M2M table for field editors on 'Map'
        db.create_table('leaflet_storage_map_editors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('map', models.ForeignKey(orm['leaflet_storage.map'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('leaflet_storage_map_editors', ['map_id', 'user_id'])

        # Adding model 'MapToTileLayer'
        db.create_table('leaflet_storage_maptotilelayer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tilelayer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.TileLayer'])),
            ('map', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.Map'])),
            ('rank', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('leaflet_storage', ['MapToTileLayer'])

        # Adding model 'Pictogram'
        db.create_table('leaflet_storage_pictogram', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('attribution', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('pictogram', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
        ))
        db.send_create_signal('leaflet_storage', ['Pictogram'])

        # Adding model 'Category'
        db.create_table('leaflet_storage_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('map', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.Map'])),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('color', self.gf('django.db.models.fields.CharField')(default='DarkBlue', max_length=32)),
            ('pictogram', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.Pictogram'], null=True, blank=True)),
            ('icon_class', self.gf('django.db.models.fields.CharField')(default='Default', max_length=32)),
            ('display_on_load', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('rank', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('leaflet_storage', ['Category'])

        # Adding model 'Marker'
        db.create_table('leaflet_storage_marker', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.Category'])),
            ('latlng', self.gf('django.contrib.gis.db.models.fields.PointField')(geography=True)),
        ))
        db.send_create_signal('leaflet_storage', ['Marker'])

        # Adding model 'Polyline'
        db.create_table('leaflet_storage_polyline', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.Category'])),
            ('latlng', self.gf('django.contrib.gis.db.models.fields.LineStringField')(geography=True)),
        ))
        db.send_create_signal('leaflet_storage', ['Polyline'])

        # Adding model 'Polygon'
        db.create_table('leaflet_storage_polygon', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['leaflet_storage.Category'])),
            ('latlng', self.gf('django.contrib.gis.db.models.fields.PolygonField')(geography=True)),
        ))
        db.send_create_signal('leaflet_storage', ['Polygon'])


    def backwards(self, orm):
        # Deleting model 'Licence'
        db.delete_table('leaflet_storage_licence')

        # Deleting model 'TileLayer'
        db.delete_table('leaflet_storage_tilelayer')

        # Deleting model 'Map'
        db.delete_table('leaflet_storage_map')

        # Removing M2M table for field editors on 'Map'
        db.delete_table('leaflet_storage_map_editors')

        # Deleting model 'MapToTileLayer'
        db.delete_table('leaflet_storage_maptotilelayer')

        # Deleting model 'Pictogram'
        db.delete_table('leaflet_storage_pictogram')

        # Deleting model 'Category'
        db.delete_table('leaflet_storage_category')

        # Deleting model 'Marker'
        db.delete_table('leaflet_storage_marker')

        # Deleting model 'Polyline'
        db.delete_table('leaflet_storage_polyline')

        # Deleting model 'Polygon'
        db.delete_table('leaflet_storage_polygon')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'leaflet_storage.category': {
            'Meta': {'ordering': "['rank']", 'object_name': 'Category'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'DarkBlue'", 'max_length': '32'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'display_on_load': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'icon_class': ('django.db.models.fields.CharField', [], {'default': "'Default'", 'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'map': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['leaflet_storage.Map']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'pictogram': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['leaflet_storage.Pictogram']", 'null': 'True', 'blank': 'True'}),
            'rank': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'leaflet_storage.licence': {
            'Meta': {'object_name': 'Licence'},
            'details': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'leaflet_storage.map': {
            'Meta': {'object_name': 'Map'},
            'center': ('django.contrib.gis.db.models.fields.PointField', [], {'geography': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'edit_status': ('django.db.models.fields.SmallIntegerField', [], {'default': '3'}),
            'editors': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'licence': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['leaflet_storage.Licence']", 'on_delete': 'models.SET_DEFAULT'}),
            'locate': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_maps'", 'to': "orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'tilelayers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['leaflet_storage.TileLayer']", 'through': "orm['leaflet_storage.MapToTileLayer']", 'symmetrical': 'False'}),
            'zoom': ('django.db.models.fields.IntegerField', [], {'default': '7'})
        },
        'leaflet_storage.maptotilelayer': {
            'Meta': {'ordering': "['rank', 'tilelayer__name']", 'object_name': 'MapToTileLayer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'map': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['leaflet_storage.Map']"}),
            'rank': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'tilelayer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['leaflet_storage.TileLayer']"})
        },
        'leaflet_storage.marker': {
            'Meta': {'object_name': 'Marker'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['leaflet_storage.Category']"}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latlng': ('django.contrib.gis.db.models.fields.PointField', [], {'geography': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'leaflet_storage.pictogram': {
            'Meta': {'object_name': 'Pictogram'},
            'attribution': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'pictogram': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'})
        },
        'leaflet_storage.polygon': {
            'Meta': {'object_name': 'Polygon'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['leaflet_storage.Category']"}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latlng': ('django.contrib.gis.db.models.fields.PolygonField', [], {'geography': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'leaflet_storage.polyline': {
            'Meta': {'object_name': 'Polyline'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['leaflet_storage.Category']"}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latlng': ('django.contrib.gis.db.models.fields.LineStringField', [], {'geography': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'leaflet_storage.tilelayer': {
            'Meta': {'object_name': 'TileLayer'},
            'attribution': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'maxZoom': ('django.db.models.fields.IntegerField', [], {'default': '18'}),
            'minZoom': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url_template': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['leaflet_storage']