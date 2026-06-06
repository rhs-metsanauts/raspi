# NASA HERA Rover - AI Coding Agent Instructions

## Project Overview
This is a Raspberry Pi-based Mars rover control system with dual communication modes (WiFi/LoRa), AI-assisted command translation, and hardware control via the `Robot.py` module. The system uses a FastAPI backend for command execution, Flask frontend for user interaction, and Ollama LLM for natural language command interpretation.

## Architecture

### Three-Layer Command Flow
1. **Frontend (FlaskServer.py)**: Web UI + AI assistant using Ollama (qwen3:0.6b model)
2. **Transmission Layer**: WiFi (direct HTTP) or LoRa (file-based queuing via `message.json`)
3. **Execution Layer**: FastAPI server (`main.py`) → `command_executor.py` → hardware

### Communication Modes
- **WiFi Mode**: Full bidirectional communication. All command types supported. Commands sent via HTTP POST to `http://localhost:8000/execute`
- **LoRa Mode**: One-way transmission only. Commands written to `D:\message.json`, transmitted by CircuitPython module, received via `serial_reader.py`. Only supports: `bash_command`, `edit_file`, `basic_action`

## Critical Conventions

### Command Types (Not Just Shell Commands!)
The word "command" refers to ANY of these 5 types—not just bash:
- `bash_command`: Shell commands (ls, df, apt, etc.)
- `edit_file`: Write files (requires `file_name`, `file_content`)
- `basic_action`: **Execute Python code** (this is how you control rover hardware!)
- `read_file`: Read file contents (WiFi only)
- `read_image`: Get image as base64 (WiFi only)

### Robot Control Pattern (CRITICAL)
All rover hardware control uses `basic_action` with Python code importing `Robot`:

```python
from Robot import *
import time

rover = Rover()
rover.setup_regular_position()  # Always initialize suspension first
rover.forward(0.7, duration=2)
rover.turn_left(0.5, duration=1)
rover.cleanup()  # MANDATORY - releases GPIO resources
```

**Never forget**: 
- Import `from Robot import *` at the start
- Call `rover.cleanup()` at the end
- Initialize suspension with `setup_regular_position()` before driving

### Rover API Quick Reference
```python
# Movement (power: 0.0-1.0)
rover.forward(power, duration=None)      # None = continuous until stop()
rover.turn_left(power, duration=None)    
rover.turn_right(power, duration=None)
rover.stop()
rover.drive_instant(left, right)         # Set motors (-1.0 to 1.0)

# Suspension
rover.setup_regular_position()           # [90, 90, 150, 30] - default driving
rover.setup_sun_position()               # [150, 35, 90, 90] - solar panel orientation
rover.set_servo_positions([a,b,c,d])     # Custom (0-180 degrees)

# Camera
rover.init_camera(camera_index=0)        # Call once before taking photos
rover.take_picture(filepath)             # Saves as filepath.png
```

## AI System Integration

### LLM Command Translation (FlaskServer.py `/ai_command`)
- Uses Ollama with structured output (Pydantic `RoverCommand` schema)
- System prompt loaded from `ai_system_prompt.md` + Robot API docs appended at runtime
- Streams thinking + content via SSE (Server-Sent Events)
- Model kept alive for 1 hour to avoid startup delays (`keep_alive='1h'`)
- Output format: `{"type": "<command_type>", "fields": {...}}`

### Transmission Mode Constraints in AI Responses
The LLM system prompt dynamically includes current mode. In LoRa mode, AI must never suggest `read_file` or `read_image` commands since responses cannot be received.

## Development Workflows

### Running the System
```powershell
# Rover (Raspberry Pi):
python main.py              # Starts FastAPI on 0.0.0.0:8000

# Control Station:
python FlaskServer.py       # Starts Flask on 0.0.0.0:5000

# LoRa Serial Reader (Rover):
python serial_reader.py     # Auto-detects CircuitPython port
python serial_reader.py --port COM5 --verbose
```

### Testing Hardware Subsystems
See `testing_files/` for component tests:
- `ServoTest.py`: Rocker-bogie servo positioning
- `RockerBogieSubsystemTest.py`: Full suspension system test
- `MPU6050.py` / `MPU-Interpreter.py`: IMU sensor tests
- `LDR.py` / `PlotLDR.py`: Light sensor tests

### LoRa Packet Structure
- Max payload: 248 bytes (252 FIFO - 4 library header)
- Header (9 bytes): Recipient ID (1) + Content ID (4) + Index (2) + Total Chunks (2)
- Content: 239 bytes per chunk
- Reassembly handled by `receiver_lora.py` (runs on CircuitPython)
- Execution via `serial_reader.py` monitoring serial output with `DATA_JSON:` prefix

## Hardware Dependencies
- **GPIO Control**: RPi.GPIO library for motor PWM (pins 17, 27, 22, 24)
- **Servo Control**: `pi_servo_hat` library (4 servos on I2C)
- **Camera**: OpenCV (`cv2`) for USB camera access
- **LoRa**: Adafruit RFM9x modules (915 MHz) with CircuitPython

## File Organization
- `main.py`: FastAPI command execution server (runs on rover)
- `FlaskServer.py`: Web UI + AI assistant (runs on control station)
- `command_executor.py`: Shared command execution logic (used by both WiFi and LoRa paths)
- `Robot.py`: Hardware abstraction (Rover, Drivebase, RockerBogie, Camera classes)
- `ai_system_prompt.md`: LLM system instructions (Robot API docs appended at runtime)
- `transmitter_lora.py`: CircuitPython code for LoRa transmission (reads `message.json`)
- `receiver_lora.py`: CircuitPython code for LoRa reception (reassembles packets)
- `serial_reader.py`: Monitors LoRa receiver serial output, executes commands

## Common Pitfalls
1. **Don't use shell commands for rover control** - Use `basic_action` with Python code
2. **Always call `rover.cleanup()`** - Failing to do so leaves GPIO in bad state
3. **Initialize suspension before driving** - Call `setup_regular_position()` first
4. **LoRa mode limitations** - Cannot use `read_file` or `read_image` (no response path)
5. **Camera initialization** - Must call `rover.init_camera()` once before `take_picture()`
6. **Timeout handling** - Default timeout is 35 seconds for commands via WiFi
