from flask import Flask, render_template, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# Configuration
FASTAPI_SERVER_URL = "http://localhost:8000/execute"
DEFAULT_TIMEOUT = 35
TRANSMISSION_MODE = "wifi"  # "wifi" or "lora"
LORA_DESTINATION = 0  # Integer destination for LoRA
LORA_MESSAGE_PATH = r"D:\message.json"  # Path where LoRA transmitter reads messages from


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


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
