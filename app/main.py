"""
Main FastAPI application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import init_db, close_db
from app.utils.redis_client import otp_redis_client, session_redis_client
from app.api.router import api_router
from app.core.middleware import LoggingMiddleware, ErrorHandlingMiddleware
from app.core.exceptions import NerulaException

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events

    Handles startup and shutdown operations
    """
    # Startup
    logger.info("Starting Neurula Health API...")

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Connect to Redis (optional for development)
        try:
            await otp_redis_client.connect()
            await session_redis_client.connect()
            logger.info("Redis clients connected")
        except Exception as redis_error:
            logger.warning(f"Redis connection failed (continuing without Redis): {redis_error}")
            logger.warning("OTP verification will use mock implementation")

        # Startup banner
        logger.info("")
        logger.info("=" * 80)
        logger.info("🚀 " + "NEURULA HEALTH API - SERVER STARTED".center(76) + " 🚀")
        logger.info("=" * 80)
        logger.info(f"📋 App Name:      {settings.APP_NAME}")
        logger.info(f"🏷️  Version:       {settings.APP_VERSION}")
        logger.info(f"🌍 Environment:   {settings.ENVIRONMENT}")
        logger.info(f"🐛 Debug Mode:    {settings.DEBUG}")
        logger.info("─" * 80)
        logger.info(f"🌐 Server URL:    http://{settings.HOST}:{settings.PORT}")
        logger.info(f"📚 API Docs:      http://{settings.HOST}:{settings.PORT}/docs")
        logger.info(f"📖 ReDoc:         http://{settings.HOST}:{settings.PORT}/redoc")
        logger.info(f"💚 Health Check:  http://{settings.HOST}:{settings.PORT}/health")
        logger.info("─" * 80)
        logger.info(f"🔒 CORS Origins:  {', '.join(settings.cors_origins_list) if settings.cors_origins_list != ['*'] else 'All origins (*)'}")
        logger.info(f"📊 Log Level:     {settings.LOG_LEVEL}")
        logger.info("=" * 80)
        logger.info("✅ Server is ready to accept connections!")
        logger.info("=" * 80)
        logger.info("")

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Neurula Health API...")

    try:
        # Close database connections
        await close_db()
        logger.info("Database connections closed")

        # Disconnect Redis (if connected)
        try:
            await otp_redis_client.disconnect()
            await session_redis_client.disconnect()
            logger.info("Redis clients disconnected")
        except Exception as redis_error:
            logger.warning(f"Redis disconnect warning: {redis_error}")

        logger.info("Application shut down successfully")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Neurula Health - Patient and Doctor Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)


# Exception handlers
@app.exception_handler(NerulaException)
async def neurula_exception_handler(request: Request, exc: NerulaException):
    """Handle custom application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "status_code": exc.status_code,
            "path": str(request.url.path),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "status_code": 422,
            "path": str(request.url.path),
            "details": errors,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.exception(f"Unexpected error: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url.path),
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# Include API router
app.include_router(api_router)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint

    Returns application status and version
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint

    Returns API information
    """
    return {
        "message": "Welcome to Neurula Health API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
