"""Worker entry point. Engine stdout/stderr go to the job log, never MCP stdout."""

from pathlib import Path
import struct
import subprocess
from tempfile import TemporaryDirectory
import time
import traceback

import numpy as np
import trimesh

from .jobs import read_json, write_json
from .runtime import install_root


def export_reference(work, resolution):
    # v0.8.1 --no-texture writes the raw dual-grid surface to GLB. Its
    # --dump-post interface exposes the welded/remeshed surface before UV baking.
    post = work / "surface.post"
    size = post.stat().st_size
    with post.open("rb") as stream:
        vertices, triangles, texels, _ = struct.unpack("<4i", stream.read(16))
        if min(vertices, triangles) < 1 or texels != 0 or size != 16 + 12 * (vertices + triangles):
            raise ValueError("Incomplete or unexpected TRELLIS.2 geometry buffer.")
        points = np.fromfile(stream, dtype="<f4", count=3 * vertices).reshape(-1, 3)
        faces = np.fromfile(stream, dtype="<i4", count=3 * triangles).reshape(-1, 3)
    if not np.isfinite(points).all() or faces.min() < 0 or faces.max() >= vertices:
        raise ValueError("Invalid coordinates or triangle indices in TRELLIS.2 geometry.")
    mesh = trimesh.Trimesh(points, faces, process=False)
    target = 150_000 if resolution == 512 else 300_000
    if triangles > target:
        print(f"Simplifying {triangles:,} surface triangles toward {target:,}.", flush=True)
        mesh = mesh.simplify_quadric_decimation(face_count=target)
    # The native surface is Z-up. glTF uses Y-up.
    mesh.apply_transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]])
    mesh.export(work / "estimate.glb", include_normals=True)
    return triangles


def inspect_mesh(path):
    mesh = trimesh.load_scene(path, process=False).to_mesh()
    if mesh.is_empty or not np.isfinite(mesh.vertices).all() or np.any(mesh.extents <= 0):
        raise ValueError(f"{path.name} has empty, flat or non-finite geometry.")
    if np.min(mesh.faces) < 0 or np.max(mesh.faces) >= len(mesh.vertices):
        raise ValueError(f"{path.name} contains invalid triangle indices.")
    # STL lists three vertices per facet. Weld shared positions in the inspection
    # copy so a closed surface can be recognized in either file format.
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    edges = np.bincount(mesh.edges_unique_inverse)
    checks = {"vertices": len(mesh.vertices), "triangles": len(mesh.faces), "bodies": int(mesh.body_count),
              "boundary_edges": int((edges == 1).sum()), "overused_edges": int((edges > 2).sum()),
              "zero_area_faces": int((mesh.area_faces == 0).sum()),
              "watertight": bool(mesh.is_watertight), "consistent_winding": bool(mesh.is_winding_consistent)}
    return mesh, checks


def collect(work, job, height_mm):
    glb = work / "estimate.glb"
    mesh, checks = inspect_mesh(glb)
    report = {"glb": str(job / glb.name), "glb_mesh": checks, "scale": "uncalibrated reference"}
    if height_mm is not None:
        # Right-handed glTF Y-up -> slicer Z-up, followed by one uniform scale.
        mesh.apply_transform([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
        mesh.apply_scale(height_mm / mesh.extents[2])
        mesh.apply_translation([0, 0, -mesh.bounds[0, 2]])
        stl = work / "estimate-mm.stl"
        mesh.export(stl)
        saved, stl_checks = inspect_mesh(stl)
        if not np.allclose(saved.bounds, mesh.bounds, atol=1e-5, rtol=1e-6):
            raise ValueError("Reopened STL bounds differ from the scaled mesh.")
        report.update(stl=str(job / stl.name), stl_span_mm=saved.extents.tolist(), stl_mesh=stl_checks)
        stl.replace(job / stl.name)
    glb.replace(job / glb.name)
    return report


def infer(work, job, request):
    root = install_root()
    # Relative image and output names also work with the native image codec
    # when a user chooses a non-ASCII job directory.
    subprocess.run([root / "bin/trellis-cli.exe", "../reference.png", "estimate.glb",
                    "--model", "trellis", "--models", root / "models", "--backend", "Vulkan",
                    "--require-gpu", "--no-texture", "--dump-post", "surface.post",
                    "--res", str(request["resolution"]), "--seed", str(request["seed"])], cwd=work, check=True)
    count = export_reference(work, request["resolution"])
    report = collect(work, job, request["height_mm"])
    report["surface_triangles_before_simplification"] = count
    return report


def main():
    job = Path.cwd()
    started = time.monotonic()
    try:
        request = read_json(job / "request.json")
        with TemporaryDirectory(dir=job) as tmp:
            if request.get("operation") == "wrap":
                from .repair import wrap_mesh
                report = wrap_mesh(Path(tmp), job, request)
            else:
                report = infer(Path(tmp), job, request)
        result = {"state": "complete", **report}
    except Exception as exc:
        traceback.print_exc()
        result = {"state": "failed", "error": str(exc)}
    result["elapsed_seconds"] = round(time.monotonic() - started, 2)
    write_json(job / "result.json", result)
    return 0 if result["state"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
