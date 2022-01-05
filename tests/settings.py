DEBUG = True
SECRET_KEY = 'secret'

DATABASES = {
    'default': {
        'NAME': 'gm2m',
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'gm2m',
)

MIDDLEWARE_CLASSES = ()  # so that Django 1.7 does not complain

ROOT_URLCONF = 'tests.urls'
