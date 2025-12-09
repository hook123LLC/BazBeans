"""
BazBeans IP Resolvers

Pluggable IP resolution strategies for load balancer integration.
"""

import socket
from typing import Dict, Optional, Callable, List
import redis
from .config import BazBeansConfig


class IPResolver:
    """Base class for IP resolution strategies."""
    
    def resolve(self, node_id: str) -> Optional[str]:
        """
        Resolve node_id to IP address.
        
        Args:
            node_id: Node identifier
            
        Returns:
            IP address or None if not found
        """
        raise NotImplementedError


class RedisIPResolver(IPResolver):
    """
    Resolves IPs using Redis where nodes self-register.
    """
    
    def __init__(self, redis_client):
        """
        Initialize resolver.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.config = BazBeansConfig()  # For key names
    
    def resolve(self, node_id: str) -> Optional[str]:
        """
        Resolve IP from Redis hash.
        
        Args:
            node_id: Node identifier
            
        Returns:
            IP address or None if not found
        """
        return self.redis.hget(self.config.node_ips_key, node_id)


class CallbackIPResolver(IPResolver):
    """
    Resolves IPs using a custom callback function.
    """
    
    def __init__(self, callback: Callable[[str], Optional[str]]):
        """
        Initialize resolver.
        
        Args:
            callback: Function that takes node_id and returns IP or None
        """
        self.callback = callback
    
    def resolve(self, node_id: str) -> Optional[str]:
        """
        Resolve IP using callback.
        
        Args:
            node_id: Node identifier
            
        Returns:
            IP address or None from callback
        """
        return self.callback(node_id)


class DNSIPResolver(IPResolver):
    """
    Resolves IPs using DNS lookup.
    """
    
    def __init__(self, domain_suffix: str = ""):
        """
        Initialize resolver.
        
        Args:
            domain_suffix: Suffix to append to node_id for DNS lookup
        """
        self.domain_suffix = domain_suffix
    
    def resolve(self, node_id: str) -> Optional[str]:
        """
        Resolve IP using DNS.
        
        Args:
            node_id: Node identifier
            
        Returns:
            IP address or None if resolution fails
        """
        hostname = f"{node_id}{self.domain_suffix}"
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror:
            return None


class StaticIPResolver(IPResolver):
    """
    Resolves IPs using a static mapping.
    """
    
    def __init__(self, mapping: Dict[str, str]):
        """
        Initialize resolver.
        
        Args:
            mapping: Dictionary mapping node_id to IP address
        """
        self.mapping = mapping
    
    def resolve(self, node_id: str) -> Optional[str]:
        """
        Resolve IP from static mapping.
        
        Args:
            node_id: Node identifier
            
        Returns:
            IP address or None if not in mapping
        """
        return self.mapping.get(node_id)


class ChainedIPResolver(IPResolver):
    """
    Chains multiple resolvers with primary and fallback support.
    """
    
    def __init__(self, primary: IPResolver, fallback: IPResolver):
        """
        Initialize chained resolver.
        
        Args:
            primary: Primary resolver to try first
            fallback: Fallback resolver if primary fails
        """
        self.primary = primary
        self.fallback = fallback
    
    def resolve(self, node_id: str) -> Optional[str]:
        """
        Resolve IP using primary, then fallback if needed.
        
        Args:
            node_id: Node identifier
            
        Returns:
            IP address or None if all resolvers fail
        """
        # Try primary first
        ip = self.primary.resolve(node_id)
        if ip:
            return ip
        
        # Try fallback
        return self.fallback.resolve(node_id)


class MultiFallbackIPResolver(IPResolver):
    """
    Chains multiple resolvers with multiple fallback support.
    """
    
    def __init__(self, resolvers: List[IPResolver]):
        """
        Initialize multi-fallback resolver.
        
        Args:
            resolvers: List of resolvers in order of preference
        """
        self.resolvers = resolvers
    
    def resolve(self, node_id: str) -> Optional[str]:
        """
        Resolve IP trying each resolver in order.
        
        Args:
            node_id: Node identifier
            
        Returns:
            IP address or None if all resolvers fail
        """
        for resolver in self.resolvers:
            ip = resolver.resolve(node_id)
            if ip:
                return ip
        return None


class AutoDetectIPResolver(IPResolver):
    """
    Resolves to the local machine's IP address.
    Useful for single-node setups or testing.
    """
    
    def __init__(self, interface: str = "0.0.0.0"):
        """
        Initialize resolver.
        
        Args:
            interface: Network interface to use
        """
        self.interface = interface
    
    def resolve(self, node_id: str) -> Optional[str]:
        """
        Return local IP address.
        
        Args:
            node_id: Node identifier (ignored)
            
        Returns:
            Local IP address
        """
        try:
            # Connect to a dummy address to get local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            # Fallback to localhost
            return "127.0.0.1"