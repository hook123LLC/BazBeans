#!/usr/bin/env python3
"""
Simple BazBeans Agent Example

This is the most basic example of a BazBeans agent.
Perfect for testing and understanding the core concepts.

What this example demonstrates:
- Basic agent setup
- Default configuration
- Simple health monitoring
- Command handling

Prerequisites:
- Redis server running
- BazBeans installed

Usage:
    python simple_agent.py
"""

import sys
from pathlib import Path

# Add bazbeans to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bazbeans import BazBeansConfig, NodeAgent


def main():
    """Run a simple BazBeans agent."""
    print("🚀 Starting Simple BazBeans Agent...")
    
    # Create basic configuration
    config = BazBeansConfig()
    
    # You can override defaults if needed
    config.redis_url = "redis://localhost:6379/0"
    config.node_id = "simple-agent"
    config.data_center = "local"
    
    print(f"📋 Configuration:")
    print(f"   Node ID: {config.node_id}")
    print(f"   Data Center: {config.data_center}")
    print(f"   Redis URL: {config.redis_url}")
    print(f"   Heartbeat TTL: {config.heartbeat_ttl}s")
    
    # Validate configuration
    try:
        config.validate()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Create agent
    agent = NodeAgent(config)
    
    # Add a simple custom health check
    @agent.health_check
    def check_memory():
        """Check if we have enough free memory."""
        import psutil
        free_percent = 100 - psutil.virtual_memory().percent
        print(f"💾 Memory check: {free_percent}% free")
        return free_percent > 10  # Require at least 10% free memory
    
    # Add a simple custom command handler
    @agent.command_handler("hello")
    def handle_hello(command):
        """Handle hello command."""
        name = command.get("name", "World")
        message = f"Hello, {name}! From {config.node_id}"
        print(f"👋 {message}")
        return {"message": message, "node": config.node_id}
    
    print("🔄 Starting agent main loop...")
    print("💡 Use 'bazbeans list-nodes' to see this agent")
    print("💡 Use 'bazbeans freeze simple-agent' to test freezing")
    print("💡 Use 'bazbeans exec simple-agent hello' to test custom command")
    print("💡 Press Ctrl+C to stop")
    
    try:
        # Run the agent (this blocks forever)
        agent.run()
    except KeyboardInterrupt:
        print("\n👋 Shutting down Simple Agent...")
    except Exception as e:
        print(f"❌ Agent error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()