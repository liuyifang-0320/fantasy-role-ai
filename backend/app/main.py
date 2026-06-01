from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import (
    RequestIdMiddleware,
    configure_logging,
    unhandled_exception_handler,
)
from app.db.init_db import init_db


configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="MVP backend for the Fantasy Role AI project.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(Exception, unhandled_exception_handler)

settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.static_dir.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
app.include_router(api_router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Fantasy Role AI backend is running",
    }
