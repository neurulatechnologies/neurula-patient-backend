"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    VerifyOTPRequest,
    OTPVerificationResponse,
    ResendOTPRequest,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
    ChangePasswordRequest,
    MessageResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.services.otp_service import OTPService
from app.utils.redis_client import get_otp_redis
from app.dependencies import get_current_user
from app.models.user import User
from app.core.exceptions import NerulaException

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user (patient)

    - Creates user account and patient profile
    - Sends OTP for verification
    - Returns user ID and confirmation
    """
    try:
        # Get OTP service
        redis_client = await get_otp_redis()
        otp_service = OTPService(redis_client)

        # Register user
        auth_service = AuthService(db, otp_service)
        user, patient, otp = await auth_service.register_user(data)

        return RegisterResponse(
            message="Registration successful. Please verify your email with the OTP sent.",
            user_id=str(user.id),
            email=user.email,
            otp_sent=True
        )

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/verify-otp", response_model=OTPVerificationResponse)
async def verify_otp(
    data: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify OTP and activate account

    - Verifies OTP code
    - Activates user account
    - Returns user data and authentication tokens
    """
    try:
        identifier = data.email or data.phone

        if not identifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or phone number required"
            )

        # Get OTP service
        redis_client = await get_otp_redis()
        otp_service = OTPService(redis_client)

        # Verify OTP
        auth_service = AuthService(db, otp_service)
        is_valid, user = await auth_service.verify_otp(identifier, data.otp)

        if not is_valid:
            return OTPVerificationResponse(
                message="OTP verification failed",
                verified=False
            )

        # Generate tokens after successful verification
        from app.schemas.auth import LoginRequest
        login_data = LoginRequest(username=user.email, password="", remember_me=False)

        # Since we already verified the user, generate tokens directly
        from app.core.security import create_access_token, create_refresh_token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        from app.config import settings
        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        return OTPVerificationResponse(
            message="Verification successful",
            verified=True,
            user=UserResponse(**user.to_dict()),
            tokens=tokens
        )

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


@router.post("/resend-otp", response_model=MessageResponse)
async def resend_otp(
    data: ResendOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend OTP to user

    - Generates new OTP
    - Sends to email or phone
    - Returns confirmation
    """
    try:
        identifier = data.email or data.phone

        if not identifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or phone number required"
            )

        # Get OTP service
        redis_client = await get_otp_redis()
        otp_service = OTPService(redis_client)

        # Resend OTP
        auth_service = AuthService(db, otp_service)
        otp = await auth_service.resend_otp(identifier)

        return MessageResponse(
            message=f"OTP sent successfully to {identifier}",
            status="success"
        )

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend OTP: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    User login

    - Authenticates user credentials
    - Returns user data and JWT tokens
    - Supports "remember me" for extended session
    """
    try:
        # Get OTP service (needed for auth service)
        redis_client = await get_otp_redis()
        otp_service = OTPService(redis_client)

        # Login
        auth_service = AuthService(db, otp_service)
        user, tokens = await auth_service.login(data)

        return LoginResponse(
            message="Login successful",
            user=UserResponse(**user.to_dict()),
            tokens=tokens
        )

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token

    - Validates refresh token
    - Issues new access token
    - Returns new token pair
    """
    try:
        # Get OTP service (needed for auth service)
        redis_client = await get_otp_redis()
        otp_service = OTPService(redis_client)

        # Refresh token
        auth_service = AuthService(db, otp_service)
        tokens = await auth_service.refresh_access_token(data.refresh_token)

        return tokens

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change user password

    - Requires authentication
    - Validates old password
    - Updates to new password
    """
    try:
        # Get OTP service (needed for auth service)
        redis_client = await get_otp_redis()
        otp_service = OTPService(redis_client)

        # Change password
        auth_service = AuthService(db, otp_service)
        await auth_service.change_password(
            str(current_user.id),
            data.old_password,
            data.new_password
        )

        return MessageResponse(
            message="Password changed successfully",
            status="success"
        )

    except NerulaException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user information

    - Requires authentication
    - Returns user profile data
    """
    return UserResponse(**current_user.to_dict())


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
):
    """
    Logout user

    - Requires authentication
    - Client should discard tokens
    - (Token blacklisting can be implemented with Redis)
    """
    # In a production environment, you would:
    # 1. Add token to Redis blacklist
    # 2. Set expiry matching token expiry
    # 3. Check blacklist in auth middleware

    return MessageResponse(
        message="Logout successful. Please discard your tokens.",
        status="success"
    )
