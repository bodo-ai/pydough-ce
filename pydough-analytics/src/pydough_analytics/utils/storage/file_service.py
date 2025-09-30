import json
from .factory import get_storage

storage = get_storage()

def save_json(key: str, obj: list):
    data = json.dumps(obj, indent=2).encode("utf-8")
    storage.upload_bytes(key, data)

def load_json(key: str) -> list:
    data = storage.download_bytes(key)
    return json.loads(data.decode("utf-8"))

def save_markdown(key: str, content: str):
    storage.upload_bytes(key, content.encode("utf-8"))

def load_markdown(key: str) -> str:
    data = storage.download_bytes(key)
    return data.decode("utf-8")

def delete_key(key: str):
    storage.delete(key)

def exists(key: str) -> bool:
    return storage.exists(key)
