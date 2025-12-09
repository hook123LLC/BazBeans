# BazBeans Installation Troubleshooting Guide

This guide helps resolve common installation issues with the BazBeans smart installer.

## Quick Diagnosis

The BazBeans installer automatically detects your installation method and adapts accordingly:

- **Package Manager Installation**: Installed via pip, pipx, or conda
- **Standalone Installation**: Traditional file-based installation
- **Fresh Installation**: No existing installation detected

## Common Issues

### Issue: "BazBeans Python package not found" after pipx install

**Symptoms:**
```bash
$ bazbeans list-nodes
Error: BazBeans Python package not found
Please ensure BazBeans is installed via pip, pipx, or conda
```

**Cause:** The CLI wrapper cannot find the pipx virtual environment.

**Solution:**

1. **Verify pipx installation:**
   ```bash
   pipx list | grep bazbeans
   ```

2. **Reinstall the CLI:**
   ```bash
   cd /path/to/BazBeans
   cd setup
   ./install.sh  # Linux/macOS
   # or
   .\install.ps1  # Windows
   ```

3. **Test the installation:**
   ```bash
   bazbeans --help
   ```

### Issue: "ModuleNotFoundError: No module named 'redis'" with pipx

**Symptoms:**
```bash
$ bazbeans list-nodes
ModuleNotFoundError: No module named 'redis'
```

**Cause:** The CLI wrapper is trying to use system Python instead of the pipx environment.

**Solution:**

The smart installer should handle this automatically. If you still see this error:

1. **Verify pipx installation:**
   ```bash
   pipx list
   ```

2. **Check if bazbeans is installed in pipx:**
   ```bash
   pipx run --spec bazbeans python -c "import redis; print('Redis available')"
   ```

3. **Reinstall the CLI wrapper:**
   ```bash
   cd /path/to/BazBeans/setup
   ./install.sh
   ```

### Issue: CLI not found after installation

**Symptoms:**
```bash
$ bazbeans
bash: bazbeans: command not found
```

**Solutions:**

**For Linux/macOS:**
```bash
# Add to PATH
export PATH="$PATH:$HOME/.local/bin"

# Make permanent
echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
source ~/.bashrc
```

**For Windows:**
```powershell
# Restart your terminal after installation
# Or manually add to PATH:
$env:PATH += ";$env:LOCALAPPDATA\BazBeans\bin"
```

### Issue: Permission denied errors

**Symptoms:**
```bash
$ ./install.sh
Permission denied
```

**Solution:**
```bash
chmod +x setup/install.sh
./setup/install.sh
```

## Installation Methods

### Method 1: pipx (Recommended for Development)

```bash
# Install with pipx
pipx install --editable .

# Install CLI wrapper
cd setup
./install.sh
```

**Advantages:**
- Isolated virtual environment
- No system package conflicts
- Easy to uninstall

**How it works:**
- The CLI wrapper detects pipx and uses `pipx run --spec bazbeans`
- All dependencies are contained in the pipx environment

### Method 2: pip (Standard Installation)

```bash
# Install with pip
pip install --user .

# Install CLI wrapper
cd setup
./install.sh
```

**Advantages:**
- Standard Python installation
- Works with existing Python environments

**How it works:**
- The CLI wrapper uses system Python
- Dependencies must be installed in the same environment

### Method 3: Standalone (No Package Manager)

```bash
# Run installer directly
cd setup
./install.sh
```

**Advantages:**
- No Python package manager required
- Self-contained installation

**How it works:**
- Copies all files to installation directory
- Installs dependencies with pip
- Creates CLI wrapper that uses the standalone installation

## Verification

### Check Installation Type

```bash
# Run the CLI with verbose output
bazbeans --help

# Check which Python is being used
which python3
python3 -c "import sys; print(sys.executable)"

# For pipx installations
pipx list | grep bazbeans
```

### Test CLI Functionality

```bash
# Basic commands
bazbeans --help
bazbeans list-nodes

# Check Redis connection
bazbeans status
```

## Manual Installation

If the automatic installer fails, you can create the CLI wrapper manually:

### For pipx installations:

```bash
cat > ~/.local/bin/bazbeans << 'EOF'
#!/bin/bash
REDIS_URL="${BAZBEANS_REDIS_URL:-redis://localhost:6379/0}"
exec pipx run --spec bazbeans python -c "from src.control_cli import cli; cli()" --redis-url "$REDIS_URL" "$@"
EOF

chmod +x ~/.local/bin/bazbeans
```

### For pip installations:

```bash
cat > ~/.local/bin/bazbeans << 'EOF'
#!/bin/bash
REDIS_URL="${BAZBEANS_REDIS_URL:-redis://localhost:6379/0}"
exec python3 -c "from src.control_cli import cli; cli()" --redis-url "$REDIS_URL" "$@"
EOF

chmod +x ~/.local/bin/bazbeans
```

## Uninstallation

### Remove CLI wrapper:
```bash
rm ~/.local/bin/bazbeans
rm ~/.local/bin/bazbeans-uninstall
```

### Remove package:
```bash
# For pipx
pipx uninstall bazbeans

# For pip
pip uninstall bazbeans

# For standalone
bazbeans-uninstall
```

### Remove configuration:
```bash
rm -rf ~/.bazbeans
```

## Getting Help

If you continue to experience issues:

1. **Check the logs:**
   - Installation output
   - CLI error messages

2. **Verify your environment:**
   ```bash
   python3 --version
   pip3 --version
   pipx --version  # if using pipx
   ```

3. **Report the issue:**
   - Include your OS and Python version
   - Include the full error message
   - Include the output of `pipx list` (if using pipx)

## Advanced Troubleshooting

### Debug the CLI wrapper

Add debug output to the wrapper:

```bash
# Edit ~/.local/bin/bazbeans
# Add these lines at the top:
set -x  # Enable debug mode
echo "Python: $(which python3)"
echo "REDIS_URL: $REDIS_URL"
```

### Check Python module paths

```bash
python3 -c "import sys; print('\n'.join(sys.path))"
```

### Verify package installation

```bash
# For pipx
pipx run --spec bazbeans python -c "import src; print(src.__file__)"

# For pip
python3 -c "import src; print(src.__file__)"
```

## Platform-Specific Notes

### Ubuntu/Debian
- May need to install `python3-pip` first
- Use `--user` flag with pip to avoid system package conflicts

### macOS
- May need to install Xcode Command Line Tools
- Use Homebrew Python if system Python is restricted

### Windows
- PowerShell execution policy may block scripts
- Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## See Also

- [Installation Guide](INSTALL-PYTHON-PACKAGE.md)
- [CLI Setup Guide](SETUP-CLI.md)
- [General Troubleshooting](TROUBLESHOOTING.md)