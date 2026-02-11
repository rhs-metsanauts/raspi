from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# Configuration - Change this to your FastAPI server URL
FASTAPI_SERVER_URL = "http://localhost:8000/execute"


@app.route('/')
def index():
    """Render the main UI page"""
    return render_template('index.html')


@app.route('/send_command', methods=['POST'])
def send_command():
    """Forward command to FastAPI server and return response"""
    try:
        data = request.get_json()
        
        # Send request to FastAPI server
        response = requests.post(FASTAPI_SERVER_URL, json=data, timeout=35)
        
        return jsonify({
            "success": True,
            "status_code": response.status_code,
            "data": response.json()
        })
    
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "error": "Could not connect to FastAPI server. Make sure it's running."
        }), 503
    
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "error": "Request timed out"
        }), 408
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/config', methods=['GET', 'POST'])
def config():
    """Get or update FastAPI server URL"""
    global FASTAPI_SERVER_URL
    
    if request.method == 'POST':
        data = request.get_json()
        FASTAPI_SERVER_URL = data.get('server_url', FASTAPI_SERVER_URL)
        return jsonify({"success": True, "server_url": FASTAPI_SERVER_URL})
    
    return jsonify({"server_url": FASTAPI_SERVER_URL})


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
