"""
BazBeans Configuration

Configuration object with sensible hardcoded defaults.
Integrators are responsible for assigning values from their own sources.
"""

import socket
from typing import List


class BazBeansConfig:
    """
    Configuration object for BazBeans components.
    
    All properties have sensible defaults. Integrators should override
    these values from their own configuration sources (env vars, config files, etc.).
    """
    
    def __init__(self, **kwargs):
        """
        Initialize configuration with optional overrides.
        
        Args:
            **kwargs: Any configuration property can be overridden here
        """
        # Redis connection
        self.redis_url: str = "redis://localhost:6379/0"
        
        # Node identification
        self.node_id: str = socket.gethostname()
        self.data_center: str = "default"
        
        # Timing configuration
        self.heartbeat_ttl: int = 30  # seconds
        self.heartbeat_interval: int = 10  # seconds
        self.command_poll_interval: int = 5  # seconds
        
        # Application configuration
        self.app_dir: str = "/opt/app"
        self.compose_file: str = "docker-compose.yml"
        self.node_port: int = 8000
        
        # Pub/sub configuration
        self.pubsub_channel: str = "bazbeans:lb_events"
        
        # Health check thresholds
        self.cpu_threshold: int = 90  # percentage
        self.memory_threshold: int = 85  # percentage
        
        # Security
        self.allowed_exec_prefixes: List[str] = [
            "docker",
            "systemctl",
            "ls",
            "cat",
            "grep",
            "ps",
            "netstat",
        ]
        
        # Redis key prefixes
        self.nodes_all_key: str = "bazbeans:nodes:all"
        self.nodes_active_key: str = "bazbeans:nodes:active"
        self.node_ips_key: str = "bazbeans:node_ips"
        
        # Apply any overrides
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration property: {key}")
    
    def validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValueError: If any configuration is invalid
        """
        if self.heartbeat_ttl <= 0:
            raise ValueError("heartbeat_ttl must be positive")
        
        if self.heartbeat_interval <= 0:
            raise ValueError("heartbeat_interval must be positive")
        
        if self.command_poll_interval <= 0:
            raise ValueError("command_poll_interval must be positive")
        
        if not (0 <= self.cpu_threshold <= 100):
            raise ValueError("cpu_threshold must be between 0 and 100")
        
        if not (0 <= self.memory_threshold <= 100):
            raise ValueError("memory_threshold must be between 0 and 100")
        
        if not self.node_id:
            raise ValueError("node_id cannot be empty")
        
        if not self.redis_url:
            raise ValueError("redis_url cannot be empty")
    
    def __repr__(self) -> str:
        """String representation of configuration (excluding sensitive data)."""
        return (
            f"BazBeansConfig("
            f"redis_url='{self.redis_url}', "
            f"node_id='{self.node_id}', "
            f"data_center='{self.data_center}', "
            f"heartbeat_ttl={self.heartbeat_ttl}, "
            f"heartbeat_interval={self.heartbeat_interval}, "
            f"command_poll_interval={self.command_poll_interval}, "
            f"app_dir='{self.app_dir}', "
            f"node_port={self.node_port})"
        )