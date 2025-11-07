"""
Doctor model for doctor-specific data
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base
from app.utils.types import GUID


class DoctorStatus(str, enum.Enum):
    """Doctor status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    SUSPENDED = "suspended"


class ConsultationType(str, enum.Enum):
    """Consultation type enumeration"""
    IN_PERSON = "In-person"
    ONLINE = "Online"
    HOME_VISIT = "Home Visit"


class Doctor(Base):
    """
    Doctor model for storing doctor-specific information

    Extends User model with professional and practice data
    """
    __tablename__ = "doctors"

    # Primary key
    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to User
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Professional details
    specialty = Column(String(255), nullable=False, index=True)
    sub_specialty = Column(String(255), nullable=True)
    license_number = Column(String(100), unique=True, nullable=False, index=True)
    years_of_experience = Column(Integer, nullable=True)

    # Qualifications
    qualifications = Column(JSON, nullable=True)  # ["MBBS", "MD", "Fellowship"]
    medical_school = Column(String(255), nullable=True)

    # Practice information
    hospital_affiliation = Column(String(255), nullable=True)
    clinic_name = Column(String(255), nullable=True)
    clinic_address = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)  # City/Area
    coordinates = Column(JSON, nullable=True)  # {"latitude": 25.xxx, "longitude": 55.xxx}

    # Consultation details
    consultation_fee = Column(Float, nullable=False, default=0.0)  # in AED
    consultation_types = Column(JSON, nullable=True)  # ["In-person", "Online", "Home Visit"]
    languages = Column(JSON, nullable=True)  # ["English", "Arabic", "Hindi"]

    # Ratings and reviews
    rating = Column(Float, default=0.0, nullable=False)  # Average rating (0-5)
    total_reviews = Column(Integer, default=0, nullable=False)
    total_consultations = Column(Integer, default=0, nullable=False)

    # Availability
    is_accepting_patients = Column(Boolean, default=True, nullable=False)
    next_available_slot = Column(DateTime, nullable=True)
    working_hours = Column(JSON, nullable=True)  # {day: {start, end, breaks}}

    # Bio and description
    bio = Column(Text, nullable=True)
    specialization_description = Column(Text, nullable=True)

    # Profile media
    avatar_url = Column(String(500), nullable=True)
    profile_images = Column(JSON, nullable=True)

    # Status
    status = Column(SQLEnum(DoctorStatus), default=DoctorStatus.ACTIVE, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)  # Verified by admin

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Doctor {self.user_id} - {self.specialty}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "specialty": self.specialty,
            "sub_specialty": self.sub_specialty,
            "license_number": self.license_number,
            "years_of_experience": self.years_of_experience,
            "qualifications": self.qualifications,
            "medical_school": self.medical_school,
            "hospital_affiliation": self.hospital_affiliation,
            "clinic_name": self.clinic_name,
            "clinic_address": self.clinic_address,
            "location": self.location,
            "coordinates": self.coordinates,
            "consultation_fee": self.consultation_fee,
            "consultation_types": self.consultation_types,
            "languages": self.languages,
            "rating": self.rating,
            "total_reviews": self.total_reviews,
            "total_consultations": self.total_consultations,
            "is_accepting_patients": self.is_accepting_patients,
            "next_available_slot": self.next_available_slot.isoformat() if self.next_available_slot else None,
            "working_hours": self.working_hours,
            "bio": self.bio,
            "specialization_description": self.specialization_description,
            "avatar_url": self.avatar_url,
            "profile_images": self.profile_images,
            "status": self.status.value,
            "verified": self.verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
