# app/routers/submissions.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from app.services.evaluator import run_tests_for_submission
from app.services.feedback_client import request_feedback
import time, json, os

router = APIRouter()

class TestcaseModel(BaseModel):
    input: str
    output: str

class SubmissionRequest(BaseModel):
    # Accept either question payload or question_id later
    question: Dict[str, Any]  # full question JSON (must include sample_testcases + hidden_testcases)
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
    # Validate question shape minimally
    q = req.question
    if not q.get("sample_testcases"):
        raise HTTPException(400, "question must include sample_testcases")
    hidden = q.get("hidden_testcases", [])
    testcases = q["sample_testcases"] + (hidden if req.run_hidden else [])
    # Run tests
    eval_out = run_tests_for_submission(req.source_code, req.language_id, testcases)
    # Score and decide if we request feedback
    need_feedback = eval_out["passed"] < eval_out["total"]
    # Build brief feedback prompt: include failed test indices and stderr/stdout for them
    failed_tests = [t for t in eval_out["tests"] if not t["passed"]]
    feedback_text = None
    if need_feedback:
        # Request hint from LLM (do not show expected output of hidden tests)
        # Only include sample testcases & failed testcases' stdout/stderr and inputs (hide expected for hidden)
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
    # Persist submission
    submission_record = {
        "timestamp": time.time(),
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
        "submission_id": str(int(time.time() * 1000))
    }
