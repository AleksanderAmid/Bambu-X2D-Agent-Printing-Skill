# Meshes, artistic models and references in Blender

## Inspect before changing anything

Use `get_addon_status` and `get_scene_info`. Request only the relevant object names and fields. Check the active mode, active and selected objects, collections, parenting, linked mesh data, instances, modifiers, shape keys, and world transforms. If several objects share a mesh, choose explicitly whether the edit affects all copies. Save a separate BLEND revision or start an isolated scene for scratch work. Preserve the user's open scene, selection and mode where practical. Avoid factory reset for a one-object edit.

For a photograph, identify known scale, projection, camera perspective, occlusion and unseen surfaces. A single perspective view is suitable for visual likeness. Fitted interfaces need reliable orthogonal views, a dimensioned drawing, a scale reference in the same plane, a scan or caliper measurements. For decoration, propose a physical size if only appearance matters. Explain which proportions are inferred.

## Edit the mesh

- Import with an explicit unit and axis policy. STL has no unit field. glTF distances are in metres. Inspect the transformed evaluated mesh. Compute bounds or section points with the evaluated object's world matrix applied to each vertex. Multiplying a local axis-aligned bounding box by a single scale value fails for rotation, nonuniform scale, hierarchy and instances.
- For a local change, mask or duplicate the affected region. Keep reference surfaces separate from sculpting, remeshing and smoothing. A global remesh can round a bore, erase embossing or close a narrow slot. Preserve the original material/UV groups if they carry requested surface detail. A texture alone does not assign printable filament regions.
- For an open scan, identify which openings are functional before filling any. For a shell with wall thickness use evaluated cross-sections. For a weak or floating detail, connect it deliberately, add a base, split for assembly, or change orientation as the design allows. Verify the silhouette in several views.
- For multimaterial work, keep intentionally touching solids aligned. Use Bambu Studio project painting or separate well-defined part solids with a shared origin. Gaps caused by independent recentering and unintended overlapping solids can change the sliced color boundaries.
- Inspect boundary/non-manifold edges, degenerate faces, normals, intersections, isolated shells, bottom contact and meaningful wall thickness. Use BMesh or a locally available 3D Print Toolbox. Inspect the result after each consequential repair. The installed MCP does not imply the toolbox extension is installed.
- For external assets or generation tools, review source rights, any upload of references, provider availability and potential cost with the actual request. Search results, textures and Gaussian-splat worlds need conversion or reconstruction before they can supply printable surfaces. Keep an entirely local route for existing models and private references.

## Export and inspect

Use `execute_blender_code` for bpy operations and `look` for targeted orthographic, underside, cross-section or multiview checks. A render may hide an internal intersection. Check numerically as well. For evaluated geometry use `obj.evaluated_get(depsgraph)`, `to_mesh()` and the evaluated object's `matrix_world`. Release temporary evaluated meshes with `to_mesh_clear()`. Include intended instances where applicable.

Export only the intended selection with deliberate axis, modifier and unit settings. Restore selection afterward. A repeatable convention for an STL already expressed in mm is import/export scale 1 with scene-unit conversion disabled, preserving raw mm coordinates in the scratch scene. A scene authored in metres needs a different conversion. Reimport the saved STL to a clean scratch collection or read it with the [independent probe](dimensions.md). Check the extent along each designed axis, feature sections, component count and orientation. After asymmetric edits compare the left/right or front/back landmarks too.

For a failed operation, read the scene again. Identify newly created objects, incomplete files and changed modifiers before deciding whether another call is needed. Use a fresh output name for a revised export. See the [Blender tool reference](blender-tools.md).
