from flask import Flask, jsonify, request
from controllers.ipmi_controller import ipmi_bp
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Register blueprints
app.register_blueprint(ipmi_bp, url_prefix='/api/v1')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes"""
    return jsonify({'status': 'healthy', 'service': 'ipmi-api-gateway'}), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        'service': 'IPMI API Gateway',
        'version': '2.0.0',
        'description': 'API Gateway for IPMI operations with multi-server support',
        'endpoints': {
            'health_check': {
                'url': '/health',
                'method': 'GET',
                'description': 'API service health check'
            },
            'ipmi_health': {
                'url': '/api/v1/health',
                'method': 'GET',
                'description': 'IPMI connection health check',
                'parameters': 'server_id (optional)'
            },
            'servers': {
                'list_servers': {
                    'url': '/api/v1/servers',
                    'method': 'GET',
                    'description': 'List all available servers'
                },
                'all_servers_status': {
                    'url': '/api/v1/servers/status',
                    'method': 'GET',
                    'description': 'Get power status of all servers'
                }
            },
            'power_management': {
                'power_on': {
                    'url': '/api/v1/power/on',
                    'method': 'POST',
                    'description': 'Power on server',
                    'parameters': 'server_id (optional)'
                },
                'power_off': {
                    'url': '/api/v1/power/off',
                    'method': 'POST',
                    'description': 'Power off server',
                    'parameters': 'server_id (optional), force (boolean)'
                },
                'power_status': {
                    'url': '/api/v1/power/status',
                    'method': 'GET',
                    'description': 'Get current power status',
                    'parameters': 'server_id (optional)'
                },
                'power_reset': {
                    'url': '/api/v1/power/reset',
                    'method': 'POST',
                    'description': 'Reset server',
                    'parameters': 'server_id (optional)'
                }
            },
            'system_information': {
                'system_info': {
                    'url': '/api/v1/system/info',
                    'method': 'GET',
                    'description': 'Get comprehensive system information',
                    'parameters': 'server_id (optional)'
                },
                'sensor_readings': {
                    'url': '/api/v1/system/sensors',
                    'method': 'GET',
                    'description': 'Get all sensor readings',
                    'parameters': 'server_id (optional)'
                },
                'system_events': {
                    'url': '/api/v1/system/events',
                    'method': 'GET',
                    'description': 'Get system event log',
                    'parameters': 'server_id (optional), limit (integer)'
                },
                'clear_events': {
                    'url': '/api/v1/system/events',
                    'method': 'DELETE',
                    'description': 'Clear system event log',
                    'parameters': 'server_id (optional)'
                },
                'sel_info': {
                    'url': '/api/v1/system/events/info',
                    'method': 'GET',
                    'description': 'Get SEL information and statistics',
                    'parameters': 'server_id (optional)'
                }
            },
            'boot_management': {
                'get_boot_device': {
                    'url': '/api/v1/boot/device',
                    'method': 'GET',
                    'description': 'Get current boot device',
                    'parameters': 'server_id (optional)'
                },
                'set_boot_device': {
                    'url': '/api/v1/boot/device',
                    'method': 'POST',
                    'description': 'Set boot device',
                    'parameters': 'server_id (optional), device (pxe|disk|cdrom|bios|floppy|safe), persistent (boolean)'
                }
            },
            'bulk_operations': {
                'bulk_power_on': {
                    'url': '/api/v1/bulk/power/on',
                    'method': 'POST',
                    'description': 'Power on all servers'
                },
                'bulk_power_off': {
                    'url': '/api/v1/bulk/power/off',
                    'method': 'POST',
                    'description': 'Power off all servers',
                    'parameters': 'force (boolean)'
                },
                'bulk_sensors': {
                    'url': '/api/v1/bulk/sensors',
                    'method': 'GET',
                    'description': 'Get sensor readings from all servers'
                }
            }
        },
        'usage_notes': {
            'server_id': 'Optional parameter to target specific server. Can be passed as query parameter (?server_id=server1) or in JSON body',
            'multi_server_config': 'Set IPMI_HOSTS environment variable with format: server1:ip1:user:pass,server2:ip2:user:pass',
            'single_server_config': 'Set IPMI_HOST, IPMI_USER, and IPMI_PASSWORD environment variables'
        }
    }), 200

@app.route('/api/v1/docs', methods=['GET'])
def api_docs():
    """Detailed API documentation endpoint"""
    return jsonify({
        'api_documentation': {
            'version': '2.0.0',
            'base_url': '/api/v1',
            'authentication': 'None (configured via environment variables)',
            'content_type': 'application/json',
            'endpoints': {
                'health_endpoints': [
                    {
                        'endpoint': '/health',
                        'method': 'GET',
                        'description': 'Check API service health',
                        'response': '200: Service healthy'
                    },
                    {
                        'endpoint': '/api/v1/health',
                        'method': 'GET',
                        'description': 'Check IPMI connection health',
                        'parameters': ['server_id (optional)'],
                        'response': '200: IPMI healthy, 503: IPMI unhealthy'
                    }
                ],
                'server_management': [
                    {
                        'endpoint': '/api/v1/servers',
                        'method': 'GET',
                        'description': 'List all configured servers',
                        'response': '200: List of server IDs'
                    },
                    {
                        'endpoint': '/api/v1/servers/status',
                        'method': 'GET',
                        'description': 'Get power status of all servers',
                        'response': '200: Power status for each server'
                    }
                ],
                'power_management': [
                    {
                        'endpoint': '/api/v1/power/status',
                        'method': 'GET',
                        'description': 'Get current power status',
                        'parameters': ['server_id (optional)'],
                        'response': '200: Power state (on/off/unknown)'
                    },
                    {
                        'endpoint': '/api/v1/power/on',
                        'method': 'POST',
                        'description': 'Power on server',
                        'parameters': ['server_id (optional)'],
                        'response': '200: Power on command sent'
                    },
                    {
                        'endpoint': '/api/v1/power/off',
                        'method': 'POST',
                        'description': 'Power off server (graceful or forced)',
                        'parameters': ['server_id (optional)', 'force (boolean, default: false)'],
                        'body_example': '{"force": true}',
                        'response': '200: Power off command sent'
                    },
                    {
                        'endpoint': '/api/v1/power/reset',
                        'method': 'POST',
                        'description': 'Reset server',
                        'parameters': ['server_id (optional)'],
                        'response': '200: Reset command sent'
                    }
                ],
                'system_information': [
                    {
                        'endpoint': '/api/v1/system/info',
                        'method': 'GET',
                        'description': 'Get comprehensive system information (FRU, BMC, chassis)',
                        'parameters': ['server_id (optional)'],
                        'response': '200: System information object'
                    },
                    {
                        'endpoint': '/api/v1/system/sensors',
                        'method': 'GET',
                        'description': 'Get all sensor readings (temperature, voltage, fans)',
                        'parameters': ['server_id (optional)'],
                        'response': '200: Array of sensor readings'
                    },
                    {
                        'endpoint': '/api/v1/system/events',
                        'method': 'GET',
                        'description': 'Get system event log entries',
                        'parameters': ['server_id (optional)', 'limit (integer, default: 50)'],
                        'response': '200: Array of event log entries'
                    },
                    {
                        'endpoint': '/api/v1/system/events',
                        'method': 'DELETE',
                        'description': 'Clear system event log',
                        'parameters': ['server_id (optional)'],
                        'response': '200: Event log cleared'
                    },
                    {
                        'endpoint': '/api/v1/system/events/info',
                        'method': 'GET',
                        'description': 'Get SEL information and statistics',
                        'parameters': ['server_id (optional)'],
                        'response': '200: SEL information'
                    }
                ],
                'boot_management': [
                    {
                        'endpoint': '/api/v1/boot/device',
                        'method': 'GET',
                        'description': 'Get current boot device configuration',
                        'parameters': ['server_id (optional)'],
                        'response': '200: Boot device information'
                    },
                    {
                        'endpoint': '/api/v1/boot/device',
                        'method': 'POST',
                        'description': 'Set next boot device',
                        'parameters': ['server_id (optional)', 'device (required)', 'persistent (boolean, default: false)'],
                        'body_example': '{"device": "pxe", "persistent": true}',
                        'valid_devices': ['pxe', 'disk', 'cdrom', 'bios', 'floppy', 'safe'],
                        'response': '200: Boot device set'
                    }
                ],
                'bulk_operations': [
                    {
                        'endpoint': '/api/v1/bulk/power/on',
                        'method': 'POST',
                        'description': 'Power on all configured servers',
                        'response': '200: Results for each server'
                    },
                    {
                        'endpoint': '/api/v1/bulk/power/off',
                        'method': 'POST',
                        'description': 'Power off all configured servers',
                        'parameters': ['force (boolean, default: false)'],
                        'body_example': '{"force": true}',
                        'response': '200: Results for each server'
                    },
                    {
                        'endpoint': '/api/v1/bulk/sensors',
                        'method': 'GET',
                        'description': 'Get sensor readings from all configured servers',
                        'response': '200: Sensor data for each server'
                    }
                ]
            },
            'error_responses': {
                '400': 'Bad Request - Invalid parameters',
                '404': 'Not Found - Endpoint not found',
                '500': 'Internal Server Error - IPMI command failed',
                '503': 'Service Unavailable - IPMI service unhealthy'
            }
        }
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)