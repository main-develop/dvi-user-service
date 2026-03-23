import os
from pathlib import Path

import environ
from django.db.backends.postgresql.psycopg_any import IsolationLevel

# Build paths inside the project like this: BASE_DIR / "subdir"
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables
env = environ.Env()
# When running without Docker
if os.path.exists(os.path.join(BASE_DIR, ".env")):
    environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

DEBUG = env("DEBUG")  # SECURITY WARNING: don't run with debug turned on in production!
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = [env("ALLOWED_HOSTS")]

# Django REST framework settings
REST_FRAMEWORK = {
    "DEFAULT_CONTENT_NEGOTIATION_CLASS": "rest_framework.negotiation.DefaultContentNegotiation",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication"
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "users.overrides.openapi.CustomAutoSchema",
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
}

# drf-standardized-errors settings
DRF_STANDARDIZED_ERRORS = {
    # ONLY the responses that correspond to these status codes will appear
    # in the API schema
    "ALLOWED_ERROR_STATUS_CODES": [
        "400",
        "401",
        "403",
        "404",
        "429",
    ],
}

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "djoser",
    "drf_spectacular",
    "drf_standardized_errors",
    "users",
]
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
AUTHENTICATION_BACKENDS = [
    "users.overrides.backends.CustomModelBackend",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = [
    "http://0.0.0.0:3000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.100.12:3000",
]
CSRF_TRUSTED_ORIGINS = [
    "http://0.0.0.0:3000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.100.12:3000",
]

ROOT_URLCONF = "user_api.urls"
URL_FORMAT_OVERRIDE = None  # The name of the format query parameter
WSGI_APPLICATION = "user_api.wsgi.application"

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_LOCATION"),
        "KEY_PREFIX": "otp",
    }
}

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "OPTIONS": {
            "client_encoding": "UTF8",
            "isolation_level": IsolationLevel.READ_COMMITTED,
        },
    }
}

AUTH_USER_MODEL = "users.User"
# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "users.validators.MaximumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = "static/"
# Directory where static files will be collected for production
STATIC_ROOT = os.path.join(BASE_DIR, "static")
