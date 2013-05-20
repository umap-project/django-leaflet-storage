# django-leaflet-storage changelog

## 0.3.0
- handle anonymous map creation
- Fix color no more displayed in map info box (cf #70)
- portuguese translation (thanks @FranciscoDS)
- fix bug when the map title was too long (making the slug too long, and so over the
  database limit for this field)
- add a setting to display map caption on map load (cf Leaflet.Storage#50)
- update to django 1.5
- first version of a CSV import
- add a Textarea in import form
- first version of data export (GeoJSON only for now)

## 0.2.0

- handle map settings management from front-end
- handle path styling options (https://github.com/yohanboniface/Leaflet.Storage/issues/26)
- remove Category.rank (https://github.com/yohanboniface/django-leaflet-storage/issues/46)
- Marker has now icon_class and pictogram fields (https://github.com/yohanboniface/django-leaflet-storage/issues/21)
- handle scale control
- basic short URL management
- fixed a bug where imports were failing if the category had a custom marker image

## 0.1.0

- first packaged version