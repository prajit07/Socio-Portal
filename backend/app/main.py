from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import ensure_pgvector

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: enable pgvector if available
    ensure_pgvector()
    yield

app = FastAPI(title="Socio Connect", version="0.1.0", lifespan=lifespan)

# CORS configuration - properly handles deployment scenarios
cors_origins = settings.cors_origins_list
# In production, if no explicit origins, allow all (for flexibility with different domains)
if not cors_origins:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Serve uploaded evidence media (local backend only — S3 files are served
# straight from the bucket / CDN via their public file_url).
if not settings.storage_is_s3:
    import os
    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
    except Exception:
        # On read-only/serverless filesystems (e.g. Vercel) we can't guarantee a
        # writable uploads dir; skip mounting so the API still boots.
        pass


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


app.include_router(api_router, prefix="/api/v1")
