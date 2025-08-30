from fastapi import APIRouter
from app.services.judge0_client import execute_code
from app.models.code_model import CodeSubmission

router = APIRouter()


@router.post("/execute")
def run_code(submission: CodeSubmission):
    result = execute_code(
        submission.source_code,
        submission.language_id,
        submission.stdin
    )
    return {"result": result}