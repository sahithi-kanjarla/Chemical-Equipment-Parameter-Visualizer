"""
Django settings for project project.

This version configures DRF to use JWT (Simple JWT) for authentication.
TokenAuth is left available as an optional compatibility path (comment/uncomment below).
"""

from pathlib import Path
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-8usg*p#v%^gs%ud1ta==fsh3y*5696810(#3dyzols^%_s-*uy')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# For local LAN testing add your machine IP here.
# Example: ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.42']
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Media files (uploaded CSVs etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# CORS — prefer explicit origins for dev testing on phone.
# If you want to allow everything during quick debugging set CORS_ALLOW_ALL_ORIGINS = True
# but it's safer to list the React dev server origins you use.
# Example: add your machine LAN IP port where React serves (usually 3000).
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add your machine LAN address when testing from phone:
    # "http://192.168.1.42:3000",
]

# Allow credentials only if you use cookie/session authentication.
CORS_ALLOW_CREDENTIALS = False

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'corsheaders',

    # Optional legacy token system. Keep if you want to support DRF TokenAuth compatibility.
    # If you don't want TokenAuth at all, you can remove/comment the following line.
    'rest_framework.authtoken',

    # Your API app
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # keep near top
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],   # add if you have templates
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

WSGI_APPLICATION = 'project.wsgi.application'

# Database — SQLite (fine for demo)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---- DRF + Simple JWT configuration ----
REST_FRAMEWORK = {
    # By default require authentication (override per-view if needed)
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Primary: JWT (Bearer <access_token>)
        'rest_framework_simplejwt.authentication.JWTAuthentication',

        # Keep SessionAuthentication to allow the browsable API in dev
        'rest_framework.authentication.SessionAuthentication',

        # Optional/legacy: TokenAuthentication (enable below if you want the legacy token flow)
        # To enable DRF TokenAuth, uncomment the next line and run migrations:
        # 'rest_framework.authentication.TokenAuthentication',
    ],
}

# Simple JWT settings (tweak lifetimes for demo)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Development convenience:
# If you want to quickly enable ALL origins while debugging, set:
# CORS_ALLOW_ALL_ORIGINS = True
# (But prefer adding the specific origin like "http://192.168.1.42:3000")

# ----------------------------------------------------------------------------- 
# Recommended development cookie settings (not required for JWT flow)
# ----------------------------------------------------------------------------- 
SESSION_COOKIE_SAMESITE = None
CSRF_COOKIE_SAMESITE = None
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
# ----------------------------------------------------------------------------- 

# ----------------------------------------------------------------------------- 
# Notes:
# - If you enable TokenAuthentication (uncomment the TokenAuthentication line above),
#   make sure 'rest_framework.authtoken' is present in INSTALLED_APPS (it is),
#   then run migrations:
#       python manage.py makemigrations
#       python manage.py migrate
#
# - Do NOT commit SECRET_KEY or other secrets to public Git. For demo it's okay,
#   but for any public repo move secrets into environment variables or a .env file.
# -----------------------------------------------------------------------------
