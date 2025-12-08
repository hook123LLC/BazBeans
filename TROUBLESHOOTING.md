# BazBeans Troubleshooting Guide

> Solutions to common issues and diagnostic procedures for BazBeans clusters.

## 🔍 Quick Diagnosis

### Health Check Commands

```bash
# Check overall cluster health
bazbeans list-nodes

# Check specific node status
bazbeans status <node-id>

# Test Redis connectivity
redis-cli -h <redis-host> ping

# Check Redis for BazBeans data
redis-cli -h <redis-host> SMEMBERS bazbeans:nodes:all
```

## 🚨 Common Issues & Solutions

### Connection Issues

#### "Redis connection failed"
**Symptoms:**
- Agent fails to start with connection error
- CLI commands timeout
- No nodes appear in list

**Causes & Solutions:**

1. **Redis not running**
   ```bash
   # Check if Redis is running
   systemctl status redis-server  # Linux
   brew services list | grep redis  # macOS
   
   # Start Redis
   sudo systemctl start redis-server  # Linux
   brew services start redis  # macOS
   redis-server  # Direct start
   ```

2. **Wrong Redis URL**
   ```bash
   # Test connection
   redis-cli -h your-redis-host -p 6379 ping
   
   # Update configuration
   export BAZBEANS_REDIS_URL="redis://correct-host:6379/0"
   ```

3. **Firewall blocking Redis**
   ```bash
   # Check if port 6379 is open
   telnet redis-host 6379
   
   # Open firewall (Ubuntu example)
   sudo ufw allow 6379
   ```

4. **Network connectivity**
   ```bash
   # Test network path
   ping redis-host
   traceroute redis-host
   ```

### Agent Issues

#### "Node not appearing in active list"
**Symptoms:**
- Agent starts but node shows as inactive
- `bazbeans list-nodes` shows ✗ for your node

**Diagnostic Steps:**
```bash
# 1. Check if agent process is running
ps aux | grep agent

# 2. Check Redis for heartbeat
redis-cli GET "bazbeans:node:your-node-id:heartbeat"

# 3. Check agent logs
tail -f /var/log/yourapp-bazbeans.log  # systemd
# or check terminal where agent is running
```

**Solutions:**

1. **Incorrect node_id**
   ```python
   # In your agent script, ensure node_id is unique
   config.node_id = "dc1-server01"  # Must be unique across cluster
   ```

2. **Heartbeat configuration**
   ```python
   # Increase heartbeat TTL if network is slow
   config.heartbeat_ttl = 60  # seconds
   config.heartbeat_interval = 15  # seconds
   ```

3. **Redis permissions**
   ```bash
   # Check Redis auth if enabled
   redis-cli -a your-password ping
   ```

#### "Agent keeps freezing"
**Symptoms:**
- Node repeatedly freezes and unfreezes
- Health checks failing

**Common Causes:**

1. **Resource thresholds too low**
   ```python
   # Adjust thresholds in config
   config.cpu_threshold = 95  # Increase from default 90
   config.memory_threshold = 90  # Increase from default 85
   ```

2. **Custom health check failures**
   ```python
   # Add debugging to health checks
   @agent.health_check
   def check_database():
       try:
           result = db.is_connected()
           print(f"Database check: {result}")  # Debug output
           return result
       except Exception as e:
           print(f"Database check error: {e}")
           return False
   ```

3. **Docker container issues**
   ```bash
   # Check container status
   docker ps
   docker logs container-name
   
   # Restart containers if needed
   docker-compose restart
   ```

### CLI Issues

#### "bazbeans command not found"
**Symptoms:**
- Command not found after installation
- Permission denied errors

**Solutions:**

1. **Reinstall CLI**
   ```bash
   cd bazbeans/setup
   ./install.sh  # Linux/macOS
   # or
   .\install.ps1  # Windows
   ```

2. **Check PATH**
   ```bash
   # Check if bazbeans is in PATH
   which bazbeans
   echo $PATH | grep bazbeans
   
   # Add to PATH if needed
   export PATH="$PATH:$HOME/.local/bin"
   ```

3. **Use Python directly**
   ```bash
   python -m bazbeans.control_cli --help
   python -m bazbeans.control_cli list-nodes
   ```

#### "Permission denied" errors
**Symptoms:**
- Can't write configuration files
- Can't access Redis

**Solutions:**
```bash
# Fix file permissions
chmod +x ~/.local/bin/bazbeans
chmod 755 ~/.bazbeans/

# Check Redis permissions
redis-cli -h redis-host ACL WHOAMI
```

### Load Balancer Issues

#### "Nginx not updating"
**Symptoms:**
- Nodes freeze/unfreeze but Nginx doesn't change
- Upstream config not updating

**Diagnostic Steps:**
```bash
# 1. Check Nginx updater logs
tail -f /var/log/nginx-updater.log

# 2. Check Redis pub/sub
redis-cli PUBLISH bazbeans:lb_events '{"test": "message"}'

# 3. Test Nginx config
nginx -t
```

**Solutions:**

1. **Pub/sub channel mismatch**
   ```python
   # Ensure channel names match
   config.pubsub_channel = "bazbeans:lb_events"  # Must be same everywhere
   ```

2. **IP resolution issues**
   ```python
   # Test IP resolution manually
   from bazbeans.ip_resolvers import RedisIPResolver
   resolver = RedisIPResolver(redis_client)
   ip = resolver.resolve("your-node-id")
   print(f"Resolved IP: {ip}")
   ```

3. **Nginx permissions**
   ```bash
   # Check if Nginx can write config
   sudo -u nginx touch /etc/nginx/conf.d/test.conf
   sudo rm /etc/nginx/conf.d/test.conf
   ```

## 🔧 Advanced Diagnostics

### Redis State Analysis

```bash
# Check all BazBeans keys
redis-cli --scan --pattern "bazbeans:*"

# Monitor Redis activity
redis-cli MONITOR

# Check memory usage
redis-cli INFO memory

# Check connected clients
redis-cli CLIENT LIST
```

### Network Diagnostics

```bash
# Test Redis from each node
for node in node1 node2 node3; do
    echo "Testing from $node:"
    ssh $node "redis-cli -h redis-host ping"
done

# Check port accessibility
nmap -p 6379 redis-host

# Monitor network traffic
tcpdump -i any port 6379
```

### Performance Issues

```bash
# Check system resources
top
htop
iotop
df -h

# Check Redis performance
redis-cli --latency-history
redis-cli INFO stats

# Check agent performance
ps aux | grep agent
strace -p <agent-pid>
```

## 📋 Diagnostic Checklist

### When a Node is Misbehaving

- [ ] Agent process running? (`ps aux | grep agent`)
- [ ] Redis accessible? (`redis-cli ping`)
- [ ] Heartbeat present? (`redis-cli GET "bazbeans:node:id:heartbeat"`)
- [ ] System resources OK? (`top`, `df -h`)
- [ ] Network connectivity? (`ping redis-host`)
- [ ] Custom health checks passing? (check agent logs)
- [ ] Configuration correct? (review config file)

### When CLI Commands Fail

- [ ] CLI installed? (`which bazbeans`)
- [ ] Redis connection? (`redis-cli ping`)
- [ ] Configuration loaded? (`bazbeans --help`)
- [ ] Permissions OK? (`ls -la ~/.bazbeans/`)
- [ ] Network reachable? (`telnet redis-host 6379`)

### When Load Balancer Not Updating

- [ ] Nginx updater running? (`ps aux | grep nginx-updater`)
- [ ] Pub/sub working? (`redis-cli PUBLISH bazbeans:lb_events test`)
- [ ] IP resolution working? (check resolver logs)
- [ ] Nginx config valid? (`nginx -t`)
- [ ] File permissions OK? (`ls -la /etc/nginx/conf.d/`)

## 🆘 Getting Help

### Collect Diagnostic Information

```bash
# Create diagnostic bundle
mkdir bazbeans-diagnostics
cd bazbeans-diagnostics

# System info
uname -a > system-info.txt
python --version >> system-info.txt
redis-cli INFO server >> system-info.txt

# BazBeans state
bazbeans list-nodes > cluster-state.txt
redis-cli --scan --pattern "bazbeans:*" > redis-keys.txt

# Configuration
cat ~/.bazbeans/config.yaml > config.txt

# Logs (last 1000 lines)
journalctl -u yourapp-bazbeans --tail 1000 > agent.log
```

### When to Ask for Help

- **Critical Issues:** Cluster completely down, production outage
- **Persistent Issues:** Same problem recurring after restarts
- **Performance Issues:** Slow response times, high resource usage
- **Configuration Issues:** Can't figure out proper setup

### What to Include in Support Requests

1. **System Information**
   - OS version and architecture
   - Python version
   - Redis version
   - BazBeans version

2. **Configuration**
   - Redis connection details
   - Node configuration
   - Network topology

3. **Error Messages**
   - Full error output
   - Log files
   - Timestamps

4. **Steps to Reproduce**
   - What you were trying to do
   - Commands you ran
   - Expected vs actual behavior

## 📚 Additional Resources

- **Architecture:** [Architecture Guide](ARCHITECTURE.md)
- **Setup:** [CLI Setup Guide](SETUP-CLI.md)
- **Deployment:** [Agent Deployment Guide](AGENT-DEPLOYMENT.md)
- **Examples:** [Examples Folder](examples/)
- **Configuration:** [Configuration Reference](README.md#configuration)

---

**🎯 Goal:** Quickly identify and resolve common BazBeans issues  
**⏱️ Time to Resolution:** Most issues in 5-10 minutes with this guide