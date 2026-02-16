from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import requests
import json
import os
from ollama import chat
from pydantic import BaseModel
from typing import Optional

app = Flask(__name__)

# Configuration
FASTAPI_SERVER_URL = "http://localhost:8000/execute"
DEFAULT_TIMEOUT = 35
TRANSMISSION_MODE = "wifi"  # "wifi" or "lora"
LORA_DESTINATION = 0  # Integer destination for LoRA
LORA_MESSAGE_PATH = r"D:\message.json"  # Path where LoRA transmitter reads messages from
OLLAMA_MODEL = "qwen3:0.6b"  # Ollama model for AI assistant

# Load AI system prompt from markdown file
_PROMPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_system_prompt.md")
with open(_PROMPT_PATH, "r", encoding="utf-8") as _f:
    AI_SYSTEM_PROMPT = _f.read()

# Load Robot.py source so the LLM knows every available class/method
_ROBOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Robot.py")
with open(_ROBOT_PATH, "r", encoding="utf-8") as _f:
    _ROBOT_SOURCE = _f.read()

AI_SYSTEM_PROMPT += "\n\n## Robot.py Source Code\n\n```python\n" + _ROBOT_SOURCE + "\n```\n"


class RoverCommand(BaseModel):
    """Structured output the LLM must produce."""
    type: str  # bash_command | edit_file | basic_action | read_file | read_image
    fields: dict


@app.route('/')
def index():
    """Render the main UI page"""
    return render_template('index.html')


@app.route('/send_command', methods=['POST'])
def send_command():
    """Forward command via WiFi to FastAPI server, or save to file for LoRA"""
    try:
        data = request.get_json()
        mode = data.pop('mode', TRANSMISSION_MODE)

        if mode == 'lora':
            return _send_lora(data)
        else:
            return _send_wifi(data)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def _send_wifi(data):
    """Send command over WiFi to FastAPI server"""
    try:
        timeout = data.pop('timeout', DEFAULT_TIMEOUT)
        response = requests.post(FASTAPI_SERVER_URL, json=data, timeout=timeout)

        return jsonify({
            "success": True,
            "status_code": response.status_code,
            "data": response.json()
        })

    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "error": "Could not connect to Rover. Make sure it's powered on and connected to the network."
        }), 503

    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "error": "Request timed out"
        }), 408


def _send_lora(data):
    """Save command as JSON to file for LoRA transmission"""
    try:
        lora_dest = data.pop('lora_destination', LORA_DESTINATION)
        data.pop('timeout', None)

        # Build payload with Recipient field for the LoRA transmitter
        payload = {"Recipient": int(lora_dest)}
        payload.update(data)

        with open(LORA_MESSAGE_PATH, 'w') as f:
            json.dump(payload, f, indent=2)

        return jsonify({
            "success": True,
            "data": {
                "status": "queued",
                "message": f"Payload written to {LORA_MESSAGE_PATH} for LoRA transmission",
                "recipient": int(lora_dest),
                "payload_size": len(json.dumps(payload))
            }
        })

    except (FileNotFoundError, OSError) as e:
        return jsonify({
            "success": False,
            "error": "Cannot write to LoRA module. Please check that the LoRA transmitter is connected and the drive is accessible."
        }), 503
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to write LoRA message file: {str(e)}"
        }), 500


@app.route('/config', methods=['GET', 'POST'])
def config():
    """Get or update server configuration"""
    global FASTAPI_SERVER_URL, DEFAULT_TIMEOUT, TRANSMISSION_MODE, LORA_DESTINATION

    if request.method == 'POST':
        data = request.get_json()
        FASTAPI_SERVER_URL = data.get('server_url', FASTAPI_SERVER_URL)
        DEFAULT_TIMEOUT = data.get('timeout', DEFAULT_TIMEOUT)
        TRANSMISSION_MODE = data.get('mode', TRANSMISSION_MODE)
        LORA_DESTINATION = data.get('lora_destination', LORA_DESTINATION)
        return jsonify({
            "success": True,
            "server_url": FASTAPI_SERVER_URL,
            "timeout": DEFAULT_TIMEOUT,
            "mode": TRANSMISSION_MODE,
            "lora_destination": LORA_DESTINATION
        })

    return jsonify({
        "server_url": FASTAPI_SERVER_URL,
        "timeout": DEFAULT_TIMEOUT,
        "mode": TRANSMISSION_MODE,
        "lora_destination": LORA_DESTINATION
    })


@app.route('/ai_command', methods=['POST'])
def ai_command():
    """Stream an LLM response that decides the command type and body."""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        history = data.get('history', [])
        mode = data.get('mode', TRANSMISSION_MODE)

        if not user_message:
            return jsonify({"success": False, "error": "No message provided"}), 400

        # Build messages list: system prompt (with current mode), then history, then user msg
        system_content = AI_SYSTEM_PROMPT + f"\n\n## Current Transmission Mode\nThe current mode is **{mode}**."
        messages = [{"role": "system", "content": system_content}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        def generate():
            """SSE generator that streams thinking + final JSON."""
            thinking_buffer = ""
            content_buffer = ""
            in_thinking = False

            stream = chat(
                model=OLLAMA_MODEL,
                messages=messages,
                think=True,
                stream=True,
                format=RoverCommand.model_json_schema(),
            )

            for chunk in stream:
                # Thinking tokens
                if chunk.message.thinking:
                    if not in_thinking:
                        in_thinking = True
                        yield f"data: {json.dumps({'type': 'thinking_start'})}\n\n"
                    thinking_buffer += chunk.message.thinking
                    yield f"data: {json.dumps({'type': 'thinking', 'content': chunk.message.thinking})}\n\n"

                # Content tokens (the actual JSON answer)
                if chunk.message.content:
                    if in_thinking:
                        in_thinking = False
                        yield f"data: {json.dumps({'type': 'thinking_end'})}\n\n"
                    content_buffer += chunk.message.content
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk.message.content})}\n\n"

            # Parse final structured result
            try:
                command = RoverCommand.model_validate_json(content_buffer)
                yield f"data: {json.dumps({'type': 'result', 'command': command.model_dump()})}\n\n"
            except Exception as parse_err:
                yield f"data: {json.dumps({'type': 'error', 'error': f'Failed to parse LLM output: {str(parse_err)}'})}\n\n"

            yield "data: {\"type\": \"done\"}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
