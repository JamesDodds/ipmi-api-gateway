# IPMI API Gateway

This project serves as an API gateway for `ipmitool` to access Supermicro servers' IPMI, designed to be called by Home Assistant. It provides a simple interface to manage server operations such as starting, stopping, and checking the health of the servers. It has no security on it (yet) so run at your own risk.

## Features

- **Single & Multi-Server Support** - Manage one or multiple IPMI devices
- **Power Management** - Power on/off/reset servers with graceful and forced options
- **System Monitoring** - Get sensor readings, system information, and event logs
- **Boot Management** - Control boot device selection (PXE, disk, CDROM, etc.)
- **Bulk Operations** - Execute commands across multiple servers simultaneously
- **Docker & Kubernetes Ready** - Easy deployment with container orchestration

## Project Structure

```
ipmi-api-gateway
├── src
│   ├── app.py                # Entry point of the application
│   ├── controllers           # Contains API request handlers
│   │   ├── __init__.py
│   │   └── ipmi_controller.py # Handles IPMI related API requests
│   ├── services              # Contains business logic
│   │   ├── __init__.py
│   │   └── ipmi_service.py   # Interacts with ipmitool
│   └── utils                 # Utility functions and validators
│       ├── __init__.py
│       └── validators.py      # Validates input data for API requests
├── docker
│   └── Dockerfile            # Docker image build instructions
├── k8s
│   ├── deployment.yaml       # Kubernetes deployment configuration
│   ├── service.yaml          # Kubernetes service configuration
│   └── configmap.yaml        # ConfigMap for application configuration
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker application configuration
├── CONFIGURATION.md          # Detailed configuration guide
└── README.md                 # Project documentation
```

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ipmi-api-gateway
   ```

2. **Configure IPMI credentials** in `docker-compose.yml`:
   ```yaml
   environment:
     - FLASK_ENV=development
     - IPMI_HOST=192.168.1.197    # Your IPMI device IP
     - IPMI_USER=ADMIN            # Your IPMI username
     - IPMI_PASSWORD=ADMIN        # Your IPMI password
   ```

3. **Build and run:**
   ```bash
   docker build -f docker/Dockerfile -t ipmi-api-gateway .
   docker-compose up
   ```

4. **Test the API:**
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:5000/health" -Method GET
   ```

## Configuration

📖 **See [CONFIGURATION.md](CONFIGURATION.md) for detailed setup instructions**, including:
- Single server setup
- Multi-server configurations
- Kubernetes deployment
- Security considerations
- Troubleshooting guide

## API Endpoints

### Core Endpoints
- `GET /health` - API service health check
- `GET /api/v1/health` - IPMI connection health check
- `GET /api/v1/servers` - List all configured servers
- `GET /api/v1/docs` - Detailed API documentation

### Power Management
- `GET /api/v1/power/status` - Get current power status
- `POST /api/v1/power/on` - Power on the server
- `POST /api/v1/power/off` - Power off server (supports `force` parameter)
- `POST /api/v1/power/reset` - Reset the server

### System Information
- `GET /api/v1/system/info` - Get comprehensive system information
- `GET /api/v1/system/sensors` - Get all sensor readings (temperature, voltage, fans)
- `GET /api/v1/system/events` - Get system event log
- `DELETE /api/v1/system/events` - Clear system event log

### Boot Management
- `GET /api/v1/boot/device` - Get current boot device
- `POST /api/v1/boot/device` - Set boot device (PXE, disk, CDROM, BIOS, etc.)

### Bulk Operations (Multi-Server)
- `GET /api/v1/servers/status` - Get power status of all servers
- `POST /api/v1/bulk/power/on` - Power on all servers
- `POST /api/v1/bulk/power/off` - Power off all servers
- `GET /api/v1/bulk/sensors` - Get sensor data from all servers

## Quick Testing Commands

### Basic Power Management
```powershell
# Check power status
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/power/status" -Method GET

# Power on server
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/power/on" -Method POST

# Forced power off
$body = @{ force = $true } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/power/off" -Method POST -Body $body -ContentType "application/json"

# Power on with 45-second countdown
1..45 | ForEach-Object { Write-Host "Powering on in $($_) seconds..." -NoNewline; Start-Sleep 1; Write-Host "`r" -NoNewline }; Write-Host "Sending power on command..."; Invoke-RestMethod -Uri "http://localhost:5000/api/v1/power/on" -Method POST
```

### System Monitoring
```powershell
# Get sensor readings
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/system/sensors" -Method GET

# Get system information
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/system/info" -Method GET

# Get recent events
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/system/events?limit=10" -Method GET
```

### Boot Management
```powershell
# Set PXE boot for next boot
$body = @{ device = "pxe"; persistent = $false } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/boot/device" -Method POST -Body $body -ContentType "application/json"
```

### Multi-Server Operations
```powershell
# List all servers
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/servers" -Method GET

# Get status of all servers
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/servers/status" -Method GET

# Target specific server
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/power/status?server_id=server1" -Method GET
```

## Integration Examples

### Home Assistant
```yaml
# configuration.yaml
rest_command:
  server_power_on:
    url: "http://your-api-host:5000/api/v1/power/on"
    method: POST
  
  server_power_off:
    url: "http://your-api-host:5000/api/v1/power/off"
    method: POST
    payload: '{"force": true}'
    content_type: 'application/json'

sensor:
  - platform: rest
    resource: "http://your-api-host:5000/api/v1/power/status"
    name: "Server Power Status"
    value_template: "{{ value_json.power_state }}"
```

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.