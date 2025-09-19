# app/models_pydantic.py
from pydantic import BaseModel
from typing import List, Literal, Optional

class PlanTask(BaseModel):
    day: str  # e.g., "Day 1" or "Mon"
    topic: str
    activity: str  # e.g., "Revise arrays, 2 practice problems"
    duration_min: int
    notes: Optional[str] = None

class StudyPlanSchema(BaseModel):
    title: str
    weeks: int
    total_hours_per_week: int
    items: List[PlanTask]   # flattened list or grouped by week
