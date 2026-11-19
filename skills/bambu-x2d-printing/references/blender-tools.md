# Blender MCP tools

Applies to mcp-for-blender 2.3.1. Default server name is `blender`. A live Blender 5.3 scene and enabled add-on are required for scene actions. For exact argument types, enum values and limits read the installed tool schema. Degrees, unit scale and axis conventions depend on the bpy operation the caller chooses.

All entries were discovered on Windows. Entries marked **Exercised** also have a local execution result. For other entries the installed schema and upstream implementation describe the expected behavior.

## Local scene work

Use the direct Blender server for the normal mesh workflow. Preserve unrelated scene objects. Inspect the scene and saved artifacts before retrying a script after an interrupted reply.

### `get_addon_status`

Read Blender/add-on compatibility and enabled libraries/generators. In the pinned Windows build this call returned `Error checking addon status: No module named 'blender_mcp.config'` inside an ordinary text result. Read the actual result even when MCP reports success. Use `get_scene_info` and a read-only `execute_blender_code` call printing `bpy.app.version_string` to establish the local modeling connection. Leave generator/provider readiness unknown until independently observed.

Required fields — none. Optional fields — `user_prompt`. Exercised on Windows. The diagnostic returned the compatibility error above.

### `get_scene_info`

Return a text inventory and selected details by query/root/fields. Use it to choose an object and check type, transform and topology. Use evaluated geometry for physical dimensions.

Required fields — none. Optional fields — `user_prompt`, `query`, `root`, `fields`, `limit`. Exercised on the Windows reference setup.

### `execute_blender_code`

Run bpy/BMesh Python in the live session. Print the measurements, filenames and selected object count needed to verify the operation. Protect the open scene, handle modifiers, and reimport final exports.

Required fields — `code`. Optional fields — `user_prompt`. Exercised on the Windows reference setup.

### `look`

Return a visual sample from viewport, camera, target angles, frames or an image. Pick views and shading that reveal the feature. Limit image size for inspection. Measure fit from geometry.

Required fields — none. Optional fields — `mode`, `target`, `views`, `distance`, `shading`, `frames`, `frame_count`, `view`, `image`, `max_size`, `user_prompt`.

## Assets and generative services

Optional network workflows. Check enabled provider, rights, credentials, upload consent and cost as applicable. An imported result usually needs scale, topology and printability work.

### `search_assets`

Search the requested library and return candidates, provider IDs and available metadata. Distinguish surface materials/HDRIs from geometry. Choose by rights, scale and intended use.

Required fields — `source`. Optional fields — `query`, `asset_type`, `category`, `attributes`, `min_size_m`, `licence`, `animated`, `limit`, `previews`, `user_prompt`.

### `import_asset`

Download a selected provider ID into the scene, or apply a compatible asset to an object. Newly imported geometry may use different units or multiple materials. Check selection, bounds, source rights and export inclusion.

Required fields — `source`, `id`. Optional fields — `asset_type`, `target_size`, `apply_to`, `resolution`, `file_format`, `user_prompt`.

### `generate_3d`

Submit a text/image request for a single generated object or poll its existing job. Provider availability, quality and size conditioning vary. Retain the job ID and check it before paying for or submitting a duplicate. Set a verified physical scale afterward.

Required fields — none. Optional fields — `prompt`, `image`, `name`, `provider`, `quality`, `bbox_condition`, `pose_mode`, `job`, `wait_seconds`, `user_prompt`.

### `generate_gaussian_world`

Request or poll a World Labs environment. Returns a scene representation made from splats. A rough collision mesh is only a reconstruction aid. Use this for reference if requested. Build a closed printable surface separately.

Required fields — none. Optional fields — `prompt`, `image`, `name`, `resolution`, `job`, `wait_seconds`, `user_prompt`.

## Privacy and feedback

These settings have no role in measuring or slicing a part. Follow the user's existing collection choices.

### `disable_telemetry`

Disable upstream collection covered by this tool. Return the reported preference change. Use the host's documented environment setting when the user wants the anonymous usage record disabled too.

Required fields — none. Optional fields — `user_prompt`.

### `record_trajectory_feedback`

Record feedback about a captured step when trajectory capture and consent apply. Labels or corrections can contain project information. This is data submission, not CAD undo or a physical inspection.

Required fields — `feedback`. Optional fields — `correction_text`, `step_index`, `user_prompt`.

Host behavior and optional services. [Upstream README](https://github.com/ahujasid/mcp-for-blender)
