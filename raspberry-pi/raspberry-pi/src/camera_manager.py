"""
Camera Manager for Raspberry Pi Camera V3
Handles image capture, configuration, and basic processing
"""

import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from threading import Lock

try:
    from picamera2 import Picamera2
    from picamera2.encoders import JpegEncoder
    from picamera2.outputs import FileOutput
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    logging.warning("picamera2 not available, using mock camera")

from PIL import Image, ExifTags
import uuid


class CameraManager:
    """Manages Raspberry Pi Camera V3 operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize camera manager.
        
        Args:
            config: Camera configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.camera = None
        self.is_initialized = False
        self.capture_lock = Lock()
        
        # Configuration settings
        self.resolution = config.get('resolution', [4608, 2592])
        self.capture_interval = config.get('capture_interval', 5)
        self.hdr_enabled = config.get('hdr_enabled', True)
        self.compression_quality = config.get('compression_quality', 85)
        self.image_format = config.get('format', 'JPEG')
        
        # Storage settings
        self.storage_path = Path(config.get('storage_path', '/tmp/disaster_images'))
        self.max_images = config.get('max_local_images', 100)
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Camera manager initialized")
    
    def initialize(self) -> bool:
        """
        Initialize the camera hardware.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if not PICAMERA_AVAILABLE:
                self.logger.warning("Running in mock mode - picamera2 not available")
                self.is_initialized = True
                return True
            
            # Initialize Picamera2
            self.camera = Picamera2()
            
            # Configure camera
            camera_config = self.camera.create_still_configuration(
                main={"size": tuple(self.resolution)},
                lores={"size": (640, 480)},  # Lower resolution for preview
                display="lores"
            )
            
            self.camera.configure(camera_config)
            
            # Set camera controls
            self._apply_camera_settings()
            
            # Start camera
            self.camera.start()
            
            # Wait for camera to stabilize
            time.sleep(2)
            
            self.is_initialized = True
            self.logger.info("Camera initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def _apply_camera_settings(self):
        """Apply camera-specific settings and controls."""
        if not self.camera:
            return
        
        try:
            # Set auto-exposure and auto-white balance
            self.camera.set_controls({
                "AeEnable": True,
                "AwbEnable": True,
                "AwbMode": 0,  # Auto white balance
            })
            
            # Enable HDR if configured
            if self.hdr_enabled:
                self.camera.set_controls({
                    "ExposureTime": 10000,  # Microseconds
                    "AnalogueGain": 1.0,
                })
            
            self.logger.debug("Camera settings applied")
            
        except Exception as e:
            self.logger.warning(f"Failed to apply some camera settings: {e}")
    
    def capture_image(self, gps_data: Optional[Dict] = None) -> Optional[str]:
        """
        Capture a single image.
        
        Args:
            gps_data: Optional GPS data to embed in image metadata
        
        Returns:
            str: Path to captured image file, or None if capture failed
        """
        if not self.is_initialized:
            self.logger.error("Camera not initialized")
            return None
        
        with self.capture_lock:
            try:
                # Generate unique filename
                timestamp = datetime.now()
                filename = f"disaster_img_{timestamp.strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}.jpg"
                filepath = self.storage_path / filename
                
                if PICAMERA_AVAILABLE and self.camera:
                    # Capture with real camera
                    self.camera.capture_file(str(filepath))
                    self.logger.debug(f"Image captured: {filepath}")
                else:
                    # Mock capture for development/testing
                    self._create_mock_image(filepath, gps_data)
                    self.logger.debug(f"Mock image created: {filepath}")
                
                # Post-process image
                processed_path = self._process_image(filepath, gps_data)
                
                # Clean up old images if needed
                self._cleanup_old_images()
                
                return str(processed_path) if processed_path else str(filepath)
                
            except Exception as e:
                self.logger.error(f"Failed to capture image: {e}")
                return None
    
    def _create_mock_image(self, filepath: Path, gps_data: Optional[Dict] = None):
        """Create a mock image for testing when camera is not available."""
        # Create a simple test image
        width, height = self.resolution
        image = Image.new('RGB', (width, height), color='blue')
        
        # Add some basic content
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(image)
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        draw.text((50, 50), f"Mock Image - {timestamp}", fill='white')
        
        # Add GPS info if available
        if gps_data:
            gps_text = f"GPS: {gps_data.get('latitude', 'N/A')}, {gps_data.get('longitude', 'N/A')}"
            draw.text((50, 100), gps_text, fill='white')
        
        # Save image
        image.save(str(filepath), 'JPEG', quality=self.compression_quality)
    
    def _process_image(self, filepath: Path, gps_data: Optional[Dict] = None) -> Optional[Path]:
        """
        Post-process captured image.
        
        Args:
            filepath: Path to the captured image
            gps_data: Optional GPS data to embed
        
        Returns:
            Path to processed image, or None if processing failed
        """
        try:
            # Load image
            image = Image.open(filepath)
            
            # Apply basic processing
            if self.config.get('auto_enhance', True):
                image = self._enhance_image(image)
            
            # Compress if needed
            if self.compression_quality < 95:
                processed_path = filepath.with_suffix('.proc.jpg')
                image.save(
                    str(processed_path), 
                    'JPEG', 
                    quality=self.compression_quality,
                    optimize=True
                )
                
                # Remove original if processing successful
                filepath.unlink()
                return processed_path
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to process image {filepath}: {e}")
            return None
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Apply basic image enhancements."""
        try:
            from PIL import ImageEnhance
            
            # Slight contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
            
            # Slight sharpness enhancement
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.05)
            
            return image
            
        except Exception as e:
            self.logger.warning(f"Image enhancement failed: {e}")
            return image
    
    def _cleanup_old_images(self):
        """Remove old images if storage limit is exceeded."""
        try:
            image_files = sorted(
                self.storage_path.glob("*.jpg"),
                key=lambda p: p.stat().st_mtime
            )
            
            if len(image_files) > self.max_images:
                # Remove oldest images
                for old_file in image_files[:-self.max_images]:
                    old_file.unlink()
                    self.logger.debug(f"Removed old image: {old_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to cleanup old images: {e}")
    
    def capture_video(self, duration: int = 30) -> Optional[str]:
        """
        Capture video for specified duration.
        
        Args:
            duration: Video duration in seconds
        
        Returns:
            str: Path to video file, or None if capture failed
        """
        if not self.is_initialized or not PICAMERA_AVAILABLE:
            self.logger.error("Video capture not available")
            return None
        
        try:
            timestamp = datetime.now()
            filename = f"disaster_vid_{timestamp.strftime('%Y%m%d_%H%M%S')}.mp4"
            filepath = self.storage_path / filename
            
            # Configure for video recording
            video_config = self.camera.create_video_configuration()
            self.camera.configure(video_config)
            
            # Start recording
            encoder = self.camera.start_recording(str(filepath))
            time.sleep(duration)
            self.camera.stop_recording()
            
            self.logger.info(f"Video captured: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to capture video: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current camera status.
        
        Returns:
            dict: Camera status information
        """
        status = {
            'initialized': self.is_initialized,
            'mock_mode': not PICAMERA_AVAILABLE,
            'resolution': self.resolution,
            'hdr_enabled': self.hdr_enabled,
            'storage_path': str(self.storage_path),
            'image_count': len(list(self.storage_path.glob("*.jpg"))),
            'available_space_mb': self._get_available_space()
        }
        
        if self.camera and PICAMERA_AVAILABLE:
            try:
                # Get camera metadata
                status['camera_info'] = {
                    'model': 'Pi Camera V3',
                    'sensor_modes': len(self.camera.sensor_modes)
                }
            except Exception as e:
                self.logger.debug(f"Could not get camera info: {e}")
        
        return status
    
    def _get_available_space(self) -> float:
        """Get available storage space in MB."""
        try:
            stat = os.statvfs(self.storage_path)
            available_bytes = stat.f_bavail * stat.f_frsize
            return available_bytes / (1024 * 1024)  # Convert to MB
        except Exception:
            return 0.0
    
    def test_capture(self) -> bool:
        """
        Perform a test capture to verify camera functionality.
        
        Returns:
            bool: True if test successful, False otherwise
        """
        try:
            test_image = self.capture_image()
            if test_image and os.path.exists(test_image):
                # Verify image can be opened
                with Image.open(test_image) as img:
                    width, height = img.size
                    if width > 0 and height > 0:
                        self.logger.info(f"Test capture successful: {width}x{height}")
                        # Clean up test image
                        os.unlink(test_image)
                        return True
                
            self.logger.error("Test capture failed")
            return False
            
        except Exception as e:
            self.logger.error(f"Test capture error: {e}")
            return False
    
    def cleanup(self):
        """Clean up camera resources."""
        try:
            if self.camera and PICAMERA_AVAILABLE:
                self.camera.stop()
                self.camera.close()
                self.camera = None
            
            self.is_initialized = False
            self.logger.info("Camera cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during camera cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup() 