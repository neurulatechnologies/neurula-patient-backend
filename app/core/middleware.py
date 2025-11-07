"""
Middleware for authentication, CORS, logging, error handling
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import NerulaException

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": f"{duration:.3f}s",
                }
            )

            # Add custom headers
            response.headers["X-Process-Time"] = str(duration)

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} - Error: {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration": f"{duration:.3f}s",
                },
                exc_info=True
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions globally"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)

        except NerulaException as e:
            # Handle custom application exceptions
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.message,
                    "status_code": e.status_code,
                    "path": request.url.path,
                }
            )

        except ValueError as e:
            # Handle value errors (typically validation)
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": str(e),
                    "status_code": 422,
                    "path": request.url.path,
                }
            )

        except Exception as e:
            # Handle unexpected errors
            logger.exception(f"Unexpected error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "status_code": 500,
                    "path": request.url.path,
                }
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware

    Note: This is a basic implementation. For production, use Redis-based
    rate limiting or a dedicated service like Kong or Traefik.
    """

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}  # {client_ip: [(timestamp, count)]}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Skip rate limiting for health check endpoint
        if request.url.path == "/health":
            return await call_next(request)

        # Current timestamp
        current_time = time.time()

        # Clean old entries for this client
        if client_ip in self.clients:
            self.clients[client_ip] = [
                (ts, count) for ts, count in self.clients[client_ip]
                if current_time - ts < self.period
            ]

        # Calculate total requests in current period
        total_requests = sum(count for ts, count in self.clients.get(client_ip, []))

        # Check rate limit
        if total_requests >= self.calls:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "status_code": 429,
                    "retry_after": self.period,
                }
            )

        # Add current request
        if client_ip not in self.clients:
            self.clients[client_ip] = []
        self.clients[client_ip].append((current_time, 1))

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls - total_requests - 1))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))

        return response
