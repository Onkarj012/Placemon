# app/services/study_plan.py
import os, json, httpx
from app.models.plan_model import StudyPlanSchema
from app.db.models import StudyPlan
from app.db.db import SessionLocal
from tenacity import retry, stop_after_attempt, wait_fixed
from uuid import uuid4
from dotenv import load_dotenv
load_dotenv()

OR_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}", "Content-Type":"application/json"}
MODEL = os.getenv("OR_MODEL", "openrouter/auto")

SYSTEM = (
    "You are a study planner. Produce exactly one JSON object that conforms to the StudyPlanSchema. "
    "Do not include any other text or markdown. The schema is: {title, weeks, total_hours_per_week, items:[{day,topic,activity,duration_min,notes}]}."
)

@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
def _call_or(messages):
    body = {"model": MODEL, "messages": messages, "temperature": 0.0, "max_tokens": 800}
    r = httpx.post(OR_URL, headers=HEADERS, json=body, timeout=20.0)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def generate_study_plan(user_profile: dict, weak_topics: list):
    """
    user_profile: {"hours_per_week":int, "target_date":"YYYY-MM-DD", "preferred_days":["Mon","Tue"], "goal":"Get into X"}
    weak_topics: list of {"topic":"arrays","attempts":x,"accuracy":0.5}
    """
    prompt_body = f"User profile: {json.dumps(user_profile)}\nWeak topics: {json.dumps(weak_topics)}\n"
    prompt_body += "Produce a StudyPlanSchema JSON object. Prioritize weak topics. Make the plan achievable given hours_per_week."

    messages = [{"role":"system","content":SYSTEM}, {"role":"user","content":prompt_body}]
    raw = _call_or(messages)
    # attempt parse
    try:
        parsed = json.loads(raw)
    except Exception:
        # try repair once
        repair_msgs = [{"role":"system","content":"Repair to valid JSON only."}, {"role":"user","content":raw}]
        raw = _call_or(repair_msgs)
        parsed = json.loads(raw)
    # validate via pydantic
    plan = StudyPlanSchema(**parsed)
    # add plan id wrapper
    plan_obj = plan.model_dump()
    plan_obj["id"] = str(uuid4())
    return plan_obj


def save_study_plan(user_id: int, plan_obj: dict):
    db = SessionLocal()
    try:
        sp = StudyPlan(user_id=user_id, title=plan_obj.get("title","Study Plan"), raw=plan_obj)
        db.add(sp)
        db.commit()
        db.refresh(sp)
        return sp.id
    finally:
        db.close()