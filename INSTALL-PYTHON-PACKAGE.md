# BazBeans Installation Guide

This guide explains how to install BazBeans as a Python package.

## Requirements

- Python 3.8 or higher
- pip (Python package installer)
- Redis server (for cluster coordination)

## Installation Methods

### 1. Install from Source (Development)

Clone the repository and install in development mode:

```bash
git clone https://github.com/bazbeans/bazbeans.git
cd bazbeans
pip install -e .
```

### 2. Install with Optional Dependencies

Install with Docker support:

```bash
pip install -e .[docker]
```

Install with development dependencies:

```bash
pip install -e .[dev]
```

Install with all optional dependencies:

```bash
pip install -e .[docker,dev]
```

### 3. Install from PyPI (when published)

```bash
pip install bazbeans
```

## Verify Installation

Run the installation test:

```bash
python test_installation.py
```

This will verify that all components can be imported and basic functionality works.

## Command-Line Tools

After installation, the following commands will be available:

- `bazbeans-cli` - Administrative command-line interface
- `bazbeans-agent` - Node agent (for running on cluster nodes)
- `bazbeans-updater` - Nginx configuration updater

## Configuration

BazBeans uses a `BazBeansConfig` object with sensible defaults. You can override these in your code:

```python
from src.config import BazBeansConfig

config = BazBeansConfig(
    redis_url="redis://your-redis:6379/0",
    node_id="my-node-1",
    data_center="us-west-1"
)
```

## Usage Examples

### Basic Node Agent

```python
from src.node_agent import NodeAgent
from src.config import BazBeansConfig

config = BazBeansConfig()
agent = NodeAgent(config)
agent.run()  # This will run indefinitely
```

### CLI Usage

```bash
# List all nodes
bazbeans-cli list-nodes

# Freeze a node
bazbeans-cli freeze node-1 --reason "Maintenance"

# Send command to all nodes
bazbeans-cli update --dc us-west-1
```

### Nginx Updater

```python
from src.nginx_updater import NginxUpdater
from src.config import BazBeansConfig

config = BazBeansConfig()
updater = NginxUpdater(config)
updater.run()  # Listens for pub/sub events
```

## Troubleshooting

### Import Errors

If you get import errors, make sure the package is properly installed:

```bash
pip list | grep bazbeans
python -c "import src; print('Success')"
```

### Redis Connection Issues

Make sure Redis is running and accessible:

```bash
redis-cli ping
```

### Permission Issues

On Linux/macOS, you might need to use `sudo` for certain operations:

```bash
sudo bazbeans-updater  # For nginx configuration updates
```

## Development

For development, install in editable mode:

```bash
pip install -e .[dev]
```

This allows you to modify code without reinstalling.

## Dependencies

See `requirements.txt` for the full list of dependencies.

Core dependencies:
- redis>=4.5.0 - Redis client
- click>=8.0.0 - CLI framework
- psutil>=5.9.0 - System utilities
- tabulate>=0.9.0 - Table formatting

Optional dependencies:
- docker>=6.0.0 - Docker integration