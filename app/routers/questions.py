from fastapi import APIRouter, Query
from app.services.api import generate_question

router = APIRouter()

@router.get("/generate-question")
def get_question(topic: str = Query(...), difficulty: str = Query("medium")):
    result =  generate_question(topic, difficulty)
    return {"question" : result}