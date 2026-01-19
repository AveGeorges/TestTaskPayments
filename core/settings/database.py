import environ

env = environ.Env()

DATABASES = {
    'default': env.db(),
}

if env("DJANGO_ENV") == "production":
    DATABASES['default']['CONN_MAX_AGE'] = 600
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000'
    }
    
    DATABASES['read_replica'] = env.db('READ_REPLICA_URL', default=None)
    if DATABASES['read_replica']:
        DATABASES['read_replica']['CONN_MAX_AGE'] = 600
