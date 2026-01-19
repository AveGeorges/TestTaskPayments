from .base import *
from .apps import *
from .middleware import *
from .database import *
from .security import *
from .rest_framework import *
from .celery import *
from .logging import *

# Django Silk - профилирование (только в development)
import environ
env = environ.Env()
if env("DJANGO_ENV") == "development":
    from .silk import *
