import os
from pathlib import Path
from .base import StorageInterface

LOCAL_STORAGE_PATH = Path.cwd()

class LocalStorage(StorageInterface):
    def __init__(self):
        self.base_path = LOCAL_STORAGE_PATH

    def upload_bytes(self, key: str, data: bytes):
        full_path = os.path.join(self.base_path, key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)

    def download_bytes(self, key: str) -> bytes:
        full_path = os.path.join(self.base_path, key)
        with open(full_path, "rb") as f:
            return f.read()

    def delete(self, key: str):
        full_path = os.path.join(self.base_path, key)
        if os.path.exists(full_path):
            os.remove(full_path)

    def exists(self, key: str) -> bool:
        return os.path.exists(os.path.join(self.base_path, key))
