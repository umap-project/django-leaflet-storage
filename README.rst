---------
Important
---------

Version 0.5 totally review the modelisation: instead of one model per feature (Marker, Polygon, Polyline),
now all data are stored as geojson attached to the DataLayer.


======================
Django-Leaflet-Storage
======================

Provide collaborative maps for your Django project.

Django-Leaflet-Storage is a backend for `Leaflet.Storage <https://github.com/yohanboniface/Leaflet.Storage>`_, built on top of `Geodjango <http://geodjango.org/>`_ and `Leaflet <http://leaflet.cloudmade.com/>`_.

Check the demo `here <http://umap.fluv.io>`_




-----------------------
Maintained repositories
-----------------------

* `Github <https://github.com/yohanboniface/django-leaflet-storage>`_
* `Bitbucket <https://bitbucket.org/yohanboniface/django-leaflet-storage>`_


------------
Installation
------------

.. note::
   You will need a geo aware database. See `Geodjango doc <https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/>`_ for backend installation.

Then you can pip install the app::

    pip install django-leaflet-storage

Add `leaflet_storage` to you apps::

    INSTALLED_APPS = (
        ...
        "leaflet_storage",
    )

Include `leaflet_storage` urls::

   (r'', include('leaflet_storage.urls')),

Create tables (add `--migrate` if you are using `South <http://south.aeracode.org/>`_::

    python manage.py syncdb --migrate


-----------
Basic usage
-----------

From the Django admin (for now), you need to create at least:

- one TileLayer instance
- one Licence instance

Then, go to the map creation page (something like http://localhost:8017/map/new), and you will be able to add features (Marker, Polygon...).
