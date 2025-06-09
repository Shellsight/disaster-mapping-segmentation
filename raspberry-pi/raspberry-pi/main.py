#!/usr/bin/env python3
"""
Disaster Response Pi Camera System
Main application for capturing images and uploading to GCP
"""

import os
import sys
import time
import json
import logging
import signal
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import yaml
import click
from colorama import Fore, Style, init

# Local imports
from src.camera_manager import CameraManager
from src.network_manager import NetworkManager
from src.gcp_uploader import GCPUploader
from src.gps_tracker import GPSTracker
from src.system_monitor import SystemMonitor
from src.config_manager import ConfigManager
from src.logger_setup import setup_logging

# Initialize colorama for colored terminal output
init(autoreset=True)

class DisasterCameraSystem:
    """Main system controller for the disaster response camera system."""
    
    def __init__(self, config_path: str = "config/system.yaml"):
        """Initialize the disaster camera system."""
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        self.running = False
        self.threads = []
        
        # Initialize components
        self.logger = setup_logging(
            log_level=self.config.get('logging', {}).get('level', 'INFO'),
            log_file=self.config.get('logging', {}).get('file', '/var/log/disaster-camera.log')
        )
        
        self.camera_manager = None
        self.network_manager = None
        self.gcp_uploader = None
        self.gps_tracker = None
        self.system_monitor = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Disaster Camera System initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def initialize_components(self) -> bool:
        """Initialize all system components."""
        try:
            self.logger.info("Initializing system components...")
            
            # Initialize camera manager
            self.camera_manager = CameraManager(self.config['camera'])
            if not self.camera_manager.initialize():
                self.logger.error("Failed to initialize camera")
                return False
            
            # Initialize network manager
            self.network_manager = NetworkManager(self.config['network'])
            if not self.network_manager.initialize():
                self.logger.error("Failed to initialize network")
                return False
            
            # Initialize GCP uploader
            self.gcp_uploader = GCPUploader(self.config['gcp'])
            if not self.gcp_uploader.initialize():
                self.logger.error("Failed to initialize GCP uploader")
                return False
            
            # Initialize GPS tracker
            self.gps_tracker = GPSTracker(self.config.get('gps', {}))
            if not self.gps_tracker.initialize():
                self.logger.warning("GPS tracker initialization failed, continuing without GPS")
            
            # Initialize system monitor
            self.system_monitor = SystemMonitor(self.config.get('monitoring', {}))
            self.system_monitor.initialize()
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False
    
    def start(self):
        """Start the disaster camera system."""
        self.logger.info("Starting Disaster Camera System...")
        
        if not self.initialize_components():
            self.logger.error("Component initialization failed, aborting startup")
            return False
        
        self.running = True
        
        # Start background threads
        self._start_background_threads()
        
        # Main capture loop
        self._main_capture_loop()
        
        return True
    
    def stop(self):
        """Stop the disaster camera system."""
        self.logger.info("Stopping Disaster Camera System...")
        self.running = False
        
        # Wait for background threads to finish
        for thread in self.threads:
            thread.join(timeout=5.0)
        
        # Cleanup components
        if self.camera_manager:
            self.camera_manager.cleanup()
        if self.network_manager:
            self.network_manager.cleanup()
        if self.gcp_uploader:
            self.gcp_uploader.cleanup()
        if self.gps_tracker:
            self.gps_tracker.cleanup()
        if self.system_monitor:
            self.system_monitor.cleanup()
        
        self.logger.info("System stopped successfully")
    
    def _start_background_threads(self):
        """Start background monitoring and upload threads."""
        
        # System monitoring thread
        monitor_thread = threading.Thread(
            target=self._system_monitor_loop,
            name="SystemMonitor",
            daemon=True
        )
        monitor_thread.start()
        self.threads.append(monitor_thread)
        
        # Network monitoring thread
        network_thread = threading.Thread(
            target=self._network_monitor_loop,
            name="NetworkMonitor",
            daemon=True
        )
        network_thread.start()
        self.threads.append(network_thread)
        
        # Upload worker thread
        upload_thread = threading.Thread(
            target=self._upload_worker_loop,
            name="UploadWorker",
            daemon=True
        )
        upload_thread.start()
        self.threads.append(upload_thread)
        
        self.logger.info("Background threads started")
    
    def _main_capture_loop(self):
        """Main image capture loop."""
        capture_interval = self.config['camera'].get('capture_interval', 5)
        
        self.logger.info(f"Starting main capture loop (interval: {capture_interval}s)")
        
        while self.running:
            try:
                # Capture image
                image_path = self.camera_manager.capture_image()
                if image_path:
                    # Get GPS data if available
                    gps_data = None
                    if self.gps_tracker and self.gps_tracker.is_active():
                        gps_data = self.gps_tracker.get_current_location()
                    
                    # Add to upload queue
                    self.gcp_uploader.add_to_queue(image_path, gps_data)
                    
                    self.logger.info(f"Image captured and queued: {image_path}")
                else:
                    self.logger.warning("Failed to capture image")
                
                # Wait for next capture
                time.sleep(capture_interval)
                
            except Exception as e:
                self.logger.error(f"Error in capture loop: {e}")
                time.sleep(1)  # Brief pause before retrying
    
    def _system_monitor_loop(self):
        """Background system monitoring loop."""
        monitor_interval = self.config.get('monitoring', {}).get('interval', 30)
        
        while self.running:
            try:
                if self.system_monitor:
                    stats = self.system_monitor.get_system_stats()
                    
                    # Log critical conditions
                    if stats.get('temperature', 0) > 80:
                        self.logger.warning(f"High temperature: {stats['temperature']}°C")
                    
                    if stats.get('memory_percent', 0) > 90:
                        self.logger.warning(f"High memory usage: {stats['memory_percent']}%")
                    
                    if stats.get('disk_percent', 0) > 95:
                        self.logger.warning(f"Low disk space: {stats['disk_percent']}% used")
                
                time.sleep(monitor_interval)
                
            except Exception as e:
                self.logger.error(f"Error in system monitor loop: {e}")
                time.sleep(monitor_interval)
    
    def _network_monitor_loop(self):
        """Background network monitoring loop."""
        monitor_interval = self.config.get('network', {}).get('monitor_interval', 15)
        
        while self.running:
            try:
                if self.network_manager:
                    status = self.network_manager.check_connectivity()
                    
                    if not status['connected']:
                        self.logger.warning("Network connectivity lost, attempting reconnection...")
                        self.network_manager.reconnect()
                    
                    # Log signal strength if available
                    if status.get('signal_strength'):
                        self.logger.debug(f"Signal strength: {status['signal_strength']} dBm")
                
                time.sleep(monitor_interval)
                
            except Exception as e:
                self.logger.error(f"Error in network monitor loop: {e}")
                time.sleep(monitor_interval)
    
    def _upload_worker_loop(self):
        """Background upload worker loop."""
        while self.running:
            try:
                if self.gcp_uploader and self.network_manager:
                    # Check if we have network connectivity
                    if self.network_manager.is_connected():
                        # Process upload queue
                        self.gcp_uploader.process_queue()
                    else:
                        self.logger.debug("No network connectivity, skipping upload")
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                self.logger.error(f"Error in upload worker loop: {e}")
                time.sleep(5)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        status = {
            'running': self.running,
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        if self.camera_manager:
            status['components']['camera'] = self.camera_manager.get_status()
        
        if self.network_manager:
            status['components']['network'] = self.network_manager.get_status()
        
        if self.gcp_uploader:
            status['components']['uploader'] = self.gcp_uploader.get_status()
        
        if self.gps_tracker:
            status['components']['gps'] = self.gps_tracker.get_status()
        
        if self.system_monitor:
            status['components']['system'] = self.system_monitor.get_system_stats()
        
        return status


@click.command()
@click.option('--config', '-c', default='config/system.yaml', help='Configuration file path')
@click.option('--daemon', '-d', is_flag=True, help='Run as daemon')
@click.option('--test', '-t', is_flag=True, help='Run in test mode')
@click.option('--status', '-s', is_flag=True, help='Show system status')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def main(config, daemon, test, status, verbose):
    """Disaster Response Pi Camera System"""
    
    # Print banner
    print(f"{Fore.CYAN}{Style.BRIGHT}")
    print("╔════════════════════════════════════════════════╗")
    print("║         Disaster Response Camera System        ║")
    print("║              Raspberry Pi Module               ║")
    print("╚════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")
    
    if not os.path.exists(config):
        print(f"{Fore.RED}Error: Configuration file not found: {config}{Style.RESET_ALL}")
        sys.exit(1)
    
    try:
        system = DisasterCameraSystem(config)
        
        if status:
            # Show status and exit
            status_info = system.get_status()
            print(json.dumps(status_info, indent=2))
            return
        
        if test:
            # Run in test mode
            print(f"{Fore.YELLOW}Running in test mode...{Style.RESET_ALL}")
            system.initialize_components()
            
            # Test camera
            if system.camera_manager:
                print("Testing camera...")
                test_image = system.camera_manager.capture_image()
                if test_image:
                    print(f"{Fore.GREEN}✓ Camera test passed: {test_image}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}✗ Camera test failed{Style.RESET_ALL}")
            
            # Test network
            if system.network_manager:
                print("Testing network...")
                net_status = system.network_manager.check_connectivity()
                if net_status['connected']:
                    print(f"{Fore.GREEN}✓ Network test passed{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}✗ Network test failed{Style.RESET_ALL}")
            
            return
        
        if daemon:
            # Run as daemon (implement proper daemonization if needed)
            print(f"{Fore.GREEN}Starting in daemon mode...{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}Starting in foreground mode...{Style.RESET_ALL}")
        
        # Start the system
        system.start()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == '__main__':
    main() 