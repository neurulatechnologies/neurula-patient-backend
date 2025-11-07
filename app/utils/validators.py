"""
Custom validation utilities
"""
import re
from typing import Tuple, Optional


def validate_emirates_id(emirates_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate UAE Emirates ID format

    Format: 784-XXXX-XXXXXXX-X (15 digits total, starting with 784)

    Args:
        emirates_id: Emirates ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not emirates_id:
        return False, "Emirates ID is required"

    # Remove hyphens for validation
    clean_id = emirates_id.replace("-", "").replace(" ", "")

    # Must be 15 digits
    if not clean_id.isdigit():
        return False, "Emirates ID must contain only digits"

    if len(clean_id) != 15:
        return False, "Emirates ID must be 15 digits long"

    # Must start with 784 (UAE country code)
    if not clean_id.startswith("784"):
        return False, "Emirates ID must start with 784"

    return True, None


def validate_phone_number(phone: str, country_code: str = "+971") -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate and format phone number

    Args:
        phone: Phone number to validate
        country_code: Expected country code (default: +971 for UAE)

    Returns:
        Tuple of (is_valid, formatted_phone, error_message)
    """
    if not phone:
        return False, None, "Phone number is required"

    # Remove spaces, hyphens, parentheses
    clean_phone = re.sub(r"[\s\-\(\)]", "", phone)

    # Check if starts with country code
    if not clean_phone.startswith(country_code):
        # Try adding country code
        if clean_phone.startswith("0"):
            clean_phone = country_code + clean_phone[1:]
        elif clean_phone.startswith("+"):
            return False, None, f"Invalid country code. Expected: {country_code}"
        else:
            clean_phone = country_code + clean_phone

    # UAE phone numbers: +971 XX XXX XXXX (total 13 chars including +971)
    if country_code == "+971":
        if len(clean_phone) != 13:
            return False, None, "Invalid UAE phone number format. Expected: +971 XX XXX XXXX"

        if not clean_phone[1:].isdigit():
            return False, None, "Phone number must contain only digits after country code"

    return True, clean_phone, None


def validate_password_strength(password: str, min_length: int = 8) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength

    Requirements:
    - Minimum length
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Password to validate
        min_length: Minimum password length

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"

    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email format

    Args:
        email: Email to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"

    # Basic email regex
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        return False, "Invalid email format"

    return True, None


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

    # Remove control characters except newlines and tabs
    text = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]", "", text)

    return text.strip()
