from functools import wraps
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)

def validate_request(required_fields=None):
    """Decorator to validate request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if required_fields:
                if not request.is_json:
                    return jsonify({'error': 'Request must be JSON'}), 400
                
                data = request.get_json()
                missing_fields = []
                
                for field in required_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing_fields
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_power_action(action):
    """Validate power action parameters"""
    valid_actions = ['on', 'off', 'reset', 'soft']
    return action.lower() in valid_actions

def validate_ipmi_hostname(hostname):
    """Basic validation for IPMI hostname/IP"""
    if not hostname or len(hostname.strip()) == 0:
        return False
    
    # Basic length check
    if len(hostname) > 255:
        return False
    
    return True

def validate_credentials(username, password):
    """Validate IPMI credentials format"""
    if not username or not password:
        return False
    
    if len(username.strip()) == 0 or len(password.strip()) == 0:
        return False
    
    return True

# Legacy validation functions for backward compatibility
def validate_ipmi_command(command):
    valid_commands = ['power', 'status', 'reset', 'boot']
    if command not in valid_commands:
        raise ValueError(f"Invalid IPMI command: {command}. Valid commands are: {', '.join(valid_commands)}.")

def validate_server_id(server_id):
    if not isinstance(server_id, int) or server_id <= 0:
        raise ValueError("Server ID must be a positive integer.")

def validate_parameters(params):
    if not isinstance(params, dict):
        raise ValueError("Parameters must be provided as a dictionary.")
    for key, value in params.items():
        if not isinstance(key, str) or not value:
            raise ValueError(f"Invalid parameter: {key} with value: {value}. Keys must be strings and values must not be empty.")