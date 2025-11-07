"""
API Router - combines all API endpoints
"""
from fastapi import APIRouter

from app.api.v1 import auth, patients, doctors, ocr

# Create API v1 router
api_v1_router = APIRouter(prefix="/v1")

# Include all endpoint routers
api_v1_router.include_router(auth.router)
api_v1_router.include_router(patients.router)
api_v1_router.include_router(doctors.router)
api_v1_router.include_router(ocr.router)

# Main API router
api_router = APIRouter(prefix="/api")
api_router.include_router(api_v1_router)
