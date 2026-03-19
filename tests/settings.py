from geosearch.settings import *  # noqa: F403, F405

# The reason the settings are defined here, is to make them independent
# of the regular project sources. Otherwise, the project needs to have
# knowledge of the test framework.

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Remove propagate=False so caplog can read those messages.
LOGGING = {
    **LOGGING,
    "root": {
        "level": "DEBUG",
        "handlers": ["console"],
    },
    "loggers": {
        name: {
            **conf,
            "propagate": True,
        }
        for name, conf in LOGGING["handlers"].items()
    },
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Prevent tests to crash because of missing staticfiles manifests
WHITENOISE_MANIFEST_STRICT = False
STORAGES = {
    **STORAGES,
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
