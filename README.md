[![Build Status](https://travis-ci.org/umap-project/django-leaflet-storage.svg)](https://travis-ci.org/umap-project/django-leaflet-storage)
[![Requirements Status](https://requires.io/github/umap-project/django-leaflet-storage/requirements.svg?branch=master)](https://requires.io/github/umap-project/django-leaflet-storage/requirements/?branch=master)

# Django-Leaflet-Storage

Provide collaborative maps for your Django project.

Django-Leaflet-Storage is a backend for [Leaflet.Storage](https://github.com/yohanboniface/Leaflet.Storage), built on top of [Geodjango](http://geodjango.org/) and [Leaflet](http://leafletjs.com).

Check the demo [here](http://umap.fluv.io)


## Installation

You will need a geo aware database. See [Geodjango doc](https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/) for backend installation.

Then you can pip install the app:

    pip install django-leaflet-storage


Add `leaflet_storage` to you apps:

    INSTALLED_APPS = (
        ...
        "leaflet_storage",
    )

Include `leaflet_storage` urls:

    (r'', include('leaflet_storage.urls')),

Create tables:

    python manage.py migrate


## Basic usage

From the Django admin (for now), you need to create at least:

- one TileLayer instance
- one Licence instance

Then, go to the map creation page (something like http://localhost:8017/map/new), and you will be able to add features (Marker, Polygon...).
