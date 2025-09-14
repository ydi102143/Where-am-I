from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from app.core.db import engine, Base
from app.routers.goals import router as v1_goals_router
from app.routers.plan import router as v1_plan_router
from app.routers.pages import router as page_router
from app.routers.reflect import router as v1_reflect_router
from app.routers.reflect_ai import router as v1_reflect_ai_router
from app.routers.review import router as v1_review_router
from app.routers.integration import router as v1_integration_router
from app.services.scheduler import start_scheduler
import os

app = FastAPI(title="Personal PM Coach (MVP)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# Routers
app.include_router(v1_goals_router)
app.include_router(v1_plan_router)
app.include_router(v1_reflect_router)
app.include_router(v1_reflect_ai_router)
app.include_router(v1_review_router)
app.include_router(v1_integration_router)
app.include_router(page_router)

# Static
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Scheduler
if os.getenv("DISABLE_SCHEDULER", "false").lower() != "true":
    start_scheduler()
