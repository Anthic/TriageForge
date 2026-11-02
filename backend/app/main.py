"""FastAPI application entry point for TriageForge."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import tickets, triage
from app.core.config import settings
from app.core.logging import logger
from app.core.rate_limit import limiter


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Log application startup using FastAPI's lifespan lifecycle."""
    logger.info("TriageForge backend initialized with seed tickets.")
    yield


app = FastAPI(
    title="TriageForge API",
    version="1.0.0",
    description="Autonomous AI Support Triage with fully traceable agent execution.",
    lifespan=lifespan,
)
app.state.limiter = limiter

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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, __: RequestValidationError) -> JSONResponse:
    """Return a stable validation envelope without exposing request internals."""
    return JSONResponse(status_code=422, content={
        "error": {"code": "VALIDATION_ERROR", "message": "The request contains invalid data."}
    })


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(_: Request, __: RateLimitExceeded) -> JSONResponse:
    """Return rate-limit failures in the API's standard error envelope."""
    return JSONResponse(status_code=429, content={
        "error": {"code": "RATE_LIMITED", "message": "Too many triage requests. Try again shortly."}
    })


# Include Routers
app.include_router(tickets.router)
app.include_router(triage.router)


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
