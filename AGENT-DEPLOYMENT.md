# BazBeans Agent Deployment Guide

This guide covers the complete deployment process for BazBeans Agents in your environment.

For installation instructions, see the [CLI Setup Guide](SETUP-CLI.md).

## Table of Contents

1. [System Prerequisites](#system-prerequisites)
2. [Building Your Configuration](#building-your-configuration)
3. [Creating Your Agent Script](#creating-your-agent-script)
4. [VM Deployment](#vm-deployment)
5. [Updating BazBeans](#updating-bazbeans)
6. [Updating Your Agent Script](#updating-your-agent-script)

## System Prerequisites

### Redis Server

BazBeans requires a Redis server for shared state management:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify installation
redis-cli ping
# Should return: PONG
```

**Redis Configuration for Production:**

Edit `/etc/redis/redis.conf`:

```conf
# Require password (uncomment and set)
requirepass your-secure-password

# Bind to specific interfaces
bind 10.0.1.10 127.0.0.1

# Enable TLS (optional but recommended)
tls-port 6380
tls-cert-file /path/to/redis.crt
tls-key-file /path/to/redis.key
```

Restart Redis after changes:
```bash
sudo systemctl restart redis-server
```

### Python Requirements

```bash
# Python 3.8+ required
python3 --version

# Install pip if not present
sudo apt install python3-pip

# Create virtual environment (recommended)
python3 -m venv /opt/bazbeans
source /opt/bazbeans/bin/activate

# Install BazBeans dependencies
pip install -r bazbeans/requirements.txt
```

### Docker (Optional)

If using the DockerComposeCommands plugin:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

## Building Your Configuration

### Step 1: Identify Your Configuration Sources

Determine where your configuration comes from:
- Environment variables
- Configuration files
- Service discovery systems
- Hardcoded values

### Step 2: Create Configuration Mapping

Create a Python script that maps your configuration to BazBeans:

```python
from bazbeans import BazBeansConfig

def create_config() -> BazBeansConfig:
    """Create BazBeansConfig from your configuration sources."""
    config = BazBeansConfig()
    
    # Map your configuration
    config.redis_url = os.environ.get("MY_REDIS_URL", config.redis_url)
    config.node_id = os.environ.get("MY_NODE_ID", config.node_id)
    config.data_center = os.environ.get("MY_DATA_CENTER", config.data_center)
    
    # Adjust thresholds based on environment
    if os.environ.get("ENVIRONMENT") == "production":
        config.heartbeat_ttl = 60
        config.cpu_threshold = 85
        config.memory_threshold = 80
    
    return config
```

### Step 3: Define Your Health Checks

Identify what makes your application healthy:

```python
def register_health_checks(agent):
    """Register custom health checks for your application."""
    
    @agent.health_check
    def check_database():
        """Check database connectivity."""
        return database.is_connected()
    
    @agent.health_check
    def check_api_endpoint():
        """Check if API is responding."""
        try:
            r = requests.get("http://localhost:8080/health", timeout=5)
            return r.status_code == 200
        except:
            return False
    
    @agent.health_check
    def check_disk_space():
        """Check available disk space."""
        return psutil.disk_usage('/app').percent < 90
```

### Step 4: Define Custom Commands (Optional)

Add commands specific to your application:

```python
def register_custom_commands(agent):
    """Register custom command handlers."""
    
    @agent.command_handler("backup")
    def handle_backup(command):
        """Perform application backup."""
        # Your backup logic
        return {"status": "backup_started", "timestamp": time.time()}
    
    @agent.command_handler("reload_config")
    def handle_reload(command):
        """Reload application configuration."""
        # Your reload logic
        return {"status": "config_reloaded"}
```

## Creating Your Agent Script

### Basic Template

```python
#!/usr/bin/env python3
"""
Your Application BazBeans Agent
"""

import os
import sys
from pathlib import Path

# Add bazbeans to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bazbeans import BazBeansConfig, NodeAgent, DockerComposeCommands

def create_config():
    """Create and return BazBeansConfig."""
    # Your configuration mapping here
    pass

def register_plugins(agent):
    """Register plugins with the agent."""
    # Register docker-compose if needed
    agent.register_command_plugin(DockerComposeCommands(agent.config))
    
    # Register custom health checks
    register_health_checks(agent)
    
    # Register custom commands
    register_custom_commands(agent)

def main():
    """Main entry point."""
    print("Starting Your Application BazBeans Agent...")
    
    # Create configuration
    config = create_config()
    
    # Validate
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    # Create agent
    agent = NodeAgent(config)
    
    # Register plugins
    register_plugins(agent)
    
    # Run agent
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Agent error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## VM Deployment

### Step 1: Provision VM

1. Create VM with your cloud provider
2. Ensure network access to Redis server
3. Install system prerequisites (see above)

### Step 2: Deploy Application

```bash
# Create application directory
sudo mkdir -p /opt/yourapp
sudo chown $USER:$USER /opt/yourapp

# Copy your application code
scp -r ./yourapp user@vm:/opt/yourapp/

# Copy bazbeans
scp -r ./bazbeans user@vm:/opt/
```

### Step 3: Create Systemd Service

Create `/etc/systemd/system/yourapp-bazbeans.service`:

```ini
[Unit]
Description=Your Application BazBeans Agent
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=yourapp
Group=yourapp
WorkingDirectory=/opt/yourapp
Environment="PATH=/opt/yourapp/venv/bin"
ExecStart=/opt/yourapp/venv/bin/python /opt/yourapp/agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Step 4: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable yourapp-bazbeans

# Start service
sudo systemctl start yourapp-bazbeans

# Check status
sudo systemctl status yourapp-bazbeans

# View logs
sudo journalctl -u yourapp-bazbeans -f
```

### Step 5: Verify Registration

```bash
# Check if node registered
redis-cli -h your-redis-host SMEMBERS bazbeans:nodes:all

# Check if node is active
redis-cli -h your-redis-host SMEMBERS bazbeans:nodes:active

# Check heartbeat
redis-cli -h your-redis-host GET "bazbeans:node:your-node-id:heartbeat"
```

## Updating BazBeans

### Method 1: Git Update (Recommended)

```bash
# On the VM
cd /opt/bazbeans

# Pull latest changes
git pull origin main

# Update dependencies
source /opt/yourapp/venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart yourapp-bazbeans
```

### Method 2: Package Update

```bash
# Download new version
wget https://github.com/yourorg/bazbeans/archive/v1.1.0.tar.gz

# Extract and replace
cd /opt
sudo rm -rf bazbeans.old
sudo mv bazbeans bazbeans.old
sudo tar -xzf v1.1.0.tar.gz
sudo mv bazbeans-1.1.0 bazbeans
sudo chown -R yourapp:yourapp bazbeans

# Update dependencies
source /opt/yourapp/venv/bin/activate
pip install -r /opt/bazbeans/requirements.txt

# Restart service
sudo systemctl restart yourapp-bazbeans
```

### Method 3: Rolling Update

Use the control CLI for rolling updates:

```bash
# Update all nodes in datacenter
python -m bazbeans.control_cli \
    --redis-url "redis://your-redis:6379/0" \
    update --dc dc1

# Update specific node
python -m bazbeans.control_cli \
    --redis-url "redis://your-redis:6379/0" \
    send_command node-01 '{"type": "update", "wait_seconds": 10}'
```

## Updating Your Agent Script

### Method 1: Direct Deployment

```bash
# On your development machine
scp ./agent.py user@vm:/opt/yourapp/agent.py.new

# On the VM
sudo systemctl stop yourapp-bazbeans
cd /opt/yourapp
mv agent.py agent.py.backup
mv agent.py.new agent.py
sudo systemctl start yourapp-bazbeans

# Verify
sudo systemctl status yourapp-bazbeans
```

### Method 2: Git Deployment

```bash
# Initialize git on VM if not already done
cd /opt/yourapp
git init
git remote add origin https://github.com/yourorg/yourapp.git

# Pull latest agent
git pull origin main

# Restart service
sudo systemctl restart yourapp-bazbeans
```

### Method 3: Using Deploy Command

If you have the deploy_file command registered:

```bash
# Deploy new agent script
python -m bazbeans.control_cli \
    --redis-url "redis://your-redis:6379/0" \
    deploy-file node-01 ./agent.py /opt/yourapp/agent.py

# Trigger restart
python -m bazbeans.control_cli \
    --redis-url "redis://your-redis:6379/0" \
    send_command node-01 '{"type": "restart"}'
```

## Monitoring and Troubleshooting

### Check Logs

```bash
# Systemd logs
sudo journalctl -u yourapp-bazbeans -f

# BazBeans logs in Redis
redis-cli -h your-redis-host HGETALL "bazbeans:node:node-id:status"

# Check active nodes
redis-cli -h your-redis-host SMEMBERS bazbeans:nodes:active
```

### Common Issues

1. **Node not appearing in active list**
   - Check Redis connectivity
   - Verify node_id is unique
   - Check firewall rules

2. **Health checks failing**
   - Verify health check endpoints
   - Check resource thresholds
   - Review agent logs

3. **Nginx not updating**
   - Verify pub/sub channel matches
   - Check Nginx updater logs
   - Test Nginx config syntax

## Security Best Practices

1. **Redis Security**
   - Use AUTH passwords
   - Enable TLS in production
   - Restrict network access

2. **Agent Security**
   - Run as non-root user
   - Use virtual environment
   - Validate file paths

3. **Network Security**
   - Use VPN or private networks
   - Implement firewall rules
   - Monitor for unauthorized access

## Backup and Recovery

### Backup Redis Data

```bash
# Create backup
redis-cli --rdb /backup/redis-backup-$(date +%Y%m%d).rdb

# Or use BGSAVE for non-blocking backup
redis-cli BGSAVE
```

### Recover from Backup

```bash
# Stop Redis
sudo systemctl stop redis-server

# Replace RDB file
sudo cp /backup/redis-backup-20240115.rdb /var/lib/redis/dump.rdb
sudo chown redis:redis /var/lib/redis/dump.rdb

# Start Redis
sudo systemctl start redis-server
```

### Disaster Recovery

1. Have multiple Redis instances (master/slave)
2. Document all configuration
3. Test recovery procedures regularly
4. Monitor system health continuously