"""
User model for authentication and authorization
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
import uuid
import enum

from app.database import Base
from app.utils.types import GUID


class UserRole(str, enum.Enum):
    """User role enumeration"""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class User(Base):
    """
    User model for authentication

    Stores core authentication data for all user types
    """
    __tablename__ = "users"

    # Primary key
    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)

    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)

    # User details
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.PATIENT)

    # Verification status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "email": self.email,
            "phone": self.phone,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "email_verified": self.email_verified,
            "phone_verified": self.phone_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
