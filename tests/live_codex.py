"""Windows Codex end-to-end qualification. Creates job files in a fresh temp folder. No printer calls."""
import argparse
from contextlib import contextmanager
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from textwrap import dedent
from xml.etree import ElementTree
from zipfile import ZipFile

from fixtures_3d import instanced_3mf, ring_triangles, write_stl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/bambu-x2d-printing/scripts"))
from mesh_probe import measure
from plate_review import reviewed_plate
from nozzle_reach import check as check_reach

LOCAL_CALLS = {"freecad": {"get_rpc_status", "execute_code"}, "blender": {"get_scene_info", "execute_blender_code"},
               "bambu-studio": {"counterpart_self_check","slice_stl","inspect_print_file",
                                 "list_3mf_plates","counterpart_part_meshes","counterpart_make_3mf"}}


class Codex:
    def __init__(self, process):
        self.process = process
        self.seq = 0
        self.thread = None

    def send(self, data):
        self.process.stdin.write((json.dumps(data) + "\n").encode("utf-8"))
        self.process.stdin.flush()

    def request(self, method, params):
        self.seq += 1
        self.send({"id": self.seq, "method": method, "params": params})
        for line in self.process.stdout:
            msg = json.loads(line)
            if "method" in msg:
                if "id" in msg:
                    self.send({"id":msg["id"],"error":{"code":-32601,"message":"Unattended offline test"}})
                continue
            if msg.get("id") == self.seq:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error'].get('message','failed')}")
                return msg["result"]
        raise RuntimeError(f"Codex session ended during {method}")

    def tool(self, server, tool, args, expected_error=False):
        if tool not in LOCAL_CALLS[server]:
            raise ValueError(f"Outside offline qualification: {server}.{tool}")
        ret = self.request("mcpServer/tool/call", {"threadId":self.thread, "server":server,
                                                  "tool":tool, "arguments":args})
        text = "\n".join(c["text"] for c in ret["content"] if c["type"] == "text")
        if bool(ret.get("isError")) != expected_error:
            raise RuntimeError(f"{server}.{tool}: unexpected status, {text[:500]}")
        structured = ret.get("structuredContent")
        if tool == "slice_stl" and not expected_error:
            if isinstance(structured, dict) and structured.get("slicer_report", {}).get("failed"):
                raise RuntimeError("Studio reported a failed slice")
            return text
        if isinstance(structured, dict) and set(structured) == {"result"} and structured["result"] == text:
            return text
        if structured is not None:
            return structured
        try:
            return json.loads(text)
        except ValueError:
            return text


@contextmanager
def fresh_session(folder):
    executable = shutil.which("codex")
    if not executable:
        raise RuntimeError("Install Codex CLI or add it to PATH")
    p = subprocess.Popen([executable, "app-server", "--stdio"], cwd=folder, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    watchdog = threading.Timer(300, p.kill)
    watchdog.start()
    try:
        session = Codex(p)
        session.request("initialize", {"clientInfo":{"name":"x2d-offline-qualification","version":"1"},
                                       "capabilities":{"experimentalApi":True}})
        session.send({"method":"initialized","params":{}})
        skills = session.request("skills/list", {"cwds":[str(folder)],"forceReload":True})
        assert any(s["name"] == "bambu-x2d-printing" and s["enabled"]
                   for group in skills["data"] for s in group["skills"]), "Skill missing from fresh session"
        session.thread = session.request("thread/start", {"cwd":str(folder),"ephemeral":True})["thread"]["id"]
        yield session
    finally:
        watchdog.cancel()
        p.stdin.close()
        try:
            p.wait(timeout=7)
        except subprocess.TimeoutExpired:
            p.terminate()
            p.wait(timeout=7)
        p.stdout.close()


def create_and_edit(session, folder):
    first, second, stl = [str(folder/n) for n in ("v1.FCStd","v2.FCStd","from-freecad.stl")]
    script = dedent(f"""
        def x2d_release_check():
            import FreeCAD as App, MeshPart, Part
            prev = App.ActiveDocument.Name if App.ActiveDocument else None
            doc = App.newDocument("X2DReleaseWasher")
            try:
                outer = doc.addObject("Part::Cylinder","Outside")
                outer.Radius, outer.Height = 10, 3
                tool = doc.addObject("Part::Cylinder","Bore")
                tool.Radius = 3
                tool.setExpression("Height","Outside.Height")
                part = doc.addObject("Part::Cut","Washer")
                part.Base, part.Tool = outer, tool
                doc.recompute()
                outer.ViewObject.Visibility = tool.ViewObject.Visibility = False
                doc.saveAs({first!r})
                outer.Height, tool.Radius = 4, 4
                doc.recompute()
                doc.saveAs({second!r})
            finally:
                App.closeDocument(doc.Name)
                if prev in App.listDocuments(): App.setActiveDocument(prev)
            doc = App.openDocument({second!r})
            try:
                shape = doc.Washer.Shape
                assert shape.isValid() and len(shape.Solids) == 1
                assert sorted(round(2*f.Surface.Radius,6) for f in shape.Faces if isinstance(f.Surface,Part.Cylinder)) == [8,20]
                assert abs(shape.BoundBox.ZLength-4) < 1e-6
                mesh = MeshPart.meshFromShape(Shape=shape,LinearDeflection=0.015,AngularDeflection=0.08,Relative=False)
                mesh.write({stl!r})
                print("X2D_NATIVE_PASS")
            finally:
                App.closeDocument(doc.Name)
                if prev in App.listDocuments(): App.setActiveDocument(prev)
        x2d_release_check()
    """)
    ret = session.tool("freecad", "execute_code", {"code":script, "include_screenshot":False})
    assert isinstance(ret,str) and "X2D_NATIVE_PASS" in ret and Path(stl).is_file(), str(ret)[:500]
    return stl


def blender_round_trip(session, folder, original):
    checked = str(folder/"from-blender.stl")
    code = dedent(f"""
        def x2d_mesh_check():
            import bpy, bmesh
            assert bpy.context.mode == "OBJECT", "Return to Object Mode before running the isolated scene check"
            win = bpy.context.window
            previous = win.scene
            scratch = bpy.data.scenes.new("X2DReleaseScratch")
            obj = mesh = None
            try:
                win.scene = scratch
                assert bpy.ops.wm.stl_import(filepath={original!r},global_scale=1,use_scene_unit=False) == {{"FINISHED"}}
                obj = bpy.context.view_layer.objects.active
                mesh = obj.data
                ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
                corners = [ev.matrix_world @ v.co for v in ev.data.vertices]
                spans = [max(p[i] for p in corners)-min(p[i] for p in corners) for i in range(3)]
                assert all(abs(a-b)<0.03 for a,b in zip(spans,(20,20,4)))
                bm = bmesh.new()
                try:
                    bm.from_mesh(mesh)
                    assert all(e.is_manifold for e in bm.edges)
                finally:
                    bm.free()
                assert bpy.ops.wm.stl_export(filepath={checked!r},export_selected_objects=True,
                                             global_scale=1,use_scene_unit=False) == {{"FINISHED"}}
                print("X2D_BLENDER_PASS")
            finally:
                win.scene = previous
                bpy.data.scenes.remove(scratch)
                if obj is not None: bpy.data.objects.remove(obj,do_unlink=True)
                if mesh is not None and mesh.users == 0: bpy.data.meshes.remove(mesh)
        x2d_mesh_check()
    """)
    ret = session.tool("blender","execute_blender_code",{"code":code})
    assert "X2D_BLENDER_PASS" in str(ret) and "Traceback" not in str(ret) and Path(checked).is_file(), str(ret)[:500]
    outer, inner = measure(Path(checked),1,2)["loops"]
    for loop, radius in [(outer,10),(inner,4)]:
        assert max(abs(r-radius) for r in loop["radial_range_mm"]) < 0.012
        assert math.hypot(*loop["center_xy_mm"]) < 0.01
    return checked


def slice_to(session, model, destination, settings):
    output = session.tool("bambu-studio", "slice_stl", {"stl_path": str(model), **settings})
    shutil.copyfile(Path(output.strip()), destination)


def plate_test(session, folder, stl, settings):
    durable = folder/"verified-washer.gcode.3mf"
    slice_to(session, stl, durable, settings)
    listing = session.tool("bambu-studio","list_3mf_plates",{"three_mf_path":str(durable)})
    assert listing["plate_count"] == 1 and listing["plates"][0]["sliced"]
    args = {"file_path":str(durable),"bambu_model":"x2d","plate_index":0,"nozzle_diameters":[0.4,0.4],"bed_type":"textured_plate"}
    receipt = session.tool("bambu-studio","inspect_print_file", args)
    (folder/"receipt.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
    summary = reviewed_plate(durable, receipt, 1)
    assert summary["nozzles_mm"] == [0.4,0.4] and summary["materials"] == ["PLA"] and summary["plate_type"] == "textured_plate"
    assert summary["slicer"]["settings"]["layer_count"] == 20
    for bad, clue in [({"plate_index":1},"plate"),({"nozzle_diameters":[0.6,0.6]},"nozzle")]:
        rejection = session.tool("bambu-studio","inspect_print_file",args | bad, expected_error=True)
        assert clue in str(rejection).lower()
    with ZipFile(durable) as archive:
        saved = json.loads(archive.read("Metadata/project_settings.config"))
        assert "X2D" in saved["printer_settings_id"] and "PLA Basic" in str(saved["filament_settings_id"])
        assert float(saved["layer_height"]) == 0.2 and "0.20mm Standard" in saved["print_settings_id"]
        assert not check_reach(saved,1,[10,50,0,16,57,4])["inside_nozzle_envelope"]
    return summary


def multicolor_test(session, folder, settings):
    colors = ["#335588", "#F2CC55"]
    parts = []
    for index, name in enumerate(("base", "top")):
        path = folder / f"{name}.stl"
        faces = [tuple((x, y, z + 2*index) for x, y, z in tri) for tri in ring_triangles(height=2)]
        write_stl(path, faces)
        parts.append({"name": name, "filament": index+1, "color": colors[index], "stl_path": str(path)})
    project = folder / "two-color.3mf"
    result = session.tool("bambu-studio", "counterpart_make_3mf", {"parts": parts, "out_path": str(project)})
    assert result["objects"] == 1 and result["filaments"] == 2
    readback = session.tool("bambu-studio", "counterpart_part_meshes", {"three_mf_path": str(project), "out_dir": str(folder)})
    assert not readback.get("skipped") and len(readback["parts"]) == 2
    for part in readback["parts"]:
        slot = part["filament"] - 1
        assert part["name"] == parts[slot]["name"] and part["color"] == colors[slot]
        bounds = measure(Path(part["stl_path"]), 1)
        assert abs(bounds["min_mm"][2] - 2*slot) < 0.001 and abs(bounds["span_mm"][2] - 2) < 0.001
    dest = folder / "two-color-review-pending.gcode.3mf"
    two_slots = {"load_filaments": ";".join([settings["load_filaments"]] * 2),
                 "filament_colours": ";".join(colors), "arrange": True}
    slice_to(session, project, dest, settings | two_slots)
    with ZipFile(dest) as archive:
        info = ElementTree.fromstring(archive.read("Metadata/slice_info.config"))
        project_settings = json.loads(archive.read("Metadata/project_settings.config"))
        gcode = archive.read("Metadata/plate_1.gcode").decode().splitlines()
    assert project_settings["filament_colour"] == colors
    used = {f.get("color") for f in info.findall("./plate/filament")
            if f.get("used_for_object") == "true" and float(f.get("used_g")) > 0}
    assert used == set(colors), used
    ranges = {e.get("filament_list"): e.get("layer_ranges") for e in info.findall(".//layer_filament_list")}
    assert ranges == {"0": "0 9", "1": "10 19"}, ranges
    # The pinned Studio emits a bare C pre-cooling flag. The pinned inspector rejects it.
    # Verify the refusal refers to that exact command in the saved file.
    rejection = session.tool("bambu-studio", "inspect_print_file", {"file_path": str(dest), "bambu_model": "x2d",
                             "plate_index": 0, "nozzle_diameters": [0.4, 0.4], "bed_type": "textured_plate"}, expected_error=True)
    line = re.search(r"line (\d+): Print safety: missing numeric C temperature target or parameter", str(rejection))
    assert line, rejection
    assert re.fullmatch(r"M104\s+T\d+\s+S\d+\s+N\d+\s+C\s*;Multi extruder pre cooling", gcode[int(line[1])-1].strip())
    return "Two slots used on intended layers. File inspection rejected the generated pre-cooling flag. No receipt."


def instance_test(session, folder):
    for copies in (2,1):
        project = folder/f"copies-{copies}.3mf"
        instanced_3mf(project, copies)
        evidence = session.tool("bambu-studio","counterpart_part_meshes",
                                {"three_mf_path":str(project),"out_dir":str(folder)})
        assert evidence["units"] == "mm" and not evidence.get("skipped"), evidence
        parts = sorted((measure(Path(p["stl_path"]),1) for p in evidence["parts"]),key=lambda p:p["min_mm"][0])
        assert len(parts) == copies
        # The second fixture simulates losing an instance from a two-copy brief.
        assert (len(parts) == 2) == (copies == 2)
        for i, part in enumerate(parts):
            for actual,expected in zip(part["span_mm"],(25.4,50.8,12.7)):
                assert abs(actual-expected) < 0.001
            for actual,expected in zip(part["min_mm"],(76.2*i,25.4,0)):
                assert abs(actual-expected) < 0.001


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filament", type=Path, default=Path("C:/Program Files/Bambu Studio/resources/profiles/BBL/filament/Bambu PLA Basic @BBL X2D 0.4 nozzle.json"))
    parser.add_argument("--process", type=Path, help="X2D 0.20 mm Standard process profile (defaults to the matching BBL profile tree)")
    args = parser.parse_args()
    if not args.filament.is_file():
        parser.error("Supply the installed X2D 0.4 mm PLA Basic profile via --filament")
    process = args.process or args.filament.parent.parent / "process/0.20mm Standard @BBL X2D.json"
    if not process.is_file():
        parser.error("Supply the installed X2D 0.20 mm Standard process profile via --process")
    settings = {"bambu_model": "x2d", "nozzle_diameter": "0.4", "bed_type": "textured_plate",
                "slicer_profile": str(process.resolve()), "layer_height": 0.2, "slice_plate": 1,
                "use_printer_filaments": False, "load_filaments": str(args.filament.resolve())}
    if not __debug__:
        parser.error("Run without Python optimization so all checks execute")
    folder = Path(tempfile.mkdtemp(prefix="x2d-codex-qualification-"))
    print("Offline artifacts:",folder,flush=True)
    with fresh_session(folder) as session:
        assert session.tool("freecad","get_rpc_status",{})["gui_dispatch"]["ready"]
        scene = session.tool("blender","get_scene_info",{})
        assert isinstance(scene,str) and "Scene" in scene
        assert session.tool("bambu-studio","counterpart_self_check",{})["ok"]
        original = create_and_edit(session,folder)
        checked = blender_round_trip(session,folder,original)
        summary = plate_test(session,folder,checked,settings)
        instance_test(session,folder)
        color_result = multicolor_test(session, folder, settings)
    print("Passed creation, edit, reopen, independent mesh and instance checks, and single/two-color X2D slicing.")
    print(color_result)
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    main()
