"""
Patient service for managing patient profiles and data
"""
import logging
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientUpdate
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class PatientService:
    """Service for patient operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_patient_by_user_id(self, user_id: str) -> Optional[Patient]:
        """
        Get patient by user ID

        Args:
            user_id: User ID

        Returns:
            Patient or None

        Raises:
            NotFoundError: If patient not found
        """
        result = await self.db.execute(
            select(Patient).where(
                Patient.user_id == user_id,
                Patient.deleted_at == None
            )
        )
        patient = result.scalar_one_or_none()

        if not patient:
            raise NotFoundError("Patient profile not found")

        return patient

    async def get_patient_by_id(self, patient_id: str) -> Optional[Patient]:
        """
        Get patient by patient ID

        Args:
            patient_id: Patient ID

        Returns:
            Patient or None

        Raises:
            NotFoundError: If patient not found
        """
        result = await self.db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.deleted_at == None
            )
        )
        patient = result.scalar_one_or_none()

        if not patient:
            raise NotFoundError("Patient not found")

        return patient

    async def get_patient_with_user(self, user_id: str) -> tuple[Patient, User]:
        """
        Get patient with user information

        Args:
            user_id: User ID

        Returns:
            Tuple of (patient, user)

        Raises:
            NotFoundError: If patient or user not found
        """
        # Get patient
        patient = await self.get_patient_by_user_id(user_id)

        # Get user
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.deleted_at == None
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        return patient, user

    async def update_patient(self, user_id: str, data: PatientUpdate) -> Patient:
        """
        Update patient profile

        Args:
            user_id: User ID
            data: Update data

        Returns:
            Updated patient

        Raises:
            NotFoundError: If patient not found
        """
        patient = await self.get_patient_by_user_id(user_id)

        # Update fields
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(patient, field):
                setattr(patient, field, value)

        # Recalculate profile completion
        patient.profile_completion = patient.calculate_profile_completion()

        await self.db.commit()
        await self.db.refresh(patient)

        logger.info(f"Patient profile updated: {patient.id}")

        return patient

    async def get_profile_completion(self, user_id: str) -> Dict[str, any]:
        """
        Get profile completion status

        Args:
            user_id: User ID

        Returns:
            Dict with percentage and missing fields

        Raises:
            NotFoundError: If patient not found
        """
        patient = await self.get_patient_by_user_id(user_id)

        # Calculate completion
        percentage = patient.calculate_profile_completion()

        # Identify missing fields
        missing_fields = []
        field_labels = {
            "date_of_birth": "Date of Birth",
            "gender": "Gender",
            "nationality": "Nationality",
            "height": "Height",
            "weight": "Weight",
            "blood_group": "Blood Group",
            "emirate": "Emirate",
            "address": "Address",
            "emergency_contact_name": "Emergency Contact Name",
            "emergency_contact_phone": "Emergency Contact Phone",
        }

        # Check required fields
        if not patient.date_of_birth:
            missing_fields.append(field_labels["date_of_birth"])
        if not patient.gender:
            missing_fields.append(field_labels["gender"])
        if not patient.nationality:
            missing_fields.append(field_labels["nationality"])
        if not (patient.emirates_id or patient.passport_number):
            missing_fields.append("Emirates ID or Passport")
        if not patient.height:
            missing_fields.append(field_labels["height"])
        if not patient.weight:
            missing_fields.append(field_labels["weight"])
        if not patient.blood_group:
            missing_fields.append(field_labels["blood_group"])
        if not patient.emirate:
            missing_fields.append(field_labels["emirate"])
        if not patient.address:
            missing_fields.append(field_labels["address"])
        if not patient.emergency_contact_name:
            missing_fields.append(field_labels["emergency_contact_name"])
        if not patient.emergency_contact_phone:
            missing_fields.append(field_labels["emergency_contact_phone"])

        return {
            "percentage": percentage,
            "missing_fields": missing_fields
        }

    async def delete_patient(self, user_id: str):
        """
        Soft delete patient profile

        Args:
            user_id: User ID

        Raises:
            NotFoundError: If patient not found
        """
        patient = await self.get_patient_by_user_id(user_id)

        # Soft delete
        from datetime import datetime
        patient.deleted_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Patient profile deleted: {patient.id}")
