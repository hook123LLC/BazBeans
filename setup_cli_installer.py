#!/usr/bin/env python3
"""
BazBeans CLI Auto-Installer

This script automatically installs the OS-specific BazBeans CLI when the package
is installed via pip. It detects the operating system and runs the appropriate
installation script.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def detect_os():
    """Detect the current operating system."""
    system = platform.system().lower()
    
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"


def get_installer_script_path():
    """Get the path to the appropriate installer script."""
    # Get the directory where this script is located
    current_dir = Path(__file__).parent
    
    # Look the package for setup directory in
    setup_dir = current_dir / "setup"
    
    if not setup_dir.exists():
        # Try to find setup directory in the source
        setup_dir = current_dir.parent / "setup"
    
    if not setup_dir.exists():
        raise FileNotFoundError("Setup directory not found")
    
    os_type = detect_os()
    
    if os_type == "windows":
        script_path = setup_dir / "install.ps1"
    elif os_type == "macos":
        script_path = setup_dir / "install-macos.sh"
    elif os_type == "linux":
        script_path = setup_dir / "install.sh"
    else:
        raise OSError(f"Unsupported operating system: {os_type}")
    
    if not script_path.exists():
        raise FileNotFoundError(f"Installer script not found: {script_path}")
    
    return script_path, os_type


def run_cli_installer():
    """Run the OS-specific CLI installer."""
    try:
        script_path, os_type = get_installer_script_path()
        
        print(f"[bazbeans] Detected OS: {os_type}")
        print(f"[bazbeans] Running CLI installer: {script_path}")
        
        # Make script executable on Unix systems
        if os_type in ["linux", "macos"]:
            os.chmod(script_path, 0o755)
            cmd = [str(script_path)]
        else:
            # Windows PowerShell
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
        
        # Run the installer
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print("[bazbeans] CLI installation completed successfully!")
            print("[bazbeans] You can now use the 'bazbeans' command")
            
            # Show usage examples
            print("\nUsage examples:")
            print("  bazbeans --help")
            print("  bazbeans list-nodes")
            print("  bazbeans freeze <node-id>")
            
            return True
        else:
            print(f"[bazbeans] CLI installation failed with exit code: {result.returncode}")
            if result.stderr:
                print(f"[bazbeans] Error: {result.stderr}")
            if result.stdout:
                print(f"[bazbeans] Output: {result.stdout}")
            return False
            
    except FileNotFoundError as e:
        print(f"[bazbeans] Warning: {e}")
        print("[bazbeans] CLI installer not available. You can install manually using:")
        print("  cd setup && ./install.sh  # Linux/macOS")
        print("  cd setup && .\\install.ps1 # Windows")
        return False
    except subprocess.TimeoutExpired:
        print("[bazbeans] CLI installation timed out")
        return False
    except Exception as e:
        print(f"[bazbeans] Unexpected error during CLI installation: {e}")
        return False


def main():
    """Main entry point for the CLI installer."""
    print("=" * 50)
    print("BazBeans CLI Auto-Installer")
    print("=" * 50)
    
    # Check if user wants to skip CLI installation
    if "--skip-cli-install" in sys.argv:
        print("[bazbeans] Skipping CLI installation as requested")
        return
    
    # Check environment variable to skip installation
    if os.environ.get("BAZBEANS_SKIP_CLI_INSTALL"):
        print("[bazbeans] Skipping CLI installation (BAZBEANS_SKIP_CLI_INSTALL set)")
        return
    
    try:
        success = run_cli_installer()
        if not success:
            print("\n[BazBeans] CLI installation failed, but Python package is still usable.")
            print("[BazBeans] You can use the CLI via: python -m bazbeans.control_cli")
    except Exception as e:
        print(f"\n[BazBeans] Auto-installer encountered an error: {e}")
        print("[BazBeans] Python package is still fully functional.")
        print("[BazBeans] You can install the CLI manually if needed.")


if __name__ == "__main__":
    main()