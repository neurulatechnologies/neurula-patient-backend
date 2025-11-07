"""
OCR API endpoints for document scanning
"""
import os
import uuid
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ocr_service import get_ocr_service
from app.models.patient import Patient
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])

# Allowed image extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class OCRResponse(BaseModel):
    """Response model for OCR processing"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    raw_text: Optional[str] = None
    image_quality: Optional[dict] = None
    image_path: Optional[str] = None


def validate_image_file(file: UploadFile) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded image file

    Args:
        file: Uploaded file

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"

    # Check content type
    if not file.content_type or not file.content_type.startswith('image/'):
        return False, "File must be an image"

    return True, None


async def save_uploaded_file(file: UploadFile, directory: str) -> tuple[str, str]:
    """
    Save uploaded file to disk

    Args:
        file: Uploaded file
        directory: Directory to save file (e.g., 'emirates_ids', 'passports')

    Returns:
        Tuple of (file_path, filename)
    """
    # Generate unique filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    file_ext = os.path.splitext(file.filename)[1].lower()
    filename = f"{timestamp}_{unique_id}{file_ext}"

    # Create directory if it doesn't exist
    upload_dir = os.path.join("uploads", directory)
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_dir, filename)

    try:
        contents = await file.read()

        # Check file size
        if len(contents) > MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB")

        with open(file_path, 'wb') as f:
            f.write(contents)

        return file_path, filename

    except Exception as e:
        # Clean up file if it was partially written
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e

    finally:
        # Reset file pointer
        await file.seek(0)


@router.post("/emirates-id", response_model=OCRResponse, status_code=status.HTTP_200_OK)
async def process_emirates_id(
    file: UploadFile = File(..., description="Emirates ID image file"),
    db: AsyncSession = Depends(get_db)
):
    """
    Process Emirates ID image and extract information

    This endpoint accepts an image file of an Emirates ID card, processes it using OCR,
    and returns the extracted information including:
    - Emirates ID number
    - Full name
    - Nationality
    - Date of birth
    - Gender
    - Expiry date

    Args:
        file: Image file of Emirates ID (JPG, PNG, HEIC)
        db: Database session

    Returns:
        OCRResponse with extracted data or error message

    Raises:
        HTTPException: If validation fails or processing error occurs
    """
    logger.info(f"Processing Emirates ID upload: {file.filename}")

    # Validate file
    is_valid, error_msg = validate_image_file(file)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    file_path = None

    try:
        # Save uploaded file
        file_path, filename = await save_uploaded_file(file, "emirates_ids")
        logger.info(f"Saved Emirates ID image: {file_path}")

        # Get OCR service
        ocr_service = get_ocr_service()

        # Process Emirates ID
        result = ocr_service.process_emirates_id(file_path)

        # Add image path to result
        result["image_path"] = file_path

        logger.info(f"OCR processing completed. Success: {result['success']}")

        if result["success"]:
            return OCRResponse(**result)
        else:
            # Return error but with partial data if available
            return JSONResponse(
                status_code=status.HTTP_200_OK,  # Still return 200 but with success=false
                content=result
            )

    except ValueError as ve:
        # File size or validation errors
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

    except RuntimeError as re:
        # Tesseract not installed error
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re)
        )

    except Exception as e:
        # Unexpected errors
        logger.error(f"Error processing Emirates ID: {str(e)}")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )


@router.post("/passport", response_model=OCRResponse, status_code=status.HTTP_200_OK)
async def process_passport(
    file: UploadFile = File(..., description="Passport image file"),
    db: AsyncSession = Depends(get_db)
):
    """
    Process Passport image and extract information

    This endpoint accepts an image file of a passport, processes it using OCR,
    and returns the extracted information.

    Note: This is a placeholder for future implementation.

    Args:
        file: Image file of passport (JPG, PNG, HEIC)
        db: Database session

    Returns:
        OCRResponse with extracted data or error message

    Raises:
        HTTPException: Not yet implemented
    """
    logger.info(f"Processing Passport upload: {file.filename}")

    # Validate file
    is_valid, error_msg = validate_image_file(file)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    file_path = None

    try:
        # Save uploaded file
        file_path, filename = await save_uploaded_file(file, "passports")
        logger.info(f"Saved passport image: {file_path}")

        # TODO: Implement passport OCR processing
        # For now, return placeholder response
        return OCRResponse(
            success=False,
            error="Passport OCR is not yet implemented",
            image_path=file_path
        )

    except ValueError as ve:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

    except Exception as e:
        logger.error(f"Error processing passport: {str(e)}")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )


@router.get("/test", status_code=status.HTTP_200_OK)
async def test_ocr_service():
    """
    Test OCR service availability

    Returns:
        Status of OCR service and Tesseract availability
    """
    try:
        ocr_service = get_ocr_service()

        # Check Tesseract availability
        from app.services.ocr_service import TESSERACT_AVAILABLE

        return {
            "status": "available" if TESSERACT_AVAILABLE else "unavailable",
            "tesseract_installed": TESSERACT_AVAILABLE,
            "message": "OCR service is ready" if TESSERACT_AVAILABLE else "Tesseract is not installed. Please install tesseract-ocr system package."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
