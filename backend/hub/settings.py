"""
Django settings for the Connections Hub project.
"""

from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env if present.
load_dotenv(BASE_DIR / '.env')


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in {'1', 'true', 'yes', 'on'}


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env(
    'DJANGO_SECRET_KEY',
    'django-insecure-9j@7jc4@49*$9rtqw97qzka_+_pbd@a7y@4%uv2a*h@br68a!$',
)

DEBUG = env_bool('DJANGO_DEBUG', True)

ALLOWED_HOSTS = [h for h in env('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h]

# Fernet key for encrypting tokens at rest (the vault). Generated in .env; a
# throwaway dev default keeps the project runnable out of the box.
HUB_FIELD_ENCRYPTION_KEY = env(
    'HUB_FIELD_ENCRYPTION_KEY',
    'AYzC9Ly7dJjvbqyGZgBtoGN0uYauInqlZ04CBK1oZkA=',
)

# How long a brokered provider access token is considered valid (seconds).
ACCESS_TOKEN_TTL_SECONDS = int(env('ACCESS_TOKEN_TTL_SECONDS', '3600'))


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'corsheaders',
    'drf_spectacular',

    # Local apps
    'users',
    'authentication',
    'providers',
    'connections',
    'access',
    'portal',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'hub.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db' / 'db.sqlite3',
    }
}


# Custom user model
AUTH_USER_MODEL = 'users.User'


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'access.authentication.ApiKeyAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # List endpoints return plain arrays by default (scaffold-friendly).
    # Opt into pagination per-view with CustomPageNumberPagination when needed.
    'DEFAULT_THROTTLE_RATES': {
        'consumer': env('CONSUMER_THROTTLE_RATE', '120/min'),
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Connections Hub API',
    'DESCRIPTION': 'Connect client accounts once; granted projects fetch data or '
                   'short-lived tokens. Machine access uses an API key: '
                   '`Authorization: ApiKey hub_xxx`.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(env('JWT_ACCESS_MINUTES', '60'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(env('JWT_REFRESH_DAYS', '7'))),
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# CORS (dev: allow the Vite dev server)
CORS_ALLOW_ALL_ORIGINS = env_bool('CORS_ALLOW_ALL', True)
CORS_ALLOW_CREDENTIALS = True

# Base URL the backend uses to build OAuth redirect URIs back to itself.
BACKEND_BASE_URL = env('BACKEND_BASE_URL', 'http://localhost:8000')
# Where the frontend lives (used for post-connect redirects in the mock flow).
FRONTEND_BASE_URL = env('FRONTEND_BASE_URL', 'http://localhost:5173')


def _csv(key, default=''):
    return [s.strip() for s in env(key, default).split(',') if s.strip()]


# Real-provider OAuth/API configuration (used only when Provider.is_mock is False).
# Missing values are fine while a provider stays on the mock adapter.
PROVIDER_CONFIG = {
    'google-ads': {
        'client_id': env('GOOGLE_ADS_CLIENT_ID', ''),
        'client_secret': env('GOOGLE_ADS_CLIENT_SECRET', ''),
        'developer_token': env('GOOGLE_ADS_DEVELOPER_TOKEN', ''),
        'login_customer_id': env('GOOGLE_ADS_LOGIN_CUSTOMER_ID', ''),
        'api_version': env('GOOGLE_ADS_API_VERSION', 'v18'),
        'scopes': ['https://www.googleapis.com/auth/adwords'],
    },
    'meta-ads': {
        'client_id': env('META_APP_ID', ''),
        'client_secret': env('META_APP_SECRET', ''),
        'api_version': env('META_API_VERSION', 'v21.0'),
        'scopes': _csv('META_SCOPES', 'ads_read'),
    },
    'shopify': {
        'client_id': env('SHOPIFY_API_KEY', ''),
        'client_secret': env('SHOPIFY_API_SECRET', ''),
        'api_version': env('SHOPIFY_API_VERSION', '2024-10'),
        'scopes': _csv('SHOPIFY_SCOPES', 'read_orders,read_products'),
    },
}
