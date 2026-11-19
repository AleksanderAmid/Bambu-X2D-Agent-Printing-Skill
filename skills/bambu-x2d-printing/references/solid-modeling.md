# Editable solids in FreeCAD

## Choose the source and operation

A parametric feature change belongs in the FCStd document that owns it. An imported STEP can preserve exact faces and assembly placement but usually lacks the original sketch or design history. For STEP, import to a revision, inventory solids, names, local origins and placements, then use a direct feature, sketch or boolean on the intended solid. A mesh converted into thousands of planar faces rarely recovers the original engineering intent. Reconstruct functional cylinders and planes from measurements when justified. Keep the original for comparison.

1. Read `get_rpc_status` and `list_documents`. Select the right document by internal name and saved path. Inspect `get_objects` and `get_object`. Two objects can share a display label. In linked assemblies distinguish a change to one instance from a change to every instance of a shared source.
2. Choose a stable origin, symmetry plane and mounting datum. Prefer named length/angle properties, spreadsheet aliases, constrained sketches, pads, pockets and patterned holes for features the user expects to customize. Anchor sketches to stable reference geometry where practical. Preserve intentional degrees of freedom and downstream expressions.
3. For ordinary changes use `create_object` or `edit_object`. For a multi-step construction use `execute_code` and a FreeCAD document transaction. Work on a saved revision. Independently recompute, validate and inspect before committing. Avoid raw script edits to unrelated active documents. Use `execute_code_headless` for a separate scratch file when the GUI need not be touched.
4. Inspect the recomputed result and its dependencies. Check for invalid shapes, multiple unintended solids, failed features, dangling links, unintended through-cuts and suppressed features. A boolean can succeed and still remove the wrong wall. Validate the intended solid count in context. When boolean geometry is suspect use Part → Check geometry with BOP checks on the affected result.
5. Save and reopen the editable model. Export only the final intended bodies in their documented frames. Do not export the construction operands of a boolean together with the result. Preserve separate intentional components for multimaterial projects. Read back the final export and repeat critical tests.

## Example checks inside execute_code

The following assumes `final` is the selected final FreeCAD object. Read model-specific features in the proper local frame and scale.

```python
doc = final.Document
doc.recompute()
shape = final.Shape
assert not shape.isNull() and shape.isValid()
print("solids", len(shape.Solids), "volume_mm3", shape.Volume)
print("bounds_mm", shape.BoundBox.XLength, shape.BoundBox.YLength, shape.BoundBox.ZLength)
for face in shape.Faces:
    surface = face.Surface
    if isinstance(surface, Part.Cylinder):
        print("cylinder", "diameter_mm", 2 * surface.Radius, "axis", surface.Axis,
              "axis_point", surface.Center)
```

Bind `import Part` in the call. Classify cylinders by diameter, location, orientation and adjoining faces before interpreting them as holes. A fillet is also cylindrical. Verify a through-hole at multiple depths or with an appropriate section. For a hole pattern compare both center coordinates and the specified pitch. Validate the named mounting face and its thickness independently.

## Fits and print-oriented changes

Record the assembled orientation separately from bed orientation. Consider fastener access, insertion and removal, nut anti-rotation features, lead-ins, cap/head clearances, thermal expansion and contact surfaces. If a model will be split, compare the fit and assembly cost of keys, fasteners or bonded seams against printing in one piece. Place joints where the user can assemble them and where layer orientation fits the load. For matching bores, bosses, inserts or snaps, verify every mating dimension and the intended gap. Critical fit or strength may require a physical test.

For text or an emblem, verify the correct face, sense (emboss/deboss), text direction, depth and surviving strokes in the sliced layers. For a fillet, chamfer or shell change, verify the feature did not consume a thin wall or reduce required internal clearance.

## Failure recovery

FreeCAD's script namespace persists. Qualify document and object references on every new operation. `execute_code_async` is useful for work on independent geometry. Document or view work must be handed back via the supported GUI `commit()` callback. Poll the returned job ID using `get_async_status`. For GUI task timeouts check `get_task_status` and `get_rpc_status`. An operation reported as still running can finish later. After partial, retained-invalid or unknown outcomes inspect the affected revision before repeating the change. Only reload a saved document after protecting unsaved work. See the [FreeCAD tool reference](freecad-tools.md).
