"""FastAPI application entry point for TriageForge."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.routes import tickets
from app.core.config import settings
from app.core.logging import logger

app = FastAPI(
    title="TriageForge API",
    version="1.0.0",
    description="Autonomous AI Support Triage with fully traceable agent execution.",
)

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.exception_handler(HTTPException)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: HTTPException | StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        payload = exc.detail
    else:
        payload = {"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}}
    return JSONResponse(status_code=exc.status_code, content=payload)


# Include Routers
app.include_router(tickets.router)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    """Root endpoint welcoming visitors and guiding to documentation."""
    return {
        "message": "Welcome to TriageForge API",
        "docs_url": "/docs",
        "health_url": "/health",
    }


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify backend service uptime."""
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup() -> None:
    """Log server startup confirmation."""
    logger.info("TriageForge backend initialized with seed tickets.")