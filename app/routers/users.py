from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.db import get_db
from app.db import models

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def list_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return [{"id": u.id, "email": u.email, "name": u.name} for u in users]

@router.get("/{user_id}/submissions/")
def list_user_submissions(user_id: int, db: Session = Depends(get_db)):
    subs = db.query(models.Submission).filter(models.Submission.user_id == user_id).all()
    return [
        {
            "id": s.id,
            "question_id": s.question_id,
            "language_id": s.language_id,
            "score_percent": s.score_percent,
            "passed": s.passed,
            "total": s.total,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in subs
    ]

@router.get("/{user_id}/weak-topics")
def get_weak_topics(user_id: int):
    from app.services.analytics import compute_weak_topics
    return compute_weak_topics(user_id)

class UserCreate(BaseModel):
    email: str
    name: str


@router.post("/")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = models.User(email=payload.email, name=payload.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name}

@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.User).filter(models.User.id == user_id).first()
