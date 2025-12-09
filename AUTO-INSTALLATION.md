# BazBeans CLI Auto-Installation

## Overview

When you install BazBeans from PyPI using `pip install bazbeans`, the package will automatically attempt to install the OS-specific CLI tools after the Python package installation completes.

## What Gets Installed

The auto-installer detects your operating system and installs the appropriate CLI:

- **Linux**: `bazbeans` command in `/usr/local/bin` or `~/.local/bin`
- **macOS**: `bazbeans` command in `/usr/local/bin` or `~/.local/bin`  
- **Windows**: `bazbeans.bat` and `bazbeans.ps1` commands

## How It Works

1. **After pip install completes**, the auto-installer runs automatically
2. **OS Detection**: The installer detects your operating system
3. **Script Selection**: Chooses the appropriate installer script:
   - `setup/install.sh` for Linux
   - `setup/install-macos.sh` for macOS
   - `setup/install.ps1` for Windows
4. **CLI Installation**: Runs the selected script to install the command-line tool
5. **PATH Setup**: Updates your system PATH if needed (user installations)

## Controlling Auto-Installation

### Skip Auto-Installation

You can skip the CLI auto-installation in several ways:

```bash
# Set environment variable
export BAZBEANS_SKIP_CLI_INSTALL=1
pip install bazbeans

# Use pip install with options
pip install bazbeans --no-deps  # Skip dependencies (won't trigger auto-install)
pip install bazbeans --user     # User install (skips auto-install)

# Use development installation
pip install -e .                # Development install (skips auto-install)
```

### Manual CLI Installation

If you prefer to install the CLI manually:

```bash
# After installing the Python package
pip install bazbeans

# Then install CLI manually
cd setup
./install.sh        # Linux/macOS
.\install.ps1       # Windows PowerShell (run as administrator for system-wide)
```

## Error Handling

The auto-installer is designed to be robust:

- **Non-blocking**: If CLI installation fails, the Python package still works
- **Graceful degradation**: You can always use the CLI via Python modules
- **Error reporting**: Clear error messages if something goes wrong
- **Manual fallback**: Clear instructions for manual installation

## Usage After Installation

Once installed, you can use the CLI commands:

```bash
# Basic commands
bazbeans --help
bazbeans list-nodes
bazbeans freeze <node-id>
bazbeans unfreeze <node-id>

# Configuration
bazbeans status <node-id>
bazbeans exec <node-id> "docker ps"
```

## Configuration

The CLI looks for configuration in this order:

1. Environment variable: `BAZBEANS_CONFIG`
2. User config: `~/.bazbeans/config.yaml` (Linux/macOS) or `%APPDATA%\BazBeans\config.yaml` (Windows)
3. System config: `/etc/bazbeans/config.yaml` (Linux) or `%ProgramData%\BazBeans\config.yaml` (Windows)
4. Local config: `./bazbeans.yaml`

## Troubleshooting

### Command Not Found

If `bazbeans` command is not found after installation:

```bash
# Check if it's in PATH
echo $PATH | grep bazbeans

# Check installation location
which bazbeans        # Linux/macOS
where bazbeans        # Windows

# Reinstall manually if needed
cd setup && ./install.sh
```

### Permission Errors

For system-wide installations, you may need administrator privileges:

```bash
# Linux/macOS
sudo ./install.sh --system

# Windows (PowerShell as Administrator)
.\install.ps1 -System
```

### Connection Errors

The CLI needs to connect to Redis. Check your configuration:

```bash
# Test Redis connection
redis-cli -h your-redis-host ping

# Override Redis URL
export BAZBEANS_REDIS_URL="redis://correct-host:6379/0"
bazbeans list-nodes
```

## Development Mode

For developers working on BazBeans:

```bash
# Install in development mode (skips auto-install)
pip install -e .

# Manual CLI setup for development
python setup_cli_installer.py

# Use Python module directly
python -m bazbeans.control_cli --help
```

## Uninstallation

To remove the CLI:

```bash
# Use the uninstaller
bazbeans-uninstall

# Or remove manually
rm -f ~/.local/bin/bazbeans     # Linux/macOS user install
rm -rf ~/.bazbeans/             # Remove configuration
```

## Environment Variables

You can control behavior with these environment variables:

- `BAZBEANS_SKIP_CLI_INSTALL=1` - Skip CLI auto-installation
- `BAZBEANS_CONFIG` - Path to configuration file
- `BAZBEANS_REDIS_URL` - Redis connection URL
- `BAZBEANS_DATA_CENTER` - Default data center
- `BAZBEANS_CPU_THRESHOLD` - CPU threshold percentage
- `BAZBEANS_MEMORY_THRESHOLD` - Memory threshold percentage

## Support

If you encounter issues with auto-installation:

1. Check the installation logs for specific error messages
2. Try manual installation using the setup scripts
3. Use the Python modules directly as a fallback
4. Report issues on the project GitHub page

## Technical Details

### Auto-Installer Components

- `setup_cli_installer.py` - Main auto-installer script
- `setup_cli_command.py` - Custom setuptools commands
- `post_install.py` - Post-installation hook
- `setup/install.sh` - Linux installer
- `setup/install-macos.sh` - macOS installer  
- `setup/install.ps1` - Windows installer

### Security Considerations

- Auto-installer runs with user permissions (no sudo required for user install)
- Scripts are included in the package and verified
- Installation can be skipped if needed
- Manual installation always available as fallback

### Compatibility

- **Python**: 3.8+
- **Operating Systems**: Linux, macOS, Windows
- **Package Managers**: pip, conda (manual installation recommended)
- **Shells**: bash, zsh, PowerShell, cmd