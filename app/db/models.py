# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Question(Base):
    __tablename__ = "questions"
    id = Column(String, primary_key=True, index=True)  # question id from generator (uuid)
    title = Column(String)
    difficulty = Column(String)
    topics = Column(JSON)  # list of strings
    raw = Column(JSON)     # full question JSON (sample and hidden tests etc.)
    created_at = Column(DateTime, default=datetime.utcnow)

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    question_id = Column(String, ForeignKey("questions.id"), nullable=True)
    language_id = Column(Integer)
    score_percent = Column(Float)
    passed = Column(Integer)
    total = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    # relationships
    tests = relationship("SubmissionTest", back_populates="submission")

class SubmissionTest(Base):
    __tablename__ = "submission_tests"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    test_index = Column(Integer)
    stdin = Column(Text)
    expected = Column(Text)
    stdout = Column(Text)
    stderr = Column(Text)
    passed = Column(Boolean)
    time = Column(Float)
    memory = Column(Integer)
    submission = relationship("Submission", back_populates="tests")

class LongTermMemory(Base):
    __tablename__ = "long_term_memory"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    key = Column(String, index=True)   # e.g., 'goal', 'preferred_lang'
    value = Column(JSON)              # JSON blob
    updated_at = Column(DateTime, default=datetime.utcnow)

class StudyPlan(Base):
    __tablename__ = "study_plans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    raw = Column(JSON)  # store full plan JSON returned by LLM
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class StudyPlanItem(Base):
    __tablename__ = "study_plan_items"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id"))
    item_index = Column(Integer)  # position
    raw = Column(JSON)            # e.g. {"day":"Mon","task":"Practice arrays","duration_min":45}
    completed = Column(Boolean, default=False)
