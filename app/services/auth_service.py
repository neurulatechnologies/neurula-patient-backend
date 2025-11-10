"""
Authentication service for user registration, login, and JWT management
"""
import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.user import User, UserRole
from app.models.patient import Patient
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    validate_password_strength,
)
from app.core.exceptions import (
    AuthenticationError,
    ValidationError,
    DuplicateError,
    NotFoundError,
)
from app.services.otp_service import OTPService
from app.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations"""

    def __init__(self, db: AsyncSession, otp_service: OTPService):
        self.db = db
        self.otp_service = otp_service

    async def register_user(self, data: RegisterRequest) -> Tuple[User, Patient, str]:
        """
        Register a new user and create patient profile

        Args:
            data: Registration data

        Returns:
            Tuple of (user, patient, otp)

        Raises:
            DuplicateError: If email or phone already exists
            ValidationError: If validation fails
        """
        logger.info("🔐 [AUTH SERVICE] Starting user registration process...")

        # Validate password strength
        logger.info("🔍 [VALIDATION] Checking password strength...")
        is_valid, error_msg = validate_password_strength(data.password)
        if not is_valid:
            logger.error(f"❌ [VALIDATION] Password validation failed: {error_msg}")
            raise ValidationError(error_msg)
        logger.info("✅ [VALIDATION] Password strength validated")

        # Check if email already exists
        logger.info(f"🔍 [DUPLICATE CHECK] Checking if email exists: {data.email}")
        result = await self.db.execute(
            select(User).where(User.email == data.email, User.deleted_at == None)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            logger.error(f"❌ [DUPLICATE CHECK] Email already registered: {data.email}")
            raise DuplicateError("Email already registered")
        logger.info("✅ [DUPLICATE CHECK] Email is available")

        # Check if phone already exists
        logger.info(f"🔍 [DUPLICATE CHECK] Checking if phone exists: {data.phone}")
        result = await self.db.execute(
            select(User).where(User.phone == data.phone, User.deleted_at == None)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            logger.error(f"❌ [DUPLICATE CHECK] Phone already registered: {data.phone}")
            raise DuplicateError("Phone number already registered")
        logger.info("✅ [DUPLICATE CHECK] Phone is available")

        # Check if Emirates ID already exists (if provided)
        if data.emirates_id:
            logger.info(f"🔍 [DUPLICATE CHECK] Checking if Emirates ID exists: {data.emirates_id}")
            result = await self.db.execute(
                select(Patient).where(
                    Patient.emirates_id == data.emirates_id,
                    Patient.deleted_at == None
                )
            )
            existing_patient = result.scalar_one_or_none()
            if existing_patient:
                logger.error(f"❌ [DUPLICATE CHECK] Emirates ID already registered: {data.emirates_id}")
                raise DuplicateError("Emirates ID already registered")
            logger.info("✅ [DUPLICATE CHECK] Emirates ID is available")

        # Create user
        logger.info("🔄 [DATABASE] Creating user record...")
        user = User(
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=False,  # Will be verified via OTP
            email_verified=False,
            phone_verified=False,
        )

        self.db.add(user)
        logger.info("🔄 [DATABASE] Flushing user to get ID...")
        await self.db.flush()  # Get user ID without committing
        logger.info(f"✅ [DATABASE] User record created with ID: {user.id}")

        # Create patient profile
        logger.info("🔄 [DATABASE] Creating patient profile...")
        patient = Patient(
            user_id=user.id,
            date_of_birth=datetime.strptime(data.date_of_birth, "%Y-%m-%d").date() if data.date_of_birth else None,
            gender=data.gender,
            nationality=data.nationality,
            emirates_id=data.emirates_id,
            passport_number=data.passport_number,
            height=data.height,
            weight=data.weight,
            emirate=data.emirate,
            city=data.city,
            address=data.address,
            location_pin=data.location_pin,
            medical_conditions=data.medical_conditions,
        )

        self.db.add(patient)
        logger.info("✅ [DATABASE] Patient profile created")

        # Calculate profile completion
        logger.info("🔄 [PROFILE] Calculating profile completion...")
        patient.profile_completion = patient.calculate_profile_completion()
        logger.info(f"✅ [PROFILE] Profile completion: {patient.profile_completion}%")

        logger.info("🔄 [DATABASE] Committing transaction...")
        await self.db.commit()
        logger.info("✅ [DATABASE] Transaction committed successfully")

        logger.info("🔄 [DATABASE] Refreshing user and patient records...")
        await self.db.refresh(user)
        await self.db.refresh(patient)
        logger.info("✅ [DATABASE] Records refreshed")

        # Generate and send OTP
        logger.info(f"🔄 [OTP] Generating OTP for: {data.email}")
        otp, _ = await self.otp_service.generate_and_store(data.email)
        logger.info(f"✅ [OTP] OTP generated successfully")

        logger.info(f"✅ [AUTH SERVICE] User registered successfully: {user.email}")

        # TODO: Send OTP via email/SMS
        # For now, just log it (in production, this should send actual email/SMS)
        if settings.DEBUG:
            logger.info("=" * 60)
            logger.info(f"🔑 DEBUG MODE - OTP CODE: {otp}")
            logger.info(f"📧 Email: {user.email}")
            logger.info(f"👤 User ID: {user.id}")
            logger.info("=" * 60)

        return user, patient, otp

    async def verify_otp(self, identifier: str, otp: str) -> Tuple[bool, Optional[User]]:
        """
        Verify OTP and activate user

        Args:
            identifier: Email or phone number
            otp: OTP code

        Returns:
            Tuple of (is_valid, user)

        Raises:
            NotFoundError: If user not found
        """
        # Verify OTP
        is_valid, error_msg = await self.otp_service.verify(identifier, otp)
        if not is_valid:
            raise ValidationError(error_msg)

        # Get user by email or phone
        result = await self.db.execute(
            select(User).where(
                or_(User.email == identifier, User.phone == identifier),
                User.deleted_at == None
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        # Update verification status
        user.is_verified = True
        if "@" in identifier:
            user.email_verified = True
        else:
            user.phone_verified = True

        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"User verified successfully: {user.email}")

        return True, user

    async def login(self, data: LoginRequest) -> Tuple[User, TokenResponse]:
        """
        Authenticate user and generate tokens

        Args:
            data: Login credentials

        Returns:
            Tuple of (user, tokens)

        Raises:
            AuthenticationError: If credentials are invalid
        """
        logger.info("🔓 [AUTH SERVICE] Starting login process...")
        logger.info(f"🔍 [LOGIN] Username/Email/Phone: {data.username}")

        # Find user by email or phone
        logger.info("🔍 [DATABASE] Looking up user by email or phone...")
        result = await self.db.execute(
            select(User).where(
                or_(User.email == data.username, User.phone == data.username),
                User.deleted_at == None
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"❌ [LOGIN] User not found: {data.username}")
            raise AuthenticationError("Invalid credentials")
        logger.info(f"✅ [DATABASE] User found: {user.email} (ID: {user.id})")

        # Verify password
        logger.info("🔍 [VERIFICATION] Verifying password...")
        if not verify_password(data.password, user.password_hash):
            logger.error(f"❌ [VERIFICATION] Invalid password for user: {user.email}")
            raise AuthenticationError("Invalid credentials")
        logger.info("✅ [VERIFICATION] Password verified")

        # Check if user is active
        logger.info("🔍 [VERIFICATION] Checking if user is active...")
        if not user.is_active:
            logger.error(f"❌ [VERIFICATION] User is inactive: {user.email}")
            raise AuthenticationError("Account is inactive")
        logger.info("✅ [VERIFICATION] User is active")

        # Check if user is verified
        logger.info("🔍 [VERIFICATION] Checking if user is verified...")
        if not user.is_verified:
            logger.error(f"❌ [VERIFICATION] User not verified: {user.email}")
            raise AuthenticationError("Account not verified. Please verify your email/phone")
        logger.info("✅ [VERIFICATION] User is verified")

        # Generate tokens
        logger.info("🔄 [TOKEN] Generating access token...")
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        logger.info("✅ [TOKEN] Access token generated")

        # For "remember me", extend refresh token expiration
        logger.info("🔄 [TOKEN] Generating refresh token...")
        if data.remember_me:
            logger.info("   (Remember me enabled)")
            refresh_token = create_refresh_token(
                data={"sub": str(user.id)}
            )
        else:
            refresh_token = create_refresh_token(
                data={"sub": str(user.id)}
            )
        logger.info("✅ [TOKEN] Refresh token generated")

        # Update last login
        logger.info("🔄 [DATABASE] Updating last login timestamp...")
        user.last_login = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        logger.info("✅ [DATABASE] Last login updated")

        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        logger.info(f"✅ [AUTH SERVICE] User logged in successfully: {user.email}")
        logger.info(f"   - User ID: {user.id}")
        logger.info(f"   - Role: {user.role.value}")

        return user, tokens

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Generate new access token from refresh token

        Args:
            refresh_token: Refresh token

        Returns:
            New token pair

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Decode refresh token
        payload = decode_refresh_token(refresh_token)
        if not payload:
            raise AuthenticationError("Invalid or expired refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.deleted_at == None)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        # Generate new tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )

        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )

        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        logger.info(f"Tokens refreshed for user: {user.email}")

        return tokens

    async def resend_otp(self, identifier: str) -> str:
        """
        Resend OTP to user

        Args:
            identifier: Email or phone number

        Returns:
            OTP code

        Raises:
            NotFoundError: If user not found
        """
        # Check if user exists
        result = await self.db.execute(
            select(User).where(
                or_(User.email == identifier, User.phone == identifier),
                User.deleted_at == None
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        # Generate and send new OTP
        otp, _ = await self.otp_service.generate_and_store(identifier)

        # TODO: Send OTP via email/SMS
        if settings.DEBUG:
            logger.info(f"OTP for {identifier}: {otp}")

        logger.info(f"OTP resent to: {identifier}")

        return otp

    async def change_password(self, user_id: str, old_password: str, new_password: str):
        """
        Change user password

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Raises:
            AuthenticationError: If old password is invalid
            ValidationError: If new password is weak
        """
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.deleted_at == None)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        # Verify old password
        if not verify_password(old_password, user.password_hash):
            raise AuthenticationError("Invalid current password")

        # Validate new password strength
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            raise ValidationError(error_msg)

        # Update password
        user.password_hash = hash_password(new_password)
        await self.db.commit()

        logger.info(f"Password changed for user: {user.email}")
