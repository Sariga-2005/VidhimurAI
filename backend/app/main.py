"""VidhimurAI Backend — FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.errors.handlers import register_error_handlers
from app.routers import empower, research

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="VidhimurAI — Legal Intelligence API",
    description=(
        "Backend core for the VidhimurAI legal intelligence platform. "
        "Provides deterministic legal case search and citizen empowerment analysis."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — allow React dev servers + any localhost origin
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Create React App / Next.js
        "http://localhost:5173",   # Vite
        "http://localhost:5174",   # Vite (alternate port)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register routers & error handlers
# ---------------------------------------------------------------------------

app.include_router(research.router)
app.include_router(empower.router)
register_error_handlers(app)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "healthy", "service": "VidhimurAI Backend"}
