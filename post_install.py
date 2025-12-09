"""
Post-installation script for BazBeans package.

This script runs after pip install and attempts to install the OS-specific CLI.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Main entry point for post-install hook."""
    # Skip if running in certain environments
    if any(env in sys.argv for env in ['--user', '--develop', '-e']):
        print("[bazbeans] Skipping CLI auto-install for user/develop installation")
        return
    
    try:
        # Find the auto-installer script
        current_dir = Path(__file__).parent
        installer_path = current_dir / "setup_cli_installer.py"
        
        if not installer_path.exists():
            print("[bazbeans] CLI installer not found, skipping auto-installation")
            return
        
        print("\n" + "=" * 60)
        print("BazBeans CLI Auto-Installer")
        print("=" * 60)
        
        # Run the installer
        result = subprocess.run(
            [sys.executable, str(installer_path)],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n[bazbeans] CLI auto-installation completed successfully!")
        else:
            print(f"\n[bazbeans] CLI auto-installation failed (exit code: {result.returncode})")
            print("[bazbeans] You can install the CLI manually later if needed.")
            
    except Exception as e:
        print(f"[bazbeans] Auto-installation error: {e}")
        print("[bazbeans] CLI installation can be done manually using the setup scripts.")


if __name__ == "__main__":
    main()