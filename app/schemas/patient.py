"""
Pydantic schemas for patient endpoints
"""
from typing import Optional, Dict, Any
from datetime import date
from pydantic import BaseModel, Field, field_validator


class PatientCreate(BaseModel):
    """Schema for creating a patient profile"""
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern=r"^(Male|Female|Other)$")
    nationality: Optional[str] = None
    emirates_id: Optional[str] = None
    passport_number: Optional[str] = None
    height: Optional[float] = Field(None, gt=0, lt=300)
    weight: Optional[float] = Field(None, gt=0, lt=500)
    blood_group: Optional[str] = None
    emirate: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    location_pin: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PatientUpdate(BaseModel):
    """Schema for updating a patient profile"""
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern=r"^(Male|Female|Other)$")
    nationality: Optional[str] = None
    height: Optional[float] = Field(None, gt=0, lt=300)
    weight: Optional[float] = Field(None, gt=0, lt=500)
    blood_group: Optional[str] = None
    emirate: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    location_pin: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PatientResponse(BaseModel):
    """Response schema for patient data"""
    id: str
    user_id: str
    date_of_birth: Optional[str]
    gender: Optional[str]
    nationality: Optional[str]
    emirates_id: Optional[str]
    passport_number: Optional[str]
    height: Optional[float]
    weight: Optional[float]
    blood_group: Optional[str]
    emirate: Optional[str]
    city: Optional[str]
    address: Optional[str]
    location_pin: Optional[str]
    coordinates: Optional[Dict[str, float]]
    medical_conditions: Optional[str]
    allergies: Optional[str]
    medications: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    profile_completion: float
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PatientProfileCompletion(BaseModel):
    """Schema for profile completion status"""
    percentage: float = Field(..., ge=0, le=100)
    missing_fields: list[str] = []


class PatientWithUserResponse(BaseModel):
    """Response schema for patient data with user info"""
    patient: PatientResponse
    user: Dict[str, Any]  # User info from UserResponse
