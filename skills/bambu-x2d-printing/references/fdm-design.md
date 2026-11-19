# Design for the printed part

Use this guide when an engineering choice will change the manufacturability of the design. Establish which design priority matters most, such as fit, finish, load direction, appearance, print time, material use, or ease of assembly. Preserve explicit requirements. For a file-only edit, report likely printing implications without fabricating a slice or a physical test.

## Select an orientation using the part's function

| Constraint | Compare | Evidence that decides |
|---|---|---|
| Mating face, snap arm or mounting boss | Assembled load direction versus layer interfaces, plus the effect of seam and support scars | Sections through the root and fastener, layer preview, representative coupon if the load matters |
| Visible finish and embossed detail | Which face lies on the plate or support and whether it carries the intended texture | Preview the first visible skin and the layers containing the shortest stroke |
| Bore, pocket or internal duct | Vertical versus horizontal opening, entry chamfer, sag at the crown, ability to remove supports | Cuts at the mouth, mid-depth and exit, and actual perimeter paths at feature transitions |
| Tall, narrow model | First-layer contact, center of mass, available brim area, flexibility during travel | First-layer preview including brim and tower, occupied envelope and clearance |
| Large assembly | One-piece posture versus splitting into keyed components, including access for fasteners and an insertion path | Dry assembly in CAD and separate print-space checks for every component |

Keep a datum or transform connecting the assembled model to the print orientation. Compare the critical features of two candidate orientations when they trade a cleaner face against a weaker layer direction or substantial support. Use slicer estimates to choose among candidates if time or material is a goal.

## Make features survive slicing

- **Walls and ribs.** Check minimum thickness on the evaluated model, especially near a shell offset, fillet, taper or intersecting cut. Compare against the *effective extrusion widths and wall generator* in the selected profile, then inspect continuous paths on the thinnest layer. Wall count alone cannot recover a feature that the slicer omits. For a loaded boss, strengthen the connection to the wall and consider load direction as well as infill.
- **Holes and clearance.** A CAD cylinder, exported polygon, XY compensation setting and cooled hole represent different steps. Preserve specified centers and datums when correcting a diameter. A horizontal circular hole may sag at its crown. Compare orientation, chamfered/teardrop geometry if the design permits it, or removable support. For a blind hole or counterbore, verify depth and seating shoulder as well as diameter.
- **Text and decoration.** Measure the narrowest stroke, counters inside letters, depth and available layers. Verify the feature survives at the chosen nozzle/line width and that the visible view reads correctly after orientation. Surface texture in a render contributes no extrusion paths.
- **Bridges and overhangs.** Identify the first unsupported layer and the anchors at both ends of each bridge. There is no universal safe bridge length or overhang angle for every material and speed. Compare a changed orientation, local chamfer/arch, support, or a split if the supported surface is functional. Check support access after assembly.
- **Print-in-place parts.** Measure lateral and vertical gaps separately. Inspect every layer where neighboring components approach. Elephant foot, a seam, bridging or support can join otherwise separate solids. Preserve intended captive bodies and clear support-removal paths. Use a small interface coupon if a failed clearance would ruin a long job.
- **Screws, inserts and threads.** Start from the actual fastener or insert drawing. Distinguish clearance hole, pilot bore, thread diameter, head recess and insertion depth. For a heat-set insert verify wall stock and a relief below it. For a printed thread verify engagement, lead-in and a short mating sample. Nominal thread size does not prescribe a universally printable bore.
- **Enclosures and assemblies.** Check the swept path for an inserted part, battery door, tab or cable. Add alignment keys or fastener access when splitting. Compare internal clearances with the actual installed accessory and case when the object fits around another product.

## Choose process adjustments from evidence

| Observation | First place to inspect | Targeted change to consider |
|---|---|---|
| Entire part is 25.4× or 1000× out | Unit source and every import/export transform | Correct the conversion at one boundary, then remeasure |
| Outside size is correct but the exported hole is too small | Native cylinder, chord error, minimum across-flats size | Correct the feature or tessellation before applying printer compensation |
| CAD and exported geometry match but the prototype binds at its base | First-layer spread, lead-in and actual cooled dimensions | First-layer/elephant-foot correction or functional chamfer, followed by the same coupon |
| Text vanishes or a wall has interrupted paths | Layer preview by line type, nozzle width and profile | Widen the feature, change orientation or use a suitable smaller-nozzle profile |
| Support scars a mating face | Support contact location and removal direction | Reorient, relocate the seam/split or use a compatible interface material |
| Part warps or snaps in use | Material, conditioning, plate, cooling, geometry and layer direction | Test a targeted process/orientation/design change. Keep measured physical results with the revision |

For multimaterial work, distinguish decorative color, distinct structural material and support-interface material. Decide whether the second material is needed throughout the support or only at its interface. Check material temperature/adhesion compatibility and tower placement in the selected profiles. The X2D has different main and auxiliary feed paths. Confirm the actual spool, nozzle material/diameter and path compatibility before assigning a flexible, filled or support filament. Do not infer compatibility from another printer's preset. [X2D extrusion systems](https://blog.bambulab.com/two-extruders-one-purpose-what-is-x2d-direct-drive-extrusion-and-auxiliary-extrusion/) · [Designing for FFF](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)

If evidence is incomplete, deliver the verified model or candidate plate with the specific remaining question. For consequential fit, compare the first measured coupon against its nominal CAD and its saved export in the same frame. Change one relevant quantity at a time and record what improved.
