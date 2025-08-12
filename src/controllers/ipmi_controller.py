from flask import Blueprint, jsonify, request
from services.ipmi_service import IPMIService, MultiServerIPMIService
from utils.validators import validate_request
import logging

logger = logging.getLogger(__name__)

ipmi_bp = Blueprint('ipmi', __name__)

# Initialize services
try:
    multi_server_service = MultiServerIPMIService()
    ipmi_service = IPMIService()  # Default service for backward compatibility
except Exception as e:
    logger.error(f"Failed to initialize IPMI services: {str(e)}")
    multi_server_service = None
    ipmi_service = None

def get_server_service(server_id: str = None):
    """Get IPMIService instance for specific server or default"""
    if server_id:
        return IPMIService(server_id=server_id)
    return ipmi_service

def handle_server_parameter():
    """Extract server_id from request parameters"""
    server_id = request.args.get('server_id') or request.json.get('server_id') if request.is_json else None
    return server_id

# Health Check Endpoints
@ipmi_bp.route('/health', methods=['GET'])
def ipmi_health():
    """IPMI health check endpoint"""
    try:
        server_id = handle_server_parameter()
        service = get_server_service(server_id)
        
        if not service:
            return jsonify({'status': 'error', 'message': 'IPMI service not initialized'}), 500
            
        result = service.check_health()
        if result['success']:
            return jsonify({
                'status': 'healthy',
                'service': 'ipmi',
                'details': result['details']
            }), 200
        else:
            return jsonify({
                'status': 'unhealthy',
                'service': 'ipmi',
                'error': result['error']
            }), 503
    except Exception as e:
        logger.error(f"Error in ipmi_health: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Server Management Endpoints
@ipmi_bp.route('/servers', methods=['GET'])
def list_servers():
    """List all available servers"""
    try:
        if not multi_server_service:
            return jsonify({'status': 'error', 'message': 'Multi-server service not available'}), 500
            
        servers = multi_server_service.servers
        return jsonify({
            'status': 'success',
            'servers': servers,
            'count': len(servers)
        }), 200
    except Exception as e:
        logger.error(f"Error in list_servers: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@ipmi_bp.route('/servers/status', methods=['GET'])
def all_servers_status():
    """Get power status of all servers"""
    try:
        if not multi_server_service:
            return jsonify({'status': 'error', 'message': 'Multi-server service not available'}), 500
            
        result = multi_server_service.get_servers_status()
        return jsonify({
            'status': 'success',
            'operation': result['operation'],
            'summary': {
                'total_servers': result['total_servers'],
                'successful': result['successful'],
                'failed': result['total_servers'] - result['successful']
            },
            'results': result['results']
        }), 200
    except Exception as e:
        logger.error(f"Error in all_servers_status: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Power Management Endpoints
@ipmi_bp.route('/power/on', methods=['POST'])
def power_on():
    """Power on the server"""
    try:
        server_id = handle_server_parameter()
        service = get_server_service(server_id)
        
        result = service.power_on()
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'Server power on command sent',
                'output': result['output'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to power on server',
                'error': result['error'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 500
    except Exception as e:
        logger.error(f"Error in power_on: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@ipmi_bp.route('/power/off', methods=['POST'])
def power_off():
    """Power off the server"""
    try:
        server_id = handle_server_parameter()
        service = get_server_service(server_id)
        
        # Check for force parameter
        force = request.json.get('force', False) if request.is_json else False
        
        result = service.power_off(force=force)
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': f"Server power {'off' if force else 'soft shutdown'} command sent",
                'output': result['output'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to power off server',
                'error': result['error'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 500
    except Exception as e:
        logger.error(f"Error in power_off: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@ipmi_bp.route('/power/status', methods=['GET'])
def power_status():
    """Get current power status of the server"""
    try:
        server_id = handle_server_parameter()
        service = get_server_service(server_id)
        
        result = service.get_power_status()
        if result['success']:
            return jsonify({
                'status': 'success',
                'power_state': result['power_state'],
                'output': result['output'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get power status',
                'error': result['error'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 500
    except Exception as e:
        logger.error(f"Error in power_status: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@ipmi_bp.route('/power/reset', methods=['POST'])
def power_reset():
    """Reset the server"""
    try:
        server_id = handle_server_parameter()
        service = get_server_service(server_id)
        
        result = service.power_reset()
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'Server reset command sent',
                'output': result['output'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to reset server',
                'error': result['error'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 500
    except Exception as e:
        logger.error(f"Error in power_reset: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# System Information Endpoints
@ipmi_bp.route('/system/info', methods=['GET'])
def system_info():
    """Get comprehensive system information"""
    try:
        server_id = handle_server_parameter()
        service = get_server_service(server_id)
        
        result = service.get_system_info()
        if result['success']:
            return jsonify({
                'status': 'success',
                'system_info': result['system_info'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get system information',
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 500
    except Exception as e:
        logger.error(f"Error in system_info: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@ipmi_bp.route('/system/sensors', methods=['GET'])
def sensor_readings():
    """Get all sensor readings"""
    try:
        server_id = handle_server_parameter()
        service = get_server_service(server_id)
        
        result = service.get_sensor_data()
        if result['success']:
            return jsonify({
                'status': 'success',
                'sensors': result['sensors'],
                'sensor_count': result['sensor_count'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get sensor data',
                'error': result['error'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 500
    except Exception as e:
        logger.error(f"Error in sensor_readings: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@ipmi_bp.route('/system/events', methods=['GET'])
def system_events():
    """Get system event log"""
    try:
        server_id = handle_server_parameter()
        service = get_server_service(server_id)
        
        # Get limit from query parameters
        limit = request.args.get('limit', 50, type=int)
        
        result = service.get_system_event_log(limit=limit)
        if result['success']:
            return jsonify({
                'status': 'success',
                'events': result['events'],
                'event_count': result['event_count'],
                'limit': limit,
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get system event log',
                'error': result['error'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 500
    except Exception as e:
        logger.error(f"Error in system_events: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@ipmi_bp.route('/system/events', methods=['DELETE'])
def clear_system_events():
    """Clear system event log"""
    try:
        server_id = handle_server_parameter()
        service = get_server_service(server_id)
        
        result = service.clear_system_event_log()
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'System event log cleared',
                'output': result['output'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to clear system event log',
                'error': result['error'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 500
    except Exception as e:
        logger.error(f"Error in clear_system_events: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@ipmi_bp.route('/system/events/info', methods=['GET'])
def sel_info():
    """Get SEL information and statistics"""
    try:
        server_id = handle_server_parameter()
        service = get_server_service(server_id)
        
        result = service.get_sel_info()
        if result['success']:
            return jsonify({
                'status': 'success',
                'sel_info': result['output'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get SEL information',
                'error': result['error'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 500
    except Exception as e:
        logger.error(f"Error in sel_info: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Boot Management Endpoints
@ipmi_bp.route('/boot/device', methods=['GET'])
def get_boot_device():
    """Get current boot device"""
    try:
        server_id = handle_server_parameter()
        service = get_server_service(server_id)
        
        result = service.get_boot_device()
        if result['success']:
            return jsonify({
                'status': 'success',
                'boot_device': result['boot_device'],
                'raw_output': result['output'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get boot device',
                'error': result['error'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 500
    except Exception as e:
        logger.error(f"Error in get_boot_device: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@ipmi_bp.route('/boot/device', methods=['POST'])
def set_boot_device():
    """Set boot device (pxe, disk, cdrom, bios)"""
    try:
        server_id = handle_server_parameter()
        service = get_server_service(server_id)
        
        if not request.is_json:
            return jsonify({'status': 'error', 'message': 'JSON request body required'}), 400
        
        device = request.json.get('device')
        persistent = request.json.get('persistent', False)
        
        if not device:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: device'
            }), 400
        
        result = service.set_boot_device(device, persistent=persistent)
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': f"Boot device set to {device}",
                'output': result['output'],
                'device': device,
                'persistent': persistent,
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to set boot device',
                'error': result['error'],
                'server_id': result.get('server_id'),
                'hostname': result.get('hostname')
            }), 500
    except Exception as e:
        logger.error(f"Error in set_boot_device: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Bulk Operations Endpoints
@ipmi_bp.route('/bulk/power/on', methods=['POST'])
def bulk_power_on():
    """Power on all servers"""
    try:
        if not multi_server_service:
            return jsonify({'status': 'error', 'message': 'Multi-server service not available'}), 500
            
        result = multi_server_service.execute_on_all_servers('power_on')
        return jsonify({
            'status': 'success',
            'operation': 'bulk_power_on',
            'summary': {
                'total_servers': result['total_servers'],
                'successful': result['successful'],
                'failed': result['total_servers'] - result['successful']
            },
            'results': result['results']
        }), 200
    except Exception as e:
        logger.error(f"Error in bulk_power_on: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@ipmi_bp.route('/bulk/power/off', methods=['POST'])
def bulk_power_off():
    """Power off all servers"""
    try:
        if not multi_server_service:
            return jsonify({'status': 'error', 'message': 'Multi-server service not available'}), 500
        
        force = request.json.get('force', False) if request.is_json else False
        result = multi_server_service.execute_on_all_servers('power_off', force=force)
        return jsonify({
            'status': 'success',
            'operation': 'bulk_power_off',
            'force': force,
            'summary': {
                'total_servers': result['total_servers'],
                'successful': result['successful'],
                'failed': result['total_servers'] - result['successful']
            },
            'results': result['results']
        }), 200
    except Exception as e:
        logger.error(f"Error in bulk_power_off: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@ipmi_bp.route('/bulk/sensors', methods=['GET'])
def bulk_sensor_readings():
    """Get sensor readings from all servers"""
    try:
        if not multi_server_service:
            return jsonify({'status': 'error', 'message': 'Multi-server service not available'}), 500
            
        result = multi_server_service.execute_on_all_servers('get_sensor_data')
        return jsonify({
            'status': 'success',
            'operation': 'bulk_sensor_readings',
            'summary': {
                'total_servers': result['total_servers'],
                'successful': result['successful'],
                'failed': result['total_servers'] - result['successful']
            },
            'results': result['results']
        }), 200
    except Exception as e:
        logger.error(f"Error in bulk_sensor_readings: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500