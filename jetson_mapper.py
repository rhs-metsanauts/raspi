# jetson_mapper.py
"""
Jetson Nano ZED 2i spatial mapping streamer.
Run: python jetson_mapper.py
Requires: pyzed (ZED SDK), numpy, websockets
"""

import asyncio
import json
import numpy as np

try:
    import pyzed.sl as sl
    ZED_AVAILABLE = True
except ImportError:
    ZED_AVAILABLE = False

import websockets
import websockets.exceptions

VOXEL_SIZE = 0.05   # metres — 5 cm grid
WS_PORT = 9001
UPDATE_HZ = 2


def get_voxel_key(x: float, y: float, z: float, voxel_size: float = VOXEL_SIZE) -> tuple:
    """Return the integer grid index tuple for a 3D point."""
    return (
        int(np.floor(x / voxel_size)),
        int(np.floor(y / voxel_size)),
        int(np.floor(z / voxel_size)),
    )


def voxel_downsample(vertices: np.ndarray, colors: np.ndarray, voxel_size: float = VOXEL_SIZE):
    """
    Reduce points to one per voxel cell (pure numpy, no Open3D).

    Args:
        vertices: Nx3 float array of [x, y, z]
        colors:   Nx3 float array of [r, g, b] in range [0, 1]
        voxel_size: grid cell size in metres

    Returns:
        (filtered_vertices, filtered_colors, voxel_keys_set)
        voxel_keys_set: set of (ix, iy, iz) tuples for the kept points
    """
    if len(vertices) == 0:
        return vertices, colors, set()

    if len(vertices) != len(colors):
        raise ValueError(f"vertices and colors length mismatch: {len(vertices)} vs {len(colors)}")

    seen: dict[tuple, int] = {}
    for i in range(len(vertices)):
        key = get_voxel_key(float(vertices[i, 0]), float(vertices[i, 1]), float(vertices[i, 2]), voxel_size)
        if key not in seen:
            seen[key] = i

    keep = np.array(list(seen.values()), dtype=np.int32)
    return vertices[keep], colors[keep], set(seen.keys())


def height_colors(vertices: np.ndarray) -> np.ndarray:
    """
    Return Nx3 float32 RGB colors (0–1) using blue→green→red height mapping.
    Low Y = blue, mid Y = green, high Y = red.
    """
    if len(vertices) == 0:
        return np.zeros((0, 3), dtype=np.float32)

    y = vertices[:, 1]
    y_min, y_max = float(y.min()), float(y.max())
    y_range = max(y_max - y_min, 1e-6)
    t = (y - y_min) / y_range  # 0..1

    r = np.clip(t * 2.0 - 1.0, 0.0, 1.0)
    g = np.clip(1.0 - np.abs(t * 2.0 - 1.0), 0.0, 1.0)
    b = np.clip(1.0 - t * 2.0, 0.0, 1.0)

    return np.stack([r, g, b], axis=1).astype(np.float32)


class VoxelTracker:
    """Tracks which voxels have already been sent to avoid re-transmitting."""

    def __init__(self, voxel_size: float = VOXEL_SIZE):
        self.voxel_size = voxel_size
        self._sent: set[tuple] = set()

    def get_new_points(self, vertices: np.ndarray, colors: np.ndarray) -> list:
        """
        Given a full downsampled point cloud, return only points whose voxel
        has not been sent before. Updates internal sent set.

        Returns list of [x, y, z, r, g, b] with r/g/b as 0-255 ints.
        """
        if len(vertices) == 0:
            return []

        if len(vertices) != len(colors):
            raise ValueError(f"vertices and colors length mismatch: {len(vertices)} vs {len(colors)}")

        result = []
        for i in range(len(vertices)):
            key = get_voxel_key(
                float(vertices[i, 0]),
                float(vertices[i, 1]),
                float(vertices[i, 2]),
                self.voxel_size,
            )
            if key not in self._sent:
                self._sent.add(key)
                r = int(np.clip(colors[i, 0], 0.0, 1.0) * 255)
                g = int(np.clip(colors[i, 1], 0.0, 1.0) * 255)
                b = int(np.clip(colors[i, 2], 0.0, 1.0) * 255)
                result.append([
                    round(float(vertices[i, 0]), 4),
                    round(float(vertices[i, 1]), 4),
                    round(float(vertices[i, 2]), 4),
                    r, g, b,
                ])
        return result

    def clear(self):
        self._sent.clear()


class ZedMapper:
    """
    Runs the ZED SDK spatial mapping loop and streams incremental point
    cloud chunks to WebSocket clients.
    """

    def __init__(self):
        self.tracker = VoxelTracker()
        self.clients: set = set()
        self.mapping_active = False
        self.seq = 0

    # ── ZED helpers ───────────────────────────────────────────────────────────

    def _init_zed(self):
        if not ZED_AVAILABLE:
            raise RuntimeError("pyzed not installed — ZED SDK required on Jetson")

        self.zed = sl.Camera()

        init_params = sl.InitParameters()
        init_params.coordinate_units = sl.UNIT.METER
        init_params.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP
        init_params.depth_mode = sl.DEPTH_MODE.ULTRA

        status = self.zed.open(init_params)
        if status != sl.ERROR_CODE.SUCCESS:
            raise RuntimeError(f"ZED open failed: {status}")

        tracking_params = sl.PositionalTrackingParameters()
        status = self.zed.enable_positional_tracking(tracking_params)
        if status != sl.ERROR_CODE.SUCCESS:
            raise RuntimeError(f"enable_positional_tracking failed: {status}")

        mapping_params = sl.SpatialMappingParameters(
            resolution_meter=VOXEL_SIZE,
            range_meter=sl.SpatialMappingParameters.get_recommended_range(
                sl.SpatialMappingParameters.MAPPING_RESOLUTION.MEDIUM, self.zed
            ),
            save_texture=False,
            use_chunk_only=True,
        )
        status = self.zed.enable_spatial_mapping(mapping_params)
        if status != sl.ERROR_CODE.SUCCESS:
            raise RuntimeError(f"enable_spatial_mapping failed: {status}")
        print("[ZedMapper] ZED 2i initialised, spatial mapping enabled")

    def _get_rover_pos(self) -> list:
        pose = sl.Pose()
        state = self.zed.get_position(pose, sl.REFERENCE_FRAME.WORLD)
        if state == sl.POSITIONAL_TRACKING_STATE.OK:
            t = pose.get_translation(sl.Translation())
            v = t.get()
            return [round(float(v[0]), 4), round(float(v[1]), 4), round(float(v[2]), 4)]
        return [0.0, 0.0, 0.0]

    def _extract_points(self):
        """Extract full fused mesh, compute height colours, voxel-downsample."""
        mesh = sl.Mesh()
        self.zed.extract_whole_spatial_map(mesh)
        raw = mesh.vertices
        if raw is None or len(raw) == 0:
            return np.zeros((0, 3), dtype=np.float32), np.zeros((0, 3), dtype=np.float32)

        vertices = np.array(raw, dtype=np.float32)
        colors = height_colors(vertices)
        v_down, c_down, _ = voxel_downsample(vertices, colors)
        return v_down, c_down

    # ── WebSocket server ───────────────────────────────────────────────────────

    async def _broadcast(self, message: str):
        if not self.clients:
            return
        results = await asyncio.gather(
            *[ws.send(message) for ws in list(self.clients)],
            return_exceptions=True,
        )
        for ws, result in zip(list(self.clients), results):
            if isinstance(result, Exception):
                self.clients.discard(ws)

    async def _handle_client(self, websocket, path=""):
        self.clients.add(websocket)
        print(f"[ZedMapper] Client connected: {websocket.remote_address}")
        try:
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                    action = msg.get("action")
                    if action == "start":
                        self.mapping_active = True
                        print("[ZedMapper] Mapping started")
                    elif action == "stop":
                        self.mapping_active = False
                        print("[ZedMapper] Mapping stopped")
                    elif action == "clear":
                        self.mapping_active = False
                        self.tracker.clear()
                        self.seq = 0
                        self.zed.clear_spatial_map_async()
                        await websocket.send(json.dumps({"type": "cleared"}))
                        print("[ZedMapper] Map cleared")
                except (json.JSONDecodeError, KeyError):
                    pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            print("[ZedMapper] Client disconnected")

    # ── Main loop ─────────────────────────────────────────────────────────────

    async def _mapping_loop(self):
        while True:
            if self.mapping_active:
                try:
                    if self.zed.grab() == sl.ERROR_CODE.SUCCESS:
                        vertices, colors = self._extract_points()
                        new_pts = self.tracker.get_new_points(vertices, colors)
                        if new_pts:
                            rover_pos = self._get_rover_pos()
                            payload = json.dumps({
                                "type": "chunk",
                                "seq": self.seq,
                                "rover_pos": rover_pos,
                                "points": new_pts,
                            })
                            self.seq += 1
                            await self._broadcast(payload)
                except Exception as exc:
                    print(f"[ZedMapper] Loop error: {exc}")

            await asyncio.sleep(1.0 / UPDATE_HZ)

    async def run(self):
        self._init_zed()
        print(f"[ZedMapper] WebSocket server listening on ws://0.0.0.0:{WS_PORT}")
        async with websockets.serve(self._handle_client, "0.0.0.0", WS_PORT):
            await self._mapping_loop()

    def cleanup(self):
        if ZED_AVAILABLE and hasattr(self, "zed"):
            self.zed.disable_spatial_mapping()
            self.zed.disable_positional_tracking()
            self.zed.close()


if __name__ == "__main__":
    mapper = ZedMapper()
    try:
        asyncio.run(mapper.run())
    except KeyboardInterrupt:
        print("\n[ZedMapper] Shutting down…")
    finally:
        mapper.cleanup()
