from abc import ABC, abstractmethod

class StorageInterface(ABC):
    @abstractmethod
    def upload_bytes(self, key: str, data: bytes):
        """Upload raw bytes to the store under `key`."""
        pass

    @abstractmethod
    def download_bytes(self, key: str) -> bytes:
        """Download raw bytes from the store at `key`."""
        pass

    @abstractmethod
    def delete(self, key: str):
        """Delete the object at `key`."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if `key` exists."""
        pass
