import time, logging
from typing import Any, AsyncGenerator
from fastapi import FastAPI
from .routers import rag
from .core.config import settings

app_start_time = time.time()

async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logging.info("🚀 MVP backend starting")
    yield
    logging.info("� MVP backend stopped")

app = FastAPI(title="GameChat AI API (MVP)", version="0.1.0", lifespan=lifespan)

@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "gamechat-ai-backend", "version": "0.1.0"}

app.include_router(rag.router)