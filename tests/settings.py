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
    'django_nose',
)

MIDDLEWARE_CLASSES = ()  # so that Django 1.7 does not complain

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
