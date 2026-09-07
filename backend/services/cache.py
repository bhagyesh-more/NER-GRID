"""Cache Abstraction Layer for NER-GRID

Implements file and memory caching with TTL to prevent hammering external APIs.
Designed to be seamlessly replaced or augmented by Redis in production.
"""
import os
import json
import hashlib
import time
from typing import Optional, Any
from backend.config import settings


class CacheService:
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or settings.CACHE_DIR
        self._memory_cache = {}
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value if not expired."""
        now = time.time()
        # 1. Check in-memory
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if entry["expires_at"] > now:
                return entry["data"]
            else:
                del self._memory_cache[key]

        # 2. Check disk cache
        hashed = self._hash_key(key)
        file_path = os.path.join(self.cache_dir, f"{hashed}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                if entry.get("expires_at", 0) > now:
                    self._memory_cache[key] = entry  # promote to memory
                    return entry["data"]
                else:
                    os.remove(file_path)  # expired
            except Exception:
                pass
        return None

    def set(self, key: str, data: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store value with TTL."""
        ttl = ttl_seconds or settings.CACHE_DEFAULT_TTL_SECONDS
        expires_at = time.time() + ttl
        entry = {"key": key, "expires_at": expires_at, "data": data}

        # Save to memory
        self._memory_cache[key] = entry

        # Save to disk
        hashed = self._hash_key(key)
        file_path = os.path.join(self.cache_dir, f"{hashed}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(entry, f)
        except Exception:
            pass

    def clear(self) -> None:
        """Clear memory cache."""
        self._memory_cache.clear()


cache_service = CacheService()
