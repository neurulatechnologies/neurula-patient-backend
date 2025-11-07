"""
Patient API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.database import get_db
from app.schemas.patient import (
    PatientResponse,
    PatientUpdate,
    PatientProfileCompletion,
)
from app.schemas.auth import UserResponse
from app.services.patient_service import PatientService
from app.dependencies import get_current_active_patient
from app.models.user import User
from app.models.patient import Patient
from app.core.exceptions import NerulaException

router = APIRouter(prefix="/patients", tags=["Patients"])


class VerifyEmiratesIDRequest(BaseModel):
    """Request model for Emirates ID verification"""
    emirates_id: str = Field(..., description="Emirates ID to verify (format: 784-XXXX-XXXXXXX-X or 15 digits)")


class VerifyEmiratesIDResponse(BaseModel):
    """Response model for Emirates ID verification"""
    available: bool
    message: str
    exists: bool = False


@router.get("/me", response_model=PatientResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current patient profile

    - Requires authentication (patient role)
    - Returns patient profile data
    """
    try:
        patient_service = PatientService(db)
        patient = await patient_service.get_patient_by_user_id(str(current_user.id))

        return PatientResponse(**patient.to_dict())

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient_by_id(
    patient_id: str,
    current_user: User = Depends(get_current_active_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Get patient by ID

    - Requires authentication
    - Returns patient profile data
    - Patients can only view their own profile (doctors can view all)
    """
    try:
        patient_service = PatientService(db)
        patient = await patient_service.get_patient_by_id(patient_id)

        # Authorization check: patient can only view their own profile
        if current_user.role == "patient" and str(patient.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own profile"
            )

        return PatientResponse(**patient.to_dict())

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get patient: {str(e)}"
        )


@router.put("/me", response_model=PatientResponse)
async def update_my_profile(
    data: PatientUpdate,
    current_user: User = Depends(get_current_active_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current patient profile

    - Requires authentication (patient role)
    - Updates patient information
    - Recalculates profile completion percentage
    """
    try:
        patient_service = PatientService(db)
        patient = await patient_service.update_patient(str(current_user.id), data)

        return PatientResponse(**patient.to_dict())

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.get("/me/profile-completion", response_model=PatientProfileCompletion)
async def get_profile_completion(
    current_user: User = Depends(get_current_active_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Get profile completion status

    - Requires authentication (patient role)
    - Returns completion percentage and missing fields
    """
    try:
        patient_service = PatientService(db)
        completion = await patient_service.get_profile_completion(str(current_user.id))

        return PatientProfileCompletion(**completion)

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile completion: {str(e)}"
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_profile(
    current_user: User = Depends(get_current_active_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete current patient profile (soft delete)

    - Requires authentication (patient role)
    - Soft deletes the patient profile
    - User account remains but is marked as deleted
    """
    try:
        patient_service = PatientService(db)
        await patient_service.delete_patient(str(current_user.id))

        return None

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )


@router.post("/verify-emirates-id", response_model=VerifyEmiratesIDResponse, status_code=status.HTTP_200_OK)
async def verify_emirates_id(
    data: VerifyEmiratesIDRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify if Emirates ID is available for registration

    This endpoint checks if an Emirates ID number is already registered in the system.
    It does NOT require authentication, allowing users to check before completing registration.

    Args:
        data: Emirates ID to verify
        db: Database session

    Returns:
        VerifyEmiratesIDResponse indicating availability

    Example:
        Request: {"emirates_id": "784-1987-1234567-1"}
        Response: {"available": true, "message": "Emirates ID is available", "exists": false}
    """
    import re

    emirates_id = data.emirates_id.strip()

    # Normalize Emirates ID format
    # Remove all non-digit characters
    normalized_id = re.sub(r'[^\d]', '', emirates_id)

    # Validate format (must be 15 digits starting with 784)
    if len(normalized_id) != 15 or not normalized_id.startswith('784'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Emirates ID format. Must be 15 digits starting with 784."
        )

    # Format as 784-XXXX-XXXXXXX-X for consistency
    formatted_id = f"{normalized_id[:3]}-{normalized_id[3:7]}-{normalized_id[7:14]}-{normalized_id[14]}"

    try:
        # Query database for existing Emirates ID
        # Check both formatted and normalized versions
        query = select(Patient).where(
            (Patient.emirates_id == formatted_id) |
            (Patient.emirates_id == normalized_id) |
            (Patient.emirates_id == emirates_id)
        ).where(Patient.deleted_at.is_(None))

        result = await db.execute(query)
        existing_patient = result.scalars().first()

        if existing_patient:
            return VerifyEmiratesIDResponse(
                available=False,
                message="This Emirates ID is already registered",
                exists=True
            )
        else:
            return VerifyEmiratesIDResponse(
                available=True,
                message="Emirates ID is available for registration",
                exists=False
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify Emirates ID: {str(e)}"
        )
