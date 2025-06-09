# app/api/segment.py
import json
from typing import Dict, Any
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import Response
from app.services.segment import Segment
from app.core.logger import logger

# Initialize the segment service
segment_service = Segment()

# Create router with tags
router = APIRouter(tags=["segment"])

# Allowed image types
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp", "image/tiff"
}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_image_file(file: UploadFile) -> None:
    """
    Validate the uploaded image file.
    
    Args:
        file: The uploaded file to validate
        
    Raises:
        HTTPException: If file validation fails
    """
    if not file.content_type or file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )


@router.post("/segment")
async def segment_image(image: UploadFile = File(...)) -> Response:
    """
    Process an uploaded image using the Segment Anything Model (SAM).
    
    This endpoint accepts an image file and returns the processed image with
    segmentation visualization overlaid, along with detection results in the response headers.
    
    Args:
        image: The image file to process (JPEG, PNG, WebP, BMP, or TIFF)
        
    Returns:
        Response: The processed image with segmentation visualization
        
    Headers:
        - X-Segmentation-Results: JSON string containing segmentation results
        - X-Processing-Time: Processing time in seconds
        - X-Total-Objects: Number of detected objects
        
    Raises:
        HTTPException: If image processing fails or invalid file provided
    """
    try:
        # Validate the uploaded file
        validate_image_file(image)
        
        # Read the image data
        image_data = await image.read()
        
        # Check file size
        if len(image_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file provided"
            )
        
        # Process the image
        logger.info(f"Processing image: {image.filename} ({len(image_data)} bytes)")
        
        try:
            processed_image, results = segment_service.segment(image_data)
        except Exception as segment_error:
            logger.error(f"Segmentation service error: {str(segment_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process image with segmentation service"
            )
        
        # Validate results
        if not isinstance(results, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid response from segmentation service"
            )
        
        # Ensure required fields exist in results
        total_objects = results.get("total_objects", 0)
        processing_time = results.get("processing_time", 0.0)
        
        logger.info(f"Segmentation completed for {image.filename}. "
                   f"Found {total_objects} objects in {processing_time:.2f}s")
        
        # Convert results to JSON string
        try:
            results_json = json.dumps(results, ensure_ascii=False)
        except (TypeError, ValueError) as json_error:
            logger.error(f"Failed to serialize results: {str(json_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to serialize segmentation results"
            )
        
        # Return the processed image with results in headers
        return Response(
            content=processed_image,
            media_type=image.content_type,
            headers={
                "X-Segmentation-Results": results_json,
                "X-Processing-Time": str(processing_time),
                "X-Total-Objects": str(total_objects),
                "Access-Control-Expose-Headers": (
                    "X-Segmentation-Results, X-Processing-Time, X-Total-Objects"
                ),
                "Content-Disposition": f"inline; filename=processed_{image.filename}"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors and return generic error message
        logger.error(f"Unexpected error processing image {image.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the image"
        )


@router.get("/segment/health")
async def segment_health_check() -> Dict[str, Any]:
    """
    Check the health of the segmentation service.
    
    Returns:
        Dict containing the service status and capabilities
    """
    try:
        # You might want to add a health check method to your Segment service
        return {
            "status": "healthy",
            "service": "segment",
            "supported_formats": list(ALLOWED_CONTENT_TYPES),
            "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024)
        }
    except Exception as e:
        logger.error(f"Segment service health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Segmentation service is unavailable"
        )