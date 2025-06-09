"""
Configuration Manager for Disaster Response System
Handles loading and managing YAML configuration files
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages system configuration from YAML files."""
    
    def __init__(self, config_path: str = "config/system.yaml"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to main configuration file
        """
        self.config_path = Path(config_path)
        self.config = {}
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.load_config()
    
    def load_config(self) -> bool:
        """
        Load configuration from YAML file.
        
        Returns:
            bool: True if configuration loaded successfully
        """
        try:
            if not self.config_path.exists():
                self.logger.error(f"Configuration file not found: {self.config_path}")
                self._create_default_config()
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            if not self.config:
                self.logger.error("Configuration file is empty or invalid")
                self._create_default_config()
                return False
            
            self.logger.info(f"Configuration loaded from: {self.config_path}")
            return True
            
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error: {e}")
            self._create_default_config()
            return False
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self._create_default_config()
            return False
    
    def _create_default_config(self):
        """Create default configuration if none exists."""
        self.config = {
            'camera': {
                'resolution': [1920, 1080],
                'capture_interval': 10,
                'hdr_enabled': False,
                'compression_quality': 85,
                'storage_path': '/tmp/disaster_images',
                'max_local_images': 50
            },
            'network': {
                'primary': 'wifi',
                'fallback': 'ethernet',
                'retry_attempts': 3,
                'timeout': 30
            },
            'gcp': {
                'project_id': 'disaster-response-project',
                'bucket_name': 'disaster-images',
                'api_endpoint': 'https://localhost:8000',
                'credentials_file': 'config/gcp-credentials.json'
            },
            'gps': {
                'enabled': False,
                'device': '/dev/ttyUSB1',
                'baudrate': 9600
            },
            'monitoring': {
                'enabled': True,
                'interval': 60,
                'temperature_limit': 70,
                'memory_limit': 80
            },
            'logging': {
                'level': 'INFO',
                'file': '/var/log/disaster-camera.log'
            }
        }
        
        self.logger.warning("Using default configuration")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            value = self.config
            for part in key.split('.'):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
            
        Returns:
            bool: True if value was set successfully
        """
        try:
            config = self.config
            parts = key.split('.')
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            
            config[parts[-1]] = value
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting config value {key}: {e}")
            return False
    
    def save_config(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            bool: True if configuration saved successfully
        """
        try:
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to: {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def reload_config(self) -> bool:
        """
        Reload configuration from file.
        
        Returns:
            bool: True if configuration reloaded successfully
        """
        return self.load_config()
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate current configuration.
        
        Returns:
            dict: Validation results with errors and warnings
        """
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validate camera configuration
            camera_config = self.config.get('camera', {})
            
            resolution = camera_config.get('resolution', [])
            if not isinstance(resolution, list) or len(resolution) != 2:
                validation['errors'].append("Camera resolution must be a list of two integers")
                validation['valid'] = False
            
            capture_interval = camera_config.get('capture_interval', 0)
            if not isinstance(capture_interval, (int, float)) or capture_interval <= 0:
                validation['errors'].append("Camera capture_interval must be a positive number")
                validation['valid'] = False
            
            # Validate network configuration
            network_config = self.config.get('network', {})
            
            primary = network_config.get('primary', '')
            valid_interfaces = ['4g', 'wifi', 'ethernet']
            if primary not in valid_interfaces:
                validation['warnings'].append(f"Primary network interface '{primary}' may not be supported")
            
            # Validate GCP configuration
            gcp_config = self.config.get('gcp', {})
            
            credentials_file = gcp_config.get('credentials_file', '')
            if credentials_file and not os.path.exists(credentials_file):
                validation['warnings'].append(f"GCP credentials file not found: {credentials_file}")
            
            project_id = gcp_config.get('project_id', '')
            if not project_id:
                validation['errors'].append("GCP project_id is required")
                validation['valid'] = False
            
            bucket_name = gcp_config.get('bucket_name', '')
            if not bucket_name:
                validation['errors'].append("GCP bucket_name is required")
                validation['valid'] = False
            
            # Validate GPS configuration
            gps_config = self.config.get('gps', {})
            
            if gps_config.get('enabled', False):
                device = gps_config.get('device', '')
                if device and not os.path.exists(device):
                    validation['warnings'].append(f"GPS device not found: {device}")
            
            # Validate monitoring configuration
            monitoring_config = self.config.get('monitoring', {})
            
            temp_limit = monitoring_config.get('temperature_limit', 0)
            if temp_limit and (temp_limit < 50 or temp_limit > 100):
                validation['warnings'].append("Temperature limit should be between 50-100°C")
            
        except Exception as e:
            validation['errors'].append(f"Configuration validation error: {e}")
            validation['valid'] = False
        
        return validation
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            dict: Configuration section or empty dict
        """
        return self.config.get(section, {})
    
    def merge_config(self, other_config: Dict[str, Any]) -> bool:
        """
        Merge another configuration into current one.
        
        Args:
            other_config: Configuration dictionary to merge
            
        Returns:
            bool: True if merge successful
        """
        try:
            def deep_merge(base: dict, update: dict):
                for key, value in update.items():
                    if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            
            deep_merge(self.config, other_config)
            self.logger.info("Configuration merged successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error merging configuration: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """
        Export configuration to a different file.
        
        Args:
            export_path: Path to export configuration to
            
        Returns:
            bool: True if export successful
        """
        try:
            export_path = Path(export_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration exported to: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to defaults.
        
        Returns:
            bool: True if reset successful
        """
        try:
            self._create_default_config()
            self.logger.info("Configuration reset to defaults")
            return True
        except Exception as e:
            self.logger.error(f"Error resetting configuration: {e}")
            return False 