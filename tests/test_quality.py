import argparse
import asyncio
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/bambu-x2d-printing/scripts"))
sys.path.insert(0, str(ROOT / "tools"))

import catalog
from fixtures_3d import ring_triangles, write_stl
from handoff_check import next_step
from mesh_probe import measure
from nozzle_reach import check
from plate_review import reviewed_plate


class MeshTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "part.stl"

    def test_colorless_stl_in_either_encoding(self):
        for binary in (False, True):
            with self.subTest(binary=binary):
                write_stl(self.path, ring_triangles(), binary)
                m = measure(self.path, 1, 2)
                self.assertEqual(m["span_mm"], [20,20,4])
                self.assertEqual(len(m["loops"]), 2)
                self.assertAlmostEqual(m["loops"][1]["span_xy_mm"][0], 8, places=5)
                self.assertAlmostEqual(m["loops"][1]["radial_range_mm"][0], 4, delta=0.003)
                self.assertEqual([m[k] for k in ("boundary_edges","overused_edges","inconsistent_edge_pairs","degenerate_faces")], [0]*4)

    def test_wrong_bore_with_same_envelope(self):
        write_stl(self.path, ring_triangles(bore=3.3))
        report = measure(self.path, 1, 2)
        self.assertEqual(report["span_mm"], [20,20,4])
        self.assertGreater(abs(report["loops"][1]["span_xy_mm"][0] - 8), 1.3)

    def test_inch_confusion(self):
        faces = [tuple(tuple(v / 25.4 for v in p) for p in tri) for tri in ring_triangles()]
        write_stl(self.path, faces)
        self.assertAlmostEqual(measure(self.path, 25.4)["span_mm"][0], 20, places=5)
        self.assertLess(measure(self.path, 1)["span_mm"][0], 1)

    def test_open_mesh_and_reversed_facet(self):
        triangles = ring_triangles()
        write_stl(self.path, triangles[:-1])
        self.assertEqual(measure(self.path, 1)["boundary_edges"], 3)
        triangles[0] = tuple(reversed(triangles[0]))
        write_stl(self.path, triangles)
        self.assertEqual(measure(self.path, 1)["inconsistent_edge_pairs"], 3)

    def test_unapplied_scale_is_detectable_in_saved_file(self):
        write_stl(self.path, ring_triangles())
        expected_after_object_scale = [30, 20, 4]
        self.assertNotEqual(measure(self.path, 1)["span_mm"], expected_after_object_scale)
        transformed = [tuple((x*1.5,y,z) for x,y,z in tri) for tri in ring_triangles()]
        write_stl(self.path, transformed)
        self.assertEqual(measure(self.path, 1)["span_mm"], expected_after_object_scale)

    def test_coplanar_slice_explicitly_refused(self):
        write_stl(self.path, ring_triangles())
        with self.assertRaisesRegex(ValueError, "interior Z"):
            measure(self.path, 1, 0)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "test.3mf"
        self.path.write_bytes(b"synthetic opaque snapshot")
        sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.receipt = {"receipt_version":"1","evidence":"file-only","dispatch_authorized":False,
                        "selection":{"bambu_model":"x2d","plate_index":0},
                        "artifact":{"sha256":sha,"byte_length":self.path.stat().st_size,"file_format":"3mf"},
                        "inspection":{"model":"x2d","plateInternalPath":"Metadata/plate_1.gcode","sha256":sha,
                                      "nozzleDiameters":[0.4,0.4],"materials":["PLA"],"bedType":"textured_plate"}}
        self.job = dict(sha256=sha,studio_plate=1,printer="Workshop X2D",quantity=1,
                        nozzles_mm=[0.4,0.4],plate_type="textured_plate",mapping="PLA green → AMS A1",
                        print_options={"bed_leveling":True})
        self.visible = dict(self.job,final_control_verified=True)

    def test_exact_bytes_plate_and_target(self):
        self.assertEqual(reviewed_plate(self.path, self.receipt, 1)["sha256"], self.job["sha256"])
        for plate in (0,2):
            with self.assertRaises(ValueError):
                reviewed_plate(self.path, self.receipt, plate)
        wrong = copy.deepcopy(self.receipt)
        wrong["selection"]["bambu_model"] = "x1c"
        with self.assertRaises(ValueError):
            reviewed_plate(self.path, wrong, 1)
        self.path.write_bytes(b"synthetic opaque snapshot"[:-1] + b"X")
        with self.assertRaisesRegex(ValueError, "changed"):
            reviewed_plate(self.path, self.receipt, 1)

    def test_simulated_final_control(self):
        clicks = []
        last = "none"
        def simulate(action):
            nonlocal last
            state = next_step(self.job,self.visible,action,last)
            if state == "one_studio_click_eligible":
                clicks.append(self.job["sha256"])
                last = "unknown"  # simulate a lost acknowledgement
            return state
        self.assertEqual(simulate("prepare_only"), "await_operator")
        self.assertEqual(simulate("human_click"), "leave_final_control_to_operator")
        self.assertEqual(len(clicks), 0)
        self.assertEqual(simulate("approved_and_delegated"), "one_studio_click_eligible")
        self.assertEqual(simulate("approved_and_delegated"), "check_device_state")
        self.assertEqual(len(clicks), 1)

    def test_changes_invalidate_approval(self):
        for key,new in {"sha256":"other","studio_plate":2,"printer":"Different X2D","mapping":"blue A2",
                        "quantity":3,"nozzles_mm":[0.4,0.6],"plate_type":"smooth_plate",
                        "print_options":{"bed_leveling":False}}.items():
            with self.subTest(key=key):
                visible = dict(self.visible, **{key:new})
                self.assertEqual(next_step(self.job,visible,"approved_and_delegated","none"),"request_new_review")
        self.assertEqual(next_step(self.job,dict(self.visible,final_control_verified=False),
                                   "approved_and_delegated","none"),"await_operator")

    def test_ambiguously_typed_observations(self):
        for key, value in (("quantity", True), ("studio_plate", True), ("print_options", {"bed_leveling": 1})):
            with self.subTest(field=key):
                self.assertEqual(next_step(self.job, dict(self.visible, **{key: value}),
                                           "approved_and_delegated", "none"), "request_new_review")


class ReachAndCatalogTests(unittest.TestCase):
    def test_assigned_nozzle_and_height(self):
        settings = {"printer_model":"Bambu Lab X2D", "extruder_printable_height":["261","256"],
                    "extruder_printable_area":["0x0,256x0,256x256,0x256","20.5x0,256x0,256x256,20.5x256"]}
        box = [12,50,0,19,60,5]
        self.assertTrue(check(settings,0,box)["inside_nozzle_envelope"])
        self.assertFalse(check(settings,1,box)["inside_nozzle_envelope"])
        self.assertFalse(check(settings,0,[30,30,0,45,45,260.5])["inside_nozzle_envelope"])
        settings["extruder_printable_area"][1] = "0x0,5x0,3x3"
        with self.assertRaises(ValueError):
            check(settings,1,box)

    def test_all_catalog_entries_documented(self):
        data = json.loads(catalog.BASELINE.read_text(encoding="utf-8-sig"))
        self.assertEqual(catalog.documentation_errors(data), [])
        data["freecad"]["tools"]["future_tool"] = "new"
        self.assertTrue(catalog.documentation_errors(data))
        data["blender"]["prompts"].append("new_guidance")
        self.assertTrue(any("new_guidance" in message for message in catalog.documentation_errors(data)))

    def test_local_printer_host_redacted(self):
        self.assertEqual(catalog.resource_key("printer://example.internal/status"), "printer://{printer}/status")

    def test_missing_local_server_is_reported_before_launch(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "config.toml"
            config.write_text("[mcp_servers]\n", encoding="utf-8")
            args = argparse.Namespace(config=config, freecad="freecad", blender="blender", bambu="bambu-studio")
            with self.assertRaisesRegex(ValueError, "Missing local MCP registration: freecad"):
                asyncio.run(catalog.discover(args))


if __name__ == "__main__":
    unittest.main()
