#!/bin/bash
# BazBeans Installer for Ubuntu/Linux
# This script installs the 'bazbeans' command system-wide

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

# Create directories
print_info "Creating directories..."
mkdir -p "$BIN_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$BAZBEANS_HOME"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAZBEANS_SOURCE="$(dirname "$SCRIPT_DIR")"

# Check if bazbeans source exists
if [ ! -d "$BAZBEANS_SOURCE" ]; then
    print_error "BazBeans source not found at $BAZBEANS_SOURCE"
    exit 1
fi

# Install bazbeans command
print_info "Installing bazbeans command..."
cat > "$BIN_DIR/bazbeans" << 'EOF'
#!/bin/bash
# BazBeans CLI Wrapper

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

# Run the CLI
if [ -f "$BAZBEANS_HOME/bazbeans/control_cli.py" ]; then
    python3 "$BAZBEANS_HOME/bazbeans/control_cli.py" --redis-url "$REDIS_URL" "$@"
else
    echo "Error: BazBeans not found at $BAZBEANS_HOME"
    echo "Please run: bazbeans install"
    exit 1
fi
EOF

# Make executable
chmod +x "$BIN_DIR/bazbeans"

# Copy bazbeans source
print_info "Installing BazBeans files..."
$SUDO_PREFIX cp -r "$BAZBEANS_SOURCE" "$BAZBEANS_HOME"

# Install Python dependencies
print_info "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r "$BAZBEANS_HOME/requirements.txt"
else
    print_warn "pip3 not found, please install Python dependencies manually"
fi

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
    echo "Installation: $BAZBEANS_HOME"
    
    if [ "$SYSTEM_WIDE" = false ]; then
        echo
        print_warn "Remember to source your shell profile or restart your terminal"
    fi
else
    print_error "Installation failed - bazbeans command not found"
    exit 1
fi