# Dimensional verification

## Make the user's requirement measurable

Write down the critical features before choosing an export setting. For a mounted part, name the mating face, axes, hole pattern, fastener fit and insertion direction. For a costume or figurine the overall height and base contact area may be the only functional measurements. For an edit, include features that must stay at their current sizes. Use a compact record like this in the job notes.

| Feature | Datum and method | Target and source | CAD | Reopened export | Physical |
|---|---|---|---|---|---|
| Washer through-bore | Cylinder diameter and interior cross-section, measured normal to the flat faces | 8.00 mm, drawing | Measure cylindrical face | Measure inner contour | Caliper or suitable gauge if printed |
| Mounting pitch | Center to center in mounting plane | From drawing or measured mating part | Measure axes independently | Compare contour centers in that frame | Test with actual hardware |
| Overall thickness | Normal distance between mating planes | User measurement with stated uncertainty | Plane-to-plane | Same datum after applying placements | Measure after cooling |

Enter numerical results when measured. A nominal 8 mm screw, an 8 mm finished hole, and an 8 mm CAD bore are three different requirements. Ask which matters if that changes the design. Record per-side vs total/diametral clearance. For a circular 10.00 mm pin and 0.20 mm clearance *per side*, the target hole is 10.40 mm. This number illustrates the stated clearance convention. Choose print clearance from actual material/process data or a coupon.

## Resolve scale and coordinate frames

1. Normalize measurement notes to millimetres. Keep the original drawing units and conversion visible. Exactly 1 in = 25.4 mm and 1 m = 1000 mm. FreeCAD quantities carry units. Raw floats in its geometry API usually represent millimetres. Read the property type for angles, loads or other quantities.
2. An STL stores coordinates without a declared unit. Establish its scale from export provenance, a specified overall dimension, or a known feature. Do not silently select whichever unit makes it fit the bed. OBJ conventions vary. glTF uses metres for linear distances. Read import and export settings once at each boundary to prevent double conversion.
3. In Blender, inspect the scene unit system and scale, object and parent transforms, evaluated modifiers, and instance placement. A UI display-unit change can relabel a number without changing the physical geometry passed to a slicer. If using raw mesh coordinates as mm, explicitly choose that convention throughout the round trip.
4. For 3MF, use the package's declared root unit and build/component placements. Multiple rotated or mirrored instances may share a source mesh. Compare feature sizes in their part frame. Compare occupied area in the arranged build frame. A rotated part's world-axis bounding box can grow while the part stays the same size. Use `list_3mf_plates` and `counterpart_part_meshes` if an independent in-build-frame measurement is needed. Inspect its `skipped` list and map by stable part ID.
5. Distinguish the installed slicer's bed origin, a CAD origin, and the physical mating datum. Keep color bodies in a common frame. Centering each part independently changes an assembly. A negative scale can flip winding. Inspect after baking the transform.

## Choose checks with the power to disprove the design

- Use native cylinders/planes and axis distances for constrained CAD. Compare mating part and enclosure with transforms applied. A mass, volume or overall size can pass while a hole has the wrong diameter or location.
- For a mesh, check boundary/overused edges, inconsistent normals, zero-area faces, intersections, shell count and cavity connectivity as relevant. A closed mesh can still depict the wrong shape, contain self-intersections, or have features too small to slice. An open surface used deliberately as a modifier has different acceptance criteria from the printed body.
- For an interference check, place parts in the named assembly frame. A boolean common volume catches overlaps. A distance measure alone can be zero both for contact and penetration. Test insertion motion for a captured nut, key or sliding part. For a flexure inspect deflection space and layer orientation. Only report a strength value with suitable material, load, boundary conditions and validation.
- Use a digital error budget appropriate to the feature. Document how much comes from tessellation, sampling and input uncertainty. If a drawing specifies a manufacturing tolerance, keep it separate from the much smaller numerical allowance for digital round-trip checks. If only nominal dimensions were supplied, label any numerical verification threshold as your test precision. Never add an assumed tolerance to excuse a wrong model.
- On export, select the intended body, tessellate at an error below the feature's digital budget, save, reopen, and repeat the checks. For a cylindrical bore the polygon's across-flats opening can be smaller than its vertex-to-vertex diameter. Check the limiting diameter for fit. Measure first, middle and feature-transition layers in Studio for vanishing walls or closed slots.

## Use the independent STL probe

From the skill directory, with Python 3.11+:

```powershell
python scripts/mesh_probe.py "job/washer.stl" --mm-per-unit 1 --section-z 2
```

The conversion is an input you must establish. Output includes min/max and spans in mm, facet and edge counts, and each closed XY section's center, XY spans, area and nearest/farthest boundary radius from the bounding-box center. For a verified circular loop, twice the minimum radius measures the limiting diameter of its polygon. An irregular or concave loop's radius has a different meaning. Compare each relevant feature. The probe provides measurements and does not issue a universal printability pass.

The cut must cross triangle interiors. Choose a level away from vertices, flats, countersinks and chamfers unless the transition itself is the feature. Section endpoints are joined at 7 decimals in mm. Topology uses exact shared coordinates. On a huge scan, use the evaluated Blender mesh or sample an appropriate section with a BRep plane instead. An absent loop, unclosed section or unreadable file needs investigation. This probe cannot identify a solid's semantic hole names, certify shell orientation throughout, detect every intersection, measure actual extruded material, or infer STL units.

## Close the fit loop

When critical fit lacks prior evidence, make a small coupon with the same interface, datum, wall count, orientation, material, nozzle and process settings. Put several *labeled* candidate values on one coupon if that will answer the question faster. Slice and review it normally. Request human approval before its print. Once it cools, measure at specified locations with suitable equipment, repeat where relevant, and record printer/material/orientation with the result. Correct the nominal design or process based on the error observed. Keep distinct revisions so the correction is never applied twice.
