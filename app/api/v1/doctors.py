"""
Doctor API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.doctor import (
    DoctorResponse,
    DoctorListItem,
    DoctorListResponse,
    DoctorSearchFilters,
    SpecialtyResponse,
)
from app.schemas.auth import UserResponse
from app.services.doctor_service import DoctorService
from app.dependencies import get_current_user
from app.models.user import User
from app.core.exceptions import NerulaException
import math

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("", response_model=DoctorListResponse)
async def search_doctors(
    specialty: str = Query(None, description="Filter by specialty"),
    search: str = Query(None, description="Search by doctor name"),
    location: str = Query(None, description="Filter by location"),
    min_rating: float = Query(None, ge=0, le=5, description="Minimum rating"),
    max_fee: float = Query(None, ge=0, description="Maximum consultation fee"),
    consultation_type: str = Query(None, description="Filter by consultation type"),
    language: str = Query(None, description="Filter by language"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search and list doctors with filters

    - Public endpoint (no authentication required)
    - Supports filtering by specialty, location, rating, fee, etc.
    - Returns paginated results
    """
    try:
        # Create filters object
        filters = DoctorSearchFilters(
            specialty=specialty,
            search=search,
            location=location,
            min_rating=min_rating,
            max_fee=max_fee,
            consultation_type=consultation_type,
            language=language,
            page=page,
            limit=limit,
        )

        doctor_service = DoctorService(db)
        doctors, total = await doctor_service.search_doctors(filters)

        # Transform to list items
        doctor_items = []
        for doctor in doctors:
            # Get user info for name
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(User.id == doctor.user_id)
            )
            user = result.scalar_one_or_none()

            # Format experience
            experience = f"{doctor.years_of_experience} years experience" if doctor.years_of_experience else "Experienced"

            # Format next available
            next_available = "Today, 4:30 PM"  # TODO: Implement actual slot calculation
            if doctor.next_available_slot:
                next_available = doctor.next_available_slot.strftime("%a, %I:%M %p")

            doctor_items.append(
                DoctorListItem(
                    id=str(doctor.id),
                    name=user.full_name if user else "Unknown",
                    specialty=doctor.specialty,
                    experience=experience,
                    rating=f"{doctor.rating:.1f}",
                    location=doctor.location or doctor.hospital_affiliation,
                    next_available=next_available,
                    fee=f"AED {doctor.consultation_fee:.0f}",
                    avatar=doctor.avatar_url,
                )
            )

        # Calculate total pages
        total_pages = math.ceil(total / limit) if total > 0 else 0

        return DoctorListResponse(
            doctors=doctor_items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search doctors: {str(e)}"
        )


@router.get("/specialties", response_model=SpecialtyResponse)
async def get_specialties(
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of all specialties

    - Public endpoint
    - Returns unique list of specialties
    """
    try:
        doctor_service = DoctorService(db)
        specialties = await doctor_service.get_specialties()

        return SpecialtyResponse(specialties=specialties)

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get specialties: {str(e)}"
        )


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor_by_id(
    doctor_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get doctor details by ID

    - Public endpoint
    - Returns complete doctor profile
    """
    try:
        doctor_service = DoctorService(db)
        doctor = await doctor_service.get_doctor_by_id(doctor_id)

        return DoctorResponse(**doctor.to_dict())

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get doctor: {str(e)}"
        )
