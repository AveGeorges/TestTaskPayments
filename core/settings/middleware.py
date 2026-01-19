import environ

env = environ.Env()

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'payments.middleware.RateLimitMiddleware',
    'payments.middleware.SecurityHeadersMiddleware',
    'payments.middleware.RequestLoggingMiddleware',
    'payments.monitoring.DatabaseMonitoringMiddleware',  # Мониторинг медленных запросов
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Django Silk middleware - профилирование запросов (только в development)
if env("DJANGO_ENV") == "development":
    MIDDLEWARE.insert(0, 'silk.middleware.SilkyMiddleware')
