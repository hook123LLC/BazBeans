"""
BazBeans Pub/Sub Utilities

Redis pub/sub system for real-time load balancer notifications.
"""

import json
from datetime import datetime
from typing import Dict, Any, Callable, Optional
import redis
from .config import BazBeansConfig


class PubSubPublisher:
    """
    Publishes events to Redis pub/sub channels.
    """
    
    def __init__(self, config: BazBeansConfig):
        """
        Initialize publisher.
        
        Args:
            config: BazBeans configuration
        """
        self.config = config
        self.redis = redis.Redis.from_url(config.redis_url, decode_responses=True)
    
    def publish_event(self, event: str, node_id: str, reason: str = "", 
                    extra_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Publish an event to the pub/sub channel.
        
        Args:
            event: Event type (e.g., "node_frozen", "node_unfrozen")
            node_id: ID of the node
            reason: Optional reason for the event
            extra_data: Additional data to include
        """
        # Get current active nodes
        active_nodes = self.redis.smembers(self.config.nodes_active_key)
        
        # Build event payload
        payload = {
            "event": event,
            "node_id": node_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reason": reason,
            "active_nodes": list(active_nodes)
        }
        
        # Add any extra data
        if extra_data:
            payload.update(extra_data)
        
        # Publish to channel
        self.redis.publish(self.config.pubsub_channel, json.dumps(payload))


class PubSubSubscriber:
    """
    Subscribes to Redis pub/sub channels and handles events.
    """
    
    def __init__(self, config: BazBeansConfig):
        """
        Initialize subscriber.
        
        Args:
            config: BazBeans configuration
        """
        self.config = config
        self.redis = redis.Redis.from_url(config.redis_url, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        self.handlers: Dict[str, Callable] = {}
    
    def subscribe(self, channel: Optional[str] = None) -> None:
        """
        Subscribe to a channel.
        
        Args:
            channel: Channel name (defaults to config.pubsub_channel)
        """
        if channel is None:
            channel = self.config.pubsub_channel
        self.pubsub.subscribe(channel)
    
    def add_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a handler for a specific event type.
        
        Args:
            event_type: Event type to handle
            handler: Callback function that receives event data
        """
        self.handlers[event_type] = handler
    
    def listen(self) -> None:
        """
        Listen for messages and dispatch to handlers.
        This is a blocking call.
        """
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    event_type = data.get('event')
                    
                    if event_type in self.handlers:
                        self.handlers[event_type](data)
                    else:
                        # Default handler for unknown events
                        self.handle_unknown_event(data)
                        
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message['data']}")
                except Exception as e:
                    print(f"Error handling message: {e}")
    
    def handle_unknown_event(self, data: Dict[str, Any]) -> None:
        """
        Default handler for unknown event types.
        
        Args:
            data: Event data
        """
        print(f"Received unknown event: {data.get('event', 'unknown')}")
        print(f"Data: {json.dumps(data, indent=2)}")
    
    def stop(self) -> None:
        """
        Stop listening and close connection.
        """
        self.pubsub.close()
        self.redis.close()


class LoadBalancerNotifier:
    """
    Combines NodePool and PubSubPublisher to notify load balancer of changes.
    """
    
    def __init__(self, config: BazBeansConfig, node_pool):
        """
        Initialize notifier.
        
        Args:
            config: BazBeans configuration
            node_pool: NodePool instance
        """
        self.config = config
        self.node_pool = node_pool
        self.publisher = PubSubPublisher(config)
    
    def notify_frozen(self, reason: str = "") -> None:
        """
        Notify that this node has been frozen.
        
        Args:
            reason: Reason for freezing
        """
        self.publisher.publish_event(
            event="node_frozen",
            node_id=self.config.node_id,
            reason=reason
        )
    
    def notify_unfrozen(self) -> None:
        """
        Notify that this node has been unfrozen.
        """
        self.publisher.publish_event(
            event="node_unfrozen",
            node_id=self.config.node_id
        )
    
    def notify_registered(self) -> None:
        """
        Notify that this node has been registered.
        """
        self.publisher.publish_event(
            event="node_registered",
            node_id=self.config.node_id,
            extra_data={
                "data_center": self.config.data_center,
                "node_port": self.config.node_port
            }
        )
    
    def notify_removed(self) -> None:
        """
        Notify that this node has been removed.
        """
        self.publisher.publish_event(
            event="node_removed",
            node_id=self.config.node_id
        )