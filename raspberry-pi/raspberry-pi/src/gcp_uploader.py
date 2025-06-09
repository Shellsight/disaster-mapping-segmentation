"""
GCP Uploader for Disaster Response System
Handles uploading images to Google Cloud Storage and API communication
"""

import os
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from queue import Queue, Empty
import time
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    from google.cloud import storage
    from google.oauth2 import service_account
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    logging.warning("Google Cloud libraries not available")


class GCPUploader:
    """Handles uploading images to Google Cloud Platform and API communication."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize GCP uploader.
        
        Args:
            config: GCP configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.project_id = config.get('project_id')
        self.bucket_name = config.get('bucket_name')
        self.api_endpoint = config.get('api_endpoint')
        self.credentials_file = config.get('credentials_file')
        self.upload_timeout = config.get('upload_timeout', 60)
        self.retry_attempts = config.get('retry_attempts', 3)
        self.chunk_size = config.get('chunk_size', 1048576)  # 1MB
        
        # State
        self.storage_client = None
        self.bucket = None
        self.is_initialized = False
        self.upload_queue = Queue()
        self.failed_uploads = []
        self.upload_stats = {
            'total_uploads': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'bytes_uploaded': 0
        }
        
        # Threading
        self.upload_executor = ThreadPoolExecutor(max_workers=2)
        self.upload_lock = threading.Lock()
        
        self.logger.info("GCP uploader initialized")
    
    def initialize(self) -> bool:
        """
        Initialize GCP client and authenticate.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if not GCP_AVAILABLE:
                self.logger.warning("Running in mock mode - GCP libraries not available")
                self.is_initialized = True
                return True
            
            # Check credentials file exists
            if not os.path.exists(self.credentials_file):
                self.logger.error(f"GCP credentials file not found: {self.credentials_file}")
                return False
            
            # Initialize storage client
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file
            )
            
            self.storage_client = storage.Client(
                project=self.project_id,
                credentials=credentials
            )
            
            # Get bucket reference
            self.bucket = self.storage_client.bucket(self.bucket_name)
            
            # Test connectivity
            if self._test_connectivity():
                self.is_initialized = True
                self.logger.info("GCP uploader initialized successfully")
                return True
            else:
                self.logger.error("GCP connectivity test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize GCP uploader: {e}")
            return False
    
    def _test_connectivity(self) -> bool:
        """Test GCP connectivity by checking bucket access."""
        try:
            if not GCP_AVAILABLE:
                return True  # Mock mode
            
            # Try to list a few objects to test connectivity
            blobs = list(self.bucket.list_blobs(max_results=1))
            self.logger.debug("GCP connectivity test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"GCP connectivity test failed: {e}")
            return False
    
    def add_to_queue(self, image_path: str, gps_data: Optional[Dict] = None, metadata: Optional[Dict] = None):
        """
        Add image to upload queue.
        
        Args:
            image_path: Path to image file
            gps_data: Optional GPS data
            metadata: Optional additional metadata
        """
        upload_item = {
            'image_path': image_path,
            'gps_data': gps_data or {},
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat(),
            'retry_count': 0
        }
        
        self.upload_queue.put(upload_item)
        self.logger.debug(f"Added to upload queue: {image_path}")
    
    def process_queue(self):
        """Process items in the upload queue."""
        try:
            # Process one item per call to avoid blocking
            upload_item = self.upload_queue.get_nowait()
            
            # Submit to thread pool for async processing
            future = self.upload_executor.submit(self._upload_item, upload_item)
            
        except Empty:
            # No items in queue
            pass
        except Exception as e:
            self.logger.error(f"Error processing upload queue: {e}")
    
    def _upload_item(self, upload_item: Dict[str, Any]) -> bool:
        """
        Upload a single item.
        
        Args:
            upload_item: Upload item dictionary
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        image_path = upload_item['image_path']
        
        try:
            # Check if file still exists
            if not os.path.exists(image_path):
                self.logger.warning(f"Image file not found, skipping: {image_path}")
                return False
            
            # Upload to GCS
            gcs_url = self._upload_to_gcs(image_path, upload_item)
            
            if gcs_url:
                # Send to API
                api_success = self._send_to_api(image_path, gcs_url, upload_item)
                
                if api_success:
                    self._update_stats(True, os.path.getsize(image_path))
                    
                    # Clean up local file if configured
                    if self.config.get('cleanup_after_upload', True):
                        os.unlink(image_path)
                        self.logger.debug(f"Cleaned up local file: {image_path}")
                    
                    self.logger.info(f"Successfully uploaded: {image_path}")
                    return True
                else:
                    self.logger.error(f"API submission failed for: {image_path}")
            else:
                self.logger.error(f"GCS upload failed for: {image_path}")
            
            # Handle failure
            self._handle_upload_failure(upload_item)
            return False
            
        except Exception as e:
            self.logger.error(f"Error uploading {image_path}: {e}")
            self._handle_upload_failure(upload_item)
            return False
    
    def _upload_to_gcs(self, image_path: str, upload_item: Dict[str, Any]) -> Optional[str]:
        """
        Upload image to Google Cloud Storage.
        
        Args:
            image_path: Path to image file
            upload_item: Upload item metadata
            
        Returns:
            str: GCS URL if successful, None otherwise
        """
        try:
            if not GCP_AVAILABLE:
                # Mock upload for development
                mock_url = f"gs://{self.bucket_name}/mock/{os.path.basename(image_path)}"
                self.logger.debug(f"Mock GCS upload: {mock_url}")
                return mock_url
            
            # Generate blob name with timestamp and metadata
            timestamp = datetime.now().strftime('%Y/%m/%d/%H')
            filename = os.path.basename(image_path)
            blob_name = f"disaster-images/{timestamp}/{filename}"
            
            # Create blob
            blob = self.bucket.blob(blob_name)
            
            # Set metadata
            metadata = {
                'device_id': self.config.get('device_id', 'unknown'),
                'mission_id': upload_item.get('metadata', {}).get('mission_id', ''),
                'capture_time': upload_item['timestamp'],
                'content_type': 'image/jpeg'
            }
            
            # Add GPS metadata if available
            gps_data = upload_item.get('gps_data', {})
            if gps_data:
                metadata.update({
                    'gps_latitude': str(gps_data.get('latitude', '')),
                    'gps_longitude': str(gps_data.get('longitude', '')),
                    'gps_altitude': str(gps_data.get('altitude', '')),
                    'gps_accuracy': str(gps_data.get('accuracy', ''))
                })
            
            blob.metadata = metadata
            
            # Upload file
            with open(image_path, 'rb') as file_obj:
                blob.upload_from_file(
                    file_obj,
                    content_type='image/jpeg',
                    timeout=self.upload_timeout
                )
            
            # Make blob publicly readable (optional)
            # blob.make_public()
            
            gcs_url = f"gs://{self.bucket_name}/{blob_name}"
            self.logger.debug(f"Uploaded to GCS: {gcs_url}")
            return gcs_url
            
        except Exception as e:
            self.logger.error(f"GCS upload failed for {image_path}: {e}")
            return None
    
    def _send_to_api(self, image_path: str, gcs_url: str, upload_item: Dict[str, Any]) -> bool:
        """
        Send image metadata to disaster response API.
        
        Args:
            image_path: Local image path
            gcs_url: GCS URL of uploaded image
            upload_item: Upload item metadata
            
        Returns:
            bool: True if API call successful, False otherwise
        """
        try:
            # Prepare API payload
            payload = {
                'device_id': self.config.get('device_id', 'pi-001'),
                'image_url': gcs_url,
                'local_path': image_path,
                'timestamp': upload_item['timestamp'],
                'mission_id': upload_item.get('metadata', {}).get('mission_id', ''),
                'file_size': os.path.getsize(image_path)
            }
            
            # Add GPS data if available
            gps_data = upload_item.get('gps_data', {})
            if gps_data:
                payload.update({
                    'latitude': gps_data.get('latitude'),
                    'longitude': gps_data.get('longitude'),
                    'altitude': gps_data.get('altitude'),
                    'gps_accuracy': gps_data.get('accuracy')
                })
            
            # Make API request
            response = requests.post(
                f"{self.api_endpoint}/api/upload-image",
                json=payload,
                timeout=30,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'DisasterPi/1.0'
                }
            )
            
            if response.status_code == 200:
                self.logger.debug(f"API submission successful for: {image_path}")
                return True
            else:
                self.logger.error(f"API submission failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"API submission error for {image_path}: {e}")
            return False
    
    def _handle_upload_failure(self, upload_item: Dict[str, Any]):
        """Handle failed upload by retrying or moving to failed queue."""
        upload_item['retry_count'] += 1
        
        if upload_item['retry_count'] < self.retry_attempts:
            # Retry the upload
            self.logger.info(f"Retrying upload (attempt {upload_item['retry_count']}/{self.retry_attempts})")
            self.upload_queue.put(upload_item)
        else:
            # Move to failed uploads
            self.failed_uploads.append(upload_item)
            self._update_stats(False, 0)
            self.logger.warning(f"Upload failed permanently: {upload_item['image_path']}")
    
    def _update_stats(self, success: bool, bytes_uploaded: int):
        """Update upload statistics."""
        with self.upload_lock:
            self.upload_stats['total_uploads'] += 1
            if success:
                self.upload_stats['successful_uploads'] += 1
                self.upload_stats['bytes_uploaded'] += bytes_uploaded
            else:
                self.upload_stats['failed_uploads'] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current uploader status.
        
        Returns:
            dict: Uploader status information
        """
        status = {
            'initialized': self.is_initialized,
            'mock_mode': not GCP_AVAILABLE,
            'queue_size': self.upload_queue.qsize(),
            'failed_uploads': len(self.failed_uploads),
            'stats': self.upload_stats.copy(),
            'bucket_name': self.bucket_name,
            'api_endpoint': self.api_endpoint
        }
        
        return status
    
    def retry_failed_uploads(self):
        """Retry all failed uploads."""
        if not self.failed_uploads:
            return
        
        self.logger.info(f"Retrying {len(self.failed_uploads)} failed uploads")
        
        # Reset retry count and re-queue
        for upload_item in self.failed_uploads:
            upload_item['retry_count'] = 0
            self.upload_queue.put(upload_item)
        
        # Clear failed uploads list
        self.failed_uploads.clear()
    
    def cleanup(self):
        """Clean up uploader resources."""
        try:
            # Shutdown thread pool
            self.upload_executor.shutdown(wait=True)
            
            # Process remaining queue items (optional)
            remaining_items = []
            while not self.upload_queue.empty():
                try:
                    item = self.upload_queue.get_nowait()
                    remaining_items.append(item)
                except Empty:
                    break
            
            if remaining_items:
                self.logger.info(f"Saving {len(remaining_items)} unprocessed uploads")
                # Could save to file for later processing
            
            self.is_initialized = False
            self.logger.info("GCP uploader cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during uploader cleanup: {e}")
    
    def get_upload_progress(self) -> Dict[str, Any]:
        """Get current upload progress information."""
        total_queue = self.upload_queue.qsize()
        
        return {
            'queue_size': total_queue,
            'processing': total_queue > 0,
            'failed_count': len(self.failed_uploads),
            'success_rate': (
                self.upload_stats['successful_uploads'] / max(1, self.upload_stats['total_uploads'])
            ) * 100,
            'total_bytes_uploaded': self.upload_stats['bytes_uploaded'],
            'average_file_size': (
                self.upload_stats['bytes_uploaded'] / max(1, self.upload_stats['successful_uploads'])
            )
        } 