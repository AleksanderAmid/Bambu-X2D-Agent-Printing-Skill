# Four worked workflows

These examples express a digital modeling and verification procedure. Dimensions and numerical allowances belong to the example. Use the real part's specification and the user's setup for each new job.

## 1. Create a parametric washer

The requested washer has a 20 mm outside diameter, an 8 mm through-bore and a thickness of 4 mm. The user wants an editable source and a sliced preview. A PLA Basic, textured PEI, two 0.4 mm nozzles and 0.20 mm layers setup is specified for this example.

1. Read `freecad.get_rpc_status` and `list_documents`. Use an isolated document. Issue `execute_code` with the following construction, substituting new absolute output paths in an existing job directory. The cylinders retain Radius and Height as editable FreeCAD quantities. The inner height follows the outer when edited.

```python
import FreeCAD as App, Part, MeshPart
d = App.newDocument("WasherRevision")
outer = d.addObject("Part::Cylinder", "Outside")
outer.Radius, outer.Height = 10, 4
bore = d.addObject("Part::Cylinder", "Bore")
bore.Radius = 4
bore.setExpression("Height", "Outside.Height")
washer = d.addObject("Part::Cut", "Washer")
washer.Base, washer.Tool = outer, bore
d.recompute()
outer.ViewObject.Visibility = bore.ViewObject.Visibility = False
assert washer.Shape.isValid() and len(washer.Shape.Solids) == 1
print("diameters", sorted(2*f.Surface.Radius for f in washer.Shape.Faces
                          if isinstance(f.Surface, Part.Cylinder)))
print("thickness", washer.Shape.BoundBox.ZLength)
d.saveAs(native_path)
mesh = MeshPart.meshFromShape(Shape=washer.Shape, LinearDeflection=0.015,
                              AngularDeflection=0.08, Relative=False)
mesh.write(stl_path)
```

2. Reopen the saved source or check it in an isolated reader. Import the STL into a Blender scratch collection when checking a cross-application handoff. Measure the evaluated dimensions and topology. For an independent file check run `mesh_probe.py washer.stl --mm-per-unit 1 --section-z 2`. Expect two near-circular concentric contours, radii near 10 and 4 mm, and a 4 mm Z span. On the reference washer the limiting polygonal bore was 7.9984 mm. A through-hole check also uses cuts near both ends.
3. Call `bambu-studio.slice_stl` with the explicit setup in [slicing](slicing.md). Copy the returned 3MF while the server runs. Call `list_3mf_plates` and `inspect_print_file` on that copy with plate index 0 and nozzle diameters `[0.4,0.4]`. Review the sliced bore, first layer and top surface. The original Windows test artifact reported 20 layers, 455 seconds and 0.88 g. Treat subsequent times/grams as estimates from that new slice.

## 2. Customize a fitted cap and plug

A removable cap must slide over a measured 16.00 mm boss. The user specifies a **0.30 mm total diametral clearance**, cap skirt depth 6.0 mm and cap outside diameter 22.0 mm. These numbers define this example's digital fit.

1. In FreeCAD inspect the boss revision, axis and seating face with `get_object` and a geometric measurement. Derive the target cap bore as 16.30 mm, corresponding to 0.15 mm per side. Keep `BossDiameter`, `DiametralClearance` and `SkirtDepth` as named properties. Preserve 22.0 mm OD if the clearance is later edited.
2. Model the cap as a distinct body. Subtract a cylindrical cavity from the open side, stopping short of the closed top. Use axial sections through the wall and a cut at mid-skirt. Record cavity depth, minimum opening, shoulder position and remaining top thickness. Test insertion clearances in assembly position, including any lead-in.
3. Export the cap and boss with a common assembly frame or document the intentional print transforms. Independent STL sections at mid-skirt should resolve the 16.30 mm bore, and near the closed end should show a cap. Compare the bore against the measured boss. A scalar volume or a single hole section cannot confirm cavity depth.
4. Orient for clean mating surfaces, examine seam and first-layer compensation, and inspect for supports trapped inside. If physical fit has to be established before a long print, make a short labeled ring with the same mating interface and setup. Follow the regular per-job approval for a coupon. Adjust only the dimension or process supported by its measured result.

## 3. Edit a mesh without changing its mounting features

The user wants to soften the silhouette of a scanned shell and add an embossed leaf while preserving its mounting rim and two existing holes.

1. `blender.get_scene_info` → `execute_blender_code` to import with verified units into a revision. Save a BLEND source. Record rim plane, hole diameters, pitch and a section through the rim before any operation. Keep an untouched mesh copy for comparison.
2. Isolate the decorative region. Use a masked/local smoothing operation and build the leaf against the selected outside surface. Boolean or join only what should print as one solid. Do not apply whole-model smoothing to fitted features. Inspect front, underside and a section using `look`.
3. Evaluate the final modifiers, check paired edges and intersections, and measure the rim and both holes again. Export only the chosen body and read the saved STL with the same scale. Compare both centers, both diameters and the mating plane with the source. If an input lacks a known scale, request a measured reference for fitted geometry before certifying it.
4. For a design-only revision, deliver the BLEND, STL and measurements here. When a slice or printability preview is requested, inspect the layers where the leaf begins, its thinnest strokes, and the holes. If a stroke vanishes, edit its geometry or choose a suitable nozzle/profile and re-inspect.

## 4. Recolor or re-plate a multipart project

The user wants to retain a box body and raised logo as aligned components, print the logo in a second color, and prepare only the lid plate of a multi-plate release.

1. Call `list_3mf_plates` on the supplied project. Match plates by contents and name. Inspect instances, shared bodies, paintings and per-part settings. Preserve other plates in the editable project. If there are only toolpaths and no usable geometry, request the editable project for recoloring.
2. If editing an existing painted project, change the specific part/paint assignment in a Studio project revision. For newly authored separate solids already in one frame, a clean assembly can use `counterpart_make_3mf`. Example argument shape:

```json
{"parts":[{"name":"lid","stl_path":"D:/job/lid.stl","filament":1,"color":"#335588"},{"name":"leaf","stl_path":"D:/job/leaf.stl","filament":2,"color":"#F2CC55"}],"out_path":"D:/job/lid-color-project.3mf"}
```

3. Read back part IDs/count, placements and assignments. On the original project's second plate use `slice_plate=2`. For a newly made single-plate assembly use 1. Resolve one compatible profile per project filament in order and verify the nozzle used by the body, interface, support and tower. Project filament numbers and physical AMS slot IDs use distinct numbering. For mixed nozzle diameters slice in Studio's GUI.
4. Save the result, enumerate it again and pass its actual index to `inspect_print_file`. Review color boundaries, first contact, shared reach and purge-tower placement. If live spool data are unavailable, label the mapping as proposed and verify it in Studio at approval. Other plates in an existing project retain their own review and start decisions.

The release trial assembled and sliced two aligned, differently colored bodies. Layer-by-layer slot assignment was correct. The file inspector withheld its receipt on a generated pre-cooling command. The [two-color inspection note](slicing.md) describes the observed outcome and handoff.
