import json
import os
import re
from importlib import import_module

import numpy as np
from PIL import Image


_WORLD_MAT_RE = re.compile(r"^world_mat_(\d+)$")


def _camera_indices(camera_keys):
    indices = []
    for key in camera_keys:
        match = _WORLD_MAT_RE.match(key)
        if match:
            indices.append(int(match.group(1)))
    return sorted(indices)


def _decompose_projection(world_mat, scale_mat):
    cv2 = import_module("cv2")
    projection = np.asarray(world_mat, dtype=np.float64) @ np.asarray(scale_mat, dtype=np.float64)
    intrinsic, rotation, center_h = cv2.decomposeProjectionMatrix(projection[:3, :4])[:3]
    intrinsic = intrinsic / intrinsic[2, 2]
    center = (center_h[:3] / center_h[3]).reshape(3)

    w2c = np.eye(4, dtype=np.float64)
    w2c[:3, :3] = rotation
    w2c[:3, 3] = -rotation @ center
    c2w_colmap = np.linalg.inv(w2c)

    # Ref-GS' Blender reader flips columns 1:3 after loading. Store the inverse
    # convention so a generated transforms_*.json loads back to the same W2C.
    c2w_for_loader = c2w_colmap.copy()
    c2w_for_loader[:3, 1:3] *= -1
    return intrinsic, c2w_for_loader


def _frame_for_camera(scene_path, image_dir, extension, index, intrinsic, transform_matrix):
    image_name = "{:04d}".format(index)
    image_rel = os.path.join(image_dir, image_name).replace(os.sep, "/")
    image_path = os.path.join(scene_path, image_dir, image_name + extension)
    if not os.path.exists(image_path):
        return None, image_path

    with Image.open(image_path) as image:
        width, height = image.size

    return {
        "file_path": image_rel,
        "fl_x": float(intrinsic[0, 0]),
        "fl_y": float(intrinsic[1, 1]),
        "cx": float(intrinsic[0, 2]),
        "cy": float(intrinsic[1, 2]),
        "w": int(width),
        "h": int(height),
        "transform_matrix": np.asarray(transform_matrix, dtype=np.float64).tolist(),
    }, None


def _empty_transforms(first_frame=None):
    output = {
        "camera_model": "OPENCV",
        "frames": [],
    }
    if first_frame is not None:
        for key in ("fl_x", "fl_y", "cx", "cy", "w", "h"):
            output[key] = first_frame[key]
    return output


def build_smvp3d_transforms(scene_path, eval_split=True, llffhold=8, image_dir="image", extension=".png"):
    cameras_path = os.path.join(scene_path, "cameras.npz")
    if not os.path.exists(cameras_path):
        raise FileNotFoundError("Missing SMVP3D cameras file: {}".format(cameras_path))
    if llffhold <= 0:
        raise ValueError("llffhold must be positive")

    camera_data = np.load(cameras_path)
    indices = _camera_indices(camera_data.files)
    frames = []
    missing_images = []

    for index in indices:
        world_key = "world_mat_{}".format(index)
        scale_key = "scale_mat_{}".format(index)
        if scale_key not in camera_data:
            raise KeyError("Missing SMVP3D scale matrix key: {}".format(scale_key))

        intrinsic, transform_matrix = _decompose_projection(camera_data[world_key], camera_data[scale_key])
        frame, missing_image = _frame_for_camera(
            scene_path,
            image_dir,
            extension,
            index,
            intrinsic,
            transform_matrix,
        )
        if missing_image is not None:
            missing_images.append(missing_image)
            continue
        frames.append((index, frame))

    first_frame = frames[0][1] if frames else None
    train_transforms = _empty_transforms(first_frame)
    test_transforms = _empty_transforms(first_frame)

    for index, frame in frames:
        target = test_transforms if eval_split and index % llffhold == 0 else train_transforms
        target["frames"].append(frame)

    if not eval_split:
        test_transforms["frames"] = []

    summary = {
        "mode": "smvp3d_transform_conversion",
        "scene_path": os.path.abspath(scene_path),
        "cameras_path": os.path.abspath(cameras_path),
        "camera_count": len(indices),
        "converted_count": len(frames),
        "train_count": len(train_transforms["frames"]),
        "test_count": len(test_transforms["frames"]),
        "missing_images": missing_images,
        "image_dir": image_dir,
        "extension": extension,
        "eval_split": bool(eval_split),
        "llffhold": int(llffhold),
    }
    return train_transforms, test_transforms, summary


def write_smvp3d_transforms(scene_path, train_transforms, test_transforms):
    train_path = os.path.join(scene_path, "transforms_train.json")
    test_path = os.path.join(scene_path, "transforms_test.json")
    with open(train_path, "w") as handle:
        json.dump(train_transforms, handle, indent=2)
    with open(test_path, "w") as handle:
        json.dump(test_transforms, handle, indent=2)
    return train_path, test_path


def write_summary(path, summary):
    with open(path, "w") as handle:
        json.dump(summary, handle, indent=2)
