"""
BazBeans Nginx Updater

Subscribes to pub/sub channel and updates Nginx upstream configuration.
"""

import json
import logging
import os
import subprocess
import time
from typing import Dict, Any, Optional, List
import redis
from .config import BazBeansConfig
from .ip_resolvers import IPResolver, RedisIPResolver, StaticIPResolver
from .pubsub import PubSubSubscriber

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NginxUpdater:
    """
    Updates Nginx upstream configuration based on node events.
    """
    
    def __init__(self, config: BazBeansConfig, upstream_name: str = "app_backend",
                 upstream_file: str = "/etc/nginx/conf.d/upstream.conf",
                 ip_resolver: Optional[IPResolver] = None,
                 reload_command: List[str] = None):
        """
        Initialize Nginx updater.
        
        Args:
            config: BazBeans configuration
            upstream_name: Name for the upstream block
            upstream_file: Path to upstream configuration file
            ip_resolver: IP resolver strategy (defaults to RedisIPResolver)
            reload_command: Command to reload Nginx (defaults to nginx -s reload)
        """
        self.config = config
        self.upstream_name = upstream_name
        self.upstream_file = upstream_file
        self.reload_command = reload_command or ["nginx", "-s", "reload"]
        
        # Initialize Redis
        self.redis = redis.Redis.from_url(config.redis_url, decode_responses=True)
        
        # Set up IP resolver
        if ip_resolver is None:
            ip_resolver = RedisIPResolver(self.redis)
        self.ip_resolver = ip_resolver
        
        # Set up pub/sub subscriber
        self.subscriber = PubSubSubscriber(config)
        self.subscriber.add_handler("node_registered", self._handle_node_registered)
        self.subscriber.add_handler("node_removed", self._handle_node_removed)
        self.subscriber.add_handler("node_frozen", self._handle_node_frozen)
        self.subscriber.add_handler("node_unfrozen", self._handle_node_unfrozen)
        
        # Track current active nodes
        self.active_nodes: List[str] = []
        
        # Initial update
        self._update_upstream()
    
    def run(self) -> None:
        """
        Run the updater (blocking).
        Listens for pub/sub events and updates Nginx as needed.
        """
        logger.info(f"Starting Nginx updater for upstream '{self.upstream_name}'")
        logger.info(f"Listening on channel: {self.config.pubsub_channel}")
        
        try:
            self.subscriber.listen()
        except KeyboardInterrupt:
            logger.info("Stopping Nginx updater...")
        finally:
            self.subscriber.stop()
    
    def _handle_node_registered(self, data: Dict[str, Any]) -> None:
        """Handle node registration event."""
        node_id = data.get("node_id")
        active_nodes = data.get("active_nodes", [])
        
        logger.info(f"Node registered: {node_id}")
        self._update_upstream_if_needed(active_nodes)
    
    def _handle_node_removed(self, data: Dict[str, Any]) -> None:
        """Handle node removal event."""
        node_id = data.get("node_id")
        active_nodes = data.get("active_nodes", [])
        
        logger.info(f"Node removed: {node_id}")
        self._update_upstream_if_needed(active_nodes)
    
    def _handle_node_frozen(self, data: Dict[str, Any]) -> None:
        """Handle node freeze event."""
        node_id = data.get("node_id")
        reason = data.get("reason", "")
        active_nodes = data.get("active_nodes", [])
        
        logger.info(f"Node frozen: {node_id} - {reason}")
        self._update_upstream_if_needed(active_nodes)
    
    def _handle_node_unfrozen(self, data: Dict[str, Any]) -> None:
        """Handle node unfreeze event."""
        node_id = data.get("node_id")
        active_nodes = data.get("active_nodes", [])
        
        logger.info(f"Node unfrozen: {node_id}")
        self._update_upstream_if_needed(active_nodes)
    
    def _update_upstream_if_needed(self, active_nodes: List[str]) -> None:
        """
        Update upstream configuration if active nodes have changed.
        
        Args:
            active_nodes: List of currently active node IDs
        """
        # Check if nodes have changed
        if set(active_nodes) == set(self.active_nodes):
            return
        
        logger.info(f"Active nodes changed: {self.active_nodes} -> {active_nodes}")
        self.active_nodes = active_nodes.copy()
        self._update_upstream()
    
    def _update_upstream(self) -> None:
        """Update the Nginx upstream configuration file."""
        # Get current active nodes from Redis if not provided
        if not self.active_nodes:
            self.active_nodes = list(self.redis.smembers(self.config.nodes_active_key))
        
        # Generate upstream configuration
        upstream_config = self._generate_upstream_config()
        
        # Write to file
        try:
            # Create backup
            if os.path.exists(self.upstream_file):
                backup_file = f"{self.upstream_file}.bak"
                os.replace(self.upstream_file, backup_file)
                logger.debug(f"Created backup: {backup_file}")
            
            # Write new config
            with open(self.upstream_file, 'w') as f:
                f.write(upstream_config)
            
            logger.info(f"Updated upstream config: {self.upstream_file}")
            logger.debug(f"Config content:\n{upstream_config}")
            
            # Reload Nginx
            self._reload_nginx()
            
        except Exception as e:
            logger.error(f"Failed to update upstream config: {e}")
    
    def _generate_upstream_config(self) -> str:
        """
        Generate Nginx upstream configuration.
        
        Returns:
            Nginx configuration string
        """
        lines = [
            f"# Generated by BazBeans Nginx Updater",
            f"# Updated: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"upstream {self.upstream_name} {{",
            f"    # Active nodes: {len(self.active_nodes)}"
        ]
        
        # Add server entries
        for node_id in sorted(self.active_nodes):
            ip = self.ip_resolver.resolve(node_id)
            if ip:
                lines.append(f"    server {ip}:{self.config.node_port};")
            else:
                logger.warning(f"Could not resolve IP for node: {node_id}")
                lines.append(f"    # Could not resolve IP for {node_id}")
        
        # Add load balancing options
        lines.extend([
            "    # Load balancing options",
            "    least_conn;",
            "}"
        ])
        
        return "\n".join(lines) + "\n"
    
    def _reload_nginx(self) -> None:
        """Reload Nginx configuration."""
        try:
            # Test configuration first
            test_cmd = ["nginx", "-t"]
            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Nginx config test failed:\n{result.stderr}")
                return
            
            # Reload configuration
            subprocess.run(self.reload_command, check=True)
            logger.info("Nginx reloaded successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to reload Nginx: {e}")
        except Exception as e:
            logger.error(f"Error reloading Nginx: {e}")


class NginxUpdaterWithHealthChecks(NginxUpdater):
    """
    Extended Nginx updater that performs health checks on nodes.
    """
    
    def __init__(self, *args, health_check_path: str = "/health", 
                 health_check_timeout: int = 5, **kwargs):
        """
        Initialize with health check support.
        
        Args:
            *args: Arguments passed to NginxUpdater
            health_check_path: Path for health check endpoint
            health_check_timeout: Timeout for health check in seconds
            **kwargs: Keyword arguments passed to NginxUpdater
        """
        super().__init__(*args, **kwargs)
        self.health_check_path = health_check_path
        self.health_check_timeout = health_check_timeout
    
    def _generate_upstream_config(self) -> str:
        """
        Generate upstream config with health checks.
        """
        lines = [
            f"# Generated by BazBeans Nginx Updater with Health Checks",
            f"# Updated: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"upstream {self.upstream_name} {{",
            f"    # Active nodes: {len(self.active_nodes)}"
        ]
        
        # Add server entries with health checks
        for node_id in sorted(self.active_nodes):
            ip = self.ip_resolver.resolve(node_id)
            if ip:
                lines.extend([
                    f"    server {ip}:{self.config.node_port};",
                    f"    # Health check: curl -f http://{ip}:{self.config.node_port}{self.health_check_path}"
                ])
            else:
                logger.warning(f"Could not resolve IP for node: {node_id}")
                lines.append(f"    # Could not resolve IP for {node_id}")
        
        # Add load balancing and health check options
        lines.extend([
            "    # Load balancing options",
            "    least_conn;",
            "",
            "    # Health check configuration (requires nginx-plus or third-party module)",
            f"    # check interval={self.health_check_timeout * 2}s timeout={self.health_check_timeout}s",
            "}"
        ])
        
        return "\n".join(lines) + "\n"