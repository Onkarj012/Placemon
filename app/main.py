from fastapi import FastAPI
from app.routers import questions

app = FastAPI(title="Placement Prep AI")

app.include_router(questions.router, prefix="/questions", tags=["question"])

