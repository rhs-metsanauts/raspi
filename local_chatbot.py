from flask import Flask, render_template, request, jsonify
import requests
import json
import subprocess
import sys
import os

app = Flask(__name__)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL = "glm-4.7-flash"  # Primary model - GLM 4.7 Flash

def get_available_model():
    """Check which model is available and return it"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"].split(":")[0] for m in models]
            if "glm-4.7-flash" in model_names:
                return "glm-4.7-flash"
    except:
        pass
    return MODEL

def generate_code(prompt: str) -> str:
    """
    Generate code using Ollama with full context
    """
    model = get_available_model()

    # System prompt for code generation
    system_prompt = """You are an expert code generation assistant for astronauts and space mission specialists.
You help generate clean, well-documented code and command examples.

IMPORTANT INSTRUCTIONS:
1. Always provide COMPLETE, RUNNABLE CODE with examples
2. Include detailed comments explaining what the code does
3. Provide multiple examples when relevant
4. For shell commands, show the command AND example usage
5. Format code in proper markdown code blocks with language specified
6. Include error handling where appropriate
7. Provide copy-paste ready solutions

EXAMPLE FORMAT for code generation:
```python
# Complete, working example with comments
import module
def function_name():
    '''Docstring explaining the function'''
    pass
```

Always respond with full, complete solutions."""

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": f"{system_prompt}\n\nUser Request: {prompt}",
                "stream": False,
                "temperature": 0.7,
            },
            timeout=300
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "No response generated")
        else:
            return f"Error: API returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return f"Error: Cannot connect to Ollama at {OLLAMA_BASE_URL}. Is Ollama running?"
    except requests.exceptions.Timeout:
        return "Error: Request timeout. The model might be processing a large request."
    except Exception as e:
        return f"Error: {str(e)}"

def execute_command(command: str) -> dict:
    """
    Execute a shell command safely
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command execution timeout (30s)",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Generate code from a prompt"""
    data = request.json
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    code = generate_code(prompt)
    return jsonify({"code": code})

@app.route("/api/execute", methods=["POST"])
def api_execute():
    """Execute a shell command"""
    data = request.json
    command = data.get("command", "").strip()

    if not command:
        return jsonify({"error": "Empty command"}), 400

    result = execute_command(command)
    return jsonify(result)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chat/prompt with the LLM"""
    data = request.json
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    model = get_available_model()

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
            },
            timeout=300
        )

        if response.status_code == 200:
            result = response.json()
            return jsonify({"response": result.get("response", "No response generated")})
        else:
            return jsonify({"error": f"API returned status {response.status_code}"}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot connect to Ollama. Is it running?"}), 500
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/models", methods=["GET"])
def api_models():
    """Get available models"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return jsonify({
                "models": [
                    {
                        "name": m["name"],
                        "size": m.get("size", 0),
                    }
                    for m in models
                ],
                "current": get_available_model()
            })
    except:
        pass

    return jsonify({
        "models": [],
        "current": "unknown",
        "error": "Cannot connect to Ollama"
    })

if __name__ == "__main__":
    print("=" * 60)
    print("LOCAL CHATBOT WRAPPER FOR ASTRONAUTS")
    print("=" * 60)
    print(f"Starting Flask server...")
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    print(f"Primary Model: {MODEL}")
    print("\nServer will be available at: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host="localhost", port=5000)
