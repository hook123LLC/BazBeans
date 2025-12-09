"""
BazBeans Docker Commands Plugin

Example plugin providing docker-compose service management.
This demonstrates how to create pluggable command handlers.
"""

import subprocess
import time
from typing import Dict, Any
from .config import BazBeansConfig


class DockerComposeCommands:
    """
    Example plugin providing docker-compose service management commands.
    """
    
    def __init__(self, config: BazBeansConfig):
        """
        Initialize docker-compose commands.
        
        Args:
            config: BazBeans configuration
        """
        self.config = config
        self.app_dir = config.app_dir
        self.compose_file = config.compose_file
    
    def get_handlers(self) -> Dict[str, callable]:
        """
        Get command handlers for registration with NodeAgent.
        
        Returns:
            Dictionary mapping command names to handler functions
        """
        return {
            "start": self._cmd_start,
            "stop": self._cmd_stop,
            "restart": self._cmd_restart,
            "update": self._cmd_update,
            "pull": self._cmd_pull,
            "logs": self._cmd_logs,
            "status": self._cmd_status,
        }
    
    def _run_docker_compose(self, args: list) -> Dict[str, Any]:
        """
        Run a docker-compose command and return result.
        
        Args:
            args: Arguments to pass to docker-compose
            
        Returns:
            Dictionary with stdout, stderr, and returncode
        """
        cmd = ["docker-compose", "-f", self.compose_file] + args
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Command timed out after 5 minutes",
                "returncode": -1,
                "success": False
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "success": False
            }
    
    def _cmd_start(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start docker-compose services.
        
        Args:
            command: Command dictionary (may contain 'services' key)
            
        Returns:
            Result dictionary
        """
        args = ["up", "-d"]
        
        # Add specific services if provided
        if "services" in command:
            args.extend(command["services"])
        
        result = self._run_docker_compose(args)
        result["message"] = "Start command executed"
        return result
    
    def _cmd_stop(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stop docker-compose services.
        
        Args:
            command: Command dictionary (may contain 'services' key)
            
        Returns:
            Result dictionary
        """
        args = ["down"]
        
        # If specific services, use stop instead
        if "services" in command:
            args = ["stop"] + command["services"]
        
        result = self._run_docker_compose(args)
        result["message"] = "Stop command executed"
        return result
    
    def _cmd_restart(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Restart docker-compose services.
        
        Args:
            command: Command dictionary (may contain 'services' key)
            
        Returns:
            Result dictionary
        """
        args = ["restart"]
        
        # Add specific services if provided
        if "services" in command:
            args.extend(command["services"])
        
        result = self._run_docker_compose(args)
        result["message"] = "Restart command executed"
        return result
    
    def _cmd_update(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update application (pull new images and recreate).
        
        Args:
            command: Command dictionary
            
        Returns:
            Result dictionary with steps
        """
        steps = []
        
        # Step 1: Pull new images
        pull_result = self._cmd_pull({})
        steps.append({
            "step": "pull",
            "success": pull_result["success"],
            "output": pull_result["stdout"],
            "error": pull_result["stderr"]
        })
        
        if not pull_result["success"]:
            return {
                "success": False,
                "message": "Update failed during pull",
                "steps": steps
            }
        
        # Step 2: Recreate containers
        recreate_result = self._run_docker_compose(["up", "-d", "--force-recreate"])
        steps.append({
            "step": "recreate",
            "success": recreate_result["success"],
            "output": recreate_result["stdout"],
            "error": recreate_result["stderr"]
        })
        
        # Step 3: Wait and check status
        if "wait_seconds" in command:
            time.sleep(command["wait_seconds"])
            status_result = self._cmd_status({})
            steps.append({
                "step": "status_check",
                "success": status_result["success"],
                "output": status_result["stdout"],
                "error": status_result["stderr"]
            })
        
        return {
            "success": recreate_result["success"],
            "message": "Update completed",
            "steps": steps
        }
    
    def _cmd_pull(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pull latest images.
        
        Args:
            command: Command dictionary (may contain 'services' key)
            
        Returns:
            Result dictionary
        """
        args = ["pull"]
        
        # Add specific services if provided
        if "services" in command:
            args.extend(command["services"])
        
        result = self._run_docker_compose(args)
        result["message"] = "Pull command executed"
        return result
    
    def _cmd_logs(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get logs from services.
        
        Args:
            command: Command dictionary with options:
                - services: List of services (optional)
                - tail: Number of lines to show (default: 100)
                - follow: Whether to follow logs (default: false)
                
        Returns:
            Result dictionary with logs
        """
        args = ["logs"]
        
        # Add options
        if "tail" in command:
            args.extend(["--tail", str(command["tail"])])
        else:
            args.extend(["--tail", "100"])
        
        if command.get("follow", False):
            args.append("--follow")
        
        # Add services if provided
        if "services" in command:
            args.extend(command["services"])
        
        # For follow mode, we can't capture output easily
        if command.get("follow", False):
            return {
                "success": True,
                "message": "Following logs (use docker-compose directly for follow mode)",
                "command": f"cd {self.app_dir} && docker-compose -f {self.compose_file} {' '.join(args)}"
            }
        
        result = self._run_docker_compose(args)
        result["message"] = "Logs retrieved"
        return result
    
    def _cmd_status(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get status of services.
        
        Args:
            command: Command dictionary
            
        Returns:
            Result dictionary with service status
        """
        result = self._run_docker_compose(["ps"])
        result["message"] = "Service status retrieved"
        return result