from app.core.config import settings
import numpy as np
from PIL import Image
import io
import cv2
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
import time
from app.core.logger import logger

class Segment:
    def __init__(self):
        """Initialize the SAM model"""
        self.device = settings.DEVICE
        self.sam = sam_model_registry[settings.MODEL_TYPE](checkpoint=str(settings.MODEL_PATH))
        self.sam.to(device=self.device)
        self.mask_generator = SamAutomaticMaskGenerator(self.sam)
        logger.success("SAM model loaded successfully")

    def segment(self, image_data: bytes) -> tuple[bytes, dict]:
        """
        Process the image using SAM and return both the processed image and results
        
        Args:
            image_data: Raw bytes of the input image
            
        Returns:
            tuple: (processed_image_bytes, results_dict)
        """
        start_time = time.time()
        
        try:
            image_rgb = self.convert_to_image(image_data)
            masks = self.mask_generator.generate(image_rgb)
            output_image = self.annotate_image(image_rgb, masks)
            # save the output image
            cv2.imwrite("data/output.png", output_image)
            
            is_success, buffer = cv2.imencode(".png", output_image)
            if not is_success:
                raise Exception("Failed to encode output image")
            
            processed_image_bytes = buffer.tobytes()
            
            processing_time = time.time() - start_time
            results = {
                "detected_objects": [],
                "processing_time": round(processing_time, 2),
                "total_objects": len(masks)
            }
            
            return processed_image_bytes, results
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise Exception(f"Image processing error: {str(e)}")
    
    def convert_to_image(self, image_data: bytes) -> Image.Image:
        """
        Convert image bytes to RGB image

        Args:
            image_data: bytes of the image

        Returns:
            Image.Image: RGB image
        """
        image_pil = Image.open(io.BytesIO(image_data))
        image_np = np.array(image_pil)
        if len(image_np.shape) == 3 and image_np.shape[2] == 3:
            image = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        else:
            image = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        return image_rgb

    def annotate_image(self, image_rgb: np.ndarray, masks: list) -> np.ndarray:
        """
        Annotate the image with colored masks overlaid on the original image
        
        Args:
            image_rgb: RGB image as numpy array
            masks: List of masks from SAM
            
        Returns:
            np.ndarray: BGR image with colored mask overlays
        """
        if len(masks) == 0:
            # Convert RGB to BGR for cv2
            return cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        
        # Sort masks by area (largest first)
        sorted_masks = sorted(masks, key=(lambda x: x['area']), reverse=True)
        
        # Start with the original image (convert RGB to BGR for cv2)
        output_image = cv2.cvtColor(image_rgb.copy(), cv2.COLOR_RGB2BGR)
        
        # Create an overlay for all masks
        overlay = output_image.copy()
        
        # Draw each mask with a random color
        for mask_data in sorted_masks:
            mask = mask_data['segmentation']
            # Generate random color (BGR format for cv2)
            color = (
                int(np.random.randint(0, 256)),
                int(np.random.randint(0, 256)), 
                int(np.random.randint(0, 256))
            )
            
            # Apply color to the mask area
            overlay[mask] = color
        
        # Blend the overlay with the original image (30% opacity for masks)
        alpha = 0.7
        output_image = cv2.addWeighted(output_image, 1 - alpha, overlay, alpha, 0)
        
        return output_image

    