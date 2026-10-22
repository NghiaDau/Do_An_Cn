import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.embedding import get_model
from app.routers import cv, health, jobs

log = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(_: FastAPI):
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))

    # nạp model trước khi server báo sẵn sàng: "Loading weights" hiện trước "Application startup complete"
    log.info("Đang nạp model embedding...")
    await asyncio.to_thread(get_model)
    log.info("Đã nạp model embedding")

    log.info("Swagger UI: http://%s:%s/docs", host, port)
    yield


app = FastAPI(title="DACN API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(cv.router)


@app.get("/")
def root():
    return {"message": "DACN API is running"}
