"""
GPS Tracker for Raspberry Pi
Handles GPS location tracking and metadata embedding
"""

import time
import logging
import serial
from typing import Dict, Any, Optional
from datetime import datetime
import threading
from threading import Lock

try:
    import pynmea2
    PYNMEA2_AVAILABLE = True
except ImportError:
    PYNMEA2_AVAILABLE = False
    logging.warning("pynmea2 not available, using mock GPS")


class GPSTracker:
    """Handles GPS tracking for location metadata."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize GPS tracker.
        
        Args:
            config: GPS configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.enabled = config.get('enabled', True)
        self.device = config.get('device', '/dev/ttyUSB1')
        self.baudrate = config.get('baudrate', 9600)
        self.timeout = config.get('timeout', 10)
        self.min_satellites = config.get('min_satellites', 4)
        self.accuracy_threshold = config.get('accuracy_threshold', 10)
        
        # State
        self.is_initialized = False
        self.is_active = False
        self.serial_conn = None
        self.gps_lock = Lock()
        self.reader_thread = None
        self.stop_reading = False
        
        # GPS data
        self.current_location = {
            'latitude': None,
            'longitude': None,
            'altitude': None,
            'speed': None,
            'heading': None,
            'accuracy': None,
            'satellites': 0,
            'timestamp': None,
            'fix_quality': 0
        }
        
        self.logger.info("GPS tracker initialized")
    
    def initialize(self) -> bool:
        """
        Initialize GPS hardware connection.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if not self.enabled:
            self.logger.info("GPS tracking disabled in configuration")
            return True
        
        try:
            if not PYNMEA2_AVAILABLE:
                self.logger.warning("Running in mock GPS mode - pynmea2 not available")
                self.is_initialized = True
                self.is_active = True
                self._start_mock_gps()
                return True
            
            # Try to open serial connection
            self.serial_conn = serial.Serial(
                port=self.device,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            if self.serial_conn.is_open:
                self.logger.info(f"GPS serial connection opened: {self.device}")
                
                # Start GPS reader thread
                self._start_gps_reader()
                
                self.is_initialized = True
                self.is_active = True
                return True
            else:
                self.logger.error("Failed to open GPS serial connection")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize GPS: {e}")
            # Fall back to mock GPS for development
            self.logger.info("Falling back to mock GPS mode")
            self.is_initialized = True
            self.is_active = True
            self._start_mock_gps()
            return True
    
    def _start_gps_reader(self):
        """Start the GPS data reader thread."""
        self.stop_reading = False
        self.reader_thread = threading.Thread(
            target=self._gps_reader_loop,
            name="GPSReader",
            daemon=True
        )
        self.reader_thread.start()
        self.logger.info("GPS reader thread started")
    
    def _gps_reader_loop(self):
        """Main GPS data reading loop."""
        while not self.stop_reading and self.serial_conn:
            try:
                # Read line from GPS
                line = self.serial_conn.readline().decode('ascii', errors='replace').strip()
                
                if line.startswith('$'):
                    # Parse NMEA sentence
                    self._parse_nmea_sentence(line)
                
            except Exception as e:
                self.logger.debug(f"GPS read error: {e}")
                time.sleep(1)
    
    def _parse_nmea_sentence(self, sentence: str):
        """
        Parse NMEA sentence and update location data.
        
        Args:
            sentence: NMEA sentence string
        """
        try:
            msg = pynmea2.parse(sentence)
            
            # Handle different NMEA message types
            if isinstance(msg, pynmea2.GGA):
                # Global Positioning System Fix Data
                self._update_location_from_gga(msg)
            elif isinstance(msg, pynmea2.RMC):
                # Recommended Minimum Course data
                self._update_location_from_rmc(msg)
            elif isinstance(msg, pynmea2.GSV):
                # Satellites in view
                self._update_satellites_from_gsv(msg)
                
        except Exception as e:
            self.logger.debug(f"NMEA parse error: {e}")
    
    def _update_location_from_gga(self, msg):
        """Update location from GGA message."""
        with self.gps_lock:
            if msg.latitude and msg.longitude:
                self.current_location.update({
                    'latitude': float(msg.latitude),
                    'longitude': float(msg.longitude),
                    'altitude': float(msg.altitude) if msg.altitude else None,
                    'satellites': int(msg.num_sats) if msg.num_sats else 0,
                    'fix_quality': int(msg.gps_qual) if msg.gps_qual else 0,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Calculate accuracy estimate based on HDOP
                if msg.horizontal_dil:
                    hdop = float(msg.horizontal_dil)
                    self.current_location['accuracy'] = hdop * 5  # Rough estimate
    
    def _update_location_from_rmc(self, msg):
        """Update location from RMC message."""
        with self.gps_lock:
            if msg.latitude and msg.longitude:
                self.current_location.update({
                    'latitude': float(msg.latitude),
                    'longitude': float(msg.longitude),
                    'speed': float(msg.spd_over_grnd) if msg.spd_over_grnd else None,
                    'heading': float(msg.true_course) if msg.true_course else None,
                    'timestamp': datetime.now().isoformat()
                })
    
    def _update_satellites_from_gsv(self, msg):
        """Update satellite count from GSV message."""
        with self.gps_lock:
            if msg.num_sv_in_view:
                self.current_location['satellites'] = int(msg.num_sv_in_view)
    
    def _start_mock_gps(self):
        """Start mock GPS for development/testing."""
        def mock_gps_loop():
            # Myanmar coordinates (Yangon area for testing)
            base_lat = 16.8661
            base_lon = 96.1951
            
            while not self.stop_reading:
                try:
                    # Simulate slight movement
                    import random
                    lat_offset = random.uniform(-0.001, 0.001)
                    lon_offset = random.uniform(-0.001, 0.001)
                    
                    with self.gps_lock:
                        self.current_location.update({
                            'latitude': base_lat + lat_offset,
                            'longitude': base_lon + lon_offset,
                            'altitude': 50.0 + random.uniform(-5, 5),
                            'speed': random.uniform(0, 10),
                            'heading': random.uniform(0, 360),
                            'accuracy': random.uniform(3, 8),
                            'satellites': random.randint(4, 12),
                            'fix_quality': 1,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    time.sleep(2)  # Update every 2 seconds
                    
                except Exception as e:
                    self.logger.debug(f"Mock GPS error: {e}")
                    time.sleep(1)
        
        self.reader_thread = threading.Thread(
            target=mock_gps_loop,
            name="MockGPS",
            daemon=True
        )
        self.reader_thread.start()
        self.logger.info("Mock GPS started")
    
    def get_current_location(self) -> Dict[str, Any]:
        """
        Get current GPS location.
        
        Returns:
            dict: Current location data
        """
        with self.gps_lock:
            # Check if we have a valid fix
            if (self.current_location['latitude'] is not None and 
                self.current_location['longitude'] is not None and
                self.current_location['satellites'] >= self.min_satellites):
                
                return self.current_location.copy()
            else:
                return {}
    
    def is_valid_fix(self) -> bool:
        """
        Check if current GPS fix is valid.
        
        Returns:
            bool: True if GPS fix is valid, False otherwise
        """
        with self.gps_lock:
            return (
                self.current_location['latitude'] is not None and
                self.current_location['longitude'] is not None and
                self.current_location['satellites'] >= self.min_satellites and
                self.current_location['fix_quality'] > 0
            )
    
    def wait_for_fix(self, timeout: int = 60) -> bool:
        """
        Wait for valid GPS fix.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if fix acquired, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_valid_fix():
                self.logger.info("GPS fix acquired")
                return True
            
            time.sleep(1)
        
        self.logger.warning(f"GPS fix timeout after {timeout} seconds")
        return False
    
    def is_active(self) -> bool:
        """Check if GPS tracker is active."""
        return self.is_active
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current GPS status.
        
        Returns:
            dict: GPS status information
        """
        status = {
            'initialized': self.is_initialized,
            'active': self.is_active,
            'enabled': self.enabled,
            'mock_mode': not PYNMEA2_AVAILABLE,
            'device': self.device,
            'valid_fix': self.is_valid_fix(),
            'satellites': self.current_location['satellites'],
            'fix_quality': self.current_location['fix_quality'],
            'last_update': self.current_location['timestamp']
        }
        
        if self.is_valid_fix():
            status.update({
                'latitude': self.current_location['latitude'],
                'longitude': self.current_location['longitude'],
                'altitude': self.current_location['altitude'],
                'accuracy': self.current_location['accuracy']
            })
        
        return status
    
    def get_location_string(self) -> str:
        """
        Get location as formatted string.
        
        Returns:
            str: Formatted location string
        """
        location = self.get_current_location()
        if location:
            lat = location.get('latitude', 0)
            lon = location.get('longitude', 0)
            return f"{lat:.6f}, {lon:.6f}"
        return "No GPS fix"
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula.
        
        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate
            
        Returns:
            float: Distance in meters
        """
        import math
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in meters
        r = 6371000
        
        return r * c
    
    def get_movement_info(self, previous_location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get movement information compared to previous location.
        
        Args:
            previous_location: Previous GPS location
            
        Returns:
            dict: Movement information
        """
        current = self.get_current_location()
        
        if not current or not previous_location:
            return {}
        
        # Calculate distance moved
        distance = self.calculate_distance(
            previous_location['latitude'], previous_location['longitude'],
            current['latitude'], current['longitude']
        )
        
        # Calculate time difference
        try:
            prev_time = datetime.fromisoformat(previous_location['timestamp'])
            curr_time = datetime.fromisoformat(current['timestamp'])
            time_diff = (curr_time - prev_time).total_seconds()
            
            # Calculate speed
            speed = distance / time_diff if time_diff > 0 else 0
            
            return {
                'distance_moved': distance,
                'time_elapsed': time_diff,
                'calculated_speed': speed,
                'gps_speed': current.get('speed', 0)
            }
            
        except Exception as e:
            self.logger.debug(f"Movement calculation error: {e}")
            return {'distance_moved': distance}
    
    def cleanup(self):
        """Clean up GPS resources."""
        try:
            self.stop_reading = True
            self.is_active = False
            
            # Wait for reader thread to finish
            if self.reader_thread and self.reader_thread.is_alive():
                self.reader_thread.join(timeout=5)
            
            # Close serial connection
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                self.serial_conn = None
            
            self.is_initialized = False
            self.logger.info("GPS tracker cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during GPS cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup() 