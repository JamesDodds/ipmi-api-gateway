# IPMI API Gateway Configuration Guide

This guide explains how to configure the IPMI API Gateway for single-server and multi-server deployments.

## Configuration Options

The IPMI API Gateway supports three different configuration methods depending on your deployment needs.

### Option 1: Single Server Configuration (Simple)

Use this for managing a single IPMI device. This is the simplest configuration and what you'll likely start with.

**docker-compose.yml:**
```yaml
services:
  ipmi-api-gateway:
    image: ipmi-api-gateway:latest
    ports:
      - "5000:5000"
    volumes:
      - ./src:/app/src
    environment:
      - FLASK_ENV=development
      - IPMI_HOST=192.168.1.111         # Your IPMI device IP
      - IPMI_USER=USER                 # Your IPMI username
      - IPMI_PASSWORD=PASSWORD             # Your IPMI password
    networks:
      - ipmi-network

networks:
  ipmi-network:
    driver: bridge
```

**PowerShell Testing:**
```powershell
# Basic commands (no server_id needed)
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/power/status" -Method GET
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/power/on" -Method POST
```

### Option 2: Multi-Server with Shared Credentials

Use this when you have multiple IPMI devices that all use the same username and password.

**docker-compose.yml:**
```yaml
services:
  ipmi-api-gateway:
    image: ipmi-api-gateway:latest
    ports:
      - "5000:5000"
    volumes:
      - ./src:/app/src
    environment:
      - FLASK_ENV=development
      - IPMI_HOSTS=server1:192.168.1.111,server2:192.168.1.112,server3:192.168.1.113
      - IPMI_USER=USER                 # Shared username for all servers
      - IPMI_PASSWORD=PASSWORD             # Shared password for all servers
    networks:
      - ipmi-network

networks:
  ipmi-network:
    driver: bridge
```

**Format:** `server_name:ip_address,server_name:ip_address`

**PowerShell Testing:**
```powershell
# List all configured servers
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/servers" -Method GET

# Target specific server
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/power/status?server_id=server1" -Method GET

# Check all servers at once
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/servers/status" -Method GET

# Power on specific server via JSON body
$body = @{ server_id = "server1" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/power/on" -Method POST -Body $body -ContentType "application/json"
```

### Option 3: Multi-Server with Individual Credentials (Most Flexible)

Use this when you have multiple IPMI devices with different usernames and passwords.

**docker-compose.yml:**
```yaml
services:
  ipmi-api-gateway:
    image: ipmi-api-gateway:latest
    ports:
      - "5000:5000"
    volumes:
      - ./src:/app/src
    environment:
      - FLASK_ENV=development
      - IPMI_HOSTS=server1:192.168.1.111:USER:PASSWORD,server2:192.168.1.112:root:password123,server3:192.168.1.113:admin:secret456
    networks:
      - ipmi-network

networks:
  ipmi-network:
    driver: bridge
```

**Format:** `server_name:ip_address:username:password,server_name:ip_address:username:password`

**PowerShell Testing:**
```powershell
# Same commands as Option 2
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/servers" -Method GET
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/power/status?server_id=server1" -Method GET
```

## Advanced Configuration Examples

### Production Multi-Server Example
```yaml
environment:
  - IPMI_HOSTS=web-server:192.168.1.10:webadmin:web123,db-server:192.168.1.11:dbadmin:db456,backup-server:192.168.1.12:backupadmin:backup789
```

### Mixed Environment Example
```yaml
environment:
  - IPMI_HOSTS=server1:192.168.1.111:USER:PASSWORD,server2:192.168.1.112,server3:192.168.1.113
  - IPMI_USER=defaultuser     # Used for server2 and server3
  - IPMI_PASSWORD=defaultpass # Used for server2 and server3
```

## Kubernetes Configuration

For Kubernetes deployments, you can use ConfigMaps and Secrets:

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ipmi-config
data:
  IPMI_HOSTS: "server1:192.168.1.197,server2:192.168.1.198"
  IPMI_USER: "USER"
---
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ipmi-secret
type: Opaque
stringData:
  IPMI_PASSWORD: "PASSWORD"
```

## Testing Your Configuration

### 1. Check Service Health
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/health" -Method GET
```

### 2. List Available Servers
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/servers" -Method GET
```

### 3. Test IPMI Connectivity
```powershell
# For single server or default server
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/health" -Method GET

# For specific server in multi-server setup
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/health?server_id=server1" -Method GET
```

### 4. Check Power Status
```powershell
# Single server
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/power/status" -Method GET

# Specific server
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/power/status?server_id=dbadmin" -Method GET

# All servers
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/servers/status" -Method GET
```

## Troubleshooting

### Common Issues

1. **"IPMI service not initialized"**
   - Check that environment variables are set correctly
   - Verify IP addresses are reachable
   - Ensure credentials are correct

2. **"Server 'serverX' not found in configuration"**
   - Check the server name in your IPMI_HOSTS variable
   - Verify there are no spaces around server names

3. **"Command timed out"**
   - Check network connectivity to IPMI device
   - Verify IPMI device is responding
   - Check firewall settings

### Debug Commands

```powershell
# Check what servers are configured
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/servers" -Method GET

# Get detailed API documentation
Invoke-RestMethod -Uri "http://localhost:5000/api/v1/docs" -Method GET

# Check container logs
docker-compose logs ipmi-api-gateway
```

## Security Considerations

1. **Never commit passwords to version control**
2. **Use environment files for sensitive data:**
   ```bash
   # Create .env file (add to .gitignore)
   echo "IPMI_PASSWORD=your_secure_password" > .env
   ```

3. **For production, use secrets management:**
   - Docker Swarm: Use Docker secrets
   - Kubernetes: Use Secret objects
   - Cloud: Use cloud-native secret services

4. **Network security:**
   - Ensure IPMI network is isolated
   - Use VPN for remote access
   - Consider using SSH tunneling for additional security