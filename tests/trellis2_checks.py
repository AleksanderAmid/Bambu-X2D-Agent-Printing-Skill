"""Focused file and job checks. Run with the TRELLIS.2 package dependencies."""

from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image
import psutil
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/bambu-x2d-printing/scripts/trellis2"))
from x2d_trellis import jobs, runtime, worker


class TrellisTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.work = self.folder / "scratch"
        self.work.mkdir()

    def write_box(self):
        scene = trimesh.Scene()
        box = trimesh.creation.box([2, 4, 1])
        scene.add_geometry(box, transform=trimesh.transformations.translation_matrix([4, 7, -3]))
        path = self.work / "estimate.glb"
        scene.export(path)
        return path.read_bytes()

    def test_scale_axes_and_scene_transform_survive_stl_round_trip(self):
        original = self.write_box()
        report = worker.collect(self.work, self.folder, 100)
        mesh, checks = worker.inspect_mesh(Path(report["stl"]))
        np.testing.assert_allclose(mesh.bounds, [[75, 62.5, 0], [125, 87.5, 100]])
        self.assertEqual(checks["bodies"], 1)
        self.assertTrue(checks["watertight"] and checks["consistent_winding"])
        self.assertEqual(Path(report["glb"]).read_bytes(), original)

    def test_unknown_scale_leaves_glb_only(self):
        self.write_box()
        report = worker.collect(self.work, self.folder, None)
        self.assertNotIn("stl", report)
        self.assertFalse(any(self.folder.glob("*.stl")))

    def test_engine_surface_becomes_y_up_glb_and_z_up_stl(self):
        box = trimesh.creation.box([2, 1, 4])
        box.apply_translation([4, 3, 7])
        post = self.work / "surface.post"
        with post.open("wb") as stream:
            stream.write(struct.pack("<4i", len(box.vertices), len(box.faces), 0, 512))
            box.vertices.astype("<f4").tofile(stream)
            box.faces.astype("<i4").tofile(stream)
        self.assertEqual(worker.export_reference(self.work, 512), 12)
        report = worker.collect(self.work, self.folder, 100)
        glb, _ = worker.inspect_mesh(Path(report["glb"]))
        np.testing.assert_allclose(glb.bounds, [[3, 5, -3.5], [5, 9, -2.5]])
        mesh, _ = worker.inspect_mesh(Path(report["stl"]))
        np.testing.assert_allclose(mesh.bounds, [[75, 62.5, 0], [125, 87.5, 100]])

    def test_truncated_native_surface_is_rejected_before_export(self):
        (self.work / "surface.post").write_bytes(struct.pack("<4i", 128, 512, 0, 512))
        with self.assertRaisesRegex(ValueError, "geometry buffer"):
            worker.export_reference(self.work, 512)
        self.assertFalse((self.work / "estimate.glb").exists())

    def test_incomplete_engine_output_cannot_become_a_result(self):
        (self.work / "estimate.glb").write_bytes(b"glTF")
        with self.assertRaises((ValueError, OSError, IndexError)):
            worker.collect(self.work, self.folder, 100)
        self.assertFalse((self.folder / "estimate.glb").exists())

    def test_existing_job_and_transparent_input(self):
        photo = self.folder / "sample.png"
        Image.new("RGB", (10, 12)).save(photo)
        before = photo.read_bytes()
        with patch.object(runtime, "status", return_value={"installed": True, "model": "test",
                          "runtime": "test", "weights_revision": "test"}):
            with self.assertRaisesRegex(ValueError, "already exists"):
                jobs.generate(photo, self.work)
            self.assertEqual(photo.read_bytes(), before)
            self.assertEqual(list(self.work.iterdir()), [])
            Image.new("RGBA", (10, 12)).save(photo)
            new = self.work / "job"
            with self.assertRaisesRegex(ValueError, "transparent"):
                jobs.generate(photo, new)
            self.assertFalse(new.exists())

    def test_old_worker_identity_and_durable_result(self):
        jobs.write_json(self.work / "request.json", {"seed": 42})
        process = psutil.Process()
        jobs.write_json(self.work / "worker.json", {"pid": process.pid, "created": process.create_time() - 60})
        self.assertEqual(jobs.job_status(self.work)["state"], "interrupted")
        jobs.write_json(self.work / "result.json", {"state": "failed", "error": "example engine failure"})
        self.assertEqual(jobs.job_status(self.work)["error"], "example engine failure")

    def test_wrap_requires_a_sized_generation(self):
        jobs.write_json(self.work / "request.json", {"height_mm": None})
        jobs.write_json(self.work / "result.json", {"state": "complete", "glb": "estimate.glb"})
        with self.assertRaisesRegex(ValueError, "height_mm"):
            jobs.wrap(self.work, self.folder / "revision")
        self.assertFalse((self.folder / "revision").exists())

    def test_wrap_detects_a_changed_source_before_reconstruction(self):
        from x2d_trellis.repair import wrap_mesh
        (self.work / "estimate-mm.stl").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "changed after submission"):
            wrap_mesh(self.work, self.folder, {"source_job": str(self.work), "source_sha256": "old"})
        self.assertFalse((self.folder / "watertight-mm.stl").exists())


if __name__ == "__main__":
    unittest.main()
