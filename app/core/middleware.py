"""
Middleware for authentication, CORS, logging, error handling
"""
import time
import logging
import json
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import NerulaException

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware to log all requests and responses with detailed information"""

    SENSITIVE_HEADERS = ['authorization', 'cookie', 'x-api-key', 'api-key']
    MAX_BODY_LENGTH = 10000  # Maximum characters to log from request/response body

    def mask_sensitive_headers(self, headers: dict) -> dict:
        """Mask sensitive header values"""
        masked = {}
        for key, value in headers.items():
            if key.lower() in self.SENSITIVE_HEADERS:
                masked[key] = "***MASKED***"
            else:
                masked[key] = value
        return masked

    async def get_request_body(self, request: Request) -> str:
        """Safely read and log request body"""
        try:
            body = await request.body()
            if not body:
                return "Empty body"

            # Try to decode as JSON for pretty printing
            try:
                body_str = body.decode('utf-8')
                if len(body_str) > self.MAX_BODY_LENGTH:
                    return f"{body_str[:self.MAX_BODY_LENGTH]}... [truncated, total size: {len(body_str)} chars]"

                # Try to parse as JSON for prettier output
                try:
                    json_body = json.loads(body_str)
                    return json.dumps(json_body, indent=2)
                except json.JSONDecodeError:
                    return body_str
            except UnicodeDecodeError:
                return f"<Binary data, size: {len(body)} bytes>"
        except Exception as e:
            return f"<Error reading body: {str(e)}>"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()

        # Generate banner for visual separation
        logger.info("=" * 80)
        logger.info(f"🔵 REQUEST START: {request.method} {request.url.path}")
        logger.info("=" * 80)

        # Log request details
        logger.info(f"📍 Path: {request.url.path}")
        logger.info(f"🔧 Method: {request.method}")
        logger.info(f"💻 Client: {request.client.host if request.client else 'Unknown'}")

        # Log query parameters
        if request.query_params:
            logger.info(f"🔍 Query Params: {dict(request.query_params)}")

        # Log headers (masked)
        headers = self.mask_sensitive_headers(dict(request.headers))
        logger.info(f"📋 Headers: {json.dumps(headers, indent=2)}")

        # Log request body
        if request.method in ["POST", "PUT", "PATCH"]:
            # Store body for re-reading (FastAPI consumes it)
            body_bytes = await request.body()

            # Log the body
            try:
                body_str = body_bytes.decode('utf-8')
                if len(body_str) > self.MAX_BODY_LENGTH:
                    logger.info(f"📦 Request Body: {body_str[:self.MAX_BODY_LENGTH]}... [truncated, total: {len(body_str)} chars]")
                else:
                    try:
                        json_body = json.loads(body_str)
                        logger.info(f"📦 Request Body:\n{json.dumps(json_body, indent=2)}")
                    except json.JSONDecodeError:
                        logger.info(f"📦 Request Body: {body_str}")
            except UnicodeDecodeError:
                logger.info(f"📦 Request Body: <Binary data, size: {len(body_bytes)} bytes>")

            # Reconstruct request with body for downstream processing
            async def receive():
                return {"type": "http.request", "body": body_bytes}

            request._receive = receive

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info("─" * 80)
            logger.info(f"✅ Status Code: {response.status_code}")
            logger.info(f"⏱️  Duration: {duration:.3f}s")
            logger.info("=" * 80)
            logger.info(f"🟢 REQUEST END: {request.method} {request.url.path}")
            logger.info("=" * 80)
            logger.info("")  # Empty line for readability

            # Add custom headers
            response.headers["X-Process-Time"] = str(duration)

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error("─" * 80)
            logger.error(f"❌ REQUEST FAILED: {request.method} {request.url.path}")
            logger.error(f"💥 Error: {str(e)}")
            logger.error(f"⏱️  Duration: {duration:.3f}s")
            logger.error("=" * 80)
            logger.error("", exc_info=True)
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
