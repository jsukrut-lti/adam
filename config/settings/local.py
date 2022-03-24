from .base import *

DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'WileyCalculator1',
        'USER': 'postgres',
        'PASSWORD': 'jayesh123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


#INSTALLED_APPS += ['debug_toolbar',]