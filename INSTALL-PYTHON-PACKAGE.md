# BazBeans Installation Guide

This guide explains how to install BazBeans as a Python package.

## Requirements

- Python 3.8 or higher
- pip or pipx (Python package installer)
- Redis server (for cluster coordination)

## Installation Methods

### 1. Install with pipx (Recommended for Development)

[pipx](https://pypa.github.io/pipx/) provides isolated environments and is ideal for development:

```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Clone and install BazBeans
git clone https://github.com/bazbeans/bazbeans.git
cd bazbeans
pipx install --editable .

# Install the CLI wrapper
cd setup
./install.sh  # Linux/macOS
# or
.\install.ps1  # Windows
```

**Why pipx?**
- Isolated virtual environment (no dependency conflicts)
- Easy to uninstall
- Works perfectly with the smart CLI installer

### 2. Install from Source with pip (Development)

Clone the repository and install in development mode:

```bash
git clone https://github.com/bazbeans/bazbeans.git
cd bazbeans
pip install --user -e .

# Install the CLI wrapper
cd setup
./install.sh  # Linux/macOS
# or
.\install.ps1  # Windows
```

### 3. Install with Optional Dependencies

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

### 4. Install from PyPI (when published)

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

### Smart CLI Installation

BazBeans uses a **smart installer** that automatically detects your installation method:

- **Package Manager Installation** (pip/pipx/conda): Creates a lightweight wrapper that uses your package manager's environment
- **Standalone Installation**: Copies files and installs dependencies independently

After running the installer, the `bazbeans` command will be available:

```bash
bazbeans --help
bazbeans list-nodes
bazbeans freeze <node-id>
```

### Entry Points

The following entry points are also available (if your package manager created them):

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
bazbeans list-nodes

# Freeze a node
bazbeans freeze node-1 --reason "Maintenance"

# Send command to all nodes
bazbeans update --dc us-west-1

# Get help
bazbeans --help
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

### CLI Not Found

If the `bazbeans` command is not found after installation:

```bash
# For Linux/macOS
export PATH="$PATH:$HOME/.local/bin"

# For Windows
# Restart your terminal
```

See [Installation Troubleshooting Guide](INSTALL-TROUBLESHOOTING.md) for detailed solutions.

### Import Errors

If you get import errors, make sure the package is properly installed:

```bash
# For pipx
pipx list | grep bazbeans

# For pip
pip list | grep bazbeans
python -c "import src; print('Success')"
```

### Redis Connection Issues

Make sure Redis is running and accessible:

```bash
redis-cli ping
```

### Module Not Found with pipx

If you see `ModuleNotFoundError` after pipx installation, reinstall the CLI wrapper:

```bash
cd bazbeans/setup
./install.sh  # Linux/macOS
# or
.\install.ps1  # Windows
```

The smart installer will detect your pipx installation and create the appropriate wrapper.

For more troubleshooting help, see:
- [Installation Troubleshooting Guide](INSTALL-TROUBLESHOOTING.md)
- [General Troubleshooting](TROUBLESHOOTING.md)

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