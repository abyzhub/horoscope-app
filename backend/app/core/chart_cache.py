"""
In-memory + disk chart cache.
Charts are stored as JSON files keyed by birth_id (UUID string).
"""
import json
import os
import uuid
from typing import Optional, Dict, Any

CACHE_DIR = "/tmp/horoscope_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# In-memory layer for the lifetime of the server process
_memory_cache: Dict[str, Any] = {}


def _cache_path(birth_id: str) -> str:
    return os.path.join(CACHE_DIR, f"{birth_id}.json")


def save_chart(chart_payload: dict) -> str:
    """
    Persist a chart payload and return its birth_id.
    A new birth_id (UUID) is created on every save.
    """
    birth_id = str(uuid.uuid4())
    chart_payload["birth_id"] = birth_id

    # Memory
    _memory_cache[birth_id] = chart_payload

    # Disk
    with open(_cache_path(birth_id), "w") as f:
        json.dump(chart_payload, f, default=str)

    return birth_id


def load_chart(birth_id: str) -> Optional[dict]:
    """Load a chart by birth_id. Checks memory first, then disk."""
    if birth_id in _memory_cache:
        return _memory_cache[birth_id]

    path = _cache_path(birth_id)
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        _memory_cache[birth_id] = data
        return data

    return None
