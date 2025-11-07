"""
Custom exception classes
"""


class NerulaException(Exception):
    """Base exception for Neurula application"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(NerulaException):
    """Exception for authentication failures"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(NerulaException):
    """Exception for authorization failures"""
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, status_code=403)


class NotFoundError(NerulaException):
    """Exception for resource not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(NerulaException):
    """Exception for validation failures"""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class DuplicateError(NerulaException):
    """Exception for duplicate resource"""
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status_code=409)


class RateLimitError(NerulaException):
    """Exception for rate limit exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class OTPError(NerulaException):
    """Exception for OTP-related errors"""
    def __init__(self, message: str = "OTP verification failed"):
        super().__init__(message, status_code=400)
