#!/bin/bash
# BazBeans Smart Installer for Ubuntu/Linux
# This script detects the installation method and adapts accordingly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for user installation"
   print_info "Run without sudo for user installation or with sudo for system-wide installation"
   exit 1
fi

# Determine installation mode
SYSTEM_WIDE=false
if [[ "$1" == "--system" ]] || [[ "$1" == "sudo" ]]; then
    SYSTEM_WIDE=true
fi

# Installation paths
if [ "$SYSTEM_WIDE" = true ]; then
    BIN_DIR="/usr/local/bin"
    CONFIG_DIR="/etc/bazbeans"
    BAZBEANS_HOME="/opt/bazbeans"
    SUDO_PREFIX="sudo"
else
    BIN_DIR="$HOME/.local/bin"
    CONFIG_DIR="$HOME/.bazbeans"
    BAZBEANS_HOME="$HOME/.local/share/bazbeans"
    SUDO_PREFIX=""
fi

# Detect installation method
print_info "Detecting installation method..."
INSTALL_MODE="unknown"

# Check if bazbeans is already installed via package manager (pip/pipx/conda)
if command -v pipx &> /dev/null && pipx list 2>/dev/null | grep -q "bazbeans"; then
    print_info "BazBeans detected in pipx"
    INSTALL_MODE="package_manager"
elif python3 -c "import bazbeans" 2>/dev/null || python3 -c "import src.control_cli" 2>/dev/null; then
    print_info "BazBeans Python package detected (installed via pip/conda)"
    INSTALL_MODE="package_manager"
elif [ -d "$BAZBEANS_HOME" ] || [ -d "/opt/bazbeans" ]; then
    print_info "Existing standalone installation detected"
    INSTALL_MODE="standalone"
else
    print_info "No existing installation found - will perform standalone installation"
    INSTALL_MODE="fresh"
fi

# Create directories
print_info "Creating directories..."
mkdir -p "$BIN_DIR"
mkdir -p "$CONFIG_DIR"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAZBEANS_SOURCE="$(dirname "$SCRIPT_DIR")"

# Check if bazbeans source exists
if [ ! -d "$BAZBEANS_SOURCE" ]; then
    print_error "BazBeans source not found at $BAZBEANS_SOURCE"
    exit 1
fi

# Function to create CLI wrapper for package manager installations
create_package_manager_wrapper() {
    print_info "Creating CLI wrapper for package manager installation..."
    
    cat > "$BIN_DIR/bazbeans" << 'EOF'
#!/bin/bash
# BazBeans CLI Wrapper for Package Manager Installation

# Find configuration file
CONFIG_LOCATIONS=(
    "$BAZBEANS_CONFIG"
    "$HOME/.bazbeans/config.yaml"
    "/etc/bazbeans/config.yaml"
    "./bazbeans.yaml"
)

CONFIG_FILE=""
for loc in "${CONFIG_LOCATIONS[@]}"; do
    if [ -f "$loc" ]; then
        CONFIG_FILE="$loc"
        break
    fi
done

# Extract redis_url from config if available
REDIS_URL=""
if [ -n "$CONFIG_FILE" ]; then
    REDIS_URL=$(grep -E '^redis_url:' "$CONFIG_FILE" | cut -d: -f2- | tr -d ' "')
fi

# Use environment variable if set, then config, then default
if [ -z "$REDIS_URL" ]; then
    REDIS_URL="${BAZBEANS_REDIS_URL:-redis://localhost:6379/0}"
fi

# Try to run via Python module (works with pip/pipx/conda installations)
# First try pipx (which handles its own virtual environment)
if command -v pipx &> /dev/null; then
    if pipx list 2>/dev/null | grep -q "bazbeans"; then
        exec pipx run --spec bazbeans python -c "from src.control_cli import cli; cli()" --redis-url "$REDIS_URL" "$@"
    fi
fi

# Try direct Python import (for pip/conda installations)
if python3 -c "import src.control_cli" 2>/dev/null; then
    exec python3 -c "from src.control_cli import cli; cli()" --redis-url "$REDIS_URL" "$@"
elif python3 -c "import bazbeans.control_cli" 2>/dev/null; then
    exec python3 -c "from bazbeans.control_cli import cli; cli()" --redis-url "$REDIS_URL" "$@"
else
    echo "Error: BazBeans Python package not found"
    echo "Please ensure BazBeans is installed via pip, pipx, or conda"
    exit 1
fi
EOF

    chmod +x "$BIN_DIR/bazbeans"
    print_info "CLI wrapper created successfully"
}

# Function to create CLI wrapper for standalone installations
create_standalone_wrapper() {
    print_info "Creating CLI wrapper for standalone installation..."
    
    cat > "$BIN_DIR/bazbeans" << 'EOF'
#!/bin/bash
# BazBeans CLI Wrapper for Standalone Installation

# Find configuration file
CONFIG_LOCATIONS=(
    "$BAZBEANS_CONFIG"
    "$HOME/.bazbeans/config.yaml"
    "/etc/bazbeans/config.yaml"
    "./bazbeans.yaml"
)

CONFIG_FILE=""
for loc in "${CONFIG_LOCATIONS[@]}"; do
    if [ -f "$loc" ]; then
        CONFIG_FILE="$loc"
        break
    fi
done

# Extract redis_url from config if available
REDIS_URL=""
if [ -n "$CONFIG_FILE" ]; then
    REDIS_URL=$(grep -E '^redis_url:' "$CONFIG_FILE" | cut -d: -f2- | tr -d ' "')
fi

# Use environment variable if set, then config, then default
if [ -z "$REDIS_URL" ]; then
    REDIS_URL="${BAZBEANS_REDIS_URL:-redis://localhost:6379/0}"
fi

# Find bazbeans installation
BAZBEANS_HOME="${BAZBEANS_HOME:-$HOME/.local/share/bazbeans}"
if [ ! -d "$BAZBEANS_HOME" ]; then
    BAZBEANS_HOME="/opt/bazbeans"
fi

# Run the CLI from standalone installation
if [ -f "$BAZBEANS_HOME/src/control_cli.py" ]; then
    exec python3 -c "import sys, os; sys.path.insert(0, os.path.normpath(r'$BAZBEANS_HOME')); from src.control_cli import cli; cli()" --redis-url "$REDIS_URL" "$@"
else
    echo "Error: BazBeans not found at $BAZBEANS_HOME"
    echo "Please reinstall BazBeans"
    exit 1
fi
EOF

    chmod +x "$BIN_DIR/bazbeans"
    print_info "CLI wrapper created successfully"
}

# Handle installation based on detected mode
case $INSTALL_MODE in
    "package_manager")
        print_info "Installing CLI wrapper for package manager installation..."
        create_package_manager_wrapper
        
        # Check if entry points were created
        if command -v bazbeans-cli &> /dev/null; then
            print_info "Entry point 'bazbeans-cli' detected - you can also use that command"
        fi
        ;;
        
    "standalone"|"fresh")
        print_info "Performing standalone installation..."
        
        # Create installation directory
        mkdir -p "$BAZBEANS_HOME"
        
        # Copy bazbeans source
        print_info "Installing BazBeans files to $BAZBEANS_HOME..."
        cd "$BAZBEANS_SOURCE"
        shopt -s dotglob
        for item in *; do
            if [ "$item" != ".git" ]; then
                $SUDO_PREFIX cp -r "$item" "$BAZBEANS_HOME"
            fi
        done
        shopt -u dotglob
        
        # Install Python dependencies only for fresh installations
        if [ "$INSTALL_MODE" = "fresh" ]; then
            print_info "Installing Python dependencies..."
            if command -v pip3 &> /dev/null; then
                pip3 install --user -r "$BAZBEANS_HOME/requirements.txt" || print_warn "Some dependencies may have failed to install"
            else
                print_warn "pip3 not found, please install Python dependencies manually:"
                print_warn "  pip3 install --user -r $BAZBEANS_HOME/requirements.txt"
            fi
        else
            print_info "Skipping dependency installation (updating existing installation)"
        fi
        
        # Create standalone wrapper
        create_standalone_wrapper
        ;;
        
    *)
        print_error "Could not determine installation method"
        exit 1
        ;;
esac

# Install configuration file
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    print_info "Installing default configuration..."
    $SUDO_PREFIX cp "$SCRIPT_DIR/bazbeans.yaml" "$CONFIG_DIR/config.yaml"
else
    print_warn "Configuration already exists at $CONFIG_DIR/config.yaml"
fi

# Update PATH for user installation
if [ "$SYSTEM_WIDE" = false ]; then
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        print_info "Adding $BIN_DIR to PATH..."
        
        # Determine shell profile
        SHELL_PROFILE=""
        if [ -n "$BASH_VERSION" ]; then
            SHELL_PROFILE="$HOME/.bashrc"
        elif [ -n "$ZSH_VERSION" ]; then
            SHELL_PROFILE="$HOME/.zshrc"
        fi
        
        if [ -n "$SHELL_PROFILE" ]; then
            echo "" >> "$SHELL_PROFILE"
            echo "# BazBeans" >> "$SHELL_PROFILE"
            echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$SHELL_PROFILE"
            print_info "Please run: source $SHELL_PROFILE"
        else
            print_warn "Please add $BIN_DIR to your PATH"
        fi
    fi
fi

# Create uninstall script
print_info "Creating uninstall script..."
cat > "$BIN_DIR/bazbeans-uninstall" << EOF
#!/bin/bash
# BazBeans Uninstaller

echo "This will remove BazBeans from your system."
read -p "Are you sure? [y/N] " -n 1 -r
echo
if [[ \$REPLY =~ ^[Yy]\$ ]]; then
    echo "Removing bazbeans command..."
    rm -f "$BIN_DIR/bazbeans"
    
    echo "Removing BazBeans files..."
    $SUDO_PREFIX rm -rf "$BAZBEANS_HOME"
    
    echo "Removing configuration..."
    $SUDO_PREFIX rm -rf "$CONFIG_DIR"
    
    echo "BazBeans uninstalled successfully."
    echo "Note: If installed via pip/pipx, also run: pip uninstall bazbeans"
else
    echo "Uninstall cancelled."
fi
EOF

chmod +x "$BIN_DIR/bazbeans-uninstall"

# Test installation
print_info "Testing installation..."
if command -v bazbeans &> /dev/null; then
    print_info "BazBeans installed successfully!"
    echo
    echo "Usage:"
    echo "  bazbeans list-nodes"
    echo "  bazbeans freeze <node-id>"
    echo "  bazbeans --help"
    echo
    echo "Configuration: $CONFIG_DIR/config.yaml"
    
    if [ "$INSTALL_MODE" = "package_manager" ]; then
        echo "Installation: Python package (via pip/pipx/conda)"
    else
        echo "Installation: $BAZBEANS_HOME"
    fi
    
    if [ "$SYSTEM_WIDE" = false ]; then
        echo
        print_warn "Remember to source your shell profile or restart your terminal"
    fi
else
    print_error "Installation failed - bazbeans command not found"
    exit 1
fi