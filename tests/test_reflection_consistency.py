import importlib
import math
import unittest
from pathlib import Path
from types import SimpleNamespace

import torch


def _load_module():
    if not Path("utils/reflection_consistency.py").exists():
        raise AssertionError("utils/reflection_consistency.py is missing")
    return importlib.import_module("utils.reflection_consistency")


def _dummy_camera(width=2, height=2, center=(0.0, 0.0, 0.0)):
    world_view = torch.eye(4)
    world_view[3, :3] = torch.tensor(center)
    return SimpleNamespace(
        image_width=width,
        image_height=height,
        FoVx=math.pi / 2.0,
        FoVy=math.pi / 2.0,
        world_view_transform=world_view,
        full_proj_transform=torch.eye(4),
        camera_center=torch.tensor(center, dtype=torch.float32),
    )


def _dummy_render_pkg():
    spec = torch.full((3, 2, 2), 0.25)
    alpha = torch.ones(1, 2, 2)
    roughness = torch.zeros(1, 2, 2)
    depth = torch.ones(1, 2, 2)
    normal = torch.zeros(3, 2, 2)
    normal[2] = 1.0
    return {
        "spec_light": spec,
        "rend_alpha": alpha,
        "roughness_map": roughness,
        "surf_depth": depth,
        "rend_normal": normal,
        "surf_normal": normal,
    }


class ReflectionConsistencyHelperTests(unittest.TestCase):
    def test_choose_pair_camera_selects_nearby_different_camera(self):
        rc = _load_module()
        current = _dummy_camera(center=(0.0, 0.0, 0.0))
        nearby = _dummy_camera(center=(0.1, 0.0, 1.0))
        far = _dummy_camera(center=(10.0, 0.0, 0.0))

        selected = rc.choose_pair_camera([current, far, nearby], current, max_angle_deg=45.0)

        self.assertIs(selected, nearby)

    def test_backproject_depth_returns_world_points_for_each_pixel(self):
        rc = _load_module()
        cam = _dummy_camera(width=2, height=2)
        depth = torch.ones(1, 2, 2)

        points = rc.backproject_depth(cam, depth)

        self.assertEqual(points.shape, (4, 3))
        self.assertTrue(torch.isfinite(points).all())

    def test_project_points_returns_grid_depth_and_valid_mask(self):
        rc = _load_module()
        cam = _dummy_camera(width=2, height=2)
        points = torch.tensor([[0.0, 0.0, 1.0], [2.0, 0.0, 1.0]])

        grid, depth, valid = rc.project_points(cam, points)

        self.assertEqual(grid.shape, (2, 2))
        self.assertEqual(depth.shape, (2, 1))
        self.assertEqual(valid.tolist(), [True, False])

    def test_reflection_consistency_loss_is_zero_for_identical_identity_projection(self):
        rc = _load_module()
        cam = _dummy_camera(width=2, height=2)
        pkg = _dummy_render_pkg()

        loss = rc.reflection_consistency_loss(pkg, pkg, cam, cam)

        self.assertEqual(loss.ndim, 0)
        self.assertAlmostEqual(float(loss), 0.0, places=6)

    def test_reflection_consistency_loss_is_zero_for_empty_mask(self):
        rc = _load_module()
        cam = _dummy_camera(width=2, height=2)
        pkg = _dummy_render_pkg()
        pkg["rend_alpha"] = torch.zeros(1, 2, 2)

        loss = rc.reflection_consistency_loss(pkg, pkg, cam, cam)

        self.assertEqual(loss.ndim, 0)
        self.assertAlmostEqual(float(loss), 0.0, places=6)

    def test_reflection_consistency_loss_reports_missing_source_render_key(self):
        rc = _load_module()
        cam = _dummy_camera(width=2, height=2)
        src_pkg = _dummy_render_pkg()
        tgt_pkg = _dummy_render_pkg()
        del src_pkg["roughness_map"]

        with self.assertRaisesRegex(
            KeyError,
            "source render package missing required key: roughness_map",
        ):
            rc.reflection_consistency_loss(src_pkg, tgt_pkg, cam, cam)

    def test_reflection_consistency_loss_reports_missing_target_render_key(self):
        rc = _load_module()
        cam = _dummy_camera(width=2, height=2)
        src_pkg = _dummy_render_pkg()
        tgt_pkg = _dummy_render_pkg()
        del tgt_pkg["rend_alpha"]

        with self.assertRaisesRegex(
            KeyError,
            "target render package missing required key: rend_alpha",
        ):
            rc.reflection_consistency_loss(src_pkg, tgt_pkg, cam, cam)


if __name__ == "__main__":
    unittest.main()
