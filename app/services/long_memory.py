from app.db.db import SessionLocal
from app.db.models import LongTermMemory
from sqlalchemy import select, update
from datetime import datetime

def set_memory(user_id: int, key: str, value):
    db = SessionLocal()

    try:
        smtm = select(LongTermMemory).where(LongTermMemory.user_id== user_id, LongTermMemory.key == key)
        res = db.execute(smtm).scalar().first()
        if res:
            res.value = value
            res.updated_at = datetime.timezone.utc
        else:
            res = LongTermMemory(user_id = user_id, key=key, value = value)
            db.add(rec)
        db.commit()
    finally:
        db.close()

def get_memory(user_id : int, key: str):
    db = SessionLocal()

    try:
        smtm = select(LongTermMemory).where(LongTermMemory.user_id==user_id, LongTermMemory.key==key)
        res = db.execute(smtm).scalar().first()
        return res.value if res else None
    finally:
        db.close()

def list_memory(user_id: int):
    db = SessionLocal()
    try:
        smtm = select(LongTermMemory.user_id==user_id)
        res = db.execute(smtm).scalars().all()
        return [{"key":r.key, "value": r.value, "updated_at": r.updated_at.isoformat()} for r in res]
    finally:
        db.close()