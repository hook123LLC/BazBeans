#!/usr/bin/env python3
"""
Test script to verify BazBeans installation.

This script tests that the BazBeans package can be imported and basic
functionality works after installation.
"""

import sys
import traceback

def test_imports():
    """Test that all main modules can be imported."""
    print("Testing imports...")
    
    try:
        from src.config import BazBeansConfig
        print("PASS: BazBeansConfig imported successfully")
    except ImportError as e:
        print(f"FAIL: Failed to import BazBeansConfig: {e}")
        return False
    
    try:
        from src.node_pool import NodePool
        print("PASS: NodePool imported successfully")
    except ImportError as e:
        print(f"FAIL: Failed to import NodePool: {e}")
        return False
    
    try:
        from src.node_agent import NodeAgent
        print("PASS: NodeAgent imported successfully")
    except ImportError as e:
        print(f"FAIL: Failed to import NodeAgent: {e}")
        return False
    
    try:
        from src.control_cli import cli
        print("PASS: CLI imported successfully")
    except ImportError as e:
        print(f"FAIL: Failed to import CLI: {e}")
        return False
    
    try:
        from src.nginx_updater import NginxUpdater
        print("PASS: NginxUpdater imported successfully")
    except ImportError as e:
        print(f"FAIL: Failed to import NginxUpdater: {e}")
        return False
    
    try:
        from src.ip_resolvers import RedisIPResolver, DNSIPResolver
        print("PASS: IP resolvers imported successfully")
    except ImportError as e:
        print(f"FAIL: Failed to import IP resolvers: {e}")
        return False
    
    try:
        from src.docker_commands import DockerComposeCommands
        print("PASS: Docker commands imported successfully")
    except ImportError as e:
        print(f"FAIL: Failed to import Docker commands: {e}")
        return False
    
    try:
        from src.pubsub import PubSubPublisher, PubSubSubscriber
        print("PASS: PubSub components imported successfully")
    except ImportError as e:
        print(f"FAIL: Failed to import PubSub components: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of key components."""
    print("\nTesting basic functionality...")
    
    try:
        from src.config import BazBeansConfig
        config = BazBeansConfig()
        print(f"PASS: BazBeansConfig created: {config.node_id}")
        
        # Test validation
        config.validate()
        print("PASS: Configuration validation passed")
        
    except Exception as e:
        print(f"FAIL: Failed to create/validate config: {e}")
        return False
    
    try:
        from src.ip_resolvers import StaticIPResolver
        resolver = StaticIPResolver({"test-node": "192.168.1.100"})
        ip = resolver.resolve("test-node")
        assert ip == "192.168.1.100"
        print("PASS: StaticIPResolver works correctly")
        
    except Exception as e:
        print(f"FAIL: Failed StaticIPResolver test: {e}")
        return False
    
    return True

def main():
    """Main test function."""
    print("BazBeans Installation Test")
    print("=" * 40)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test basic functionality
    if not test_basic_functionality():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("PASS: All tests passed! BazBeans is installed correctly.")
        return 0
    else:
        print("FAIL: Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())