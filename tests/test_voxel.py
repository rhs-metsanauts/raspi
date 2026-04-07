# tests/test_voxel.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest
from jetson_mapper import get_voxel_key, voxel_downsample, height_colors, VoxelTracker, VOXEL_SIZE


class TestGetVoxelKey:
    def test_origin(self):
        assert get_voxel_key(0.0, 0.0, 0.0) == (0, 0, 0)

    def test_positive_coords(self):
        # 0.12 / 0.05 = 2.4 → floor = 2
        assert get_voxel_key(0.12, 0.07, 0.03) == (2, 1, 0)

    def test_points_in_same_voxel_share_key(self):
        k1 = get_voxel_key(0.01, 0.01, 0.01)
        k2 = get_voxel_key(0.04, 0.04, 0.04)
        assert k1 == k2

    def test_points_in_different_voxels_differ(self):
        k1 = get_voxel_key(0.01, 0.0, 0.0)
        k2 = get_voxel_key(0.06, 0.0, 0.0)
        assert k1 != k2

    def test_negative_coords(self):
        # -0.03 / 0.05 = -0.6 → floor = -1
        assert get_voxel_key(-0.03, 0.0, 0.0) == (-1, 0, 0)


class TestVoxelDownsample:
    def test_empty_input(self):
        v = np.zeros((0, 3), dtype=np.float32)
        c = np.zeros((0, 3), dtype=np.float32)
        rv, rc, keys = voxel_downsample(v, c)
        assert len(rv) == 0
        assert len(keys) == 0

    def test_two_points_same_voxel_kept_as_one(self):
        v = np.array([[0.01, 0.0, 0.0], [0.02, 0.0, 0.0]], dtype=np.float32)
        c = np.zeros((2, 3), dtype=np.float32)
        rv, rc, keys = voxel_downsample(v, c)
        assert len(rv) == 1
        assert len(keys) == 1

    def test_two_points_different_voxels_both_kept(self):
        v = np.array([[0.01, 0.0, 0.0], [0.10, 0.0, 0.0]], dtype=np.float32)
        c = np.zeros((2, 3), dtype=np.float32)
        rv, rc, keys = voxel_downsample(v, c)
        assert len(rv) == 2
        assert len(keys) == 2


class TestHeightColors:
    def test_empty(self):
        v = np.zeros((0, 3), dtype=np.float32)
        c = height_colors(v)
        assert c.shape == (0, 3)

    def test_single_point_is_blue(self):
        # Single point: y_min == y_max → t=0 → (r=0, g=0, b=1)
        v = np.array([[1.0, 0.5, 0.0]], dtype=np.float32)
        c = height_colors(v)
        assert c[0, 2] > 0.9  # blue component high

    def test_low_point_is_blue_high_is_red(self):
        v = np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
        c = height_colors(v)
        assert c[0, 2] > 0.9
        assert c[0, 0] < 0.1
        assert c[1, 0] > 0.9
        assert c[1, 2] < 0.1

    def test_output_range(self):
        v = np.random.rand(100, 3).astype(np.float32)
        c = height_colors(v)
        assert c.min() >= 0.0
        assert c.max() <= 1.0


class TestVoxelTracker:
    def test_new_point_returned_on_first_call(self):
        tracker = VoxelTracker()
        v = np.array([[0.1, 0.0, 0.0]], dtype=np.float32)
        c = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        result = tracker.get_new_points(v, c)
        assert len(result) == 1
        assert result[0][:3] == [round(0.1, 4), 0.0, 0.0]
        assert result[0][3:] == [255, 0, 0]

    def test_same_point_not_returned_twice(self):
        tracker = VoxelTracker()
        v = np.array([[0.01, 0.0, 0.0]], dtype=np.float32)
        c = np.zeros((1, 3), dtype=np.float32)
        tracker.get_new_points(v, c)
        result2 = tracker.get_new_points(v, c)
        assert result2 == []

    def test_clear_resets_sent_set(self):
        tracker = VoxelTracker()
        v = np.array([[0.01, 0.0, 0.0]], dtype=np.float32)
        c = np.zeros((1, 3), dtype=np.float32)
        tracker.get_new_points(v, c)
        tracker.clear()
        result = tracker.get_new_points(v, c)
        assert len(result) == 1

    def test_empty_input(self):
        tracker = VoxelTracker()
        result = tracker.get_new_points(np.zeros((0, 3)), np.zeros((0, 3)))
        assert result == []

    def test_growing_cloud_only_returns_new_points(self):
        tracker = VoxelTracker()
        v1 = np.array([[0.01, 0.0, 0.0]], dtype=np.float32)
        c1 = np.zeros((1, 3), dtype=np.float32)
        r1 = tracker.get_new_points(v1, c1)
        assert len(r1) == 1

        v2 = np.array([[0.01, 0.0, 0.0], [0.10, 0.0, 0.0]], dtype=np.float32)
        c2 = np.zeros((2, 3), dtype=np.float32)
        r2 = tracker.get_new_points(v2, c2)
        assert len(r2) == 1  # only the new point
