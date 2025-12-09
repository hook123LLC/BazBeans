# BazBeans CLI Setup Guide

> **Install the BazBeans command-line interface for managing your cluster**

This guide covers installing and setting up the BazBeans CLI tool for administrative control of your BazBeans cluster.

## 🚀 Auto-Installation (Recommended)

When you install BazBeans from PyPI using `pip install bazbeans`, the CLI is **automatically installed** for your operating system. No manual steps required!

- ✅ **Linux**: Automatically installs `bazbeans` command
- ✅ **macOS**: Automatically installs `bazbeans` command  
- ✅ **Windows**: Automatically installs `bazbeans.bat` and `bazbeans.ps1`

For detailed information about auto-installation, see the [Auto-Installation Guide](AUTO-INSTALLATION.md).

## 🛠️ Manual Installation

If you need to install the CLI manually or want to understand the process, continue with this guide.

## 🎯 What You'll Accomplish

After completing this guide, you will have:
- ✅ The `bazbeans` command installed on your system
- ✅ Configuration set up for your environment
- ✅ Ability to manage nodes across your cluster
- ✅ Working knowledge of essential CLI commands

## 📋 Prerequisites

### Required Software
- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Install Git](https://git-scm.com/downloads/)
- **Redis Server** - [Install Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/)

### System Access
- **Shell access** to your management workstation
- **Network access** to your Redis server
- **Write permissions** to install system-wide commands

## 🚀 Quick Start (2 minutes)

### Step 1: Get BazBeans

```bash
# Install BazBeans package
pip install bazbeans

# 🎉 The CLI is automatically installed for your operating system!
# You can now use 'bazbeans' commands immediately
```

### Step 2: Verify Installation (Optional)

> **Note:** With the new auto-installation feature, the CLI is automatically installed when you run `pip install bazbeans`. You can skip to Step 3 to verify.

If you want to install the CLI manually or need to re-install it:

#### 🐧 Ubuntu/Linux
```bash
cd setup
./install.sh
```

#### 🪟 Windows (PowerShell)
```powershell
cd setup
.\install.ps1
```

#### 🍎 macOS
```bash
cd setup
./install-macos.sh
```

### Step 3: Verify Installation

Choose your platform:

#### 🐧 Ubuntu/Linux
```bash
cd setup
./install.sh
```

#### 🪟 Windows (PowerShell)
```powershell
cd setup
.\install.ps1
```

#### 🍎 macOS
```bash
cd setup
./install-macos.sh
```

### Step 3: Verify Installation

```bash
# Test the command
bazbeans --help

# Should see the help output
bazbeans list-nodes --help
```

## ⚙️ Configuration

### Configuration Locations

BazBeans automatically looks for configuration in these locations (in order):

1. **Environment Variable:** `BAZBEANS_CONFIG`
2. **User Config:** `~/.bazbeans/config.yaml` (Linux/macOS) or `%APPDATA%\BazBeans\config.yaml` (Windows)
3. **System Config:** `/etc/bazbeans/config.yaml` (Linux) or `%ProgramData%\BazBeans\config.yaml` (Windows)
4. **Local Config:** `./bazbeans.yaml` (current directory)

### Creating Your First Configuration

Create a basic configuration file:

```bash
# Create config directory
mkdir -p ~/.bazbeans

# Create basic config
cat > ~/.bazbeans/config.yaml << 'EOF'
# BazBeans CLI Configuration
redis_url: "redis://localhost:6379/0"
data_center: "default"
node_port: 8000
cpu_threshold: 90
memory_threshold: 85
app_dir: "/opt/app"
compose_file: "docker-compose.yml"
EOF
```

### Production Configuration

For production use, create a more complete configuration:

```yaml
# Production BazBeans Configuration
redis_url: "redis://prod-redis.company.com:6379/0"
data_center: "us-east-1"
node_port: 8000

# Health thresholds
cpu_threshold: 85
memory_threshold: 80
heartbeat_ttl: 60

# Application settings
app_dir: "/opt/myapp"
compose_file: "docker-compose.yml"

# Security
allowed_exec_prefixes:
  - "docker"
  - "systemctl"
  - "ls"
  - "cat"
  - "grep"
```

### Environment Variable Overrides

You can override any configuration setting with environment variables:

```bash
# Quick override for different environments
export BAZBEANS_REDIS_URL="redis://staging-redis:6379/0"
bazbeans list-nodes

# Use different config file
export BAZBEANS_CONFIG="/path/to/staging.yaml"
bazbeans list-nodes

# Override specific settings
export BAZBEANS_DATA_CENTER="staging"
export BAZBEANS_CPU_THRESHOLD="95"
bazbeans list-nodes
```

## 🎮 Essential Commands

### Basic Node Management

```bash
# 📋 List all nodes with health status
bazbeans list-nodes

# 📊 Get detailed information about a node
bazbeans status web-server-01

# ❄️ Freeze a node (remove from load balancer)
bazbeans freeze web-server-01 --reason "maintenance"

# 🔥 Unfreeze a node (add back to load balancer)
bazbeans unfreeze web-server-01
```

### Service Control

```bash
# ▶️ Start services on a node
bazbeans start web-server-01

# ⏹️ Stop services on a node
bazbeans stop web-server-01

# 🔄 Restart services on a node
bazbeans restart web-server-01

# 🚀 Rolling update across datacenter
bazbeans update --dc us-east-1
```

### Operations and Debugging

```bash
# 💻 Execute shell command on node
bazbeans exec web-server-01 "docker ps"

# 📤 Deploy file to node
bazbeans deploy-file web-server-01 ./config.yaml /opt/app/config.yaml

# 🧹 Clean up dead nodes from cluster
bazbeans cleanup

# 🔍 Check cluster health
bazbeans list-nodes | grep -E "✗|⚠"
```

### Data Center Management

```bash
# 🏢 Set default data center for commands
bazbeans --dc us-east-1 list-nodes

# 🌍 Update all nodes in a datacenter
bazbeans --dc us-east-1 update

# 📊 Get datacenter summary
bazbeans --dc us-east-1 list-nodes | wc -l
```

## 🎯 Common Workflows

### Environment Switching

```bash
# 🏭 Production environment
export BAZBEANS_CONFIG="$HOME/.bazbeans/prod.yaml"
bazbeans list-nodes

# 🧪 Development environment
export BAZBEANS_CONFIG="$HOME/.bazbeans/dev.yaml"
bazbeans list-nodes

# 🔧 Quick switch function
bb-env() {
    case $1 in
        prod) export BAZBEANS_CONFIG="$HOME/.bazbeans/prod.yaml" ;;
        dev)  export BAZBEANS_CONFIG="$HOME/.bazbeans/dev.yaml" ;;
        *) echo "Usage: bb-env [prod|dev]" ;;
    esac
    echo "BazBeans config: $BAZBEANS_CONFIG"
}
```

### Maintenance Workflows

```bash
# 🛠️ Safe maintenance procedure
maintenance-mode() {
    local node=$1
    echo "Putting $node into maintenance mode..."
    
    # Freeze node
    bazbeans freeze $node --reason "scheduled maintenance"
    
    # Wait for load balancer to update
    sleep 10
    
    # Stop services
    bazbeans stop $node
    
    echo "$node is now in maintenance mode"
}

# 🔄 Recovery procedure
recovery-mode() {
    local node=$1
    echo "Bringing $node back online..."
    
    # Start services
    bazbeans start $node
    
    # Wait for services to be ready
    sleep 30
    
    # Unfreeze node
    bazbeans unfreeze $node
    
    echo "$node is back online"
}
```

### Monitoring and Alerting

```bash
# 📊 Health check script
health-check() {
    local unhealthy=$(bazbeans list-nodes | grep -E "✗" | wc -l)
    
    if [ $unhealthy -gt 0 ]; then
        echo "🚨 ALERT: $unhealthy nodes are unhealthy"
        bazbeans list-nodes | grep -E "✗"
        return 1
    else
        echo "✅ All nodes are healthy"
        return 0
    fi
}

# 📈 Cluster statistics
cluster-stats() {
    echo "📊 Cluster Statistics:"
    echo "Total nodes: $(bazbeans list-nodes | wc -l)"
    echo "Active nodes: $(bazbeans list-nodes | grep -E "✓" | wc -l)"
    echo "Frozen nodes: $(bazbeans list-nodes | grep -E "✗" | wc -l)"
}
```

### Integration Examples

#### 🤖 Ansible Integration
```yaml
# playbook.yml
- name: Update application with BazBeans coordination
  hosts: webservers
  tasks:
    - name: Freeze node in load balancer
      command: bazbeans freeze {{ inventory_hostname }} --reason "Ansible deployment"
    
    - name: Deploy application
      # Your deployment tasks here
    
    - name: Unfreeze node
      command: bazbeans unfreeze {{ inventory_hostname }}
```

#### ☸️ Kubernetes Integration
```bash
# Update Kubernetes-managed nodes
kubectl-get-nodes() {
    kubectl get pods -l app=myapp -o jsonpath='{.items[*].spec.nodeName}' | tr ' ' '\n'
}

k8s-update() {
    for node in $(kubectl-get-nodes); do
        echo "Updating Kubernetes node: $node"
        bazbeans restart $node
    done
}
```

## Troubleshooting

### Command Not Found

```bash
# Check if bazbeans is installed
which bazbeans

# Check PATH
echo $PATH | grep bazbeans

# Reinstall if needed
cd bazbeans/setup
./install.sh
```

### Connection Errors

```bash
# Test Redis connection
redis-cli -h your-redis-host ping

# Check configuration
bazbeans --help | grep -i config

# Override Redis URL
BAZBEANS_REDIS_URL="redis://correct-host:6379/0" bazbeans list-nodes
```

### Permission Errors

```bash
# Check file permissions
ls -la ~/.bazbeans/
ls -la ~/.local/bin/bazbeans

# Fix permissions
chmod +x ~/.local/bin/bazbeans
```

## Uninstallation

### Ubuntu/Linux

```bash
bazbeans-uninstall
```

### Windows

```powershell
.\uninstall-bazbeans.ps1
```

### macOS

```bash
bazbeans-uninstall
```

## Next Steps

After setup:

1. [Read the Architecture Guide](ARCHITECTURE.md) to understand the system
2. [Check the Deployment Guide](DEPLOYMENT.md) for production deployment
3. [See Examples](examples/) for integration patterns
4. [Review the API Documentation](README.md#advanced-usage) for custom development

## Getting Help

- Use `bazbeans --help` for command help
- Check the [setup documentation](setup/README.md) for platform-specific issues
- Review the [troubleshooting section](DEPLOYMENT.md#monitoring-and-troubleshooting) for common problems