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

    indices = np.floor(vertices / voxel_size).astype(np.int32)
    seen: dict[tuple, int] = {}
    for i in range(len(vertices)):
        key = (int(indices[i, 0]), int(indices[i, 1]), int(indices[i, 2]))
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
                r = int(colors[i, 0] * 255)
                g = int(colors[i, 1] * 255)
                b = int(colors[i, 2] * 255)
                result.append([
                    round(float(vertices[i, 0]), 4),
                    round(float(vertices[i, 1]), 4),
                    round(float(vertices[i, 2]), 4),
                    r, g, b,
                ])
        return result

    def clear(self):
        self._sent.clear()
