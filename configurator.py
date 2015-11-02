import os

try:
    import settings
except ImportError:
    settings = object()


def get(key, default=None):
    return os.environ.get(
        key,
        getattr(settings, key, default)
    )
