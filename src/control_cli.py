"""
BazBeans Control CLI

Administrative command-line interface for cluster control.
"""

import json
import click
import redis
import toml
from pathlib import Path
from tabulate import tabulate
from typing import Optional
try:
    from .config import BazBeansConfig
except ImportError:
    from config import BazBeansConfig


def get_version():
    """Read version from pyproject.toml"""
    try:
        # Try to read from pyproject.toml in the project root
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, 'r') as f:
                data = toml.load(f)
                return data.get('project', {}).get('version', 'unknown')
    except Exception:
        pass
    
    # Fallback to a default version if we can't read the file
    return '0.1.2'


def display_header():
    """Display the CLI header with version"""
    version = get_version()
    print(f"BazBeans CLI version {version}")
    print("=" * 50)


class ClusterController:
    """
    Controller for managing the cluster via Redis.
    """
    
    def __init__(self, config: BazBeansConfig):
        """
        Initialize controller.

        Args:
            config: BazBeans configuration
        """
        self.config = config
        self.redis = redis.Redis.from_url(config.redis_url, decode_responses=True)

    def _redis_operation(self, operation, *args, **kwargs):
        """
        Execute Redis operation with error handling.

        Args:
            operation: Redis method to call
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Result of the operation

        Raises:
            click.ClickException: With user-friendly error message on Redis connection failure
        """
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            raise click.ClickException(f"Unable to connect to Redis at {self.config.redis_url}\nPlease ensure Redis is running and accessible.")
    
    def get_all_nodes(self) -> list:
        """
        Get all registered nodes.

        Returns:
            List of node IDs
        """
        return list(self._redis_operation(self.redis.smembers, self.config.nodes_all_key))
    
    def get_active_nodes(self) -> list:
        """
        Get active nodes.

        Returns:
            List of active node IDs
        """
        return list(self._redis_operation(self.redis.smembers, self.config.nodes_active_key))
    
    def get_node_status(self, node_id: str) -> dict:
        """
        Get detailed node status.

        Args:
            node_id: Node ID

        Returns:
            Dictionary with node status
        """
        # Get heartbeat data
        heartbeat_key = f"bazbeans:node:{node_id}:heartbeat"
        heartbeat_data = self._redis_operation(self.redis.get, heartbeat_key)

        if heartbeat_data:
            heartbeat = json.loads(heartbeat_data)
        else:
            heartbeat = {"status": "NO HEARTBEAT"}

        # Get status data
        status_key = f"bazbeans:node:{node_id}:status"
        status_data = self._redis_operation(self.redis.hgetall, status_key)

        # Combine and return
        return {
            "node_id": node_id,
            **status_data,
            **heartbeat
        }
    
    def send_command(self, node_id: str, command: dict) -> None:
        """
        Send command to specific node.
        
        Args:
            node_id: Target node ID
            command: Command dictionary
        """
        queue = f"bazbeans:node:{node_id}:commands"
        self.redis.rpush(queue, json.dumps(command))
    
    def send_command_to_all(self, command: dict, filter_dc: Optional[str] = None) -> None:
        """
        Send command to all nodes (optionally filtered by datacenter).

        Args:
            command: Command dictionary
            filter_dc: Optional datacenter filter
        """
        nodes = self.get_all_nodes()

        for node in nodes:
            if filter_dc:
                # Get node's datacenter
                status = self.get_node_status(node)
                if status.get("data_center") != filter_dc:
                    continue

            self.send_command(node, command)


# CLI setup
@click.group()
@click.option('--redis-url', default='redis://localhost:6379/0',
              help='Redis connection URL')
@click.option('--data-center', default=None,
              help='Default datacenter filter for commands')
@click.pass_context
def cli(ctx, redis_url, data_center):
    """BazBeans Cluster Control CLI"""
    # Display header with version
    display_header()
    
    # Create config
    config = BazBeansConfig(redis_url=redis_url)

    # Store in context
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['default_dc'] = data_center

    # Create controller
    ctx.obj['controller'] = ClusterController(config)


@cli.command()
@click.pass_context
def list_nodes(ctx):
    """List all nodes with status"""
    controller = ctx.obj['controller']
    nodes = controller.get_all_nodes()
    active = controller.get_active_nodes()
    
    table = []
    for node in nodes:
        status = controller.get_node_status(node)
        table.append([
            node,
            "✓" if node in active else "✗",
            status.get('cpu_percent', 'N/A'),
            status.get('memory_percent', 'N/A'),
            status.get('status', 'N/A'),
            status.get('is_frozen', 'false'),
            status.get('data_center', 'N/A')
        ])
    
    print(tabulate(
        table,
        headers=['Node', 'Active', 'CPU%', 'MEM%', 'Status', 'Frozen', 'DataCenter']
    ))


@cli.command()
@click.argument('node_id')
@click.option('--reason', default='Administrative freeze',
              help='Reason for freezing')
@click.pass_context
def freeze(ctx, node_id, reason):
    """Freeze a node (remove from load balancer)"""
    controller = ctx.obj['controller']
    controller.send_command(node_id, {
        "type": "freeze",
        "reason": reason
    })
    click.echo(f"Freeze command sent to {node_id}")


@cli.command()
@click.argument('node_id')
@click.pass_context
def unfreeze(ctx, node_id):
    """Unfreeze a node"""
    controller = ctx.obj['controller']
    controller.send_command(node_id, {"type": "unfreeze"})
    click.echo(f"Unfreeze command sent to {node_id}")


@cli.command()
@click.argument('node_id')
@click.pass_context
def start(ctx, node_id):
    """Start services on node"""
    controller = ctx.obj['controller']
    controller.send_command(node_id, {"type": "start"})
    click.echo(f"Start command sent to {node_id}")


@cli.command()
@click.argument('node_id')
@click.pass_context
def stop(ctx, node_id):
    """Stop services on node"""
    controller = ctx.obj['controller']
    controller.send_command(node_id, {"type": "stop"})
    click.echo(f"Stop command sent to {node_id}")


@cli.command()
@click.argument('node_id')
@click.pass_context
def restart(ctx, node_id):
    """Restart services on node"""
    controller = ctx.obj['controller']
    controller.send_command(node_id, {"type": "restart"})
    click.echo(f"Restart command sent to {node_id}")


@cli.command()
@click.option('--dc', help='Filter by datacenter')
@click.pass_context
def update(ctx, dc):
    """Update application on nodes (rolling update)"""
    controller = ctx.obj['controller']
    filter_dc = dc or ctx.obj.get('default_dc')
    
    controller.send_command_to_all({"type": "update"}, filter_dc=filter_dc)
    
    if filter_dc:
        click.echo(f"Update command sent to nodes in datacenter '{filter_dc}'")
    else:
        click.echo("Update command sent to all nodes")


@cli.command()
@click.argument('node_id')
@click.argument('command')
@click.pass_context
def exec_cmd(ctx, node_id, command):
    """Execute shell command on node"""
    controller = ctx.obj['controller']
    controller.send_command(node_id, {
        "type": "exec",
        "command": command
    })
    click.echo(f"Command sent to {node_id}: {command}")


@cli.command()
@click.argument('node_id')
@click.argument('local_file')
@click.argument('remote_path')
@click.pass_context
def deploy_file(ctx, node_id, local_file, remote_path):
    """Deploy file to node"""
    try:
        with open(local_file, 'r') as f:
            content = f.read()
    except Exception as e:
        click.echo(f"Error reading file: {e}")
        return
    
    controller = ctx.obj['controller']
    controller.send_command(node_id, {
        "type": "deploy_file",
        "path": remote_path,
        "content": content
    })
    click.echo(f"File deployment command sent to {node_id}: {remote_path}")


@cli.command()
@click.argument('node_id')
@click.pass_context
def status(ctx, node_id):
    """Get detailed status of a node"""
    controller = ctx.obj['controller']
    status = controller.get_node_status(node_id)
    
    print(f"\nNode: {node_id}")
    print("=" * 50)
    print(f"Status: {status.get('status', 'Unknown')}")
    print(f"Data Center: {status.get('data_center', 'Unknown')}")
    print(f"Frozen: {status.get('is_frozen', 'false')}")
    print(f"Active: {status.get('is_active', 'false')}")
    
    if 'timestamp' in status:
        import datetime
        ts = float(status['timestamp'])
        dt = datetime.datetime.fromtimestamp(ts)
        print(f"Last Update: {dt}")
    
    print("\nMetrics:")
    print(f"  CPU: {status.get('cpu_percent', 'N/A')}%")
    print(f"  Memory: {status.get('memory_percent', 'N/A')}%")
    print(f"  Disk: {status.get('disk_percent', 'N/A')}%")
    
    if 'details' in status and status['details']:
        print(f"\nDetails: {status['details']}")


@cli.command()
@click.pass_context
def cleanup(ctx):
    """Clean up dead nodes from active set"""
    controller = ctx.obj['controller']
    
    # Get all nodes in active set
    active_nodes = controller.get_active_nodes()
    
    # Check each for heartbeat
    cleaned = []
    for node_id in active_nodes:
        heartbeat_key = f"bazbeans:node:{node_id}:heartbeat"
        if not controller._redis_operation(controller.redis.exists, heartbeat_key):
            controller._redis_operation(controller.redis.srem, controller.config.nodes_active_key, node_id)
            cleaned.append(node_id)
    
    if cleaned:
        click.echo(f"Cleaned up {len(cleaned)} dead nodes:")
        for node in cleaned:
            click.echo(f"  - {node}")
    else:
        click.echo("No dead nodes found")


if __name__ == "__main__":
    cli()