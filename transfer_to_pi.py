#!/usr/bin/env python3
"""
Windows Transfer Script - Send files to Raspberry Pi and start servers
Usage: python transfer_to_pi.py
"""

import requests
import os
import sys
import time

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================
PI_IP = "10.42.0.1"  # Replace with your Raspberry Pi's IP address
PI_PORT = 8001
# ============================================================================

BASE_URL = f"http://{PI_IP}:{PI_PORT}"

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_step(step_num, total_steps, text):
    """Print step progress"""
    print(f"\n[{step_num}/{total_steps}] {text}")

def check_connection():
    """Check if Pi receiver is online"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
        if response.status_code == 200:
            return True, response.json().get('message', 'Connected')
        return False, f"Unexpected status code: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused - is pi_receiver.py running?"
    except requests.exceptions.Timeout:
        return False, "Connection timeout"
    except Exception as e:
        return False, str(e)

def send_file(local_path, remote_path):
    """Send file content to Pi"""
    if not os.path.exists(local_path):
        print(f"    ✗ File not found: {local_path}")
        return False
    
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    file_size = len(content)
    print(f"    → Sending {local_path} ({file_size:,} bytes)...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/receive_file", 
            json={
                'filepath': remote_path,
                'content': content
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"    ✓ Saved to {remote_path}")
            return True
        else:
            error_msg = response.json().get('message', 'Unknown error')
            print(f"    ✗ Failed: {error_msg}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"    ✗ Transfer timed out")
        return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False

def execute_command(command, show_output=True, timeout=30):
    """Execute command on Pi"""
    try:
        response = requests.post(
            f"{BASE_URL}/execute", 
            json={'command': command},
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            if show_output:
                if result.get('stdout'):
                    print(f"    Output: {result['stdout'].strip()}")
                if result.get('stderr'):
                    print(f"    Errors: {result['stderr'].strip()}")
            return True, result
        else:
            error_msg = response.json().get('message', 'Unknown error')
            print(f"    ✗ Failed: {error_msg}")
            return False, None
            
    except requests.exceptions.Timeout:
        print(f"    ✗ Command timed out")
        return False, None
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False, None

def check_process_running(process_name):
    """Check if a process is running on Pi"""
    try:
        response = requests.post(
            f"{BASE_URL}/check_running",
            json={'process_name': process_name},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('running', False)
        return False
    except:
        return False

def kill_process(process_name):
    """Kill a process on Pi"""
    print(f"    → Stopping existing {process_name}...")
    success, _ = execute_command(f"pkill -f '{process_name}'", show_output=False)
    time.sleep(1)
    return success

def start_server_background(script_path, log_file, server_name):
    """Start a server in background with logging"""
    print(f"    → Starting {server_name}...")
    
    command = f"nohup python3 {script_path} > {log_file} 2>&1 &"
    success, _ = execute_command(command, show_output=False)
    
    if success:
        print(f"    ✓ {server_name} started (logging to {log_file})")
        return True
    else:
        print(f"    ✗ Failed to start {server_name}")
        return False

def verify_dependencies():
    """Install required Python packages on Pi"""
    print("    → Checking Python dependencies...")
    
    packages = "flask fastapi uvicorn requests"
    command = f"pip3 install {packages} --break-system-packages --quiet"
    
    success, _ = execute_command(command, show_output=False, timeout=60)
    
    if success:
        print(f"    ✓ Dependencies installed/verified")
    else:
        print(f"    ⚠ Warning: Could not verify all dependencies")
    
    return success

def main():
    """Main deployment function"""
    print_header("Raspberry Pi Deployment Tool")
    
    total_steps = 6
    
    # Step 1: Check connection
    print_step(1, total_steps, "Checking connection to Raspberry Pi")
    print(f"    Target: {PI_IP}:{PI_PORT}")
    
    connected, message = check_connection()
    if not connected:
        print(f"    ✗ Cannot connect: {message}")
        print("\n    Make sure pi_receiver.py is running on your Raspberry Pi:")
        print("      python3 pi_receiver.py")
        return 1
    
    print(f"    ✓ Connected: {message}")
    
    # Step 2: Transfer files
    print_step(2, total_steps, "Transferring files to Raspberry Pi")
    
    files_to_transfer = [
        ("flask_server.py", "/home/metsanauts/flask_server.py"),
        ("fastapi_main.py", "/home/metsanauts/fastapi_main.py")
    ]
    
    all_transferred = True
    for local_file, remote_file in files_to_transfer:
        if not send_file(local_file, remote_file):
            all_transferred = False
    
    if not all_transferred:
        print("\n    ⚠ Some files failed to transfer")
        return 1
    
    # Step 3: Install dependencies
    print_step(3, total_steps, "Installing Python dependencies")
    verify_dependencies()
    
    # Step 4: Stop existing servers
    print_step(4, total_steps, "Stopping existing servers")
    kill_process("fastapi_main.py")
    kill_process("flask_server.py")
    
    # Step 5: Start FastAPI server
    print_step(5, total_steps, "Starting FastAPI server")
    fastapi_started = start_server_background(
        "/home/metsanauts/fastapi_main.py",
        "/home/metsanauts/fastapi.log",
        "FastAPI"
    )
    
    time.sleep(2)  # Give it time to start
    
    # Step 6: Start Flask server
    print_step(6, total_steps, "Starting Flask server")
    flask_started = start_server_background(
        "/home/metsanauts/flask_server.py",
        "/home/metsanauts/flask.log",
        "Flask"
    )
    
    time.sleep(2)  # Give it time to start
    
    # Summary
    print_header("Deployment Complete!")
    
    if fastapi_started and flask_started:
        print("\n✓ Both servers are running on your Raspberry Pi")
        print(f"\n📱 Flask Web UI:    http://{PI_IP}:5000")
        print(f"⚙️  FastAPI Server:  http://{PI_IP}:8000")
        print(f"📋 API Docs:        http://{PI_IP}:8000/docs")
        
        print("\n📊 View server logs on Pi:")
        print(f"    Flask:   tail -f /home/pi/flask.log")
        print(f"    FastAPI: tail -f /home/pi/fastapi.log")
        
        print("\n🔄 To redeploy, just run this script again:")
        print(f"    python {os.path.basename(__file__)}")
        
        print("\n" + "=" * 70 + "\n")
        return 0
    else:
        print("\n⚠ Some servers failed to start")
        print("\nCheck logs on Pi:")
        print("    tail -f /home/pi/flask.log")
        print("    tail -f /home/pi/fastapi.log")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
