# BazBeans Setup Scripts

> **⚠️ Deprecation Notice:** These setup scripts are deprecated. Please use the new Python package installation method instead.

**For the latest installation instructions, see:** [INSTALL-PYTHON-PACKAGE.md](../INSTALL-PYTHON-PACKAGE.md)

## Quick Installation (Recommended)

### All Platforms

```bash
# Install BazBeans package
pip install bazbeans
```

### Legacy Installation Scripts (Deprecated)

> **Note:** These scripts are no longer maintained. Use `pip install bazbeans` instead.

#### Ubuntu/Linux

```bash
# User installation (deprecated)
./install.sh

# System-wide installation (deprecated)
sudo ./install.sh --system
```

#### Windows

```powershell
# User installation (deprecated)
.\install.ps1

# System-wide installation (deprecated)
.\install.ps1 -System
```

#### macOS

```bash
# User installation (deprecated)
./install-macos.sh

# System-wide installation (deprecated)
sudo ./install-macos.sh --system
```

## What the Installers Do

1. **Install the `bazbeans` command** - Creates a native command that wraps the Python CLI
2. **Copy BazBeans files** - Installs the BazBeans package to a standard location
3. **Install dependencies** - Installs required Python packages
4. **Set up configuration** - Creates a default configuration file
5. **Update PATH** - Adds the command to your system PATH (user installation only)

## Configuration

The `bazbeans` command looks for configuration in these locations (in order):

1. `$BAZBEANS_CONFIG` environment variable
2. `$HOME/.bazbeans/config.yaml` (Linux/macOS) or `%APPDATA%\BazBeans\config.yaml` (Windows)
3. `/etc/bazbeans/config.yaml` (Linux) or `%ProgramData%\BazBeans\config.yaml` (Windows)
4. `./bazbeans.yaml` (current directory)

### Example Configuration

```yaml
# Redis connection
redis_url: "redis://your-redis:6379/0"

# Default data center
data_center: "dc1"

# Node port
node_port: 8000

# Health thresholds
cpu_threshold: 90
memory_threshold: 85
```

## Usage After Installation

Once installed, you can use the simplified commands:

```bash
# Instead of: python -m bazbeans.control_cli --redis-url "redis://..." list-nodes
bazbeans list-nodes

# Instead of: python -m bazbeans.control_cli --redis-url "redis://..." freeze node-01
bazbeans freeze node-01

# Override config redis URL
BAZBEANS_REDIS_URL="redis://prod-redis:6379/0" bazbeans list-nodes
```

## Uninstallation

### Ubuntu/Linux

```bash
bazbeans-uninstall
```

### Windows

```powershell
.\uninstall-bazbeans.ps1
```

### macOS

```bash
bazbeans-uninstall
```

## Installation Locations

### User Installation

- **Linux/macOS**: `~/.local/share/bazbeans`
- **Windows**: `%LOCALAPPDATA%\BazBeans`
- **Config**: `~/.bazbeans/config.yaml` or `%APPDATA%\BazBeans\config.yaml`

### System Installation

- **Linux/macOS**: `/opt/bazbeans`
- **Windows**: `%ProgramFiles%\BazBeans`
- **Config**: `/etc/bazbeans/config.yaml` or `%ProgramData%\BazBeans\config.yaml`

## Troubleshooting

### Command Not Found

1. **Linux/macOS**: Make sure `~/.local/bin` is in your PATH
   ```bash
   echo $PATH | grep ~/.local/bin
   ```

2. **Windows**: Restart your terminal or run:
   ```powershell
   $env:PATH = [Environment]::GetEnvironmentVariable("PATH", "User")
   ```

### Python Not Found

The installers look for `python3` (Linux/macOS) or `python` (Windows). If you have a different Python installation:

1. Create a symlink:
   ```bash
   # Linux/macOS
   ln -s /usr/bin/python3.9 /usr/local/bin/python3
   
   # Windows (as admin)
   New-Item -ItemType SymbolicLink -Path "C:\Python39\python.exe" -Target "C:\Python39\python3.exe"
   ```

2. Or modify the installed `bazbeans` script to use your Python path

### Permission Denied

- **User installation**: Don't use sudo
- **System installation**: Use sudo/administrator privileges

### Dependencies Failed

Install manually:
```bash
pip install -r /path/to/bazbeans/requirements.txt
```

## Advanced Usage

### Multiple Configurations

You can have multiple configuration files and switch between them:

```bash
# Use production config
export BAZBEANS_CONFIG="$HOME/.bazbeans/prod.yaml"
bazbeans list-nodes

# Use development config
export BAZBEANS_CONFIG="$HOME/.bazbeans/dev.yaml"
bazbeans list-nodes
```

### Environment Variables

The `bazbeans` command respects these environment variables:

- `BAZBEANS_CONFIG` - Path to configuration file
- `BAZBEANS_REDIS_URL` - Override Redis URL
- `BAZBEANS_HOME` - Override installation directory

### Custom Installation

If you need to install to a custom location:

1. Copy the bazbeans directory manually
2. Create the `bazbeans` script in your preferred location
3. Update your PATH

Example for custom installation to `/opt/myapp/bazbeans`:

```bash
# Copy files
sudo cp -r bazbeans /opt/myapp/

# Create command
sudo tee /usr/local/bin/bazbeans > /dev/null << 'EOF'
#!/bin/bash
export BAZBEANS_HOME="/opt/myapp/bazbeans"
python3 "$BAZBEANS_HOME/bazbeans/control_cli.py" --redis-url "redis://my-redis:6379/0" "$@"
EOF

sudo chmod +x /usr/local/bin/bazbeans