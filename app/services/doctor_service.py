"""
Doctor service for managing doctor profiles and search
"""
import logging
from typing import Optional, List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from datetime import datetime

from app.models.doctor import Doctor, DoctorStatus
from app.models.user import User
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorSearchFilters
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class DoctorService:
    """Service for doctor operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_doctor_by_user_id(self, user_id: str) -> Optional[Doctor]:
        """
        Get doctor by user ID

        Args:
            user_id: User ID

        Returns:
            Doctor or None

        Raises:
            NotFoundError: If doctor not found
        """
        result = await self.db.execute(
            select(Doctor).where(
                Doctor.user_id == user_id,
                Doctor.deleted_at == None
            )
        )
        doctor = result.scalar_one_or_none()

        if not doctor:
            raise NotFoundError("Doctor profile not found")

        return doctor

    async def get_doctor_by_id(self, doctor_id: str) -> Optional[Doctor]:
        """
        Get doctor by doctor ID

        Args:
            doctor_id: Doctor ID

        Returns:
            Doctor or None

        Raises:
            NotFoundError: If doctor not found
        """
        result = await self.db.execute(
            select(Doctor).where(
                Doctor.id == doctor_id,
                Doctor.deleted_at == None
            )
        )
        doctor = result.scalar_one_or_none()

        if not doctor:
            raise NotFoundError("Doctor not found")

        return doctor

    async def get_doctor_with_user(self, doctor_id: str) -> Tuple[Doctor, User]:
        """
        Get doctor with user information

        Args:
            doctor_id: Doctor ID

        Returns:
            Tuple of (doctor, user)

        Raises:
            NotFoundError: If doctor or user not found
        """
        doctor = await self.get_doctor_by_id(doctor_id)

        # Get user
        result = await self.db.execute(
            select(User).where(
                User.id == doctor.user_id,
                User.deleted_at == None
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        return doctor, user

    async def search_doctors(self, filters: DoctorSearchFilters) -> Tuple[List[Doctor], int]:
        """
        Search doctors with filters

        Args:
            filters: Search filters

        Returns:
            Tuple of (doctors list, total count)
        """
        # Build query
        query = select(Doctor).where(
            Doctor.deleted_at == None,
            Doctor.status == DoctorStatus.ACTIVE,
            Doctor.verified == True
        )

        # Apply filters
        if filters.specialty:
            query = query.where(Doctor.specialty.ilike(f"%{filters.specialty}%"))

        if filters.search:
            # Search in user's full_name via join
            query = query.join(User).where(
                or_(
                    User.full_name.ilike(f"%{filters.search}%"),
                    Doctor.specialty.ilike(f"%{filters.search}%")
                )
            )

        if filters.location:
            query = query.where(Doctor.location.ilike(f"%{filters.location}%"))

        if filters.min_rating:
            query = query.where(Doctor.rating >= filters.min_rating)

        if filters.max_fee:
            query = query.where(Doctor.consultation_fee <= filters.max_fee)

        if filters.consultation_type:
            # Check if consultation_types array contains the type
            query = query.where(Doctor.consultation_types.contains([filters.consultation_type]))

        if filters.language:
            # Check if languages array contains the language
            query = query.where(Doctor.languages.contains([filters.language]))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar()

        # Apply pagination
        query = query.offset((filters.page - 1) * filters.limit).limit(filters.limit)

        # Order by rating (descending)
        query = query.order_by(Doctor.rating.desc())

        # Execute query
        result = await self.db.execute(query)
        doctors = result.scalars().all()

        return list(doctors), total

    async def get_specialties(self) -> List[str]:
        """
        Get list of all specialties

        Returns:
            List of specialty strings
        """
        result = await self.db.execute(
            select(Doctor.specialty).where(
                Doctor.deleted_at == None,
                Doctor.status == DoctorStatus.ACTIVE
            ).distinct()
        )
        specialties = result.scalars().all()

        return sorted(list(set(specialties)))

    async def update_doctor(self, user_id: str, data: DoctorUpdate) -> Doctor:
        """
        Update doctor profile

        Args:
            user_id: User ID
            data: Update data

        Returns:
            Updated doctor

        Raises:
            NotFoundError: If doctor not found
        """
        doctor = await self.get_doctor_by_user_id(user_id)

        # Update fields
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(doctor, field):
                setattr(doctor, field, value)

        await self.db.commit()
        await self.db.refresh(doctor)

        logger.info(f"Doctor profile updated: {doctor.id}")

        return doctor

    async def create_doctor(self, user_id: str, data: DoctorCreate) -> Doctor:
        """
        Create doctor profile

        Args:
            user_id: User ID
            data: Doctor data

        Returns:
            Created doctor

        Raises:
            ValidationError: If user already has doctor profile
        """
        # Check if doctor profile already exists
        result = await self.db.execute(
            select(Doctor).where(
                Doctor.user_id == user_id,
                Doctor.deleted_at == None
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise ValidationError("Doctor profile already exists")

        # Create doctor
        doctor = Doctor(
            user_id=user_id,
            specialty=data.specialty,
            sub_specialty=data.sub_specialty,
            license_number=data.license_number,
            years_of_experience=data.years_of_experience,
            qualifications=data.qualifications,
            medical_school=data.medical_school,
            hospital_affiliation=data.hospital_affiliation,
            clinic_name=data.clinic_name,
            clinic_address=data.clinic_address,
            location=data.location,
            coordinates=data.coordinates,
            consultation_fee=data.consultation_fee,
            consultation_types=data.consultation_types,
            languages=data.languages,
            bio=data.bio,
            specialization_description=data.specialization_description,
        )

        self.db.add(doctor)
        await self.db.commit()
        await self.db.refresh(doctor)

        logger.info(f"Doctor profile created: {doctor.id}")

        return doctor

    async def delete_doctor(self, user_id: str):
        """
        Soft delete doctor profile

        Args:
            user_id: User ID

        Raises:
            NotFoundError: If doctor not found
        """
        doctor = await self.get_doctor_by_user_id(user_id)

        # Soft delete
        doctor.deleted_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Doctor profile deleted: {doctor.id}")
