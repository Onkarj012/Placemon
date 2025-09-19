# app/routers/submissions.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from app.services.evaluator import run_tests_for_submission
from app.services.feedback_client import request_feedback
from app.db.db import SessionLocal
from app.db.models import Submission, SubmissionTest, Question
import time, json, os, uuid
from datetime import datetime

router = APIRouter()

class TestcaseModel(BaseModel):
    input: str
    output: str

class SubmissionRequest(BaseModel):
    # Accept either question payload or question_id later
    user_id: Optional[int] = None                # optional user id
    question: Dict[str, Any]                     # full question JSON (must include sample_testcases + hidden_testcases)
    source_code: str
    language_id: int
    run_hidden: bool = True

class SubmissionResponse(BaseModel):
    ok: bool
    score_percent: float
    passed: int
    total: int
    tests: List[Dict[str, Any]]
    feedback: Optional[str] = None
    submission_id: str

# Ensure the submissions log file exists
LOG_PATH = os.getenv("SUBMISSIONS_LOG", "app/data/submissions.jsonl")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

@router.post("/submit", response_model=SubmissionResponse)
def submit_solution(req: SubmissionRequest):
    q = req.question
    # Minimal validation
    if not q.get("sample_testcases"):
        raise HTTPException(status_code=400, detail="question must include sample_testcases")

    # Ensure question has an id; generate if missing
    if not q.get("id"):
        q["id"] = str(uuid.uuid4())

    hidden = q.get("hidden_testcases", [])
    testcases = q["sample_testcases"] + (hidden if req.run_hidden else [])

    # Run tests via evaluator
    eval_out = run_tests_for_submission(req.source_code, req.language_id, testcases)

    # Decide if feedback is needed (if not all tests passed)
    need_feedback = eval_out["passed"] < eval_out["total"]
    failed_tests = [t for t in eval_out["tests"] if not t["passed"]]
    feedback_text = None
    if need_feedback:
        feedback_payload = {
            "question_title": q.get("title"),
            "failed_tests": [
                {"index": t["index"], "stdin": t["stdin"], "stdout": t["stdout"], "stderr": t["stderr"]} for t in failed_tests
            ],
            "language_id": req.language_id,
            "source_code": req.source_code
        }
        try:
            feedback_text = request_feedback(feedback_payload)
        except Exception as e:
            feedback_text = f"Feedback generation failed: {e}"

    # Persist submission to DB (and ensure question exists in questions table)
    db = SessionLocal()
    try:
        # Ensure question stored in questions table
        qid = q.get("id")
        existing_q = db.get(Question, qid)
        if not existing_q:
            question_row = Question(
                id=qid,
                title=q.get("title", "")[:255],
                difficulty=q.get("difficulty", "unknown"),
                topics=q.get("topics", []),
                raw=q
            )
            db.add(question_row)
            db.commit()

        # Create submission record
        sub = Submission(
            user_id=req.user_id,
            question_id=qid,
            language_id=req.language_id,
            score_percent=eval_out["score_percent"],
            passed=eval_out["passed"],
            total=eval_out["total"],
            created_at=datetime.utcnow()
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)

        # Create per-test records
        for t in eval_out["tests"]:
            st = SubmissionTest(
                submission_id=sub.id,
                test_index=t.get("index"),
                stdin=t.get("stdin"),
                expected=t.get("expected"),
                stdout=t.get("stdout"),
                stderr=t.get("stderr"),
                passed=bool(t.get("passed")),
                time=t.get("time"),
                memory=t.get("memory")
            )
            db.add(st)
        db.commit()
    except Exception as e:
        db.rollback()
        # still persist to JSONL log for audit
        submission_record = {
            "timestamp": time.time(),
            "question_id": q.get("id"),
            "language_id": req.language_id,
            "score": eval_out["score_percent"],
            "passed": eval_out["passed"],
            "total": eval_out["total"],
            "eval": eval_out,
            "feedback": feedback_text,
            "db_error": str(e)
        }
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(submission_record) + "\n")
        raise HTTPException(status_code=500, detail=f"Database error saving submission: {e}")
    finally:
        db.close()

    # Also append to JSONL log (audit)
    submission_record = {
        "timestamp": time.time(),
        "submission_id": sub.id,
        "user_id": req.user_id,
        "question_id": q.get("id"),
        "language_id": req.language_id,
        "score": eval_out["score_percent"],
        "passed": eval_out["passed"],
        "total": eval_out["total"],
        "eval": eval_out,
        "feedback": feedback_text
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(submission_record) + "\n")

    return {
        "ok": True,
        "score_percent": eval_out["score_percent"],
        "passed": eval_out["passed"],
        "total": eval_out["total"],
        "tests": eval_out["tests"],
        "feedback": feedback_text,
        "submission_id": str(sub.id)
    }


# Simpler alias endpoint: accepts a minimal payload and records a submission
class SimpleSubmissionIn(BaseModel):
    user_id: Optional[int] = None
    question_id: Optional[str] = None
    topic: Optional[str] = None
    score: float
    passed: int
    total: int


@router.post("/")
def create_simple_submission(payload: SimpleSubmissionIn):
    db = SessionLocal()
    try:
        sub = Submission(
            user_id=payload.user_id,
            question_id=payload.question_id,
            language_id=0,
            score_percent=float(payload.score),
            passed=payload.passed,
            total=payload.total,
            created_at=datetime.utcnow()
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)

        record = {
            "timestamp": time.time(),
            "submission_id": sub.id,
            "user_id": payload.user_id,
            "question_id": payload.question_id,
            "topic": payload.topic,
            "score": payload.score,
            "passed": payload.passed,
            "total": payload.total,
        }
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(record) + "\n")

        return {"ok": True, "submission_id": sub.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create submission: {e}")
    finally:
        db.close()


@router.get("/user/{user_id}")
def list_submissions_by_user(user_id: int):
    db = SessionLocal()
    try:
        subs = db.query(Submission).filter(Submission.user_id == user_id).all()
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
    finally:
        db.close()
