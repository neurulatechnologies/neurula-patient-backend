"""
Security utilities: JWT, password hashing, encryption, validation
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token (must include 'sub' for user ID)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token

    Args:
        data: Data to encode in the token (must include 'sub' for user ID)

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify token type
        if payload.get("type") != "access":
            return None

        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT refresh token

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify token type
        if payload.get("type") != "refresh":
            return None

        return payload
    except JWTError:
        return None


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength

    Requirements:
    - Minimum length from settings
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"

    return True, None


def validate_emirates_id(emirates_id: str) -> bool:
    """
    Validate UAE Emirates ID format

    Format: 784-XXXX-XXXXXXX-X

    Args:
        emirates_id: Emirates ID to validate

    Returns:
        True if valid format, False otherwise
    """
    # Remove hyphens for validation
    clean_id = emirates_id.replace("-", "")

    # Must be 15 digits
    if not clean_id.isdigit() or len(clean_id) != 15:
        return False

    # Must start with 784 (UAE country code)
    if not clean_id.startswith("784"):
        return False

    return True


def validate_phone_number(phone: str, country_code: str = "+971") -> tuple[bool, Optional[str]]:
    """
    Validate phone number format

    Args:
        phone: Phone number to validate
        country_code: Expected country code (default: +971 for UAE)

    Returns:
        Tuple of (is_valid, formatted_phone_or_error)
    """
    # Remove spaces, hyphens, parentheses
    clean_phone = re.sub(r"[\s\-\(\)]", "", phone)

    # Check if starts with country code
    if not clean_phone.startswith(country_code):
        # Try adding country code
        if clean_phone.startswith("0"):
            clean_phone = country_code + clean_phone[1:]
        else:
            clean_phone = country_code + clean_phone

    # UAE phone numbers: +971 XX XXX XXXX (total 13 chars including +971)
    if country_code == "+971":
        if len(clean_phone) != 13:
            return False, "Invalid UAE phone number format. Expected: +971 XX XXX XXXX"

    return True, clean_phone


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    if not text:
        return text

    # Remove potential HTML/script tags
    text = re.sub(r"<[^>]*>", "", text)

    # Remove null bytes
    text = text.replace("\x00", "")

    return text.strip()
