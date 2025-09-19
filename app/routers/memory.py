# app/routers/memory.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any
from app.services.short_memory import append_short_memory, get_short_memory, clear_short_memory
from app.services.long_memory import set_memory, get_memory, list_memory

router = APIRouter(prefix="/memory", tags=["memory"])

class ShortMemIn(BaseModel):
    user_id: int
    role: str
    text: str

@router.post("/short")
def add_short(mem: ShortMemIn):
    append_short_memory(mem.user_id, mem.role, mem.text)
    return {"ok": True}

@router.get("/short/{user_id}")
def read_short(user_id: int):
    return {"ok": True, "memory": get_short_memory(user_id)}

class LongMemIn(BaseModel):
    user_id: int
    key: str
    value: Any

@router.post("/long")
def add_long(mem: LongMemIn):
    set_memory(mem.user_id, mem.key, mem.value)
    return {"ok": True}

@router.get("/long/{user_id}/{key}")
def read_long(user_id: int, key: str):
    val = get_memory(user_id, key)
    return {"ok": True, "value": val}

@router.get("/long/list/{user_id}")
def list_long(user_id: int):
    return {"ok": True, "items": list_memory(user_id)}
