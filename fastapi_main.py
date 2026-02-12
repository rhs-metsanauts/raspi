from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import subprocess
import os
import sys
from io import StringIO

app = FastAPI(title="Remote Command Server")


class CommandPayload(BaseModel):
    type: str
    command: Optional[str] = None
    file_name: Optional[str] = None
    file_content: Optional[str] = None
    action: Optional[str] = None


@app.post("/execute")
async def execute_command(payload: CommandPayload):
    """
    Execute various commands based on the payload type:
    - bash_command: Run bash/shell commands
    - edit_file: Write content to a file
    - basic_action: Execute Python code
    - read_file: Read file contents
    """
    try:
        if payload.type == "bash_command":
            if not payload.command:
                return {
                    "status": "error",
                    "type": "bash_command",
                    "message": "Validation failed",
                    "error_type": "ValidationError",
                    "error_message": "command field is required for bash_command"
                }
           
            try:
                # Execute bash command
                result = subprocess.run(
                    payload.command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
               
                return {
                    "status": "success",
                    "type": "bash_command",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "command": payload.command
                }
           
            except subprocess.TimeoutExpired:
                return {
                    "status": "error",
                    "type": "bash_command",
                    "message": "Command execution timed out",
                    "error_type": "TimeoutError",
                    "error_message": f"Command '{payload.command}' exceeded 30 second timeout",
                    "command": payload.command
                }
           
            except Exception as e:
                return {
                    "status": "error",
                    "type": "bash_command",
                    "message": "Command execution failed",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "command": payload.command
                }
       
        elif payload.type == "edit_file":
            if not payload.file_name or payload.file_content is None:
                return {
                    "status": "error",
                    "type": "edit_file",
                    "message": "Validation failed",
                    "error_type": "ValidationError",
                    "error_message": "file_name and file_content are required for edit_file"
                }
           
            try:
                # Write content to file
                with open(payload.file_name, 'w') as f:
                    f.write(payload.file_content)
               
                return {
                    "status": "success",
                    "type": "edit_file",
                    "message": f"File '{payload.file_name}' written successfully",
                    "file_name": payload.file_name,
                    "bytes_written": len(payload.file_content)
                }
           
            except PermissionError:
                return {
                    "status": "error",
                    "type": "edit_file",
                    "message": "Permission denied",
                    "error_type": "PermissionError",
                    "error_message": f"Cannot write to '{payload.file_name}' - permission denied",
                    "file_name": payload.file_name
                }
           
            except FileNotFoundError:
                return {
                    "status": "error",
                    "type": "edit_file",
                    "message": "Directory not found",
                    "error_type": "FileNotFoundError",
                    "error_message": f"Directory for '{payload.file_name}' does not exist",
                    "file_name": payload.file_name
                }
           
            except Exception as e:
                return {
                    "status": "error",
                    "type": "edit_file",
                    "message": "File write failed",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "file_name": payload.file_name
                }
       
        elif payload.type == "basic_action":
            if not payload.action:
                raise HTTPException(status_code=400, detail="action field is required for basic_action")
           
            # Execute Python code and capture stdout
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
                exec(payload.action, {"__builtins__": __builtins__}, local_namespace)
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
       
        elif payload.type == "read_file":
            if not payload.file_name:
                return {
                    "status": "error",
                    "type": "read_file",
                    "message": "Validation failed",
                    "error_type": "ValidationError",
                    "error_message": "file_name is required for read_file"
                }
           
            try:
                # Read file contents
                if not os.path.exists(payload.file_name):
                    return {
                        "status": "error",
                        "type": "read_file",
                        "message": "File not found",
                        "error_type": "FileNotFoundError",
                        "error_message": f"File '{payload.file_name}' does not exist",
                        "file_name": payload.file_name
                    }
               
                with open(payload.file_name, 'r') as f:
                    content = f.read()
               
                return {
                    "status": "success",
                    "type": "read_file",
                    "file_name": payload.file_name,
                    "content": content,
                    "size_bytes": len(content)
                }
           
            except PermissionError:
                return {
                    "status": "error",
                    "type": "read_file",
                    "message": "Permission denied",
                    "error_type": "PermissionError",
                    "error_message": f"Cannot read '{payload.file_name}' - permission denied",
                    "file_name": payload.file_name
                }
           
            except UnicodeDecodeError:
                return {
                    "status": "error",
                    "type": "read_file",
                    "message": "File encoding error",
                    "error_type": "UnicodeDecodeError",
                    "error_message": f"Cannot read '{payload.file_name}' - file may be binary or have invalid encoding",
                    "file_name": payload.file_name
                }
           
            except Exception as e:
                return {
                    "status": "error",
                    "type": "read_file",
                    "message": "File read failed",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "file_name": payload.file_name
                }
       
        else:
            return {
                "status": "error",
                "type": payload.type,
                "message": "Unknown command type",
                "error_type": "ValidationError",
                "error_message": f"Unknown type: '{payload.type}'. Supported types: bash_command, edit_file, basic_action, read_file"
            }
   
    except Exception as e:
        # Catch-all for any unexpected errors
        return {
            "status": "error",
            "type": payload.type if hasattr(payload, 'type') else "unknown",
            "message": "Unexpected server error",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "Remote Command Server is running",
        "supported_types": ["bash_command", "edit_file", "basic_action", "read_file"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
