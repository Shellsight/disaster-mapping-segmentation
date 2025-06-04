from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response
from app.services.segment import Segment


segment_service = Segment()
router = APIRouter(prefix="/segment", tags=["segment"])


@router.post("/")
async def segment_image(image: UploadFile = File(...)):
    """
    Process an uploaded image and return the segmented image along with results
    
    Args:
        image: The image file to process
        
    Returns:
        The processed image and detection results
    """
    # Read the image data
    image_data = await image.read()
    
    # Process the image
    processed_image, results = segment_service.segment(image_data)
    
    # Return the processed image and results
    return Response(
        content=processed_image,
        media_type=image.content_type or "image/png",
        headers={
            "X-Segmentation-Results": str(results)
        }
    )

