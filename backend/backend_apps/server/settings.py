"""
Django settings for server project.

Generated by 'django-admin startproject' using Django 3.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import os
from pathlib import Path

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = bool(int(os.environ.get('DEBUG', default=0)))

ALLOWED_HOSTS = ['64.227.106.224', 'localhost', '127.0.0.1']

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # my apps
    'image_classifier',
    # third party
    'rest_framework.authtoken',
    'rest_auth',
    'corsheaders',
    'rest_framework',
]
CORS_ORIGIN_ALLOW_ALL = True

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django_cprofile_middleware.middleware.ProfilerMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

if not DEBUG:
    MIDDLEWARE.remove('django_cprofile_middleware.middleware.ProfilerMiddleware')

SESSION_ENGINE = "django.contrib.sessions.backends.file"

ROOT_URLCONF = 'server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'server.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': os.environ.get('SQL_ENGINE'),
        'HOST': os.environ.get('SQL_HOST'),
        'NAME': os.environ.get('SQL_DATABASE'),
        'USER': os.environ.get('SQL_USER'),
        'PASSWORD': os.environ.get('SQL_PASSWORD'),
        'PORT': os.environ.get('SQL_PORT'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    )
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# # Get loglevel from env
# LOGLEVEL = os.getenv('DJANGO_LOGLEVEL', 'info').upper()

LOG_LEVEL = "INFO" if DEBUG else "WARNING"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    # "formatters": {
    #     "default": {
    #         "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d %(funcName)s - %(message)s"
    #     },
    # },
    "handlers": {"console": {"class": "logging.StreamHandler"}},  # , "formatter": "default"
    "loggers": {
        "": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
        },
    }
}

if not DEBUG:
    del LOGGING["loggers"][""]["handlers"]
    del LOGGING["handlers"]

ENABLE_SENTRY = False

if not DEBUG and ENABLE_SENTRY:
    sentry_sdk.init(
        dsn=os.environ.get('sentry_secret'),
        integrations=[DjangoIntegration()],

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=0.5,

        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True
    )

# Redis and Celery Conf
# CELERY_IMPORTS = ['apps.image_classifier.tasks']
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_BROKER")
CELERY_ACKS_LATE = True
CELERY_SEND_EVENTS = False
CELERY_IGNORE_RESULT = True
BROKER_POOL_LIMIT = 1
BROKER_HEARTBEAT = None
BROKER_CONNECTION_TIMEOUT = 30
CELERY_RESULT_BACKEND = None
CELERY_EVENT_QUEUE_EXPIRES = 60
#CELERYD_PREFETCH_MULTIPLIER = 0


STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

IMAGES_DIR = os.path.join(MEDIA_ROOT, 'images')

if not os.path.exists(MEDIA_ROOT) or not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("CELERY_BROKER"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
