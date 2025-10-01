from .local_storage import LocalStorage

def get_storage() -> LocalStorage:
    """
    Returns a StorageInterface implementation based on settings.STORAGE_BACKEND.
    """
    return LocalStorage()
