"""
BazBeans - Generic Multi-Node Control Plane Toolkit

A reusable toolkit for orchestrating distributed applications across multiple nodes.
Provides node self-management, administrative control, and load balancer integration.
"""

from .config import BazBeansConfig
from .node_pool import NodePool
from .node_agent import NodeAgent
from .control_cli import cli
from .nginx_updater import NginxUpdater
from .ip_resolvers import (
    RedisIPResolver,
    CallbackIPResolver,
    DNSIPResolver,
    StaticIPResolver,
    ChainedIPResolver,
)
from .docker_commands import DockerComposeCommands

__version__ = "0.1.0"
__all__ = [
    "BazBeansConfig",
    "NodePool",
    "NodeAgent",
    "cli",
    "NginxUpdater",
    "RedisIPResolver",
    "CallbackIPResolver",
    "DNSIPResolver",
    "StaticIPResolver",
    "ChainedIPResolver",
    "DockerComposeCommands",
]