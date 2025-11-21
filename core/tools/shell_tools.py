"""
Shell Execution Tools
"""
import subprocess
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
        # Security warning: In a real prod env, this needs strict sandboxing!
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60 # Default timeout
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
            
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"
