from fastapi import APIRouter, HTTPException, Query
from app.services.api import generate_question

router = APIRouter()

@router.get("/generate-question")
def get_question(
    topic: str = Query(..., description="topic, e.g. arrays or percentages"),
    difficulty: str = Query("medium", regex="^(easy|medium|hard)$"),
    type: str = Query("coding", regex="^(coding|aptitude)$")
):
    try:
        q = generate_question(question_type=type, topic=topic, difficulty=difficulty)
        return {"ok": True, "question": q}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))