# 3D Mapping Feature Design

**Date:** 2026-04-07
**Status:** Approved

---

## Context

The rover control app currently supports sending commands and receiving responses over WiFi or LoRa. This feature adds live 3D terrain mapping using a ZED 2i stereo camera mounted on the rover, running on a Jetson Nano. As the rover moves, the map grows and becomes more defined in real-time in the astronaut's browser — no manual triggering required beyond pressing Start.

---

## Hardware

| Component | Role |
|---|---|
| ZED 2i (USB3 → Jetson Nano) | Stereo depth + RGB, built-in IMU, ZED SDK spatial mapping |
| Jetson Nano | Runs ZED SDK, computes fused point cloud, serves WebSocket |
| Astronaut laptop | Runs Flask server, proxies map data to browser via SSE |

The Pi and Jetson are independent systems on the same WiFi LAN. No changes to the Pi's role.

---

## Architecture

```
ZED 2i
  │ USB3
  ▼
jetson_mapper.py  (Jetson Nano, port 9001)
  - ZED SDK SpatialMapping loop @ ~2Hz
  - Extracts incremental fused point cloud chunks
  - Voxel downsamples to 0.05m grid (Open3D)
  - WebSocket server: pushes JSON chunks to all connected clients
    { "points": [[x,y,z,r,g,b], ...], "rover_pos": [x,y,z], "seq": <int> }
  │
  │ WiFi LAN (WebSocket, port 9001)
  ▼
FlaskServer.py  (astronaut laptop)
  - Background thread: WS client connected to Jetson
  - Buffers incoming chunks in a queue
  - GET /map_stream  — SSE endpoint, streams chunks to browser as they arrive
  - POST /map_control — body: {"action": "start"|"stop"|"clear"}, forwarded to Jetson
  │
  │ HTTP SSE
  ▼
Browser (Map tab, index.html)
  - Three.js BufferGeometry + Points
  - Appends new points per chunk (never rebuilds full cloud)
  - Color: RGB from ZED when available; height-mapped (blue→green→red) as fallback
  - OrbitControls: rotate, pan, zoom
  - Top-down minimap: 160×160px canvas overlay, rover path as white line
  - Stats strip: point count, coverage area (m²), elapsed time
```

---

## New Files

### `jetson_mapper.py` (new, runs on Jetson Nano)

Responsibilities:
- Open ZED camera, enable spatial mapping with `MEDIUM` resolution and 0.05m voxel size
- Maintains a Python `set` of already-sent voxel grid indices (`(ix, iy, iz)` tuples at 0.05m resolution)
- Main loop at ~2Hz:
  - Call `zed.extract_whole_spatial_map()` to get the full fused point cloud (grows over time as rover explores)
  - Voxel downsample with Open3D `voxel_down_sample(0.05)`
  - Compute new points: voxels in current cloud whose grid index is not in the sent set
  - Add new voxel indices to the sent set
  - Serialize only new points to JSON: `{"type": "chunk", "points": [...], "rover_pos": [x,y,z], "seq": N}`
  - Broadcast to all connected WebSocket clients (skip broadcast if 0 new points)
- WebSocket server on `0.0.0.0:9001` using `websockets` library
- Handles `start`, `stop`, `clear` control messages from Flask
- On `clear`: resets spatial map and resets seq to 0

Dependencies (Jetson): `pyzed` (ZED Python API), `open3d`, `websockets`, `numpy`

---

### Changes to `FlaskServer.py`

Add at module level:
- `JETSON_WS_URL = "ws://192.168.1.100:9001"` — default placeholder; astronaut sets the real Jetson IP via the Config section in the UI (stored in `/config`), same pattern as `FASTAPI_SERVER_URL`
- `map_chunk_queue: queue.Queue` — thread-safe buffer between WS client and SSE
- Background thread `_jetson_ws_thread()`: connects to Jetson WS, puts received JSON into queue, auto-reconnects on disconnect

New endpoints:
- `GET /map_stream` — `text/event-stream` response, reads from `map_chunk_queue` and yields `data: <json>\n\n`. Sends `{"type":"keepalive"}` every 15s if queue is empty.
- `POST /map_control` — accepts `{"action": "start"|"stop"|"clear"}`, forwards to Jetson over WS, returns `{"success": true}`
- `GET /map_status` — returns `{"connected": bool, "point_count": int, "seq": int}`

Update `GET /config` and `POST /config` to include `jetson_ws_url`.

---

### Changes to `templates/index.html`

**Tab bar** — added above `.content`:
```
[ Commands ]  [ Map ]
```
Tab switching shows/hides `#tab-commands` and `#tab-map` divs. No JS framework needed — plain classList toggle.

**Map tab (`#tab-map`) layout:**
```
┌─ top bar ──────────────────────────────────────────┐
│  ● CONNECTED / ○ DISCONNECTED    [START] [STOP] [CLEAR]  │
└────────────────────────────────────────────────────┘
┌─ Three.js canvas (100% width, 520px tall) ─────────┐
│                                                      │
│                   3D point cloud                     │
│                                           ┌─minimap─┐│
│                                           │  160×160 ││
│                                           └─────────┘│
└────────────────────────────────────────────────────┘
┌─ stats strip ──────────────────────────────────────┐
│  Points: 0     Coverage: 0.0 m²     Time: 00:00    │
└────────────────────────────────────────────────────┘
```

**Three.js setup:**
- Import via CDN: `three.min.js` + `OrbitControls.js`
- Scene: black background, ambient light, `AxesHelper` for orientation
- Point cloud: single `THREE.Points` with `THREE.BufferGeometry`
  - Position and color `Float32Array` buffers, grown dynamically
  - `geometry.setDrawRange(0, pointCount)` updated each chunk (no full rebuild)
- Camera: `PerspectiveCamera`, initial position looking down at slight angle
- Minimap: separate `<canvas>` element overlaid in CSS, drawn with Canvas 2D API
  - Accumulates rover XZ path as white line, scales to fit bounds
- SSE consumer: `EventSource('/map_stream')`, on message → parse JSON → append points → update minimap → update stats

---

## Data Format

Each WebSocket/SSE message is a JSON object:

```json
{
  "type": "chunk",
  "seq": 42,
  "rover_pos": [1.23, 0.05, -0.87],
  "points": [
    [x, y, z, r, g, b],
    ...
  ]
}
```

- `x, y, z`: meters, ZED world frame (Y-up)
- `r, g, b`: 0–255 integer RGB from ZED left camera
- Typical chunk size: 500–2000 points at 0.05m voxel spacing
- Keepalive: `{"type": "keepalive"}` every 15s when idle

Control messages (browser → Flask → Jetson):
```json
{ "action": "start" }
{ "action": "stop" }
{ "action": "clear" }
```

---

## Error Handling

| Failure | Behavior |
|---|---|
| Jetson WS unreachable | Flask WS thread retries every 5s; `/map_status` returns `connected: false`; browser status dot shows red |
| ZED camera not found | `jetson_mapper.py` exits with clear error message |
| SSE client disconnects | Flask generator catches `GeneratorExit`, cleans up |
| Chunk parse error | Browser logs warning, skips chunk, does not crash |
| Map tab not active | SSE still runs; points accumulate; no rendering cost (Three.js render loop pauses when tab hidden via `document.visibilitychange`) |

---

## Coordinate System

ZED 2i default: right-handed, Y-up, Z toward camera.
- Three.js default: right-handed, Y-up — compatible, no transform needed.
- Minimap: projects XZ plane (top-down view).

---

## Performance Targets

| Metric | Target |
|---|---|
| Point cloud update rate | ~2Hz (every 500ms) |
| Voxel grid resolution | 0.05m (5cm) |
| Max points in scene | ~500,000 (well within Three.js limits) |
| WS message size | < 50KB per chunk after downsampling |
| Browser frame rate | ≥ 30fps with up to 500k points |

---

## Out of Scope

- Mesh surface reconstruction (point cloud only for now)
- Saving/exporting the map
- LoRa mode mapping (WiFi only — LoRa bandwidth is insufficient)
- Running on the Pi (Jetson only)
