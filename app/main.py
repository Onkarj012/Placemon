from fastapi import FastAPI
from app.routers import questions, executor, submissions   # 👈 add submissions

app = FastAPI(title="Placement Prep AI")

app.include_router(questions.router, prefix="/questions", tags=["question"])
app.include_router(executor.router, prefix="/executor", tags=["executor"])
app.include_router(submissions.router, prefix="/submissions", tags=["submissions"])  # 👈 now it works
