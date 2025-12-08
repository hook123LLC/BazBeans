# BazBeans Examples

This folder contains integration examples and sample configurations for different use cases.

## 📁 Available Examples

### 🎯 **Basic Examples**
- **[simple_agent.py](simple_agent.py)** - Minimal agent setup for testing
- **[web_server_agent.py](web_server_agent.py)** - Web application with health checks

### 🏢 **Production Examples**
- *See [For Future Consideration](#for-future-consideration) for plugin examples*

### 🔌 **Plugin Examples**
- *See [For Future Consideration](#for-future-consideration) for plugin examples*

### 🌐 **Load Balancer Examples**
- *See [For Future Consideration](#for-future-consideration) for load balancer examples*

## 🚀 Quick Start with Examples

### 1. Try the Simple Agent
```bash
cd examples
python simple_agent.py
```

### 2. Test Web Server Example
```bash
cd examples
python web_server_agent.py
```

### 3. Explore Production Integration
```bash
cd examples
# Review hook123_agent.py for real-world patterns
cat hook123_agent.py
```

## 📋 Example Categories

### By Use Case

#### 🌐 Web Applications
- FastAPI/Django/Flask applications
- Health check endpoints
- Load balancer integration
- Rolling updates

#### 📦 Microservices
- Docker-compose integration
- Service discovery
- Inter-service communication
- Container health monitoring

#### 🗄️ Database Servers
- Replication monitoring
- Query performance checks
- Backup coordination
- Failover handling

#### 🏢 Enterprise
- Multi-datacenter deployment
- Security integration
- Custom command handlers
- Monitoring integration

### By Complexity

#### 🟢 Beginner (5-10 lines)
- `simple_agent.py` - Basic agent setup

#### 🟡 Intermediate (20-50 lines)
- `web_server_agent.py` - Web server with health checks

#### 🔴 Advanced (100+ lines)
- `hook123_agent.py` - Production integration

#### 🟠 Future Examples
- *See [For Future Consideration](#for-future-consideration) for additional examples*

## 🛠️ Running Examples

### Prerequisites
```bash
# Install BazBeans
pip install -r ../bazbeans/requirements.txt

# Start Redis
redis-server
```

### Basic Setup
```bash
# Clone and setup
git clone https://github.com/yourorg/bazbeans.git
cd bazbeans/examples

# Install dependencies
pip install -r requirements.txt

# Run example
python simple_agent.py
```

### Configuration
```bash
# Copy example config
cp config.example.yaml config.yaml

# Edit for your environment
nano config.yaml

# Run with config
BAZBEANS_CONFIG=config.yaml python web_server_agent.py
```

## 📚 Learning Path

### 1. Start Here
1. **[simple_agent.py](simple_agent.py)** - Understand basic agent

### 2. Build Skills
1. **[web_server_agent.py](web_server_agent.py)** - Real application with health checks

### 3. Production Ready
1. **[hook123_agent.py](hook123_agent.py)** - Study real integration patterns

### 4. Expand Your Knowledge
- *See [For Future Consideration](#for-future-consideration) for additional learning examples*

## 🔧 Customization

### Adapting Examples

1. **Copy the example**
   ```bash
   cp web_server_agent.py my_app_agent.py
   ```

2. **Modify configuration**
   ```python
   config.node_id = "my-app-server"
   config.app_dir = "/opt/myapp"
   ```

3. **Add custom health checks**
   ```python
   @agent.health_check
   def check_my_app():
       # Your custom logic
       return my_app.is_healthy()
   ```

4. **Test your changes**
   ```bash
   python my_app_agent.py
   ```

### Best Practices

- ✅ Start with simple examples
- ✅ Test in development first
- ✅ Add logging for debugging
- ✅ Use environment variables for config
- ✅ Implement proper error handling
- ✅ Monitor resource usage

## 🆘 Troubleshooting

### Common Issues

**Agent not starting:**
```bash
# Check Redis connection
redis-cli ping

# Verify configuration
python -c "from bazbeans import BazBeansConfig; print(BazBeansConfig().validate())"
```

**Health checks failing:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Check logs
tail -f /var/log/bazbeans.log
```

**Load balancer not updating:**
```bash
# Check Nginx config
nginx -t

# Test pub/sub
redis-cli PUBLISH bazbeans:lb_events '{"test": "message"}'
```

### Getting Help

- **[Troubleshooting Guide](../bazbeans/TROUBLESHOOTING.md)** - Common solutions
- **[Architecture Guide](../bazbeans/ARCHITECTURE.md)** - System understanding
- **GitHub Issues** - Report problems with examples

## 🤝 Contributing

We welcome contributions to the examples! Please:

1. **Follow the patterns** - Use existing examples as templates
2. **Add documentation** - Explain what your example does
3. **Include requirements** - List any dependencies
4. **Test thoroughly** - Ensure examples work as documented
5. **Use clear naming** - Make file names descriptive

### Example Template
```python
#!/usr/bin/env python3
"""
Example: [Brief description]

This example demonstrates:
- [Feature 1]
- [Feature 2]
- [Feature 3]

Prerequisites:
- [Software 1]
- [Software 2]

Usage:
    python this_example.py
"""

# [Your code here]
```

## 🗂️ For Future Consideration

> **Note:** These examples are planned for future development but are not yet implemented.

### 🎯 **Additional Basic Examples**
- **[database_agent.py](database_agent.py)** - Database server monitoring with replication checks
- **[minimal_config.py](minimal_config.py)** - Configuration-only example
- **[health_check_basic.py](health_check_basic.py)** - Simple health check implementations

### 🏢 **Additional Production Examples**
- **[microservices_cluster.py](microservices_cluster.py)** - Multi-service deployment orchestration
- **[enterprise_setup.py](enterprise_setup.py)** - Multi-datacenter configuration and scaling

### 🔌 **Plugin Examples**
- **[custom_health_checks.py](custom_health_checks.py)** - Advanced health monitoring patterns
- **[custom_commands.py](custom_commands.py)** - Business logic integration examples
- **[ip_resolution_strategies.py](ip_resolution_strategies.py)** - Network configuration patterns

### 🌐 **Load Balancer Examples**
- **[nginx_integration.py](nginx_integration.py)** - Nginx upstream management and configuration
- **[ha_integration.py](ha_integration.py)** - High Availability setup patterns
- **[cloud_lb_integration.py](cloud_lb_integration.py)** - Cloud load balancer integration

### 📚 **Additional Learning Examples**
- **Configuration Management** - Environment-specific configuration patterns
- **Security Integration** - Authentication and authorization examples
- **Monitoring Integration** - Prometheus, Grafana, and other monitoring tools
- **Container Orchestration** - Kubernetes and Docker Swarm patterns
- **Testing Patterns** - Unit and integration testing for BazBeans agents

---

**🎯 Goal:** Provide working examples for every common use case  
**📈 Difficulty:** From beginner to advanced  
**🔄 Updates:** Examples updated with each release