from django.conf import settings
from .local_storage import LocalStorage

def get_storage() -> LocalStorage:
    """
    Returns a StorageInterface implementation based on settings.STORAGE_BACKEND.
    """
    backend = settings.STORAGE_BACKEND.lower()
    return LocalStorage()
