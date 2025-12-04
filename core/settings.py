from pathlib import Path
import os

import environ

from storages.backends.s3boto3 import S3Boto3Storage

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    SECRET_KEY=(str, ""),
    CSRF_TRUSTED_ORIGINS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
    AWS_ACCESS_KEY_ID=(str, ""),
    AWS_SECRET_ACCESS_KEY=(str, ""),
    AWS_STORAGE_BUCKET_NAME=(str, ""),
    AWS_STORAGE_BUCKET_FOLDER=(str, ""),
    DATABASE_URL=(str, ""),
    EMAIL_HOST=(str, ""),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
    DEFAULT_FROM_EMAIL=(str, ""),
    EMAIL_PORT=(int, 587),
    EMAIL_USE_TLS=(bool, True),
    SERVER_EMAIL=(str, ""),
    TELEGRAM_BOT_TOKEN=(str, ""),
    TELEGRAM_CHAT_ID=(str, "")
)

environ.FileAwareEnv.read_env(os.path.join(BASE_DIR, ".env"))


SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")


CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")


INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    
    'rest_framework',
    'drf_spectacular',
    'django_filters',
    'corsheaders',
    'tinymce',
    'django_select2',
    'storages',

    'payments',

]


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'core.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = "core.asgi.application"


DATABASES = {
    'default': env.db(),
}


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
ALLOWED_DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'xls', 'xlsx']


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


LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'Europe/Moscow'
DATETIME_FORMAT = "%d.%m.%Y %H:%M"
DATE_FORMAT = "%d.%m.%Y"
USE_L10N = True
USE_I18N = True
USE_TZ = True


LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ]
}


SPECTACULAR_SETTINGS = {
    "TITLE": "API для системы выплат",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "DESCRIPTION": "API для управления заявками на выплату",
    "TAGS": [
        {"name": "Платежи", "description": "Операции с заявками на выплату"},
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": True,
}


TINYMCE_DEFAULT_CONFIG = {
    'height': 500,
    'menubar': False,
    'plugins': 'link image code',
    'toolbar': 'undo redo | bold italic | link image | code',
    'content_css': '/static/css/tinymce.css',
}


UNFOLD = {
    "SITE_TITLE": "Система выплат",
    "SITE_HEADER": "Система выплат",
    "SITE_SYMBOL": "home",
    "WYSIWYG_OPTIONS": {
        "height": 400,
        "plugins": ["link", "lists"],
        "toolbar": "undo redo | bold italic | link",
    },
    "STYLES": [
        "/static/css/custom_admin.css",
    ],
}

# Celery настройки
# if env("DJANGO_ENV") == "production":
#     # Для продакшена используем Redis в Docker
#     CELERY_BROKER_URL = 'redis://redis:6379/0'
#     CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
# else:
#     # Для разработки используем локальный Redis
#     CELERY_BROKER_URL = 'redis://localhost:6379/0'
#     CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# CELERY_BEAT_SCHEDULE = {
#     'expire-pending-bookings-every-hour': {
#         'task': 'bookings.tasks.expire_pending_bookings_task',
#         'schedule': 3600,  # каждый час
#     },
# }

# # Дополнительные настройки Celery для продакшена
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TIMEZONE = 'Europe/Moscow'
# CELERY_ENABLE_UTC = True


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

FORM_EMAIL_RECIPIENTS = [
    env("DEFAULT_FROM_EMAIL"),
]

ADMIN_URL = "/admin/"


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'clients': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'cars': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'bookings': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'tariffs': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

            
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class S3StorageConfig:
    @staticmethod
    def get_settings(env):
        return {
            "AWS_ACCESS_KEY_ID": env("AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": env("AWS_SECRET_ACCESS_KEY"),
            "AWS_STORAGE_BUCKET_NAME": env("AWS_STORAGE_BUCKET_NAME"),
            "AWS_STORAGE_BUCKET_FOLDER": env("AWS_STORAGE_BUCKET_FOLDER"),
            "AWS_S3_ENDPOINT_URL": "https://s3.timeweb.cloud",
            "AWS_S3_REGION_NAME": "ru-1",
            "AWS_S3_FILE_OVERWRITE": False,
            "AWS_DEFAULT_ACL": "public-read",
            "AWS_QUERYSTRING_AUTH": False,
            "AWS_S3_VERIFY": False,
            "AWS_S3_ADDRESSING_STYLE": "virtual",
            "AWS_S3_SIGNATURE_VERSION": "s3",
            "AWS_S3_CUSTOM_DOMAIN": f"{env('AWS_STORAGE_BUCKET_NAME')}.s3.timeweb.cloud",
        }

    @staticmethod
    def get_static_media_settings(bucket_name, folder):
        return {
            "STATIC_URL": f"https://{bucket_name}.s3.timeweb.cloud/{folder}/static/",
            "MEDIA_URL": f"https://{bucket_name}.s3.timeweb.cloud/{folder}/media/",
            "MEDIA_ROOT": "",
        }

s3_settings = S3StorageConfig.get_settings(env)
globals().update(s3_settings)

class MediaStorage(S3Boto3Storage):
    location = f'{env("AWS_STORAGE_BUCKET_FOLDER")}/media'


class StaticStorage(S3Boto3Storage):
    location = f'{env("AWS_STORAGE_BUCKET_FOLDER")}/static'


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}