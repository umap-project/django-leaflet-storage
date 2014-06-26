import io
import os

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.utils.translation import to_locale


class Command(BaseCommand):

    def handle(self, *args, **options):
        for code, name in settings.LANGUAGES:
            code = to_locale(code)
            print "Processing", name
            path = finders.find('storage/src/locale/{code}.json'.format(code=code))
            if not path:
                print "No file for", code, "Skipping"
            else:
                with io.open(path, "r", encoding="utf-8") as f:
                    print "Found file", path
                    self.render(code, f.read())

    def render(self, code, json):
        path = os.path.join(
            settings.STATIC_ROOT,
            "storage/src/locale/",
            "{code}.js".format(code=code)
        )
        with io.open(path, "w", encoding="utf-8") as f:
            content = render_to_string('leaflet_storage/locale.js', {
                "locale": json,
                "locale_code": code
            })
            print "Exporting to", path
            f.write(content)
