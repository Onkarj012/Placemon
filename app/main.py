from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import questions, executor, submissions, users  
from app.routers import plans, memory
from app.db.db import create_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown (if needed)

app = FastAPI(title="Placement Prep AI", lifespan=lifespan)

app.include_router(questions.router, prefix="/questions", tags=["question"])
app.include_router(executor.router, prefix="/executor", tags=["executor"])
app.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
app.include_router(users.router)
app.include_router(plans.router)
app.include_router(plans.alias_router)
app.include_router(memory.router)
