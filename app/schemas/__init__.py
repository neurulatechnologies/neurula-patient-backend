"""
Pydantic schemas for API validation and serialization
"""
from app.schemas.auth import (
    RegisterRequest,
    VerifyOTPRequest,
    ResendOTPRequest,
    LoginRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    LoginResponse,
    RegisterResponse,
    OTPVerificationResponse,
    MessageResponse,
)

from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientProfileCompletion,
    PatientWithUserResponse,
)

from app.schemas.doctor import (
    DoctorCreate,
    DoctorUpdate,
    DoctorResponse,
    DoctorListItem,
    DoctorSearchFilters,
    DoctorListResponse,
    DoctorWithUserResponse,
    SpecialtyResponse,
)

__all__ = [
    # Auth
    "RegisterRequest",
    "VerifyOTPRequest",
    "ResendOTPRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "TokenResponse",
    "UserResponse",
    "LoginResponse",
    "RegisterResponse",
    "OTPVerificationResponse",
    "MessageResponse",
    # Patient
    "PatientCreate",
    "PatientUpdate",
    "PatientResponse",
    "PatientProfileCompletion",
    "PatientWithUserResponse",
    # Doctor
    "DoctorCreate",
    "DoctorUpdate",
    "DoctorResponse",
    "DoctorListItem",
    "DoctorSearchFilters",
    "DoctorListResponse",
    "DoctorWithUserResponse",
    "SpecialtyResponse",
]
