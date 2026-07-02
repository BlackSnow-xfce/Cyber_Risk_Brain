import time
from typing import Any, Dict, Optional


class InMemoryCache:

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, dict] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)

        if not entry:
            return None

        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any) -> None:
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + self.ttl_seconds
        }

    def clear(self) -> None:
        self._store.clear()
