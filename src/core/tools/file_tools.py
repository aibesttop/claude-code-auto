"""
File System Tools
"""
import os
from pathlib import Path
from src.core.tool_registry import tool

@tool
def read_file(path: str) -> str:
    """
    Reads the content of a file.
    
    Args:
        path: The absolute or relative path to the file.
        
    Returns:
        The content of the file as a string.
    """
    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"Error: File not found at {path}"
        
        return file_path.read_text(encoding='utf-8')
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def write_file(path: str, content: str) -> str:
    """
    Writes content to a file. Creates directories if they don't exist.

    Args:
        path: The path to the file.
        content: The content to write.

    Returns:
        Success message with verification or error.
    """
    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        file_path.write_text(content, encoding='utf-8')

        # CRITICAL: Verify the file was actually written
        if not file_path.exists():
            return f"Error: File write completed but {path} does not exist on disk (silent write failure)"

        # Verify content matches
        written_content = file_path.read_text(encoding='utf-8')
        if written_content != content:
            return f"Error: File written but content mismatch detected in {path}"

        # Return success with verification details
        file_size = file_path.stat().st_size
        return f"Successfully wrote to {path} (verified: {file_size} bytes)"

    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool
def list_dir(path: str = ".") -> str:
    """
    Lists files in a directory.
    
    Args:
        path: The directory path (default: current directory).
        
    Returns:
        List of files and directories.
    """
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return f"Error: Directory not found at {path}"
            
        items = []
        for item in dir_path.iterdir():
            type_str = "DIR" if item.is_dir() else "FILE"
            items.append(f"[{type_str}] {item.name}")
            
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"
