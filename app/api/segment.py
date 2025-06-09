from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import Response
from app.services.segment import Segment
from app.core.logger import logger
import json


segment_service = Segment()
router = APIRouter(tags=["segment"])


@router.post("/segment")
async def segment_image(image: UploadFile = File(...)):
    """
    Process an uploaded image using the Segment Anything Model (SAM)
    
    Args:
        image: The image file to process
        
    Returns:
        The processed image with segmentation visualization and detection results
    """
    try:
        # Read the image data
        image_data = await image.read()
        
        # Process the image
        logger.info(f"Processing image: {image.filename}")
        processed_image, results = segment_service.segment(image_data)
        logger.info(f"Segmentation completed. Found {results['total_objects']} objects")
        
        # Convert results to JSON string
        results_json = json.dumps(results)
        
        # Return the processed image and results
        return Response(
            content=processed_image,
            media_type=image.content_type,
            headers={
                "X-Segmentation-Results": results_json,
                "X-Processing-Time": str(results["processing_time"]),
                "X-Total-Objects": str(results["total_objects"]),
                "Access-Control-Expose-Headers": "X-Segmentation-Results, X-Processing-Time, X-Total-Objects"
            }
        )
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

