"""Main FastAPI application entry point."""

from fastapi import FastAPI
from app.api import briefing, health

app = FastAPI(title="Bionic Interviewer API", version="0.1.0")

app.include_router(health.router)
app.include_router(briefing.router)

