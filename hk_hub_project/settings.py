import os
import shutil
import sys
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load optional local secrets.
load_dotenv(BASE_DIR / '.env', override=True)
load_dotenv(BASE_DIR / '.env.local', override=True)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-hk-hub-huongkhe-secret-key-2026-secure-token')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

raw_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '*')
if raw_hosts.strip() == '*':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [h.strip() for h in raw_hosts.split(',') if h.strip()]
    for d in ['.trycloudflare.com', '.pages.dev', '.workers.dev', 'edumentor.io.vn', '.edumentor.io.vn', 'localhost', '127.0.0.1']:
        if d not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(d)

# Cloudflare & Reverse Proxy SSL/CSRF Settings
raw_csrf = os.environ.get(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    'http://localhost:8000,http://127.0.0.1:8000,https://*.trycloudflare.com,https://*.pages.dev,https://*.workers.dev,https://edumentor.io.vn,https://*.edumentor.io.vn'
)
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in raw_csrf.split(',') if origin.strip()]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 3600 if not DEBUG else 0

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'corsheaders',

    # HK Student Hub Domain Apps
    'core.apps.CoreConfig',
    'conduct.apps.ConductConfig',
    'competition.apps.CompetitionConfig',
    'alerts.apps.AlertsConfig',
    'counseling.apps.CounselingConfig',
    'reports.apps.ReportsConfig',
]

MIDDLEWARE = [
    'core.middleware.CloudflareRealIPMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.SampleDatabaseReadOnlyMiddleware',
    'core.middleware.PasswordChangeRequiredMiddleware',
    'core.middleware.AccountStatusEnforcementMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hk_hub_project.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'hk_hub_project.wsgi.application'

# Database
# Vercel's local filesystem is temporary and is not shared between instances.
# In sample mode, always copy the packaged, sanitized SQLite dataset to /tmp;
# never fall back to a configured cloud DATABASE_URL.
VERCEL_ENVIRONMENT = os.environ.get('VERCEL_ENV', '').lower()
USE_SAMPLE_DATABASE = (
    os.environ.get('USE_SAMPLE_DATABASE', '').lower() in {'1', 'true', 'yes'}
    or os.environ.get('VERCEL') == '1'
    or VERCEL_ENVIRONMENT in {'production', 'preview'}
)

if USE_SAMPLE_DATABASE:
    SAMPLE_DATABASE_SOURCE = BASE_DIR / 'sample_data' / 'demo.sqlite3'
    if not SAMPLE_DATABASE_SOURCE.is_file():
        raise RuntimeError(f'Sample database is missing: {SAMPLE_DATABASE_SOURCE}')

    deployment_key = os.environ.get('VERCEL_URL', 'local').replace('/', '_').replace('\\', '_')
    SAMPLE_DATABASE_RUNTIME = Path('/tmp') / f'hk-student-hub-{deployment_key}.sqlite3'
    if not SAMPLE_DATABASE_RUNTIME.exists():
        shutil.copyfile(SAMPLE_DATABASE_SOURCE, SAMPLE_DATABASE_RUNTIME)

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': SAMPLE_DATABASE_RUNTIME,
            'OPTIONS': {'timeout': 20},
        }
    }
    # Signed-cookie sessions let independent serverless instances validate the
    # same session without writing to a database-backed session table.
    SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
else:
    # Use cached_db session engine to eliminate 95%+ of session DB lookups
    SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
    if 'test' in sys.argv:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'test_local.sqlite3',
            }
        }
    else:
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if DATABASE_URL:
            db_config = dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=int(os.environ.get('DB_CONN_MAX_AGE', '300')),
                conn_health_checks=True,
                ssl_require=DATABASE_URL.startswith(('postgres://', 'postgresql://')),
            )
            # Optimize for connection pooling & serverless postgres (Neon / PgBouncer)
            if 'postgres' in db_config.get('ENGINE', ''):
                db_config['DISABLE_SERVER_SIDE_CURSORS'] = True
            DATABASES = {'default': db_config}
        else:
            DB_ENGINE = os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3')
            DB_NAME = os.environ.get('DB_NAME', 'db.sqlite3')
            DATABASES = {
                'default': {
                    'ENGINE': DB_ENGINE,
                    'NAME': BASE_DIR / DB_NAME if DB_ENGINE == 'django.db.backends.sqlite3' else DB_NAME,
                    'OPTIONS': {'timeout': 30} if DB_ENGINE == 'django.db.backends.sqlite3' else {},
                    'USER': os.environ.get('DB_USER', ''),
                    'PASSWORD': os.environ.get('DB_PASSWORD', ''),
                    'HOST': os.environ.get('DB_HOST', ''),
                    'PORT': os.environ.get('DB_PORT', ''),
                }
            }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (for evidence and secure uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache Configuration: Redis if configured, otherwise high-performance LocMemCache
REDIS_URL = os.environ.get('REDIS_URL') or os.environ.get('UPSTASH_REDIS_REST_URL')
if REDIS_URL and REDIS_URL.startswith(('redis://', 'rediss://')):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'TIMEOUT': 300,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'hk-student-hub-memcache',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 15000,
                'CULL_FREQUENCY': 4,
            }
        }
    }

# REST Framework Configuration
IS_TESTING = 'test' in sys.argv
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
}

if not IS_TESTING:
    REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ]
    REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
        'anon': os.environ.get('DRF_ANON_THROTTLE', '300/minute'),
        'user': os.environ.get('DRF_USER_THROTTLE', '2000/minute'),
    }

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True

# School Brand Information Defaults
SCHOOL_NAME = "TRƯỜNG THPT HƯƠNG KHÊ – HÀ TĨNH"
APP_NAME = "HK Student Hub"
APP_SLOGAN = "Kỷ cương số – Thi đua minh bạch – Đồng hành cùng học sinh"

AVATAR_MAX_UPLOAD_SIZE = int(os.environ.get('AVATAR_MAX_UPLOAD_SIZE', str(5 * 1024 * 1024)))
AVATAR_MAX_PIXELS = int(os.environ.get('AVATAR_MAX_PIXELS', '20000000'))

# Email Configuration
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').strip().lower() in {'1', 'true', 'yes'}
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'false').strip().lower() in {'1', 'true', 'yes'}
GMAIL_SENDER_EMAIL = os.environ.get('GMAIL_SENDER_EMAIL', '').strip()
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '').replace(' ', '')
EMAIL_HOST_USER = (
    os.environ.get('EMAIL_HOST_USER', '').strip()
    or GMAIL_SENDER_EMAIL
)
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '') or GMAIL_APP_PASSWORD
DEFAULT_FROM_EMAIL = (
    os.environ.get('DEFAULT_FROM_EMAIL', '').strip()
    or (f'HK Student Hub <{EMAIL_HOST_USER}>' if EMAIL_HOST_USER else '')
)
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '10'))
SCHOOL_UNION_NOTIFICATION_EMAIL = os.environ.get('SCHOOL_UNION_NOTIFICATION_EMAIL', '')
FRONTEND_BASE_URL = os.environ.get('FRONTEND_BASE_URL', 'https://edumentor.io.vn').rstrip('/')
PASSWORD_RESET_TIMEOUT = int(os.environ.get('PASSWORD_RESET_TIMEOUT', '86400'))  # 24 hours in seconds
SMTP_EMAIL_CONFIGURED = bool(EMAIL_HOST_USER and EMAIL_HOST_PASSWORD and DEFAULT_FROM_EMAIL)

# Google OAuth 2.0 Configuration
GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '').strip()
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '').strip()
GOOGLE_OAUTH_CALLBACK_URL = os.environ.get('GOOGLE_OAUTH_CALLBACK_URL', '').strip()
GOOGLE_OAUTH_CONFIGURED = bool(GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET)
