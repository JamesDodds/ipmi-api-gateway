import subprocess
import json
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class IPMIService:
    """Service class for IPMI operations using ipmitool"""
    
    def __init__(self, server_id: str = None):
        self.config_path = os.environ.get('IPMI_CONFIG_PATH', '/etc/ipmi/config.json')
        self.server_id = server_id
        self.servers_config = self._load_config()
        
        # If server_id is provided, use that specific server, otherwise use the first/default
        if server_id:
            if server_id not in self.servers_config:
                raise ValueError(f"Server '{server_id}' not found in configuration")
            self.config = self.servers_config[server_id]
        else:
            # Use first server as default or single server config
            if isinstance(self.servers_config, dict) and 'hostname' in self.servers_config:
                # Single server configuration
                self.config = self.servers_config
            else:
                # Multi-server configuration - use first server
                first_server = next(iter(self.servers_config.keys()))
                self.config = self.servers_config[first_server]
                self.server_id = first_server
    
    def _load_config(self) -> Dict[str, Any]:
        """Load IPMI configuration from file or environment variables"""
        # Try loading from file first (Kubernetes deployment)
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                # Check if it's multi-server config
                if 'servers' in config:
                    return config['servers']
                else:
                    # Single server config
                    required_fields = ['hostname', 'username', 'password']
                    for field in required_fields:
                        if field not in config:
                            raise ValueError(f"Missing required field: {field}")
                    return config
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in config file {self.config_path}")
                raise Exception("Invalid IPMI configuration format")
        
        # Fallback to environment variables (Docker Compose or direct run)
        logger.info("Config file not found, using environment variables")
        
        # Check for multi-server environment variables
        ipmi_hosts = os.environ.get('IPMI_HOSTS')
        if ipmi_hosts:
            return self._parse_multi_server_env(ipmi_hosts)
        
        # Single server configuration
        config = {
            'hostname': os.environ.get('IPMI_HOST'),
            'username': os.environ.get('IPMI_USER'), 
            'password': os.environ.get('IPMI_PASSWORD')
        }
        
        # Validate environment variables
        required_fields = ['hostname', 'username', 'password']
        missing_fields = [field for field in required_fields if not config.get(field)]
        
        if missing_fields:
            raise Exception(f"Missing required environment variables: {missing_fields}. "
                          f"Please set IPMI_HOST, IPMI_USER, and IPMI_PASSWORD environment variables "
                          f"or provide a config file at {self.config_path}")
        
        return config
    
    def _parse_multi_server_env(self, ipmi_hosts: str) -> Dict[str, Dict[str, str]]:
        """Parse multi-server environment variable format"""
        # Format: server1:192.168.1.100:user:pass,server2:192.168.1.101:user:pass
        servers = {}
        for host_config in ipmi_hosts.split(','):
            parts = host_config.strip().split(':')
            if len(parts) >= 4:
                server_name = parts[0]
                servers[server_name] = {
                    'hostname': parts[1],
                    'username': parts[2],
                    'password': parts[3]
                }
            elif len(parts) == 2:
                # Format: server1:192.168.1.100 (use default credentials)
                server_name = parts[0]
                servers[server_name] = {
                    'hostname': parts[1],
                    'username': os.environ.get('IPMI_USER', 'admin'),
                    'password': os.environ.get('IPMI_PASSWORD', 'admin')
                }
        return servers
    
    def get_available_servers(self) -> List[str]:
        """Get list of available server IDs"""
        if isinstance(self.servers_config, dict) and 'hostname' in self.servers_config:
            return ['default']
        return list(self.servers_config.keys())
    
    def _execute_ipmi_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute ipmitool command with proper error handling"""
        try:
            # Build the full ipmitool command
            cmd = [
                'ipmitool',
                '-I', 'lanplus',
                '-H', self.config['hostname'],
                '-U', self.config['username'],
                '-P', self.config['password']
            ] + command.split()
            
            # Create a safe command for logging (hide password)
            safe_cmd = [
                'ipmitool',
                '-I', 'lanplus',
                '-H', self.config['hostname'],
                '-U', self.config['username'],
                '-P', '[HIDDEN]'
            ] + command.split()
            
            logger.info(f"Executing IPMI command on {self.config['hostname']}: {' '.join(safe_cmd)}")
            
            # Execute the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout.strip(),
                    'error': None,
                    'server_id': self.server_id,
                    'hostname': self.config['hostname']
                }
            else:
                logger.error(f"IPMI command failed on {self.config['hostname']}: {result.stderr}")
                return {
                    'success': False,
                    'output': result.stdout.strip(),
                    'error': result.stderr.strip(),
                    'server_id': self.server_id,
                    'hostname': self.config['hostname']
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"IPMI command timed out on {self.config['hostname']}")
            return {
                'success': False,
                'output': '',
                'error': 'Command timed out',
                'server_id': self.server_id,
                'hostname': self.config['hostname']
            }
        except Exception as e:
            logger.error(f"Error executing IPMI command on {self.config['hostname']}: {str(e)}")
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'server_id': self.server_id,
                'hostname': self.config['hostname']
            }
    
    # Power Management Methods
    def power_on(self) -> Dict[str, Any]:
        """Power on the server"""
        return self._execute_ipmi_command('chassis power on')
    
    def power_off(self, force: bool = False) -> Dict[str, Any]:
        """Power off the server"""
        if force:
            return self._execute_ipmi_command('chassis power off')
        else:
            return self._execute_ipmi_command('chassis power soft')
    
    def power_reset(self) -> Dict[str, Any]:
        """Reset the server"""
        return self._execute_ipmi_command('chassis power reset')
    
    def get_power_status(self) -> Dict[str, Any]:
        """Get current power status"""
        result = self._execute_ipmi_command('chassis power status')
        
        if result['success']:
            # Parse the power status from output
            output = result['output'].lower()
            if 'power is on' in output:
                power_state = 'on'
            elif 'power is off' in output:
                power_state = 'off'
            else:
                power_state = 'unknown'
            
            result['power_state'] = power_state
        
        return result
    
    # System Information Methods
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        commands = {
            'fru': 'fru',
            'bmc_info': 'bmc info',
            'chassis_status': 'chassis status',
            'system_info': 'fru print'
        }
        
        results = {}
        for key, cmd in commands.items():
            result = self._execute_ipmi_command(cmd)
            results[key] = result
        
        return {
            'success': all(r['success'] for r in results.values()),
            'system_info': results,
            'server_id': self.server_id,
            'hostname': self.config['hostname']
        }
    
    def get_sensor_data(self) -> Dict[str, Any]:
        """Get all sensor readings (temperature, voltage, fans, etc.)"""
        result = self._execute_ipmi_command('sensor', timeout=45)
        
        if result['success']:
            # Parse sensor data into structured format
            sensors = self._parse_sensor_output(result['output'])
            result['sensors'] = sensors
            result['sensor_count'] = len(sensors)
        
        return result
    
    def _parse_sensor_output(self, output: str) -> List[Dict[str, str]]:
        """Parse sensor command output into structured data"""
        sensors = []
        lines = output.split('\n')
        
        for line in lines:
            if '|' in line:
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 3:
                    sensor = {
                        'name': parts[0],
                        'value': parts[1],
                        'unit': parts[2] if len(parts) > 2 else '',
                        'status': parts[3] if len(parts) > 3 else '',
                        'lower_nr': parts[4] if len(parts) > 4 else '',
                        'lower_cr': parts[5] if len(parts) > 5 else '',
                        'lower_nc': parts[6] if len(parts) > 6 else '',
                        'upper_nc': parts[7] if len(parts) > 7 else '',
                        'upper_cr': parts[8] if len(parts) > 8 else '',
                        'upper_nr': parts[9] if len(parts) > 9 else ''
                    }
                    sensors.append(sensor)
        
        return sensors
    
    def get_system_event_log(self, limit: int = 50) -> Dict[str, Any]:
        """Get system event log entries"""
        result = self._execute_ipmi_command('sel list')
        
        if result['success']:
            # Parse SEL entries
            events = self._parse_sel_output(result['output'], limit)
            result['events'] = events
            result['event_count'] = len(events)
        
        return result
    
    def _parse_sel_output(self, output: str, limit: int) -> List[Dict[str, str]]:
        """Parse SEL output into structured data"""
        events = []
        lines = output.split('\n')[:limit]  # Limit number of events
        
        for line in lines:
            if line.strip():
                # SEL format: ID | Date | Time | Sensor | Event | Value
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 4:
                    event = {
                        'id': parts[0],
                        'timestamp': f"{parts[1]} {parts[2]}" if len(parts) > 2 else parts[1],
                        'sensor': parts[3] if len(parts) > 3 else '',
                        'event': parts[4] if len(parts) > 4 else '',
                        'value': parts[5] if len(parts) > 5 else ''
                    }
                    events.append(event)
        
        return events
    
    def clear_system_event_log(self) -> Dict[str, Any]:
        """Clear the system event log"""
        return self._execute_ipmi_command('sel clear')
    
    def get_sel_info(self) -> Dict[str, Any]:
        """Get SEL information and statistics"""
        return self._execute_ipmi_command('sel info')
    
    # Boot Device Management
    def set_boot_device(self, device: str, persistent: bool = False) -> Dict[str, Any]:
        """Set next boot device (pxe, disk, cdrom, bios)"""
        valid_devices = ['pxe', 'disk', 'cdrom', 'bios', 'floppy', 'safe']
        if device.lower() not in valid_devices:
            return {
                'success': False,
                'error': f"Invalid boot device '{device}'. Valid options: {', '.join(valid_devices)}",
                'server_id': self.server_id,
                'hostname': self.config['hostname']
            }
        
        options = 'options=persistent' if persistent else 'options=efiboot'
        return self._execute_ipmi_command(f'chassis bootdev {device} {options}')
    
    def get_boot_device(self) -> Dict[str, Any]:
        """Get current boot device setting"""
        result = self._execute_ipmi_command('chassis bootparam get 5')
        
        if result['success']:
            # Parse boot device from output
            boot_device = self._parse_boot_device_output(result['output'])
            result['boot_device'] = boot_device
        
        return result
    
    def _parse_boot_device_output(self, output: str) -> Dict[str, str]:
        """Parse boot device parameter output"""
        boot_info = {}
        lines = output.split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                boot_info[key.strip().lower().replace(' ', '_')] = value.strip()
        
        return boot_info
    
    def check_health(self) -> Dict[str, Any]:
        """Check IPMI connection and basic health"""
        try:
            # Test basic connectivity with chassis status
            result = self._execute_ipmi_command('chassis status')
            
            if result['success']:
                # Parse chassis status for additional health info
                details = {
                    'ipmi_connection': 'healthy',
                    'chassis_status': result['output'],
                    'server_id': self.server_id,
                    'hostname': self.config['hostname']
                }
                
                # Try to get power status as additional health check
                power_result = self.get_power_status()
                if power_result['success']:
                    details['power_status'] = power_result['power_state']
                
                return {
                    'success': True,
                    'details': details
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'server_id': self.server_id,
                    'hostname': self.config['hostname']
                }
                
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'server_id': self.server_id,
                'hostname': self.config['hostname']
            }

    # Legacy methods for backward compatibility
    def start_server(self, ip_address=None):
        """Legacy method - redirects to power_on"""
        return self.power_on()

    def stop_server(self, ip_address=None):
        """Legacy method - redirects to power_off"""
        return self.power_off()

    def check_status(self, ip_address=None):
        """Legacy method - redirects to get_power_status"""
        return self.get_power_status()

# Multi-server service wrapper
class MultiServerIPMIService:
    """Service to manage multiple IPMI servers"""
    
    def __init__(self):
        self.base_service = IPMIService()
        self.servers = self.base_service.get_available_servers()
    
    def get_service_for_server(self, server_id: str) -> IPMIService:
        """Get IPMIService instance for specific server"""
        return IPMIService(server_id=server_id)
    
    def execute_on_all_servers(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute operation on all servers"""
        results = {}
        
        for server_id in self.servers:
            try:
                service = self.get_service_for_server(server_id)
                if hasattr(service, operation):
                    method = getattr(service, operation)
                    results[server_id] = method(**kwargs)
                else:
                    results[server_id] = {
                        'success': False,
                        'error': f"Operation '{operation}' not supported",
                        'server_id': server_id
                    }
            except Exception as e:
                results[server_id] = {
                    'success': False,
                    'error': str(e),
                    'server_id': server_id
                }
        
        return {
            'operation': operation,
            'total_servers': len(self.servers),
            'successful': sum(1 for r in results.values() if r.get('success', False)),
            'results': results
        }
    
    def get_servers_status(self) -> Dict[str, Any]:
        """Get status of all servers"""
        return self.execute_on_all_servers('get_power_status')