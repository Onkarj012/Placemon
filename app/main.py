from fastapi import FastAPI
from app.routers import questions, executor


app = FastAPI(title="Placement Prep AI")

app.include_router(questions.router, prefix="/questions", tags=["question"])
app.include_router(executor.router, prefix="/executor", tags=["executor"])

