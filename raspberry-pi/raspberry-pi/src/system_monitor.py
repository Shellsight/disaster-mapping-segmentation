"""
System Monitor for Raspberry Pi
Tracks hardware health and performance metrics
"""

import os
import time
import logging
import psutil
from typing import Dict, Any
from datetime import datetime


class SystemMonitor:
    """Monitors system health and performance metrics."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize system monitor.
        
        Args:
            config: System monitoring configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.enabled = config.get('enabled', True)
        self.interval = config.get('interval', 30)
        self.temperature_limit = config.get('temperature_limit', 80)
        self.memory_limit = config.get('memory_limit', 90)
        self.disk_limit = config.get('disk_limit', 95)
        self.cpu_limit = config.get('cpu_limit', 85)
        
        # State
        self.is_initialized = False
        self.last_stats = {}
        
        self.logger.info("System monitor initialized")
    
    def initialize(self) -> bool:
        """
        Initialize system monitoring.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            if not self.enabled:
                self.logger.info("System monitoring disabled")
                return True
            
            # Test if we can get basic system stats
            test_stats = self.get_system_stats()
            if test_stats:
                self.is_initialized = True
                self.logger.info("System monitor initialized successfully")
                return True
            else:
                self.logger.error("Failed to get system stats")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize system monitor: {e}")
            return False
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get current system statistics.
        
        Returns:
            dict: System statistics
        """
        try:
            stats = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'temperature': self._get_cpu_temperature(),
                'uptime': self._get_uptime(),
                'load_average': self._get_load_average(),
                'network_stats': self._get_network_stats(),
                'processes': self._get_top_processes()
            }
            
            # Add Raspberry Pi specific stats
            pi_stats = self._get_pi_specific_stats()
            stats.update(pi_stats)
            
            self.last_stats = stats
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting system stats: {e}")
            return self.last_stats
    
    def _get_cpu_temperature(self) -> float:
        """Get CPU temperature in Celsius."""
        try:
            # Try Raspberry Pi specific method first
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0
                return temp
        except Exception:
            try:
                # Fallback to psutil sensors (if available)
                temps = psutil.sensors_temperatures()
                if 'cpu_thermal' in temps:
                    return temps['cpu_thermal'][0].current
                elif temps:
                    # Use first available temperature sensor
                    first_sensor = next(iter(temps.values()))
                    if first_sensor:
                        return first_sensor[0].current
            except Exception:
                pass
        
        return 0.0
    
    def _get_uptime(self) -> float:
        """Get system uptime in seconds."""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
                return uptime_seconds
        except Exception:
            return 0.0
    
    def _get_load_average(self) -> Dict[str, float]:
        """Get system load average."""
        try:
            load1, load5, load15 = os.getloadavg()
            return {
                '1min': load1,
                '5min': load5,
                '15min': load15
            }
        except Exception:
            return {'1min': 0.0, '5min': 0.0, '15min': 0.0}
    
    def _get_network_stats(self) -> Dict[str, Any]:
        """Get network interface statistics."""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errin': net_io.errin,
                'errout': net_io.errout,
                'dropin': net_io.dropin,
                'dropout': net_io.dropout
            }
        except Exception:
            return {}
    
    def _get_top_processes(self, limit: int = 5) -> list:
        """Get top processes by CPU usage."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage and return top processes
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            return processes[:limit]
            
        except Exception:
            return []
    
    def _get_pi_specific_stats(self) -> Dict[str, Any]:
        """Get Raspberry Pi specific statistics."""
        stats = {}
        
        try:
            # GPU memory split
            stats['gpu_memory'] = self._get_gpu_memory()
            
            # GPU temperature
            stats['gpu_temperature'] = self._get_gpu_temperature()
            
            # Throttling status
            stats['throttled'] = self._get_throttled_status()
            
            # Voltage
            stats['voltage'] = self._get_core_voltage()
            
            # Clock frequencies
            stats['clocks'] = self._get_clock_frequencies()
            
        except Exception as e:
            self.logger.debug(f"Error getting Pi-specific stats: {e}")
        
        return stats
    
    def _get_gpu_memory(self) -> int:
        """Get GPU memory allocation in MB."""
        try:
            result = os.popen('vcgencmd get_mem gpu').read().strip()
            if 'gpu=' in result:
                return int(result.split('=')[1].replace('M', ''))
        except Exception:
            pass
        return 0
    
    def _get_gpu_temperature(self) -> float:
        """Get GPU temperature in Celsius."""
        try:
            result = os.popen('vcgencmd measure_temp').read().strip()
            if 'temp=' in result:
                temp_str = result.split('=')[1].replace("'C", '')
                return float(temp_str)
        except Exception:
            pass
        return 0.0
    
    def _get_throttled_status(self) -> Dict[str, bool]:
        """Get throttling status."""
        try:
            result = os.popen('vcgencmd get_throttled').read().strip()
            if 'throttled=' in result:
                throttled_hex = result.split('=')[1]
                throttled_int = int(throttled_hex, 16)
                
                return {
                    'under_voltage_detected': bool(throttled_int & 0x1),
                    'arm_frequency_capped': bool(throttled_int & 0x2),
                    'currently_throttled': bool(throttled_int & 0x4),
                    'soft_temperature_limit': bool(throttled_int & 0x8),
                    'under_voltage_occurred': bool(throttled_int & 0x10000),
                    'arm_frequency_capping_occurred': bool(throttled_int & 0x20000),
                    'throttling_occurred': bool(throttled_int & 0x40000),
                    'soft_temperature_limit_occurred': bool(throttled_int & 0x80000)
                }
        except Exception:
            pass
        
        return {}
    
    def _get_core_voltage(self) -> float:
        """Get core voltage."""
        try:
            result = os.popen('vcgencmd measure_volts core').read().strip()
            if 'volt=' in result:
                voltage_str = result.split('=')[1].replace('V', '')
                return float(voltage_str)
        except Exception:
            pass
        return 0.0
    
    def _get_clock_frequencies(self) -> Dict[str, int]:
        """Get current clock frequencies."""
        clocks = {}
        clock_types = ['arm', 'core', 'h264', 'isp', 'v3d', 'uart', 'pwm', 'emmc', 'pixel', 'vec', 'hdmi', 'dpi']
        
        for clock_type in clock_types:
            try:
                result = os.popen(f'vcgencmd measure_clock {clock_type}').read().strip()
                if f'frequency({clock_type})=' in result:
                    freq_str = result.split('=')[1]
                    clocks[clock_type] = int(freq_str)
            except Exception:
                continue
        
        return clocks
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check system health and return status.
        
        Returns:
            dict: Health status with warnings and alerts
        """
        stats = self.get_system_stats()
        health = {
            'status': 'healthy',
            'warnings': [],
            'alerts': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Check temperature
        temp = stats.get('temperature', 0)
        if temp > self.temperature_limit:
            health['alerts'].append(f"High CPU temperature: {temp:.1f}°C")
            health['status'] = 'critical'
        elif temp > self.temperature_limit - 10:
            health['warnings'].append(f"Elevated CPU temperature: {temp:.1f}°C")
            if health['status'] == 'healthy':
                health['status'] = 'warning'
        
        # Check memory usage
        memory = stats.get('memory_percent', 0)
        if memory > self.memory_limit:
            health['alerts'].append(f"High memory usage: {memory:.1f}%")
            health['status'] = 'critical'
        elif memory > self.memory_limit - 10:
            health['warnings'].append(f"Elevated memory usage: {memory:.1f}%")
            if health['status'] == 'healthy':
                health['status'] = 'warning'
        
        # Check disk usage
        disk = stats.get('disk_percent', 0)
        if disk > self.disk_limit:
            health['alerts'].append(f"Low disk space: {disk:.1f}% used")
            health['status'] = 'critical'
        elif disk > self.disk_limit - 5:
            health['warnings'].append(f"Disk space getting low: {disk:.1f}% used")
            if health['status'] == 'healthy':
                health['status'] = 'warning'
        
        # Check CPU usage
        cpu = stats.get('cpu_percent', 0)
        if cpu > self.cpu_limit:
            health['warnings'].append(f"High CPU usage: {cpu:.1f}%")
            if health['status'] == 'healthy':
                health['status'] = 'warning'
        
        # Check throttling
        throttled = stats.get('throttled', {})
        if throttled.get('currently_throttled'):
            health['alerts'].append("System is currently being throttled")
            health['status'] = 'critical'
        elif throttled.get('under_voltage_detected'):
            health['warnings'].append("Under-voltage condition detected")
            if health['status'] == 'healthy':
                health['status'] = 'warning'
        
        return health
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of key system metrics."""
        stats = self.get_system_stats()
        
        return {
            'cpu_usage': f"{stats.get('cpu_percent', 0):.1f}%",
            'memory_usage': f"{stats.get('memory_percent', 0):.1f}%",
            'disk_usage': f"{stats.get('disk_percent', 0):.1f}%",
            'temperature': f"{stats.get('temperature', 0):.1f}°C",
            'uptime_hours': stats.get('uptime', 0) / 3600,
            'load_1min': stats.get('load_average', {}).get('1min', 0),
            'health_status': self.check_health()['status']
        }
    
    def cleanup(self):
        """Clean up system monitor resources."""
        try:
            self.is_initialized = False
            self.logger.info("System monitor cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during system monitor cleanup: {e}") 