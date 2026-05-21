"""
Shared command execution logic for both the FastAPI server and the LoRa serial reader.
Supports: bash_command, edit_file, basic_action, read_file, read_image
"""

import subprocess
import os
import sys
from io import StringIO
import base64


def execute_bash_command(command: str, timeout: int = 30) -> dict:
    """Execute a bash/shell command and return the result."""
    if not command:
        return {
            "status": "error",
            "type": "bash_command",
            "message": "Validation failed",
            "error_type": "ValidationError",
            "error_message": "command field is required for bash_command"
        }

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            "status": "success",
            "type": "bash_command",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "command": command
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "type": "bash_command",
            "message": "Command execution timed out",
            "error_type": "TimeoutError",
            "error_message": f"Command '{command}' exceeded {timeout} second timeout",
            "command": command
        }

    except Exception as e:
        return {
            "status": "error",
            "type": "bash_command",
            "message": "Command execution failed",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "command": command
        }


def execute_edit_file(file_name: str, file_content: str) -> dict:
    """Write content to a file."""
    if not file_name or file_content is None:
        return {
            "status": "error",
            "type": "edit_file",
            "message": "Validation failed",
            "error_type": "ValidationError",
            "error_message": "file_name and file_content are required for edit_file"
        }

    try:
        with open(file_name, 'w') as f:
            f.write(file_content)

        return {
            "status": "success",
            "type": "edit_file",
            "message": f"File '{file_name}' written successfully",
            "file_name": file_name,
            "bytes_written": len(file_content)
        }

    except PermissionError:
        return {
            "status": "error",
            "type": "edit_file",
            "message": "Permission denied",
            "error_type": "PermissionError",
            "error_message": f"Cannot write to '{file_name}' - permission denied",
            "file_name": file_name
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "type": "edit_file",
            "message": "Directory not found",
            "error_type": "FileNotFoundError",
            "error_message": f"Directory for '{file_name}' does not exist",
            "file_name": file_name
        }

    except Exception as e:
        return {
            "status": "error",
            "type": "edit_file",
            "message": "File write failed",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "file_name": file_name
        }


def execute_basic_action(action: str) -> dict:
    """Execute Python code and capture stdout."""
    if not action:
        return {
            "status": "error",
            "type": "basic_action",
            "message": "Validation failed",
            "error_type": "ValidationError",
            "error_message": "action field is required for basic_action"
        }

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    redirected_output = StringIO()
    redirected_error = StringIO()
    sys.stdout = redirected_output
    sys.stderr = redirected_error

    local_namespace = {}
    error_occurred = False
    error_message = ""
    error_type = ""

    try:
        exec(action, {"__builtins__": __builtins__}, local_namespace)
        output = redirected_output.getvalue()
    except Exception as e:
        error_occurred = True
        error_type = type(e).__name__
        error_message = str(e)
        output = redirected_output.getvalue()
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    if error_occurred:
        return {
            "status": "error",
            "type": "basic_action",
            "message": "Python code execution failed",
            "error_type": error_type,
            "error_message": error_message,
            "output": output
        }

    return {
        "status": "success",
        "type": "basic_action",
        "message": "Python code executed successfully",
        "output": output,
        "namespace": str(local_namespace)
    }


def execute_read_file(file_name: str) -> dict:
    """Read file contents."""
    if not file_name:
        return {
            "status": "error",
            "type": "read_file",
            "message": "Validation failed",
            "error_type": "ValidationError",
            "error_message": "file_name is required for read_file"
        }

    try:
        if not os.path.exists(file_name):
            return {
                "status": "error",
                "type": "read_file",
                "message": "File not found",
                "error_type": "FileNotFoundError",
                "error_message": f"File '{file_name}' does not exist",
                "file_name": file_name
            }

        with open(file_name, 'r') as f:
            content = f.read()

        return {
            "status": "success",
            "type": "read_file",
            "file_name": file_name,
            "content": content,
            "size_bytes": len(content)
        }

    except PermissionError:
        return {
            "status": "error",
            "type": "read_file",
            "message": "Permission denied",
            "error_type": "PermissionError",
            "error_message": f"Cannot read '{file_name}' - permission denied",
            "file_name": file_name
        }

    except UnicodeDecodeError:
        return {
            "status": "error",
            "type": "read_file",
            "message": "File encoding error",
            "error_type": "UnicodeDecodeError",
            "error_message": f"Cannot read '{file_name}' - file may be binary or have invalid encoding",
            "file_name": file_name
        }

    except Exception as e:
        return {
            "status": "error",
            "type": "read_file",
            "message": "File read failed",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "file_name": file_name
        }


def execute_read_image(file_name: str) -> dict:
    """Read an image file and return it as base64."""
    if not file_name:
        return {
            "status": "error",
            "type": "read_image",
            "message": "Validation failed",
            "error_type": "ValidationError",
            "error_message": "file_name is required for read_image"
        }

    try:
        if not os.path.exists(file_name):
            return {
                "status": "error",
                "type": "read_image",
                "message": "Image not found",
                "error_type": "FileNotFoundError",
                "error_message": f"Image '{file_name}' does not exist",
                "file_name": file_name
            }

        with open(file_name, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')

        file_ext = os.path.splitext(file_name)[1].lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(file_ext, 'image/png')

        return {
            "status": "success",
            "type": "read_image",
            "file_name": file_name,
            "image_data": image_base64,
            "mime_type": mime_type,
            "size_bytes": len(image_data)
        }

    except PermissionError:
        return {
            "status": "error",
            "type": "read_image",
            "message": "Permission denied",
            "error_type": "PermissionError",
            "error_message": f"Cannot read '{file_name}' - permission denied",
            "file_name": file_name
        }

    except Exception as e:
        return {
            "status": "error",
            "type": "read_image",
            "message": "Image read failed",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "file_name": file_name
        }


SUPPORTED_TYPES = ["bash_command", "edit_file", "basic_action", "read_file", "read_image"]


def execute_command(payload: dict) -> dict:
    """
    Route a command payload to the appropriate executor.
    
    payload must contain a 'type' key. Depending on the type:
      - bash_command:  requires 'command'
      - edit_file:     requires 'file_name' and 'file_content'
      - basic_action:  requires 'action'
      - read_file:     requires 'file_name'
      - read_image:    requires 'file_name'
    """
    cmd_type = payload.get("type")

    if cmd_type == "bash_command":
        return execute_bash_command(payload.get("command"))

    elif cmd_type == "edit_file":
        return execute_edit_file(payload.get("file_name"), payload.get("file_content"))

    elif cmd_type == "basic_action":
        return execute_basic_action(payload.get("action"))

    elif cmd_type == "read_file":
        return execute_read_file(payload.get("file_name"))

    elif cmd_type == "read_image":
        return execute_read_image(payload.get("file_name"))

    else:
        return {
            "status": "error",
            "type": cmd_type,
            "message": "Unknown command type",
            "error_type": "ValidationError",
            "error_message": f"Unknown type: '{cmd_type}'. Supported types: {', '.join(SUPPORTED_TYPES)}"
        }
