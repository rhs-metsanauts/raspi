from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from command_executor import execute_command, SUPPORTED_TYPES

app = FastAPI(title="Remote Command Server")


class CommandPayload(BaseModel):
    type: str
    command: Optional[str] = None
    file_name: Optional[str] = None
    file_content: Optional[str] = None
    action: Optional[str] = None


@app.post("/execute")
async def handle_execute(payload: CommandPayload):
    """
    Execute various commands based on the payload type:
    - bash_command: Run bash/shell commands
    - edit_file: Write content to a file
    - basic_action: Execute Python code
    - read_file: Read file contents
    - read_image: Read image as base64
    """
    try:
        return execute_command(payload.model_dump())
    except Exception as e:
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
        "supported_types": SUPPORTED_TYPES
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
