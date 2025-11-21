"""
Shell Execution Tools
"""
import subprocess
from pathlib import Path
from core.tool_registry import tool

@tool
def run_command(command: str) -> str:
    """
    Executes a shell command and returns the output.
    
    Args:
        command: The command to execute (e.g., 'ls -la', 'python script.py').
        
    Returns:
        Combined stdout and stderr.
    """
    try:
        # Basic safety guards (best-effort; should be replaced by real sandbox)
        lowered = command.lower()
        banned = ["rm -rf", "shutdown", "reboot", "format", "mkfs", ":(){", "poweroff", "del /", "rd /s", "chmod 777 /", "chown root"]
        if any(b in lowered for b in banned):
            return "Error: Command blocked by safety policy."

        if len(command) > 500:
            return "Error: Command too long."

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,  # Tighter default timeout
            cwd=str(Path.cwd())
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
            
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"
