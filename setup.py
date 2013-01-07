#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs

from setuptools import setup, find_packages

import leaflet_storage

long_description = codecs.open('README.rst', "r", "utf-8").read()

with open('requirements.pip') as reqs:
    install_requires = [
        line for line in reqs.read().split('\n') if (line and not
                                                     line.startswith(('--', 'git')))
    ]

setup(
    name="django-leaflet-storage",
    version=leaflet_storage.__version__,
    author=leaflet_storage.__author__,
    author_email=leaflet_storage.__contact__,
    description=leaflet_storage.__doc__,
    keywords="django leaflet geodjango",
    url=leaflet_storage.__homepage__,
    download_url="https://github.com/yohanboniface/django-leaflet-storage/downloads",
    packages=find_packages(),
    include_package_data=True,
    platforms=["any"],
    zip_safe=True,
    install_requires=install_requires,
    long_description=long_description,

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        #"License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
    ],
)
