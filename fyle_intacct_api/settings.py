"""
Django settings for fyle_intacct_api project.

Generated by 'django-admin startproject' using Django 3.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""
import sys
import os
from logging.config import dictConfig
from .logging_middleware import WorkerIDFilter

import dj_database_url

from .sentry import Sentry

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.environ.get('DEBUG') == 'True' else False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS').split(',')

ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
E2E_TESTS_CLIENT_SECRET = os.environ.get('E2E_TESTS_CLIENT_SECRET')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Installed Apps
    'rest_framework',
    'corsheaders',
    'django_q',
    'fyle_rest_auth',
    'fyle_accounting_mappings',

    # User Created Apps
    'apps.users',
    'apps.workspaces',
    'apps.fyle',
    'apps.sage_intacct',
    'apps.tasks',
    'apps.mappings',
    'apps.internal',

    'fyle_accounting_library.common_resources',
]

MIDDLEWARE = [
    'request_logging.middleware.LoggingMiddleware',
    'fyle_intacct_api.logging_middleware.LogPostRequestMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'fyle_intacct_api.logging_middleware.ErrorHandlerMiddleware',
]

ROOT_URLCONF = 'fyle_intacct_api.urls'
APPEND_SLASH = False

AUTH_USER_MODEL = 'users.User'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'workspaces/templates')],
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

FYLE_REST_AUTH_SERIALIZERS = {
    'USER_DETAILS_SERIALIZER': 'apps.users.serializers.UserSerializer'
}

FYLE_REST_AUTH_SETTINGS = {
    'async_update_user': True
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        'apps.workspaces.permissions.WorkspacePermissions'
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'fyle_rest_auth.authentication.FyleJWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100
}

WSGI_APPLICATION = 'fyle_intacct_api.wsgi.application'

SERVICE_NAME = os.environ.get('SERVICE_NAME')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{levelname} %s {asctime} {name} {worker_id} {message}' % SERVICE_NAME, 'style': '{'
        },
        'verbose': {
            'format': '{levelname} %s {asctime} {module} {message} ' % SERVICE_NAME, 'style': '{'
        },
        'requests': {
            'format': 'request {levelname} %s {asctime} {message}' % SERVICE_NAME, 'style': '{'
        }
    },
    'filters': {
        'worker_id': {
            '()': WorkerIDFilter,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'filters': ['worker_id'],
        },
        'request_logs': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'requests'
        },
        'debug_logs': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'sageintacctsdk.apis.api_base': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True
        },
        'django.request': {'handlers': ['request_logs'], 'propagate': False},
    },
}

dictConfig(LOGGING)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'auth_cache',
    }
}

Q_CLUSTER = {
    'name': 'fyle_intacct_api',
    # The number of tasks will be stored in django q tasks
    "save_limit": 100000,
    'retry': 14400,
    'timeout': 900, # 15 mins
    'catch_up': False,
    'workers': 4,
    # How many tasks are kept in memory by a single cluster.
    # Helps balance the workload and the memory overhead of each individual cluster
    'queue_limit': 10,
    'cached': False,
    'orm': 'default',
    'ack_failures': True,
    'poll': 5,
    'max_attempts': 1,
    'attempt_count': 1,
    # The number of tasks a worker will process before recycling.
    # Useful to release memory resources on a regular basis.
    'recycle': os.environ.get('DJANGO_Q_RECYCLE', 50),
    # The maximum resident set size in kilobytes before a worker will recycle and release resources.
    # Useful for limiting memory usage.
    'max_rss': 100000, # 100mb
    'ALT_CLUSTERS': {
        'import': {
            'retry': 14400,
            'timeout': 900
        },
    }
}


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    'default': dj_database_url.config()
}


DATABASES['cache_db'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'cache.db'
}

DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True

DATABASE_ROUTERS = ['fyle_intacct_api.cache_router.CacheRouter']

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

# Fyle Settings
BRAND_ID = os.environ.get('BRAND_ID', 'fyle')
API_URL = os.environ.get('API_URL')
FYLE_TOKEN_URI = os.environ.get('FYLE_TOKEN_URI')
FYLE_CLIENT_ID = os.environ.get('FYLE_CLIENT_ID')
FYLE_CLIENT_SECRET = os.environ.get('FYLE_CLIENT_SECRET')
FYLE_BASE_URL = os.environ.get('FYLE_BASE_URL')
FYLE_JOBS_URL = os.environ.get('FYLE_JOBS_URL')
FYLE_APP_URL = os.environ.get('APP_URL')
FYLE_EXPENSE_URL = os.environ.get('FYLE_APP_URL')
INTEGRATIONS_SETTINGS_API = os.environ.get('INTEGRATIONS_SETTINGS_API')
INTACCT_INTEGRATION_APP_URL = os.environ.get('INTACCT_INTEGRATION_APP_URL')
INTEGRATIONS_APP_URL = os.environ.get('INTEGRATIONS_APP_URL')
HELP_ARTICLE_DOMAIN = os.environ.get('HELP_ARTICLE_DOMAIN')

# Sage Intacct Settings
SI_SENDER_ID = os.environ.get('SI_SENDER_ID')
SI_SENDER_PASSWORD = os.environ.get('SI_SENDER_PASSWORD')
SENDGRID_API_KEY = os.environ.get('SENDGRID_KEY')
EMAIL = os.environ.get('SENDGRID_EMAIL')
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'

CACHE_EXPIRY = 3600

CORS_ORIGIN_ALLOW_ALL = True

# Sentry
Sentry.init()

CORS_ALLOW_HEADERS = [
    'sentry-trace',
    'authorization',
    'content-type'
]


# Toggle sandbox mode (when running in DEBUG mode)
SENDGRID_SANDBOX_MODE_IN_DEBUG=False

# echo to stdout or any other file-like object that is passed to the backend via the stream kwarg.
SENDGRID_ECHO_TO_STDOUT=True
