import environ

env = environ.Env()

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
    
    'rest_framework',
    'drf_spectacular',
    'django_filters',
    'corsheaders',
    'django_redis',
    
    'payments',
]

# Django Silk - профилирование запросов (только в development)
if env("DJANGO_ENV") == "development":
    INSTALLED_APPS.insert(0, 'silk')
