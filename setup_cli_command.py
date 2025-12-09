"""
Custom setuptools command for BazBeans CLI auto-installation.

This module provides a custom setuptools command that automatically installs
the OS-specific BazBeans CLI when the package is installed via pip.
"""

from setuptools import Command
from setuptools.command.install import install
import subprocess
import sys
import os
from pathlib import Path


class BazBeansCLIInstallCommand(install):
    """Custom install command that auto-installs the CLI."""
    
    description = "Auto-install OS-specific BazBeans CLI after package installation"
    
    def run(self):
        """Run the install command and then auto-install CLI."""
        # Run the standard install first
        install.run(self)
        
        # Auto-install the CLI
        self.auto_install_cli()
    
    def auto_install_cli(self):
        """Automatically install the OS-specific CLI."""
        try:
            # Find the auto-installer script
            current_dir = Path(__file__).parent
            installer_path = current_dir / "setup_cli_installer.py"
            
            if not installer_path.exists():
                print("[bazbeans] CLI installer not found, skipping auto-installation")
                return
            
            print("\n" + "=" * 50)
            print("BazBeans CLI Auto-Installer")
            print("=" * 50)
            
            # Run the installer
            result = subprocess.run(
                [sys.executable, str(installer_path)],
                capture_output=False,  # Let the installer handle output
                text=True
            )
            
            if result.returncode == 0:
                print("[bazbeans] CLI auto-installation completed successfully!")
            else:
                print(f"[bazbeans] CLI auto-installation failed (exit code: {result.returncode})")
                print("[bazbeans] You can install the CLI manually later if needed.")
                
        except Exception as e:
            print(f"[bazbeans] Auto-installation error: {e}")
            print("[bazbeans] CLI installation can be done manually using the setup scripts.")


class BazBeansCLIInstallDevelopCommand(BazBeansCLIInstallCommand):
    """Auto-install CLI for development installations."""
    
    description = "Auto-install OS-specific BazBeans CLI after develop installation"
    
    def run(self):
        """Run the develop command and then auto-install CLI."""
        # For development installs, we don't want to auto-install CLI
        # as it might interfere with the development environment
        install.run(self)
        print("[bazbeans] Skipping CLI auto-installation for development installation")
        print("[bazbeans] You can manually install CLI using: python setup_cli_installer.py")


# Register the custom commands
def get_cmdclass():
    """Return the custom command classes for setuptools."""
    return {
        'install_cli': BazBeansCLIInstallCommand,
        'develop_cli': BazBeansCLIInstallDevelopCommand,
    }