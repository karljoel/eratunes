"""
Django settings for eratunes project.
"""

import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-h2n0t)#$s9v#wp+-myyp*wna(=2c#^g=22nb5o8z&&%x-*&7j!')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ========== ALLOWED HOSTS ==========
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'eratunez.com',
    'www.eratunez.com',
    '.onrender.com',
]

# ========== CSRF TRUSTED ORIGINS ==========
CSRF_TRUSTED_ORIGINS = [
    'https://eratunez.com',
    'https://www.eratunez.com',
    'https://*.onrender.com',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',  # For S3 storage
    'music',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eratunes.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'music.context_processors.admin_notifications',
                'music.context_processors.ads_context',
                'music.context_processors.user_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'eratunes.wsgi.application'

# ========== DATABASE ==========
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600
    )
}

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

# ========== STATIC & MEDIA FILES ==========
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ========== AUTH ==========
ADMIN_SITE_HEADER = "EraTunez Admin"
AUTH_USER_MODEL = 'music.CustomUser'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
# ADMIN_SITE_HEADER = "EraTunez Admin"
# ========== EMAIL ==========
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ========== SECURITY ==========
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# ========== BACKBLAZE B2 STORAGE ==========
# Your Backblaze Credentials
AWS_ACCESS_KEY_ID = '00506f34a75eeb10000000001'
AWS_SECRET_ACCESS_KEY = 'K005fLTFFWB6sa9XulhuCv8uAiDuH58'
AWS_STORAGE_BUCKET_NAME = 'EraTunezstore'
AWS_S3_ENDPOINT_URL = 'https://s3.us-east-005.backblazeb2.com'
AWS_S3_REGION_NAME = 'us-east-005'
AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Storage Configuration
STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Media URL (where files will be served from)
MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.backblazeb2.com/'
MEDIA_ROOT = ''