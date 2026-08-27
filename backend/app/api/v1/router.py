from fastapi import APIRouter

from app.api.v1 import auth, problems, evidence, ai, tags, notifications

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(problems.router)
api_router.include_router(evidence.router)
api_router.include_router(ai.router)
api_router.include_router(tags.router)
api_router.include_router(notifications.router)
