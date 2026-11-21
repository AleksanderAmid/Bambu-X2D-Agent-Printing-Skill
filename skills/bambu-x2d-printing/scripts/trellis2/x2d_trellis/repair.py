"""Opt-in watertight revision. Keep the TRELLIS.2 surface for comparison."""

from pathlib import Path

import numpy as np
import point_cloud_utils as pcu
import trimesh

from .runtime import sha256
from .worker import inspect_mesh


def wrap_mesh(work, job, request):
    path = Path(request["source_job"]) / "estimate-mm.stl"
    if sha256(path) != request["source_sha256"]:
        raise ValueError("The source STL changed after submission.")
    source, _ = inspect_mesh(path)
    target = 150_000 if request["resolution"] == 512 else 300_000
    print("Reconstructing a watertight surface.", flush=True)
    vertices, faces = pcu.make_mesh_watertight(np.asarray(source.vertices),
                                               np.asarray(source.faces, dtype=np.int32), target)
    if len(faces) > target:
        vertices, faces, _, _ = pcu.decimate_triangle_mesh(vertices, faces, target)
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    if mesh.volume < 0:
        mesh.invert()
    mesh.apply_scale(request["height_mm"] / mesh.extents[2])
    mesh.apply_translation([0, 0, -mesh.bounds[0, 2]])
    candidate = work / "watertight-mm.stl"
    mesh.export(candidate)
    saved, checks = inspect_mesh(candidate)
    if not saved.is_volume or checks["zero_area_faces"]:
        raise ValueError("The wrapped STL still has topology defects. Inspect the reference in Blender.")
    if not np.allclose(saved.bounds, mesh.bounds, atol=1e-5, rtol=1e-6):
        raise ValueError("Reopened wrap bounds differ from the sized mesh.")
    dest = job / candidate.name
    candidate.rename(dest)
    return {"stl": str(dest), "stl_span_mm": saved.extents.tolist(),
            "stl_mesh": checks, "volume_mm3": float(saved.volume)}
