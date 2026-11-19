# Projects and slicing in Bambu Studio

## Preserve the project structure

Distinguish a geometry-only 3MF, an editable Studio project with plate/object settings, and a sliced project holding `Metadata/plate_N.gcode`. A suffix alone does not identify all contents. Start with `list_3mf_plates`. Inspect instance counts, designer plate order, build items, objects, parts, painted features and filament slots. Check the archive in a read-only viewer if a modifier matters. Inspect copies when making changes. A mesh extracted by `counterpart_part_meshes` is in build-frame millimetres. Its output can omit nonprinting modifiers, negative volumes or unsupported parts. Rebuilding the entire project from those STLs can lose painting, support blockers and per-object settings. Edit the original project structure where those matter. If a sliced file has toolpaths only, request the editable source for a geometric change.

For multiple parts produced from CAD, export in a common coordinate system. Use `counterpart_make_3mf` for clean multipart color projects where the supplied parts and assignments express the intended result. Compare the new and original plate manifests before trusting any reconstructed project. If repeat copies are requested, check actual instance count after arranging.

## Resolve settings for this job

1. Select `bambu_model="x2d"` and the installed X2D machine preset for the actual nozzle diameter(s) and flow type. Determine the plate surface and material, filament profile, intended color-to-slot mapping and whether supports use another nozzle or material. Local print profiles describe a proposed setup. Confirm live setup via Studio, operator or authorized telemetry when preparing a physical job.
2. Use the installed matching profile tree. Stock profiles inherit base settings and G-code. The MCP resolves them when slicing. Avoid sending a foreign project unchanged to another machine. Preview-only work can use a disclosed assumption for hardware or filament, then require a match at print handoff. For an existing project inspect `get_slice_settings` before overriding it.
3. Check print orientation, first-layer footprint, bridges, overhangs, wall widths, support access and material used. Verify hole/slot size and strength along the intended load directions. Consider the effect of seam, elephant-foot correction and XY compensation on mating faces. Avoid global scaling to fix a local hole. Coordinate design clearance and slicer compensation so each correction is applied once.
4. Evaluate per-nozzle printable polygons, height, excluded regions, plate margins and travel clearances with the actual arranged parts. The nominal main-head envelope is 256 × 256 × 260 mm. The published common dual-head working volume is 235.5 × 256 × 256 mm. In the tested 0.4 mm profile the auxiliary polygon begins at X = 20.5 mm. The actual profile and job layout decide the usable coordinates. Test support, brim, prime tower, and any sequential head clearance in addition to the model footprint. Mixed physical nozzle diameters require GUI slicing with this connector version.
5. Inspect material compatibility for the selected main or auxiliary feed path. For dual-material interfaces verify which tool extrudes the part, support body and interface layer, layer changes and flush/purge structures. A color swatch or filament type in the file cannot prove that spool is loaded.

## Slice and keep the result

For a positioned feature, test a resolved X2D rectangular nozzle envelope with the helper below. The six values are min X/Y/Z followed by max X/Y/Z in bed-frame mm. Index 1 is the auxiliary nozzle in the tested profile. This example should fall outside its left edge. Check excluded areas, tower, skirts and head clearances separately in Studio.

```powershell
python scripts/nozzle_reach.py "job/plate.gcode.3mf" --nozzle 1 --bounds 10 50 0 16 57 4
```

`list_3mf_plates` and `inspect_print_file` use zero-based indexes. `slice_stl.slice_plate` selects one plate using **one-based** numbering. Zero requests all plates. Preserve both the human plate name/number and its index. For example, slice the second plate with `slice_plate=2`, then inspect the relevant output plate using its own newly enumerated index. A single-plate export may be renumbered. Match the parts and selected plate in the output.

For a known-mm STL, two standard 0.4 mm nozzles, PLA Basic and textured PEI, use the following example. Resolve both profiles on the actual host. For an existing project, inspect and preserve its process and plate unless the user requests a change or the target hardware requires one.

```json
{"stl_path":"D:/job/part.stl","bambu_model":"x2d","nozzle_diameter":"0.4","bed_type":"textured_plate","slicer_profile":"C:/Program Files/Bambu Studio/resources/profiles/BBL/process/0.20mm Standard @BBL X2D.json","slice_plate":1,"layer_height":0.2,"use_printer_filaments":false,"load_filaments":"C:/Program Files/Bambu Studio/resources/profiles/BBL/filament/Bambu PLA Basic @BBL X2D 0.4 nozzle.json"}
```

Read the result of `slice_stl`. The tested server returns the output path in a text content block and the slicer report in structured content. Check the report for failure or warnings. Its temporary folder can disappear when the server session closes. While the session is alive, copy the returned file to a new durable job filename and confirm the copy exists. For a preserved project use the saved project settings where suitable, or `slice_with_template` for a known matching template. If the CLI cannot express a painted edit, mixed nozzle setup, or project-specific feature faithfully, prepare and slice the saved revision in Studio. Reinspect the resulting plate.

## Inspect the exact saved plate

Call `inspect_print_file` with the durable path, `bambu_model="x2d"`, its zero-based `plate_index`, and known `nozzle_diameters` and bed type when available. Check both MCP `isError` and returned status/content. Record the v1 file-only receipt, SHA-256, selected plate, nozzle diameters, materials, settings, time, grams and layer count when present. `include_preview=true` supplies composite toolpath views. Use Studio's layer slider or inspect extruding paths at the feature's actual layer heights for first-layer contact, holes, thin walls, supports, inaccessible cavities, material transitions and the top surface. Travel moves and purge lines can extend far beyond the model's outline.

If a feature or plate is wrong, correct the source or settings, slice to a new file, and inspect again. If the result changes, discard the old job approval. A passed file check does not observe the real printer, plate cleanliness, loaded filament, mechanical calibration or physical dimensions. Use [Windows print handoff](handoff.md) for the final decision.

**Known two-color inspection failure on the tested versions.** With a stock X2D process, two PLA Basic slots, and a color change halfway up the part, Studio 02.09.01.70 wrote the intended colors into layers 1–10 and 11–20. Connector 1.1.98 rejected Studio's multi-extruder pre-cooling line with `missing numeric C temperature target or parameter`. For this result, deliver the editable color project and identify the slice as awaiting inspection. Preserve the diagnostic and review the original output in Studio. Keep the agent's physical handoff pending until a supported configuration produces a file that passes inspection. Do not edit temperature commands or suppress the inspector to obtain a receipt. Other color projects need their own inspection. [Pinned inspector implementation](https://github.com/DMontgomery40/bambu-printer-mcp/blob/9a590fbd1e83e875ef093fc2093d9a021161ef95/src/safety/print-file.ts)
