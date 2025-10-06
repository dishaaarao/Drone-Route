INSTALLED_APPS = [
    # ...
    'rest_framework',
    'corsheaders',
    'leaflet',
    'django.contrib.gis',
    'dronedelivery',
    'channels',
]

# Add to MIDDLEWARE
MIDDLEWARE = [
    # ...
    'corsheaders.middleware.CorsMiddleware',
    # ...
]

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True  # For development only

# Leaflet config
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (28.6139, 77.2090),  # Default center (Delhi)
    'DEFAULT_ZOOM': 12,
    'MAX_ZOOM': 20,
    'MIN_ZOOM': 3,
    'SCALE': 'both',
    'ATTRIBUTION_PREFIX': 'Drone Delivery System'
}

# Database - Update with your PostgreSQL details
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'dronedelivery',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Channels
ASGI_APPLICATION = 'dronehackon.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Periodic tasks
CELERY_BEAT_SCHEDULE = {
    'simulate-drone-movement': {
        'task': 'dronedelivery.tasks.simulate_drone_movement',
        'schedule': 5.0,  # Run every 5 seconds
    },
}