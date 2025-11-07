"""
Pydantic schemas for doctor endpoints
"""
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class DoctorCreate(BaseModel):
    """Schema for creating a doctor profile"""
    specialty: str = Field(..., min_length=2, max_length=255)
    sub_specialty: Optional[str] = None
    license_number: str = Field(..., min_length=5, max_length=100)
    years_of_experience: Optional[int] = Field(None, ge=0, le=70)
    qualifications: Optional[List[str]] = None
    medical_school: Optional[str] = None
    hospital_affiliation: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    location: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    consultation_fee: float = Field(..., ge=0)
    consultation_types: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    bio: Optional[str] = None
    specialization_description: Optional[str] = None


class DoctorUpdate(BaseModel):
    """Schema for updating a doctor profile"""
    specialty: Optional[str] = None
    sub_specialty: Optional[str] = None
    years_of_experience: Optional[int] = Field(None, ge=0, le=70)
    qualifications: Optional[List[str]] = None
    medical_school: Optional[str] = None
    hospital_affiliation: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    location: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    consultation_fee: Optional[float] = Field(None, ge=0)
    consultation_types: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    is_accepting_patients: Optional[bool] = None
    bio: Optional[str] = None
    specialization_description: Optional[str] = None
    avatar_url: Optional[str] = None


class DoctorResponse(BaseModel):
    """Response schema for doctor data"""
    id: str
    user_id: str
    specialty: str
    sub_specialty: Optional[str]
    license_number: str
    years_of_experience: Optional[int]
    qualifications: Optional[List[str]]
    medical_school: Optional[str]
    hospital_affiliation: Optional[str]
    clinic_name: Optional[str]
    clinic_address: Optional[str]
    location: Optional[str]
    coordinates: Optional[Dict[str, float]]
    consultation_fee: float
    consultation_types: Optional[List[str]]
    languages: Optional[List[str]]
    rating: float
    total_reviews: int
    total_consultations: int
    is_accepting_patients: bool
    next_available_slot: Optional[str]
    working_hours: Optional[Dict]
    bio: Optional[str]
    specialization_description: Optional[str]
    avatar_url: Optional[str]
    profile_images: Optional[List[str]]
    status: str
    verified: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DoctorListItem(BaseModel):
    """Schema for doctor list items (simplified)"""
    id: str
    name: str
    specialty: str
    experience: Optional[str]  # "12 years experience"
    rating: str  # "4.8"
    location: Optional[str]
    next_available: Optional[str]  # "Today, 4:30 PM"
    fee: str  # "AED 180"
    avatar: Optional[str]


class DoctorSearchFilters(BaseModel):
    """Schema for doctor search filters"""
    specialty: Optional[str] = None
    search: Optional[str] = None  # Search by name
    location: Optional[str] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    max_fee: Optional[float] = Field(None, ge=0)
    consultation_type: Optional[str] = None
    language: Optional[str] = None
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)


class DoctorListResponse(BaseModel):
    """Response schema for doctor list"""
    doctors: List[DoctorListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class DoctorWithUserResponse(BaseModel):
    """Response schema for doctor data with user info"""
    doctor: DoctorResponse
    user: Dict  # User info


class SpecialtyResponse(BaseModel):
    """Response schema for specialty list"""
    specialties: List[str]
