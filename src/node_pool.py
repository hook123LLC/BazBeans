"""
BazBeans Node Pool

Manages the shared state of all nodes in Redis.
"""

import json
import time
from typing import List, Dict, Any, Optional
import redis
from .config import BazBeansConfig


class NodePool:
    """
    Manages node registration, heartbeats, and status in Redis.
    """
    
    def __init__(self, config: BazBeansConfig):
        """
        Initialize node pool.
        
        Args:
            config: BazBeans configuration
        """
        self.config = config
        self.redis = redis.Redis.from_url(config.redis_url, decode_responses=True)
        
        # Build key names
        self.heartbeat_key = f"bazbeans:node:{config.node_id}:heartbeat"
        self.status_key = f"bazbeans:node:{config.node_id}:status"
        self.command_queue = f"bazbeans:node:{config.node_id}:commands"
    
    def register(self) -> None:
        """
        Register this node in the pool.
        """
        pipe = self.redis.pipeline()
        pipe.sadd(self.config.nodes_all_key, self.config.node_id)
        pipe.sadd(self.config.nodes_active_key, self.config.node_id)
        pipe.hset(self.status_key, mapping={
            "status": "registered",
            "details": "",
            "timestamp": time.time(),
            "data_center": self.config.data_center,
            "is_frozen": "false",
            "is_active": "true"
        })
        pipe.execute()
    
    def heartbeat(self, metrics: Dict[str, Any]) -> None:
        """
        Send heartbeat with metrics.
        
        Args:
            metrics: Dictionary of metrics to include
        """
        heartbeat_data = {
            "timestamp": time.time(),
            "node_id": self.config.node_id,
            "data_center": self.config.data_center,
            **metrics
        }
        
        # Set heartbeat with TTL
        self.redis.setex(
            self.heartbeat_key,
            self.config.heartbeat_ttl,
            json.dumps(heartbeat_data)
        )
    
    def freeze(self, reason: str = "") -> None:
        """
        Freeze this node (remove from active pool).
        
        Args:
            reason: Reason for freezing
        """
        pipe = self.redis.pipeline()
        pipe.srem(self.config.nodes_active_key, self.config.node_id)
        pipe.hset(self.status_key, mapping={
            "status": "frozen",
            "details": reason,
            "timestamp": time.time(),
            "is_frozen": "true",
            "is_active": "false"
        })
        pipe.execute()
    
    def unfreeze(self) -> None:
        """
        Unfreeze this node (add back to active pool).
        """
        pipe = self.redis.pipeline()
        pipe.sadd(self.config.nodes_active_key, self.config.node_id)
        pipe.hset(self.status_key, mapping={
            "status": "active",
            "details": "Unfrozen",
            "timestamp": time.time(),
            "is_frozen": "false",
            "is_active": "true"
        })
        pipe.execute()
    
    def get_active_nodes(self) -> List[str]:
        """
        Get all nodes with recent heartbeats.
        
        Returns:
            List of active node IDs
        """
        all_nodes = self.redis.smembers(self.config.nodes_active_key)
        active = []
        
        for node_id in all_nodes:
            hb_key = f"bazbeans:node:{node_id}:heartbeat"
            if self.redis.exists(hb_key):
                active.append(node_id)
            else:
                # Auto-cleanup dead nodes
                self.redis.srem(self.config.nodes_active_key, node_id)
        
        return active
    
    def get_all_nodes(self) -> List[str]:
        """
        Get all registered nodes.
        
        Returns:
            List of all node IDs
        """
        return list(self.redis.smembers(self.config.nodes_all_key))
    
    def get_node_status(self, node_id: str) -> Dict[str, Any]:
        """
        Get detailed status for a specific node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Dictionary with node status information
        """
        # Get heartbeat data
        heartbeat_data = self.redis.get(f"bazbeans:node:{node_id}:heartbeat")
        if heartbeat_data:
            heartbeat = json.loads(heartbeat_data)
        else:
            heartbeat = {"status": "NO HEARTBEAT"}
        
        # Get status data
        status_data = self.redis.hgetall(f"bazbeans:node:{node_id}:status")
        
        # Combine and return
        return {
            "node_id": node_id,
            **status_data,
            **heartbeat
        }
    
    def cleanup_dead_nodes(self) -> List[str]:
        """
        Remove nodes without recent heartbeats from active set.
        
        Returns:
            List of node IDs that were cleaned up
        """
        active_nodes = self.redis.smembers(self.config.nodes_active_key)
        cleaned = []
        
        for node_id in active_nodes:
            hb_key = f"bazbeans:node:{node_id}:heartbeat"
            if not self.redis.exists(hb_key):
                self.redis.srem(self.config.nodes_active_key, node_id)
                cleaned.append(node_id)
        
        return cleaned
    
    def send_command(self, node_id: str, command: Dict[str, Any]) -> None:
        """
        Send a command to a specific node.
        
        Args:
            node_id: Target node ID
            command: Command dictionary
        """
        queue = f"bazbeans:node:{node_id}:commands"
        self.redis.rpush(queue, json.dumps(command))
    
    def get_command(self) -> Optional[Dict[str, Any]]:
        """
        Get next command from this node's queue.
        
        Returns:
            Command dictionary or None if no commands
        """
        command_data = self.redis.lpop(self.command_queue)
        if command_data:
            return json.loads(command_data)
        return None
    
    def update_status(self, status: str, details: str = "") -> None:
        """
        Update node status.
        
        Args:
            status: Status string
            details: Optional details
        """
        self.redis.hset(self.status_key, mapping={
            "status": status,
            "details": details,
            "timestamp": time.time()
        })
    
    def register_ip(self, ip_address: str) -> None:
        """
        Register this node's IP address for load balancer resolution.
        
        Args:
            ip_address: IP address of this node
        """
        self.redis.hset(self.config.node_ips_key, self.config.node_id, ip_address)
    
    def get_node_ip(self, node_id: str) -> Optional[str]:
        """
        Get registered IP address for a node.
        
        Args:
            node_id: Node ID
            
        Returns:
            IP address or None if not found
        """
        return self.redis.hget(self.config.node_ips_key, node_id)