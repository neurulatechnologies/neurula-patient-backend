"""
Tests for authentication endpoints
"""
import pytest
from fastapi import status


class TestRegistration:
    """Test user registration"""

    def test_register_success(self, client, test_user_data):
        """Test successful user registration"""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Registration successful. Please verify your email with the OTP sent."
        assert "user_id" in data
        assert data["email"] == test_user_data["email"]
        assert data["otp_sent"] is True

    def test_register_duplicate_email(self, client, test_user_data):
        """Test registration with duplicate email"""
        # Register first user
        client.post("/api/v1/auth/register", json=test_user_data)

        # Try to register again with same email
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client, test_user_data):
        """Test registration with invalid email"""
        test_user_data["email"] = "invalid-email"
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_weak_password(self, client, test_user_data):
        """Test registration with weak password"""
        test_user_data["password"] = "weak"
        response = client.post("/api/v1/auth/register", json=test_user_data)

        # Should fail validation
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_register_invalid_phone(self, client, test_user_data):
        """Test registration with invalid phone number"""
        test_user_data["phone"] = "123456"
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    """Test user login"""

    @pytest.fixture(autouse=True)
    async def setup(self, client, test_user_data):
        """Register and verify a user before each login test"""
        # This is a simplified version - in real tests, you'd need to handle OTP verification
        # For now, we'll just test the registration part
        self.user_data = test_user_data
        self.client = client

    def test_login_unverified_user(self, client, test_user_data, test_login_data):
        """Test login with unverified account"""
        # Register user
        client.post("/api/v1/auth/register", json=test_user_data)

        # Try to login without verification
        response = client.post("/api/v1/auth/login", json=test_login_data)

        # Should fail because account is not verified
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_invalid_credentials(self, client, test_login_data):
        """Test login with invalid credentials"""
        test_login_data["password"] = "WrongPassword123!"
        response = client.post("/api/v1/auth/login", json=test_login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent@test.com",
            "password": "Test@1234",
            "remember_me": False
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestOTP:
    """Test OTP functionality"""

    def test_verify_otp_invalid(self, client):
        """Test OTP verification with invalid code"""
        response = client.post("/api/v1/auth/verify-otp", json={
            "email": "test@neurula.health",
            "otp": "000000"
        })

        # Should fail - no OTP exists or invalid
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_verify_otp_invalid_format(self, client):
        """Test OTP verification with invalid format"""
        response = client.post("/api/v1/auth/verify-otp", json={
            "email": "test@neurula.health",
            "otp": "12345"  # Only 5 digits
        })

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_resend_otp_nonexistent_user(self, client):
        """Test resending OTP for non-existent user"""
        response = client.post("/api/v1/auth/resend-otp", json={
            "email": "nonexistent@test.com"
        })

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTokenRefresh:
    """Test token refresh"""

    def test_refresh_with_invalid_token(self, client):
        """Test token refresh with invalid refresh token"""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid-token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestHealthCheck:
    """Test health check endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "version" in data
