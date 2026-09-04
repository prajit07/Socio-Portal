from fastapi import APIRouter

from app.api.v1 import (
    auth,
    problems,
    evidence,
    ai,
    tags,
    notifications,
    universities,
    teams,
    proposals,
    industries,
    collaborations,
    government,
    admin,
    engagement,
    geocoding,
    classification_feedback,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(problems.router)
api_router.include_router(evidence.router)
api_router.include_router(ai.router)
api_router.include_router(tags.router)
api_router.include_router(notifications.router)
api_router.include_router(universities.router)
api_router.include_router(teams.router)
api_router.include_router(proposals.router)
api_router.include_router(industries.router)
api_router.include_router(collaborations.router)
api_router.include_router(government.router)
api_router.include_router(admin.router)
api_router.include_router(engagement.router)
api_router.include_router(geocoding.router)
api_router.include_router(classification_feedback.router)
