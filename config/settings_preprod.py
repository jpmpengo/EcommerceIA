import os
from django.core.exceptions import ImproperlyConfigured
from .settings import *

def required(name):
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(name + " obligatoire en preproduction")
    return value

DEBUG = False
SECRET_KEY = required("PREPROD_SECRET_KEY")
ALLOWED_HOSTS = [x.strip() for x in required("PREPROD_ALLOWED_HOSTS").split(",") if x.strip()]
DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": required("PREPROD_DB_NAME"), "USER": required("PREPROD_DB_USER"), "PASSWORD": required("PREPROD_DB_PASSWORD"), "HOST": required("PREPROD_DB_HOST"), "PORT": os.getenv("PREPROD_DB_PORT", "5432")}}
STATIC_ROOT = BASE_DIR / "staticfiles"
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 0
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CSRF_TRUSTED_ORIGINS = [x.strip() for x in required("PREPROD_CSRF_TRUSTED_ORIGINS").split(",") if x.strip()]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
