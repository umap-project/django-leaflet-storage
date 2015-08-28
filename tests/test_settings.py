from django.conf.global_settings import *   # noqa
SECRET_KEY = 'fake-key'
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    'django.contrib.sessions',
    'django.contrib.gis',
    "tests",
    "leaflet_storage",
]
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'testdb',
    }
}
ROOT_URLCONF = 'leaflet_storage.urls'
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
)
TEMPLATE_CONTEXT_PROCESSORS += (
    'django.template.context_processors.request',
)
LOGIN_URL = '/login/'
SITE_URL = 'http://domain.org'
