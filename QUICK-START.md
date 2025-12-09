# BazBeans Quick Start Guide

> Get BazBeans running in 5 minutes with this step-by-step guide.

## 🎯 What You'll Accomplish

In this quick start, you will:
- ✅ Set up a Redis server for coordination
- ✅ Install the BazBeans CLI
- ✅ Run your first node agent
- ✅ Manage your cluster with basic commands

## 📋 Prerequisites (2 minutes)

### Required Software
- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Redis Server** - [Install Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/)
- **Git** - [Install Git](https://git-scm.com/downloads)

### System Requirements
- **Memory:** 512MB minimum per node
- **Disk:** 100MB free space
- **Network:** Port 6379 (Redis) accessible between nodes

### Quick Install Commands

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip redis-server git
```

**macOS:**
```bash
brew install python redis git
```

**Windows:**
```powershell
# Install Python from python.org
# Install Redis for Windows or use Docker
# Install Git from git-scm.com
```

## 🚀 Step 1: Start Redis (30 seconds)

```bash
# Start Redis server
redis-server

# In another terminal, verify it's running
redis-cli ping
# Should return: PONG
```

## 📦 Step 2: Install BazBeans CLI (1 minute)

```bash
# Install BazBeans package
pip install bazbeans

# 🎉 The CLI is automatically installed for your OS!
# You can now use 'bazbeans' commands immediately
```

> **New Feature:** BazBeans now automatically installs the CLI for your operating system when you run `pip install bazbeans`. No manual setup required!

## 🤖 Step 3: Run Your First Agent (1 minute)

Create a simple agent file `my_agent.py`:

```python
#!/usr/bin/env python3
from bazbeans import BazBeansConfig, NodeAgent

# Create configuration
config = BazBeansConfig()
config.redis_url = "redis://localhost:6379/0"
config.node_id = "my-first-node"

# Create and run agent
agent = NodeAgent(config)
print("Starting agent...")
agent.run()  # This will run forever
```

Run your agent:
```bash
python my_agent.py
```

## 🎮 Step 4: Manage Your Cluster (1 minute)

In a new terminal, use the CLI to manage your node:

```bash
# List all nodes
bazbeans list-nodes

# Check your node's status
bazbeans status my-first-node

# Freeze your node (remove from load balancer)
bazbeans freeze my-first-node --reason "testing"

# Unfreeze your node
bazbeans unfreeze my-first-node
```

## 🎉 Congratulations!

You now have:
- ✅ A running BazBeans cluster
- ✅ A managed node agent
- ✅ CLI control over your cluster

## 🔧 What's Next?

### For Production Deployment
- Read the [Agent Deployment Guide](AGENT-DEPLOYMENT.md)
- Set up proper security and authentication
- Configure load balancer integration

### For Advanced Features
- Add custom health checks
- Create command plugins
- Set up Nginx integration

### For Understanding the System
- Read the [Architecture Guide](ARCHITECTURE.md)
- Check the [Examples](examples/) folder
- Review the [Configuration Reference](README.md#configuration)

## 🆘 Common Issues

### "Redis connection failed"
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server
```

### "bazbeans command not found"
```bash
# With auto-installation, this should work automatically after pip install
# If not, try reinstalling:
pip install bazbeans

# Or use Python directly
python -m bazbeans.control_cli --help

# For manual CLI installation (if needed)
cd setup
./install.sh
```

### "Node not appearing in list"
```bash
# Check if agent is running
ps aux | grep my_agent.py

# Check Redis for node
redis-cli SMEMBERS bazbeans:nodes:all
```

## 📚 Need More Help?

- **Troubleshooting:** [Troubleshooting Guide](TROUBLESHOOTING.md)
- **Full Documentation:** [README.md](README.md)
- **Examples:** [Examples Folder](examples/)
- **Architecture:** [Architecture Guide](ARCHITECTURE.md)

---

**⏱️ Total Time:** ~5 minutes  
**🎯 Goal:** Working BazBeans cluster with CLI management