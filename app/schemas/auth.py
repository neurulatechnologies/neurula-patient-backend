"""
Pydantic schemas for authentication endpoints
"""
from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class RegisterRequest(BaseModel):
    """Request schema for user registration"""
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+971\d{9}$")  # UAE format: +971XXXXXXXXX
    password: str = Field(..., min_length=8)

    # Registration method
    registration_method: str = Field(..., pattern=r"^(emirates_id|passport|manual)$")

    # Demographics
    date_of_birth: Optional[str] = None  # Format: yyyy-mm-dd
    gender: Optional[str] = Field(None, pattern=r"^(Male|Female|Other)$")
    nationality: Optional[str] = None

    # Identification
    emirates_id: Optional[str] = None  # Format: 784-XXXX-XXXXXXX-X
    passport_number: Optional[str] = None

    # Physical measurements
    height: Optional[float] = Field(None, gt=0, lt=300)  # in cm
    weight: Optional[float] = Field(None, gt=0, lt=500)  # in kg

    # Address
    emirate: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    location_pin: Optional[str] = None

    # Medical
    medical_conditions: Optional[str] = None

    @field_validator("emirates_id")
    @classmethod
    def validate_emirates_id(cls, v):
        if v:
            clean_id = v.replace("-", "")
            if not clean_id.isdigit() or len(clean_id) != 15 or not clean_id.startswith("784"):
                raise ValueError("Invalid Emirates ID format. Expected: 784-XXXX-XXXXXXX-X")
        return v


class VerifyOTPRequest(BaseModel):
    """Request schema for OTP verification"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")

    @field_validator("otp")
    @classmethod
    def validate_otp_digits(cls, v):
        if not v.isdigit():
            raise ValueError("OTP must contain only digits")
        return v


class ResendOTPRequest(BaseModel):
    """Request schema for resending OTP"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    """Request schema for user login"""
    username: str = Field(..., min_length=3)  # Can be email or phone
    password: str = Field(..., min_length=8)
    remember_me: bool = False


class RefreshTokenRequest(BaseModel):
    """Request schema for refreshing access token"""
    refresh_token: str = Field(..., min_length=10)


class ChangePasswordRequest(BaseModel):
    """Request schema for changing password"""
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request schema for resetting password"""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)


# Response Schemas

class TokenResponse(BaseModel):
    """Response schema for authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """Response schema for user data"""
    id: str
    email: str
    phone: Optional[str]
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    email_verified: bool
    phone_verified: bool
    created_at: str
    last_login: Optional[str]

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Response schema for successful login"""
    message: str
    user: UserResponse
    tokens: TokenResponse


class RegisterResponse(BaseModel):
    """Response schema for successful registration"""
    message: str
    user_id: str
    email: str
    otp_sent: bool


class OTPVerificationResponse(BaseModel):
    """Response schema for OTP verification"""
    message: str
    verified: bool
    user: Optional[UserResponse] = None
    tokens: Optional[TokenResponse] = None


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    status: str = "success"
