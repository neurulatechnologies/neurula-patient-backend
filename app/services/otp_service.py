"""
OTP service for generating, storing, and verifying OTPs
"""
import random
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta

from app.config import settings
from app.utils.redis_client import RedisClient
from app.core.exceptions import OTPError, RateLimitError

logger = logging.getLogger(__name__)


class OTPService:
    """Service for managing OTPs"""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.otp_length = settings.OTP_LENGTH
        self.otp_expire_minutes = settings.OTP_EXPIRE_MINUTES
        self.max_attempts = settings.OTP_MAX_ATTEMPTS
        self.resend_cooldown = settings.OTP_RESEND_COOLDOWN_SECONDS

    def _generate_otp(self) -> str:
        """Generate a random OTP"""
        return "".join([str(random.randint(0, 9)) for _ in range(self.otp_length)])

    def _get_otp_key(self, identifier: str) -> str:
        """Get Redis key for OTP"""
        return f"otp:{identifier}"

    def _get_attempts_key(self, identifier: str) -> str:
        """Get Redis key for OTP attempts"""
        return f"otp_attempts:{identifier}"

    def _get_resend_key(self, identifier: str) -> str:
        """Get Redis key for resend cooldown"""
        return f"otp_resend:{identifier}"

    def _get_rate_limit_key(self, identifier: str) -> str:
        """Get Redis key for rate limiting"""
        return f"otp_rate_limit:{identifier}"

    async def generate_and_store(self, identifier: str) -> Tuple[str, int]:
        """
        Generate and store OTP in Redis

        Args:
            identifier: User identifier (email or phone)

        Returns:
            Tuple of (otp, expires_in_seconds)

        Raises:
            RateLimitError: If rate limit exceeded
            OTPError: If resend cooldown not elapsed
        """
        # Check rate limit (max 5 OTPs per hour)
        rate_limit_key = self._get_rate_limit_key(identifier)
        rate_limit_count = await self.redis.get(rate_limit_key)

        if rate_limit_count and int(rate_limit_count) >= settings.OTP_RATE_LIMIT_PER_HOUR:
            raise RateLimitError("Too many OTP requests. Please try again later.")

        # Check resend cooldown
        resend_key = self._get_resend_key(identifier)
        if await self.redis.exists(resend_key):
            ttl = await self.redis.ttl(resend_key)
            raise OTPError(f"Please wait {ttl} seconds before requesting a new OTP")

        # Generate OTP
        otp = self._generate_otp()

        # Store OTP in Redis with expiration
        otp_key = self._get_otp_key(identifier)
        expire_seconds = self.otp_expire_minutes * 60
        await self.redis.set(otp_key, otp, ex=expire_seconds)

        # Reset attempts counter
        attempts_key = self._get_attempts_key(identifier)
        await self.redis.set(attempts_key, "0", ex=expire_seconds)

        # Set resend cooldown
        await self.redis.set(resend_key, "1", ex=self.resend_cooldown)

        # Increment rate limit counter
        if not rate_limit_count:
            await self.redis.set(rate_limit_key, "1", ex=3600)  # 1 hour
        else:
            await self.redis.incr(rate_limit_key)

        logger.info(f"Generated OTP for {identifier}")

        return otp, expire_seconds

    async def verify(self, identifier: str, otp: str) -> Tuple[bool, Optional[str]]:
        """
        Verify OTP

        Args:
            identifier: User identifier (email or phone)
            otp: OTP to verify

        Returns:
            Tuple of (is_valid, error_message)
        """
        otp_key = self._get_otp_key(identifier)
        attempts_key = self._get_attempts_key(identifier)

        # Check if OTP exists
        stored_otp = await self.redis.get(otp_key)
        if not stored_otp:
            return False, "OTP expired or not found"

        # Check attempts
        attempts = await self.redis.get(attempts_key)
        if attempts and int(attempts) >= self.max_attempts:
            # Delete OTP after max attempts
            await self.redis.delete(otp_key)
            await self.redis.delete(attempts_key)
            return False, "Maximum verification attempts exceeded. Please request a new OTP"

        # Verify OTP
        if otp != stored_otp:
            # Increment attempts
            await self.redis.incr(attempts_key)
            remaining_attempts = self.max_attempts - (int(attempts) + 1 if attempts else 1)

            if remaining_attempts <= 0:
                await self.redis.delete(otp_key)
                await self.redis.delete(attempts_key)
                return False, "Invalid OTP. Maximum attempts exceeded"

            return False, f"Invalid OTP. {remaining_attempts} attempts remaining"

        # OTP is valid - delete it
        await self.redis.delete(otp_key)
        await self.redis.delete(attempts_key)

        logger.info(f"OTP verified successfully for {identifier}")

        return True, None

    async def delete_otp(self, identifier: str):
        """
        Delete OTP from Redis

        Args:
            identifier: User identifier (email or phone)
        """
        otp_key = self._get_otp_key(identifier)
        attempts_key = self._get_attempts_key(identifier)

        await self.redis.delete(otp_key)
        await self.redis.delete(attempts_key)

        logger.info(f"Deleted OTP for {identifier}")

    async def get_ttl(self, identifier: str) -> int:
        """
        Get remaining TTL for OTP

        Args:
            identifier: User identifier (email or phone)

        Returns:
            TTL in seconds, -1 if OTP doesn't exist
        """
        otp_key = self._get_otp_key(identifier)
        return await self.redis.ttl(otp_key)

    async def can_resend(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if OTP can be resent

        Args:
            identifier: User identifier (email or phone)

        Returns:
            Tuple of (can_resend, cooldown_seconds)
        """
        resend_key = self._get_resend_key(identifier)

        if await self.redis.exists(resend_key):
            ttl = await self.redis.ttl(resend_key)
            return False, ttl

        return True, 0


# For testing purposes (development only)
async def get_otp_for_testing(redis_client: RedisClient, identifier: str) -> Optional[str]:
    """
    Get OTP from Redis for testing (development only)

    WARNING: This should only be used in development/testing environments
    """
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("Cannot retrieve OTP in production environment")

    otp_key = f"otp:{identifier}"
    return await redis_client.get(otp_key)
