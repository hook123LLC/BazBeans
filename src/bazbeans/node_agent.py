"""
BazBeans Node Agent

The agent that runs on each node, handling health checks,
command processing, and load balancer notifications.
"""

import json
import logging
import os
import psutil
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional

try:
    import docker
except ImportError:
    docker = None

from .config import BazBeansConfig
from .node_pool import NodePool
from .pubsub import LoadBalancerNotifier


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NodeAgent:
    """
    Agent that runs on each node for self-management and command handling.
    """
    
    def __init__(self, config: BazBeansConfig):
        """
        Initialize node agent.
        
        Args:
            config: BazBeans configuration
        """
        self.config = config
        self.config.validate()
        
        # Initialize components
        self.pool = NodePool(config)
        self.notifier = LoadBalancerNotifier(config, self.pool)
        
        # State
        self.is_active = True
        self.is_frozen = False
        self.running = False
        
        # Pluggable components
        self.health_checks: List[Callable[[], bool]] = []
        self.command_handlers: Dict[str, Callable] = {}
        
        # Docker client for container checks
        if docker:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                logger.warning(f"Docker not available: {e}")
                self.docker_client = None
        else:
            logger.warning("Docker module not available - container checks disabled")
            self.docker_client = None
        
        # Register built-in command handlers
        self._register_builtin_handlers()
    
    def _register_builtin_handlers(self) -> None:
        """Register built-in command handlers."""
        self.command_handlers.update({
            "freeze": self._cmd_freeze,
            "unfreeze": self._cmd_unfreeze,
            "exec": self._cmd_exec,
            "deploy_file": self._cmd_deploy_file,
            "health_check": self._cmd_health_check,
        })
    
    def health_check(self, func: Callable[[], bool]) -> None:
        """
        Decorator to register a health check.
        
        Args:
            func: Function that returns True if healthy, False otherwise
        """
        self.health_checks.append(func)
        return func
    
    def command_handler(self, command_name: str) -> Callable:
        """
        Decorator to register a command handler.
        
        Args:
            command_name: Name of command to handle
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Callable:
            self.command_handlers[command_name] = func
            return func
        return decorator
    
    def register_command_plugin(self, plugin) -> None:
        """
        Register a command plugin.
        
        Args:
            plugin: Plugin with get_handlers() method
        """
        if hasattr(plugin, 'get_handlers'):
            handlers = plugin.get_handlers()
            self.command_handlers.update(handlers)
            logger.info(f"Registered plugin with handlers: {list(handlers.keys())}")
        else:
            logger.error("Plugin must have get_handlers() method")
    
    def run(self) -> None:
        """
        Run the agent main loop.
        This is a blocking call.
        """
        logger.info(f"Starting NodeAgent for {self.config.node_id}")
        
        # Register node
        self.pool.register()
        self.notifier.notify_registered()
        
        # Register IP for load balancer
        my_ip = self._detect_ip()
        if my_ip:
            self.pool.register_ip(my_ip)
            logger.info(f"Registered IP: {my_ip}")
        
        self.running = True
        
        try:
            while self.running:
                # Send heartbeat
                self._send_heartbeat()
                
                # Check self health
                if not self.is_frozen:
                    self._check_self_health()
                
                # Process commands
                self._handle_commands()
                
                # Sleep until next iteration
                time.sleep(self.config.command_poll_interval)
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self._shutdown()
    
    def _detect_ip(self) -> Optional[str]:
        """
        Detect this node's IP address.
        
        Returns:
            IP address or None if detection fails
        """
        try:
            # Try to get the IP that connects to Redis
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return None
    
    def _send_heartbeat(self) -> None:
        """Send heartbeat with system metrics."""
        metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "is_frozen": self.is_frozen,
            "is_active": self.is_active,
            "timestamp": time.time()
        }
        
        self.pool.heartbeat(metrics)
    
    def _check_self_health(self) -> None:
        """Run all health checks and freeze if any fail."""
        # Built-in checks
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        
        if cpu > self.config.cpu_threshold:
            self.freeze(f"High CPU usage: {cpu}%")
            return
        
        if mem > self.config.memory_threshold:
            self.freeze(f"High memory usage: {mem}%")
            return
        
        # Check Docker containers if available
        if self.docker_client:
            try:
                containers = self.docker_client.containers.list()
                unhealthy = []
                for container in containers:
                    # Check if container is running
                    if container.status != "running":
                        unhealthy.append(container.name)
                
                if unhealthy:
                    self.freeze(f"Unhealthy containers: {', '.join(unhealthy)}")
                    return
            except Exception as e:
                logger.error(f"Error checking containers: {e}")
                self.freeze(f"Docker error: {e}")
                return
        
        # Run custom health checks
        for check in self.health_checks:
            try:
                if not check():
                    self.freeze(f"Custom health check failed: {check.__name__}")
                    return
            except Exception as e:
                logger.error(f"Health check error: {e}")
                self.freeze(f"Health check error: {e}")
                return
    
    def _handle_commands(self) -> None:
        """Process commands from queue."""
        command = self.pool.get_command()
        if not command:
            return
        
        cmd_type = command.get("type")
        logger.info(f"Executing command: {cmd_type}")
        
        handler = self.command_handlers.get(cmd_type)
        if handler:
            try:
                result = handler(command)
                self.pool.update_status(f"executed_{cmd_type}", json.dumps(result))
                success = result.get('success', True)
                logger.info(f"Command {cmd_type} completed: {success}")
                if not success:
                    logger.debug(result)
            except Exception as e:
                logger.error(f"Command {cmd_type} failed: {e}")
                self.pool.update_status(f"error_{cmd_type}", str(e))
        else:
            logger.error(f"Unknown command: {cmd_type}")
            self.pool.update_status("error", f"Unknown command: {cmd_type}")
    
    def freeze(self, reason: str = "") -> None:
        """
        Freeze this node (remove from active pool).
        
        Args:
            reason: Reason for freezing
        """
        if not self.is_frozen:
            self.is_frozen = True
            self.pool.freeze(reason)
            self.notifier.notify_frozen(reason)
            logger.warning(f"Node frozen: {reason}")
    
    def unfreeze(self) -> None:
        """Unfreeze this node."""
        if self.is_frozen:
            self.is_frozen = False
            self.pool.unfreeze()
            self.notifier.notify_unfrozen()
            logger.info("Node unfrozen")
    
    def _shutdown(self) -> None:
        """Clean shutdown."""
        self.running = False
        self.pool.redis.srem(self.config.nodes_active_key, self.config.node_id)
        self.pool.update_status("stopped", "Graceful shutdown")
        self.notifier.notify_removed()
        logger.info("Node agent stopped")
    
    # Built-in command handlers
    def _cmd_freeze(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle freeze command."""
        reason = command.get("reason", "Administrative action")
        self.freeze(reason)
        return {"status": "frozen", "reason": reason}
    
    def _cmd_unfreeze(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unfreeze command."""
        self.unfreeze()
        return {"status": "active"}
    
    def _cmd_exec(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute shell command."""
        cmd = command.get("command")
        if not cmd:
            return {"error": "No command specified"}
        
        # Security: check whitelist
        allowed = any(cmd.startswith(prefix) for prefix in self.config.allowed_exec_prefixes)
        if not allowed:
            return {"error": f"Command not allowed. Allowed prefixes: {self.config.allowed_exec_prefixes}"}
        
        try:
            print(f"[DEBUG] : self.config.app_dir {self.config.app_dir}")
            result = subprocess.run(
                cmd,
                cwd=self.config.app_dir,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out after 30 seconds"}
        except Exception as e:
            return {"error": str(e)}
    
    def _cmd_deploy_file(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy file to node."""
        file_path = command.get("path")
        content = command.get("content")
        
        if not file_path or content is None:
            return {"error": "Missing path or content"}
        
        try:
            # Security: prevent directory traversal
            file_path = os.path.normpath(file_path)
            if file_path.startswith(".."):
                return {"error": "Path traversal not allowed"}
            
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
            return {"status": "deployed", "path": file_path}
        except Exception as e:
            return {"error": str(e)}
    
    def _cmd_health_check(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Run health check and report."""
        self._check_self_health()
        return {
            "healthy": not self.is_frozen,
            "frozen": self.is_frozen,
            "active": self.is_active
        }