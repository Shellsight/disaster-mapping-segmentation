"""
Network Manager for Raspberry Pi
Handles 4G/LTE and WiFi connectivity with automatic failover
"""

import os
import time
import logging
import subprocess
import json
import netifaces
from typing import Dict, Any, Optional, List
import requests
from threading import Lock


class NetworkManager:
    """Manages network connectivity for the disaster response system."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize network manager.
        
        Args:
            config: Network configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.primary_interface = config.get('primary', '4g')
        self.fallback_interface = config.get('fallback', 'wifi')
        self.retry_attempts = config.get('retry_attempts', 3)
        self.timeout = config.get('timeout', 30)
        self.monitor_interval = config.get('monitor_interval', 15)
        self.auto_reconnect = config.get('auto_reconnect', True)
        
        # State
        self.is_initialized = False
        self.current_interface = None
        self.connection_lock = Lock()
        self.last_test_time = 0
        self.connectivity_status = {
            'connected': False,
            'interface': None,
            'ip_address': None,
            'signal_strength': None,
            'data_usage': 0
        }
        
        self.logger.info("Network manager initialized")
    
    def initialize(self) -> bool:
        """
        Initialize network interfaces and check connectivity.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing network interfaces...")
            
            # Check available interfaces
            available_interfaces = self._get_available_interfaces()
            self.logger.info(f"Available network interfaces: {available_interfaces}")
            
            # Try to establish connection
            if self._establish_connection():
                self.is_initialized = True
                self.logger.info("Network manager initialized successfully")
                return True
            else:
                self.logger.error("Failed to establish network connection")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize network manager: {e}")
            return False
    
    def _get_available_interfaces(self) -> List[str]:
        """Get list of available network interfaces."""
        try:
            interfaces = netifaces.interfaces()
            # Filter out loopback and virtual interfaces
            real_interfaces = []
            for iface in interfaces:
                if not iface.startswith(('lo', 'docker', 'br-', 'veth')):
                    real_interfaces.append(iface)
            return real_interfaces
        except Exception as e:
            self.logger.error(f"Error getting network interfaces: {e}")
            return []
    
    def _establish_connection(self) -> bool:
        """Establish network connection using primary or fallback interface."""
        with self.connection_lock:
            # Try primary interface first
            if self._connect_interface(self.primary_interface):
                self.current_interface = self.primary_interface
                return True
            
            # Fall back to secondary interface
            self.logger.warning(f"Primary interface ({self.primary_interface}) failed, trying fallback")
            if self._connect_interface(self.fallback_interface):
                self.current_interface = self.fallback_interface
                return True
            
            self.logger.error("All network interfaces failed")
            return False
    
    def _connect_interface(self, interface_type: str) -> bool:
        """
        Connect to specific interface type.
        
        Args:
            interface_type: Type of interface ('4g', 'wifi', 'ethernet')
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if interface_type == '4g':
                return self._connect_4g()
            elif interface_type == 'wifi':
                return self._connect_wifi()
            elif interface_type == 'ethernet':
                return self._connect_ethernet()
            else:
                self.logger.error(f"Unknown interface type: {interface_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to {interface_type}: {e}")
            return False
    
    def _connect_4g(self) -> bool:
        """Connect to 4G/LTE network."""
        try:
            self.logger.info("Attempting 4G/LTE connection...")
            
            # Check if USB modem is present
            usb_devices = subprocess.run(['lsusb'], capture_output=True, text=True)
            if 'Qualcomm' not in usb_devices.stdout and 'Huawei' not in usb_devices.stdout:
                self.logger.warning("No 4G modem detected")
                return False
            
            # Use NetworkManager to connect (if available)
            try:
                result = subprocess.run([
                    'nmcli', 'connection', 'up', 'type', 'gsm'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    self.logger.info("4G connection established via NetworkManager")
                    return self._test_connectivity()
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.logger.debug("NetworkManager not available, trying wvdial")
            
            # Fallback to wvdial
            try:
                result = subprocess.run([
                    'wvdial'
                ], capture_output=True, text=True, timeout=30)
                
                if "connected" in result.stdout.lower():
                    self.logger.info("4G connection established via wvdial")
                    return self._test_connectivity()
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.logger.warning("wvdial not available")
            
            return False
            
        except Exception as e:
            self.logger.error(f"4G connection failed: {e}")
            return False
    
    def _connect_wifi(self) -> bool:
        """Connect to WiFi network."""
        try:
            self.logger.info("Attempting WiFi connection...")
            
            # Check if WiFi interface is available
            wifi_interfaces = [iface for iface in netifaces.interfaces() if iface.startswith('wlan')]
            if not wifi_interfaces:
                self.logger.warning("No WiFi interface found")
                return False
            
            wifi_interface = wifi_interfaces[0]
            
            # Use NetworkManager if available
            try:
                # Scan for networks
                subprocess.run(['nmcli', 'device', 'wifi', 'rescan'], 
                             capture_output=True, timeout=10)
                
                # Connect to configured network
                result = subprocess.run([
                    'nmcli', 'device', 'wifi', 'connect', 
                    self.config.get('wifi_ssid', 'backup-network'),
                    'password', self.config.get('wifi_password', '')
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    self.logger.info("WiFi connection established")
                    return self._test_connectivity()
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.logger.debug("NetworkManager WiFi connection failed")
            
            # Fallback to wpa_supplicant
            try:
                # This is a simplified approach - in practice you'd need proper wpa_supplicant config
                self.logger.debug("Attempting manual WiFi connection")
                subprocess.run(['ifconfig', wifi_interface, 'up'], timeout=10)
                time.sleep(2)
                return self._test_connectivity()
                
            except subprocess.TimeoutExpired:
                self.logger.warning("Manual WiFi connection timeout")
            
            return False
            
        except Exception as e:
            self.logger.error(f"WiFi connection failed: {e}")
            return False
    
    def _connect_ethernet(self) -> bool:
        """Connect to Ethernet network."""
        try:
            self.logger.info("Checking Ethernet connection...")
            
            # Check if Ethernet interface is available and has carrier
            eth_interfaces = [iface for iface in netifaces.interfaces() if iface.startswith('eth')]
            if not eth_interfaces:
                self.logger.warning("No Ethernet interface found")
                return False
            
            eth_interface = eth_interfaces[0]
            
            # Check carrier status
            carrier_file = f"/sys/class/net/{eth_interface}/carrier"
            if os.path.exists(carrier_file):
                with open(carrier_file, 'r') as f:
                    carrier = f.read().strip()
                    if carrier != '1':
                        self.logger.warning("Ethernet cable not connected")
                        return False
            
            # Bring interface up
            subprocess.run(['ifconfig', eth_interface, 'up'], timeout=10)
            
            # Try DHCP
            result = subprocess.run(['dhclient', eth_interface], 
                                  capture_output=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info("Ethernet connection established")
                return self._test_connectivity()
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ethernet connection failed: {e}")
            return False
    
    def _test_connectivity(self) -> bool:
        """Test internet connectivity."""
        try:
            # Test multiple endpoints for reliability
            test_urls = [
                'http://httpbin.org/status/200',
                'http://google.com',
                'http://cloudflare.com'
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        self.logger.debug(f"Connectivity test passed: {url}")
                        self._update_connectivity_status(True)
                        return True
                except requests.RequestException:
                    continue
            
            self.logger.warning("All connectivity tests failed")
            self._update_connectivity_status(False)
            return False
            
        except Exception as e:
            self.logger.error(f"Connectivity test error: {e}")
            self._update_connectivity_status(False)
            return False
    
    def _update_connectivity_status(self, connected: bool):
        """Update the connectivity status information."""
        self.connectivity_status['connected'] = connected
        self.connectivity_status['interface'] = self.current_interface
        
        if connected:
            # Get IP address
            self.connectivity_status['ip_address'] = self._get_current_ip()
            
            # Get signal strength if on cellular
            if self.current_interface == '4g':
                self.connectivity_status['signal_strength'] = self._get_signal_strength()
        
        self.last_test_time = time.time()
    
    def _get_current_ip(self) -> Optional[str]:
        """Get current public IP address."""
        try:
            response = requests.get('http://httpbin.org/ip', timeout=10)
            if response.status_code == 200:
                ip_info = response.json()
                return ip_info.get('origin')
        except Exception:
            pass
        return None
    
    def _get_signal_strength(self) -> Optional[int]:
        """Get cellular signal strength in dBm."""
        try:
            # This would need to be implemented based on the specific modem
            # For now, return a mock value
            return -65  # Mock signal strength
        except Exception:
            return None
    
    def check_connectivity(self) -> Dict[str, Any]:
        """
        Check current connectivity status.
        
        Returns:
            dict: Connectivity status information
        """
        # Only test if enough time has passed since last test
        if time.time() - self.last_test_time > 30:
            self._test_connectivity()
        
        return self.connectivity_status.copy()
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to network."""
        self.logger.info("Attempting network reconnection...")
        return self._establish_connection()
    
    def is_connected(self) -> bool:
        """Check if currently connected to network."""
        status = self.check_connectivity()
        return status.get('connected', False)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current network manager status.
        
        Returns:
            dict: Network status information
        """
        status = {
            'initialized': self.is_initialized,
            'current_interface': self.current_interface,
            'primary_interface': self.primary_interface,
            'fallback_interface': self.fallback_interface,
            'connectivity': self.connectivity_status.copy(),
            'last_test': self.last_test_time,
            'auto_reconnect': self.auto_reconnect
        }
        
        return status
    
    def switch_interface(self, interface_type: str) -> bool:
        """
        Manually switch to a different network interface.
        
        Args:
            interface_type: Type of interface to switch to
            
        Returns:
            bool: True if switch successful, False otherwise
        """
        self.logger.info(f"Switching to interface: {interface_type}")
        
        # Disconnect current interface if needed
        if self.current_interface:
            self._disconnect_interface(self.current_interface)
        
        # Connect to new interface
        if self._connect_interface(interface_type):
            self.current_interface = interface_type
            return True
        
        return False
    
    def _disconnect_interface(self, interface_type: str):
        """Disconnect from specific interface type."""
        try:
            if interface_type == '4g':
                subprocess.run(['pkill', 'wvdial'], capture_output=True)
            elif interface_type == 'wifi':
                subprocess.run(['nmcli', 'device', 'disconnect', 'type', 'wifi'], 
                             capture_output=True)
        except Exception as e:
            self.logger.debug(f"Error disconnecting {interface_type}: {e}")
    
    def get_data_usage(self) -> Dict[str, int]:
        """Get data usage statistics (if available)."""
        try:
            # This would need to be implemented based on system capabilities
            # For now, return mock data
            return {
                'bytes_sent': 1024000,
                'bytes_received': 5120000,
                'total_usage': 6144000
            }
        except Exception:
            return {'bytes_sent': 0, 'bytes_received': 0, 'total_usage': 0}
    
    def cleanup(self):
        """Clean up network manager resources."""
        try:
            if self.current_interface:
                self._disconnect_interface(self.current_interface)
            
            self.is_initialized = False
            self.logger.info("Network manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during network cleanup: {e}") 