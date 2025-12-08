#!/usr/bin/env python3
"""
Web Server BazBeans Agent Example

This example shows how to integrate BazBeans with a web application.
Perfect for FastAPI, Django, Flask, or any HTTP-based service.

What this example demonstrates:
- Web application health checks
- HTTP endpoint monitoring
- Docker-compose integration
- Load balancer coordination
- Service management commands

Prerequisites:
- Redis server running
- BazBeans installed
- Web application on port 8000 (or modify port in config)

Usage:
    python web_server_agent.py
"""

import sys
import time
import requests
from pathlib import Path

# Add bazbeans to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bazbeans import BazBeansConfig, NodeAgent, DockerComposeCommands


def main():
    """Run a web server agent with comprehensive monitoring."""
    print("🌐 Starting Web Server BazBeans Agent...")
    
    # Create web server configuration
    config = BazBeansConfig()
    
    # Web server specific settings
    config.redis_url = "redis://localhost:6379/0"
    config.node_id = "web-server-01"
    config.data_center = "us-east-1"
    config.node_port = 8000  # Your web app port
    config.app_dir = "/opt/webapp"  # Where your docker-compose.yml is
    config.compose_file = "docker-compose.yml"
    
    # Health thresholds for web servers
    config.cpu_threshold = 85  # Web servers can handle higher CPU
    config.memory_threshold = 80
    config.heartbeat_ttl = 30
    config.heartbeat_interval = 10
    
    print(f"📋 Web Server Configuration:")
    print(f"   Node ID: {config.node_id}")
    print(f"   Data Center: {config.data_center}")
    print(f"   App Port: {config.node_port}")
    print(f"   App Directory: {config.app_dir}")
    print(f"   CPU Threshold: {config.cpu_threshold}%")
    print(f"   Memory Threshold: {config.memory_threshold}%")
    
    # Validate configuration
    try:
        config.validate()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Create agent
    agent = NodeAgent(config)
    
    # Register Docker-compose commands for service management
    agent.register_command_plugin(DockerComposeCommands(config))
    print("🐳 Registered Docker-compose commands")
    
    # Add web server specific health checks
    
    @agent.health_check
    def check_web_health():
        """Check if the web application is responding."""
        try:
            url = f"http://localhost:{config.node_port}/health"
            response = requests.get(url, timeout=5)
            healthy = response.status_code == 200
            print(f"🌐 Web health check: {response.status_code}")
            return healthy
        except requests.exceptions.RequestException as e:
            print(f"❌ Web health check failed: {e}")
            return False
    
    @agent.health_check
    def check_web_response_time():
        """Check if web response time is acceptable."""
        try:
            start_time = time.time()
            url = f"http://localhost:{config.node_port}/health"
            response = requests.get(url, timeout=5)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            print(f"⚡ Response time: {response_time:.0f}ms")
            return response_time < 2000  # Require response under 2 seconds
        except:
            return False
    
    @agent.health_check
    def check_disk_space():
        """Check disk space for logs and uploads."""
        import psutil
        disk_usage = psutil.disk_usage(config.app_dir).percent
        print(f"💾 Disk usage: {disk_usage}%")
        return disk_usage < 90
    
    @agent.health_check
    def check_database_connection():
        """Check if database is accessible (if applicable)."""
        try:
            # Example: Check if database port is open
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 5432))  # PostgreSQL
            sock.close()
            
            db_healthy = result == 0
            print(f"🗄️ Database connection: {'OK' if db_healthy else 'FAILED'}")
            return db_healthy
        except:
            # If no database, return True (not required)
            print("🗄️ Database: Not configured")
            return True
    
    # Add web server specific command handlers
    
    @agent.command_handler("deploy")
    def handle_deploy(command):
        """Handle deployment with zero-downtime."""
        print("🚀 Starting deployment...")
        
        # Pull latest images
        pull_result = agent.command_handlers["pull"]({})
        
        if not pull_result.get("success"):
            return {"success": False, "error": "Failed to pull images"}
        
        # Perform rolling restart
        restart_result = agent.command_handlers["restart"]({})
        
        # Wait and verify health
        time.sleep(10)
        
        # Check if web app is healthy
        try:
            response = requests.get(f"http://localhost:{config.node_port}/health", timeout=5)
            healthy = response.status_code == 200
        except:
            healthy = False
        
        return {
            "success": healthy,
            "message": "Deployment completed" if healthy else "Deployment failed - health check failed",
            "pull_result": pull_result,
            "restart_result": restart_result
        }
    
    @agent.command_handler("clear_cache")
    def handle_clear_cache(command):
        """Clear application cache."""
        print("🧹 Clearing cache...")
        
        try:
            # Example: Clear Redis cache
            response = requests.post(f"http://localhost:{config.node_port}/admin/clear-cache", timeout=10)
            success = response.status_code == 200
            
            return {
                "success": success,
                "message": "Cache cleared" if success else "Failed to clear cache"
            }
        except:
            return {"success": False, "error": "Cache clear endpoint not available"}
    
    @agent.command_handler("get_metrics")
    def handle_get_metrics(command):
        """Get application metrics."""
        try:
            response = requests.get(f"http://localhost:{config.node_port}/metrics", timeout=5)
            if response.status_code == 200:
                return {
                    "success": True,
                    "metrics": response.json()
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except:
            return {"success": False, "error": "Metrics endpoint not available"}
    
    @agent.command_handler("backup")
    def handle_backup(command):
        """Create application backup."""
        print("💾 Creating backup...")
        
        try:
            # Example: Trigger backup endpoint
            response = requests.post(f"http://localhost:{config.node_port}/admin/backup", timeout=30)
            success = response.status_code == 200
            
            return {
                "success": success,
                "message": "Backup started" if success else "Backup failed",
                "backup_id": response.json().get("backup_id") if success else None
            }
        except:
            return {"success": False, "error": "Backup endpoint not available"}
    
    print("🔄 Starting web server agent...")
    print("💡 Available commands:")
    print("   - bazbeans freeze web-server-01")
    print("   - bazbeans unfreeze web-server-01")
    print("   - bazbeans start web-server-01")
    print("   - bazbeans stop web-server-01")
    print("   - bazbeans restart web-server-01")
    print("   - bazbeans exec web-server-01 deploy")
    print("   - bazbeans exec web-server-01 clear_cache")
    print("   - bazbeans exec web-server-01 get_metrics")
    print("   - bazbeans exec web-server-01 backup")
    print("💡 Press Ctrl+C to stop")
    
    try:
        # Run the agent
        agent.run()
    except KeyboardInterrupt:
        print("\n👋 Shutting down Web Server Agent...")
    except Exception as e:
        print(f"❌ Agent error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()