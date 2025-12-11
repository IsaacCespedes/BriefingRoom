"""Main FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, briefing, daily, health, interviews, transcripts, vapi, emotions

app = FastAPI(title="Bionic Interviewer API", version="0.1.0")

# Configure CORS
# Allow frontend origin from environment variable or default to localhost:3000
allowed_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://0.0.0.0:3000,http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(briefing.router, prefix="/api", tags=["briefing"])
app.include_router(daily.router, prefix="/api", tags=["daily"])
app.include_router(interviews.router, prefix="/api", tags=["interviews"])
app.include_router(transcripts.router, prefix="/api", tags=["transcripts"])
app.include_router(emotions.router, prefix="/api", tags=["emotions"])
app.include_router(vapi.router, prefix="/api", tags=["vapi"])

