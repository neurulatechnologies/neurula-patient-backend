"""
Patient model for patient-specific data
"""
from datetime import datetime, date
from sqlalchemy import Column, String, Date, Float, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base
from app.utils.types import GUID


class Gender(str, enum.Enum):
    """Gender enumeration"""
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class Patient(Base):
    """
    Patient model for storing patient-specific information

    Extends User model with medical and demographic data
    """
    __tablename__ = "patients"

    # Primary key
    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to User
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Demographics
    date_of_birth = Column(Date, nullable=True)
    gender = Column(SQLEnum(Gender), nullable=True)
    nationality = Column(String(100), nullable=True)

    # Identification
    emirates_id = Column(String(20), unique=True, nullable=True, index=True)
    passport_number = Column(String(50), unique=True, nullable=True, index=True)
    emirates_id_image_path = Column(String(500), nullable=True)  # Path to Emirates ID scan
    passport_image_path = Column(String(500), nullable=True)  # Path to Passport scan

    # Physical measurements
    height = Column(Float, nullable=True)  # in cm
    weight = Column(Float, nullable=True)  # in kg
    blood_group = Column(String(5), nullable=True)  # A+, B-, O+, etc.

    # Address information
    emirate = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    location_pin = Column(String(255), nullable=True)  # Google Maps pin or coordinates
    coordinates = Column(JSON, nullable=True)  # {"latitude": 25.xxx, "longitude": 55.xxx}

    # Medical information
    medical_conditions = Column(Text, nullable=True)  # Comma-separated or text
    allergies = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    # Profile completion
    profile_completion = Column(Float, default=0.0, nullable=False)  # Percentage 0-100

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Patient {self.user_id}>"

    def calculate_profile_completion(self) -> float:
        """Calculate profile completion percentage"""
        fields = [
            self.date_of_birth,
            self.gender,
            self.nationality,
            self.emirates_id or self.passport_number,  # At least one ID
            self.height,
            self.weight,
            self.blood_group,
            self.emirate,
            self.address,
            self.emergency_contact_name,
            self.emergency_contact_phone,
        ]

        filled_fields = sum(1 for field in fields if field is not None)
        total_fields = len(fields)

        return round((filled_fields / total_fields) * 100, 2)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender.value if self.gender else None,
            "nationality": self.nationality,
            "emirates_id": self.emirates_id,
            "passport_number": self.passport_number,
            "emirates_id_image_path": self.emirates_id_image_path,
            "passport_image_path": self.passport_image_path,
            "height": self.height,
            "weight": self.weight,
            "blood_group": self.blood_group,
            "emirate": self.emirate,
            "city": self.city,
            "address": self.address,
            "location_pin": self.location_pin,
            "coordinates": self.coordinates,
            "medical_conditions": self.medical_conditions,
            "allergies": self.allergies,
            "medications": self.medications,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "profile_completion": self.profile_completion,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
