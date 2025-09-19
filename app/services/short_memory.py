from collections import deque
from typing import Dict, Deque, Any
import time

_MAX_ITEMS = 30

# user_id -> deque of {"role": "user"|"assistant", "text": "...", "ts": 123}
_short_memory: Dict[int, Deque] = {}

def append_short_memory(user_id: int, role: str, text: str, ts: float = None):
    if ts is None:
        ts = time.time()
    if user_id not in _short_memory:
        _short_memory[user_id] = deque(maxlen=_MAX_ITEMS)
    _short_memory[user_id].append({"role": role, "text": text, "ts": ts})

def get_short_memory(user_id: int):
    return list(_short_memory.get(user_id, []))

def clear_short_memory(user_id: int):
    _short_memory.pop(user_id, None)