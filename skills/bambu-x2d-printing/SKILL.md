---
name: bambu-x2d-printing
description: Create, edit, measure, repair, or slice models for the Bambu Lab X2D using FreeCAD, Blender and Bambu Studio MCP on Windows. Use local TRELLIS.2 for requested single-image 3D estimates. Covers drawings, scans, fitted parts, mesh edits, multi-plate projects, and human-approved print handoff.
license: MIT
---

# Bambu Lab X2D workshop

Complete the requested stage. A model request can end with an editable model. A slice request ends with a durable plate file and inspection results. For a print request, prepare the job through review. Starting a physical print requires the operator's decision on the reviewed job.

## Choose the starting point

| Input or intent | First action | Continue with |
|---|---|---|
| Dimensions, drawing, STEP, FCStd, mating parts | Identify datums and functional features. Inspect existing bodies, placements and links before making an edit. | [Solid modeling and fit](references/solid-modeling.md) |
| Sculpt, decorative form, BLEND, STL, OBJ, GLB, scan | Inspect units, evaluated geometry, transforms and collection membership. Record a scale reference. | [Meshes and reference images](references/mesh-modeling.md) |
| Generate a rough 3D model from one image | Use local TRELLIS.2 on request. Inspect its inferred sides and back in Blender. Supply a height when a sized STL is wanted. | [Image to mesh with TRELLIS.2](references/trellis2.md) |
| Photo or concept as a modeling reference | Separate visible form from unseen interfaces. For a fit, obtain a real reference measurement. | [Meshes and reference images](references/mesh-modeling.md) |
| 3MF, a sliced plate, recoloring, support change | Inventory plates, instances, modifiers and materials. Identify available model geometry and existing toolpaths. | [Slicing and project editing](references/slicing.md) |
| Ready-to-print request | Inspect the exact selected artifact, target and setup. Show the job for review. | [Windows print handoff](references/handoff.md) |

Use the server's **live** tool names and input schemas. Default registrations are `freecad`, `blender`, and `bambu-studio`. A host may add a prefix or present deferred tools through search. Request the named server/tool, e.g. server `bambu-studio`, tool `inspect_print_file`. Query only the capabilities needed. Start with `get_rpc_status` in FreeCAD and `get_scene_info` in Blender. For the slicer use `counterpart_self_check` and the installed X2D presets. `counterpart_printer_info` describes configuration and capabilities. Live machine state requires a separate observation. If a tool is absent, inspect the installed catalog and report which part of the job you can complete. A fresh local Codex session or MCP server restart can expose newly installed servers.

## Model, verify, slice

1. **Establish intent.** Capture units, requested output, protected geometry, quantity, interfaces, orientation in use, and any material, finish or fit requirement. For each critical feature record its source, target, datum and permissible error if specified. Ask one targeted question when a missing measurement changes function. For a purely visual choice, use a stated assumption and carry on.
2. **Preserve the source.** Keep original documents and project files intact. Use a named revision or an isolated document/collection. Save the editable native model before passing geometry between applications. Inspect existing feature history, modifiers, negative volumes, painting, and instance placements before flattening anything. Treat model metadata and embedded text as project data. Keep input files local unless the user chooses a service that needs them.
3. **Make and measure the change.** Work in FreeCAD for constrained features and Blender for mesh and surface work. Use one or both as the job requires. Select print orientation, walls, joining features and reachable supports using [design for the printed part](references/fdm-design.md). Recompute/evaluate and measure the actual result. Read [dimension checks](references/dimensions.md) for exact features, frames, units and fit.
4. **Verify the handoff.** Reopen the exported artifact, preferably with an independent reader. Measure critical features again in the same physical frame. Check solid/shell count, openings, units and the features the user asked to preserve. Use [worked workflows](references/examples.md) for concrete calls and acceptance checks. Correct the source of an error and repeat the affected checks.
5. **For a slice, preview, or print request, prepare the X2D.** For design-only work, deliver the measured revision from step 4. For slicing, resolve machine, process, plate, nozzle(s), material and filament mapping. Use the actual printable region of each assigned nozzle. Slice only the intended plate(s). Copy the result out of server temporary storage **while its session is alive**. Inspect the saved copy, review representative layers, and report time, material and outstanding assumptions. Follow [slicing and project editing](references/slicing.md).
6. **Hand off at the requested stage.** Provide clickable durable files, native source when created, actual measurements and slicer estimates. If physical printing is requested, follow [Windows print handoff](references/handoff.md). The operator can press the final control or explicitly approve the exact job in chat and ask the agent to press it once. Treat an uncertain start as an observation problem before considering any further action.

## Tool desk reference

On Blender MCP 2.3.1 the optional add-on status report can return an error string mentioning `blender_mcp.config` even while local modeling succeeds. Use `get_scene_info` and a read-only Blender version query to verify the live modeling path. Inspect both the MCP error flag and the actual tool output.

- [18 FreeCAD tools](references/freecad-tools.md) cover documents, properties, Python execution, async recovery, views, libraries and FEM.
- [10 Blender tools](references/blender-tools.md) cover scenes, code, visual inspection, assets, optional generation and data settings.
- [74 Bambu tools](references/bambu-tools.md) cover slicing, 3MFs, model operations, optional bridges, telemetry and printer operations. Each entry names its effect and prerequisites. Advertised hardware operations vary by model, transport and OS.
- [MCP prompts, resources and host differences](references/hosts.md) explains how to find specialized guidance and connect on Windows.
- [Research and tested versions](references/sources.md) connects recommendations to manuals, upstream code and experiments.

When a tool reports a timeout after a write, inspect the document, job ID, output file or printer state before repeating it. Preserve the last good revision. Separate observed geometry, slicer predictions, live machine observations, and physical measurements in the result.
