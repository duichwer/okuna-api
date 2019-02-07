"""
Django settings for openbook project.

Generated by 'django-admin startproject' using Django 1.11.16.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import logging.config
import os
import sys

import sentry_sdk
from django.utils.translation import gettext_lazy  as _
from dotenv import load_dotenv, find_dotenv
from sentry_sdk.integrations.django import DjangoIntegration

# Logging config
from openbook_common.utils.environment import EnvironmentChecker

LOGGING_CONFIG = None
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            # exact format is not important, this is the minimum information
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        }
    },
    'loggers': {
        # root logger
        '': {
            'level': 'INFO',
            'handlers': ['console'],
        },
    },
})

logger = logging.getLogger(__name__)

# Load dotenv
load_dotenv(verbose=True, dotenv_path=find_dotenv())

# The current execution environment
ENVIRONMENT = os.environ.get('ENVIRONMENT')

if not ENVIRONMENT:
    if 'test' in sys.argv:
        logger.info('No ENVIRONMENT variable found but test detected. Setting ENVIRONMENT=TEST_VALUE')
        ENVIRONMENT = EnvironmentChecker.TEST_VALUE
    else:
        raise NameError('ENVIRONMENT environment variable is required')

environment_checker = EnvironmentChecker(environment_value=ENVIRONMENT)

# Django SECRET_KEY
SECRET_KEY = os.environ.get('SECRET_KEY')

if not SECRET_KEY:
    raise NameError('SECRET_KEY environment variable is required')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = environment_checker.is_debug()
IS_PRODUCTION = environment_checker.is_production()
IS_BUILD = environment_checker.is_build()
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS')
if IS_PRODUCTION:
    if not ALLOWED_HOSTS:
        raise NameError('ALLOWED_HOSTS environment variable is required when running on a production environment')
    ALLOWED_HOSTS = [allowed_host.strip() for allowed_host in ALLOWED_HOSTS.split(',')]
else:
    if ALLOWED_HOSTS:
        logger.info('ALLOWED_HOSTS environment variable ignored.')
    ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    # Has to be before contrib admin
    # See https://django-modeltranslation.readthedocs.io/en/latest/installation.html#required-settings
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'django_nose',
    'storages',
    'django_media_fixtures',
    'openbook_common',
    'openbook_auth',
    'openbook_posts',
    'openbook_circles',
    'openbook_connections',
    'openbook_importer',
    'openbook_lists',
    'openbook_follows',
    'openbook_communities',
    'openbook_invitations',
    'openbook_tags',
    'openbook_categories',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'openbook_common.middleware.TimezoneMiddleware'
]

ROOT_URLCONF = 'openbook.urls'

AUTH_USER_MODEL = 'openbook_auth.User'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')

if IS_BUILD:
    NOSE_ARGS = [
        '--cover-erase',
        '--cover-package=.',
        '--with-spec', '--spec-color',
        '--with-coverage', '--cover-xml',
        '--verbosity=1', '--nologcapture']
else:
    NOSE_ARGS = [
        '--cover-erase',
        '--cover-package=.',
        '--with-spec', '--spec-color',
        '--with-coverage', '--cover-html',
        '--cover-html-dir=reports/cover', '--verbosity=1', '--nologcapture', '--nocapture']

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'openbook.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

if IS_BUILD or TESTING:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'open-book-api'
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('RDS_DB_NAME'),
            'USER': os.environ.get('RDS_USERNAME'),
            'PASSWORD': os.environ.get('RDS_PASSWORD'),
            'HOST': os.environ.get('RDS_HOSTNAME'),  # Or an IP Address that your DB is hosted on
            'PORT': os.environ.get('RDS_PORT'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4'
            },
        }
    }

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

# REST Framework config

REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    )
}

UNICODE_JSON = True

# The sentry DSN for error reporting
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if IS_PRODUCTION:
    if not SENTRY_DSN:
        raise NameError('SENTRY_DSN environment variable is required when running on a production environment')
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()]
    )
else:
    if SENTRY_DSN:
        logger.info('SENTRY_DSN environment variable ignored.')

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/


TIME_ZONE = 'Europe/Amsterdam'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

LANGUAGES = [
    ('es', _('Spanish')),
    ('en', _('English')),
]

LANGUAGE_CODE = 'en'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_URL = '/static/'

MEDIA_ROOT = os.environ.get('MEDIA_ROOT', './media')

MEDIA_URL = os.environ.get('MEDIA_URL', '/media/')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'openbook/static'),
)

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Openbook config

USERNAME_MAX_LENGTH = 30
POST_MAX_LENGTH = 560
POST_COMMENT_MAX_LENGTH = 280
PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = 100
CIRCLE_MAX_LENGTH = 100
COLOR_ATTR_MAX_LENGTH = 7
LIST_MAX_LENGTH = 100
PROFILE_NAME_MAX_LENGTH = 192
PROFILE_LOCATION_MAX_LENGTH = 64
PROFILE_BIO_MAX_LENGTH = 150
WORLD_CIRCLE_ID = 1
PASSWORD_RESET_TIMEOUT_DAYS = 1
COMMUNITY_NAME_MAX_LENGTH = 32
COMMUNITY_TITLE_MAX_LENGTH = 32
COMMUNITY_DESCRIPTION_MAX_LENGTH = 500
COMMUNITY_USER_ADJECTIVE_MAX_LENGTH = 16
COMMUNITY_USERS_ADJECTIVE_MAX_LENGTH = 16
COMMUNITY_RULES_MAX_LENGTH = 150
COMMUNITY_TAGS_MAX_AMOUNT = 5
TAG_NAME_MAX_LENGTH = 32
CATEGORY_NAME_MAX_LENGTH = 32
CATEGORY_TITLE_MAX_LENGTH = 64
CATEGORY_DESCRIPTION_MAX_LENGTH = 64

# Email Config

EMAIL_BACKEND = 'django_amazon_ses.EmailBackend'
AWS_SES_REGION = os.environ.get('AWS_SES_REGION')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
SERVICE_EMAIL_ADDRESS = os.environ.get('SERVICE_EMAIL_ADDRESS')
EMAIL_HOST = os.environ.get('EMAIL_HOST')

# AWS Storage config

AWS_PUBLIC_MEDIA_LOCATION = os.environ.get('AWS_PUBLIC_MEDIA_LOCATION')
AWS_STATIC_LOCATION = 'static'
AWS_PRIVATE_MEDIA_LOCATION = os.environ.get('AWS_PRIVATE_MEDIA_LOCATION')
AWS_DEFAULT_ACL = None

if IS_PRODUCTION:
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')
    AWS_S3_ENCRYPTION = True
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }

    STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, AWS_STATIC_LOCATION)

    STATICFILES_STORAGE = 'openbook.storage_backends.S3StaticStorage'

    DEFAULT_FILE_STORAGE = 'openbook.storage_backends.S3PublicMediaStorage'

    PRIVATE_FILE_STORAGE = 'openbook.storage_backends.S3PrivateMediaStorage'
