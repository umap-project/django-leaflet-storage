import shutil
import tempfile

from django.conf import settings
from django.test.runner import DiscoverRunner


class Runner(DiscoverRunner):

    def setup_test_environment(self):
        "Create temp directory and update MEDIA_ROOT and default storage."
        super(Runner, self).setup_test_environment()
        settings._original_media_root = settings.MEDIA_ROOT
        self._temp_media = tempfile.mkdtemp()
        settings.MEDIA_ROOT = self._temp_media

    def teardown_test_environment(self):
        "Delete temp storage."
        super(Runner, self).teardown_test_environment()
        shutil.rmtree(self._temp_media, ignore_errors=True)
        settings.MEDIA_ROOT = settings._original_media_root
        del settings._original_media_root
