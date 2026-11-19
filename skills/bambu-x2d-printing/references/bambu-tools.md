# Bambu Studio and printer MCP tools

Applies to bambu-printer-mcp 1.1.98, registered as `bambu-studio`. The sections below distinguish local files, configuration, optional services and physical equipment. Read the live schema for types, ranges and defaults. Use profile names and local paths that actually exist. Keep LAN credentials in local configuration. Optional credential fields listed below describe the interface. Avoid putting real values in prompts, logs or public files. The [X2D handoff](handoff.md) applies to all routes that could start a print.

Use text search for the exact tool name. Local preparation proceeds from project inventory → settings → slicing → durable copy → file inspection. Material lookup, live monitoring and optional design bridges are conditional.

All entries were discovered on Windows. Entries marked **Exercised** also have a local execution result. For other entries the installed schema and upstream implementation describe the expected behavior.

## Model files and geometry

These calls read local files or create derived files. Preserve the input and copy desired results to durable storage before server exit. Verify scale, topology and protected features after a transform.

### `get_stl_info`

Read bounds, dimensions and facet count from the named STL. Use for triage and spotting large unit errors. Values follow the coordinate convention of the input. An independent feature measurement is needed for a fitted part.

Required fields — `stl_path`. Optional fields — none.

### `scale_stl`

Write a scaled mesh using dimensionless per-axis multipliers. Uniform scaling can fix a known unit conversion. Anisotropic scaling distorts round holes. Record factors and measure the saved output.

Required fields — `stl_path`. Optional fields — `scale_x`, `scale_y`, `scale_z`.

### `rotate_stl`

Write a rotated mesh using X/Y/Z angles in degrees. Verify the intended datum, handedness and contact face afterward. Preserve original assembly placement separately.

Required fields — `stl_path`. Optional fields — `angle_x`, `angle_y`, `angle_z`.

### `center_model`

Translate a mesh about its center to the origin. The output changes the build frame and may put material below Z=0. Use it for a standalone mesh and recheck assembly registration if placement matters.

Required fields — `stl_path`. Optional fields — none.

### `lay_flat`

Find a qualifying face and return the resulting STL. Read the structured `laid_flat` flag because the server can return the original file when the flag is false. Compare contact area, supports, load direction and surface finish before accepting the pose.

Required fields — `stl_path`. Optional fields — none.

### `extend_stl_base`

Add the specified base extension in mm and return a derived STL. Measure the new bottom plane and check recesses, drain holes and mating surfaces for unintended changes.

Required fields — `stl_path`, `extension_height`. Optional fields — none.

### `merge_vertices`

Merge near-coincident vertices using a tolerance in mesh units under the agreed mm convention. Inspect tiny gaps, thin features, topology and normals after welding. Recover from an overly aggressive merge by using the input revision.

Required fields — `stl_path`. Optional fields — `tolerance`.

### `counterpart_make_3mf`

Combine explicitly positioned STL parts into a new multipart 3MF with declared colors/filaments. Inspect the returned project, relative placement, part count and filament assignments. Use a new output path.

Required fields — `parts`, `out_path`. Optional fields — none. Exercised on Windows by assembling two registered solids and reading back their placement, colors and filament IDs.

### `counterpart_part_meshes`

Extract printable parts/instances into a new folder under `out_dir`. Returns transformed mm STLs, stable IDs and available plate, color and size data. Read `skipped`. Exports alone cannot preserve support modifiers or painting edits.

Required fields — `three_mf_path`, `out_dir`. Optional fields — none. Exercised on Windows with repeated instances, nested transforms and inch-to-mm conversion.

## Templates, slicing and plate evidence

The Studio CLI and compatible profiles are required to slice. Ordinary offline file inspection needs no printer or credentials. File inspection never grants physical start approval.

### `list_templates`

Enumerate the local template registry and available names. Resolve the intended template before slicing. An empty list is an opportunity to use installed presets.

Required fields — none. Optional fields — `template_dir`.

### `save_template`

Register a copied project or profile under a local template name. This writes reusable state. Verify the source, resulting name, machine and material before making it a default.

Required fields — `source_path`. Optional fields — `template_name`, `template_dir`.

### `get_slice_settings`

Read saved project/profile settings and, where provided, preview process overrides. Check the reported treatment of the project's own process. Use a real slice to verify effective settings in toolpaths.

Required fields — none. Optional fields — `source_path`, `template_name`, `template_dir`, `slicer_profile`, `template_3mf_path`, `layer_height`, `nozzle_diameter`, `wall_loops`, `sparse_infill_density`, `enable_support`, `support_type`, `quality`, `strength`.

### `list_3mf_plates`

Read plate names, zero-based indexes, instances, part/filament assignments and optional thumbnails. Compare plate contents by identity before and after re-export. Inspect the new output again when a single plate is renumbered.

Required fields — `three_mf_path`. Optional fields — `include_thumbnails`. Exercised on the Windows reference setup.

### `list_3mf_plate_objects`

Read sliced objects on the selected zero-based plate including the identifiers used by object skipping and available bounds. Distinguish copy/skip IDs from project object IDs. An empty list may reflect missing slice labels.

Required fields — `three_mf_path`. Optional fields — `plate_index`. Exercised on the Windows reference setup.

### `slice_stl`

Invoke the configured slicer for an STL or 3MF and return the output path. Give the exact machine and nozzle profile. Single plate selection is one-based. Zero slices all. Material selection, orientation, process overrides and support choices affect the result. Copy it immediately, then inspect the saved plate.

Required fields — `stl_path`, `bambu_model`. Optional fields — `manual_filament_changes`, `slicer_type`, `slicer_path`, `slicer_profile`, `template_3mf_path`, `template_name`, `template_dir`, `nozzle_diameter`, `bed_type`, `nozzle_type`, `nozzle_volume_type`, `use_printer_filaments`, `uptodate`, `repetitions`, `orient`, `arrange`, `ensure_on_bed`, `clone_objects`, `skip_objects`, `load_filaments`, `filament_profile`, `load_filament_ids`, `filament_colours`, `enable_timelapse`, `allow_mix_temp`, `scale`, `rotate`, `rotate_x`, `rotate_y`, `min_save`, `skip_modified_gcodes`, `pause_at_layers`, `slice_plate`, `quality`, `strength`, `layer_height`, `wall_loops`, `sparse_infill_density`, `enable_support`, `support_type`, `support_threshold_angle`. Exercised on the Windows reference setup.

### `slice_with_template`

Resolve a named saved template and slice the specified model. Check machine and nozzle compatibility, relative geometry, template assignments and which overrides the live schema accepts. Preserve the output while the server runs.

Required fields — `stl_path`, `template_name`, `bambu_model`. Optional fields — `template_dir`, `slicer_type`, `slicer_path`, `slicer_profile`, `nozzle_diameter`, `bed_type`, `nozzle_type`, `nozzle_volume_type`, `use_printer_filaments`, `host`, `bambu_serial`, `bambu_token`, `load_filaments`, `load_filament_ids`, `filament_colours`, `ensure_on_bed`, `arrange`, `orient`, `repetitions`, `scale`, `rotate`, `rotate_x`, `rotate_y`, `min_save`, `skip_modified_gcodes`, `pause_at_layers`, `slice_plate`.

### `inspect_print_file`

Read an exact private snapshot and return a versioned file-only receipt. Supply the actual model and zero-based plate index, optionally both nozzle diameters, bed and a preview. Check SHA-256, target, internal plate G-code, materials, settings and estimates. A rejection blocks review of that job until fixed.

Required fields — `file_path`, `bambu_model`. Optional fields — `plate_index`, `nozzle_diameters`, `bed_type`, `include_preview`. Exercised on the Windows reference setup.

### `design_guidance`

Read an upstream design topic on demand. Use fit, flexure, assembly, multicolor or after-slice guidance according to the user's task. Treat suggested dimensions as hypotheses and verify them against the part and setup.

Required fields — `name`. Optional fields — none.

## Server setup and optional design engines

The normal Windows workflow uses the direct FreeCAD, Blender and Studio servers. Discovering an optional tool does not install its backend. Setup/update calls can download software or change application files.

### `counterpart_printer_info`

Read server identity, configured printer/model and broad capabilities. This does not contact the printer. A print capability flag by itself cannot establish a functioning X2D Windows transport.

Required fields — none. Optional fields — `bambu_model`, `host`, `bambu_serial`, `bambu_token`. Exercised on the Windows reference setup.

### `counterpart_self_check`

Check the runtime dependencies and the installed bambu-node patch. A pass identifies a usable server runtime. Separately verify profiles and an offline slice.

Takes an empty argument object. Exercised on the Windows reference setup.

### `counterpart_setup_fields`

List the configuration fields and slicer/profile discovery information for this installation. Use it to diagnose an executable or profile path. Keep local configuration out of published examples.

Required fields — none. Optional fields — `serial`.

### `counterpart_diagnostics`

Collect bounded diagnostic files about configuration, versions and recent errors. Review for local identifiers and sensitive project information before sharing externally. No printer readiness claim follows from logs.

Required fields — none. Optional fields — `printer`, `max_bytes`.

### `counterpart_discover_printers`

Listen on the local network for announced printers and return candidate identities. Use when discovery is requested. Pick the intended device explicitly. An announcement alone does not prove pairing or job readiness.

Required fields — none. Optional fields — `duration_ms`.

### `counterpart_print_route`

Omit `route` to read active routes and availability. Providing `route` changes routing and can persist settings locally. Inspect options before any requested change. Windows X2D handoff stays in Studio for this release.

Required fields — none. Optional fields — `route`.

### `cad_status`

Read availability/version of the optional confined code-CAD engine. The pinned release implements confinement on supported macOS/Linux systems. Use the installed FreeCAD MCP on Windows.

Takes an empty argument object.

### `cad_setup`

Inspect optional code-CAD prerequisites. `install=true` attempts to provision the separate engine. Windows lacks its required confinement. A setup failure leaves the normal FreeCAD/Blender workflow available.

Required fields — none. Optional fields — `install`.

### `cad_examples`

List optional engine design examples or retrieve an individual recipe. Validate any adopted dimensions and assumptions. Reading an example does not execute a model or establish clearance.

Required fields — none. Optional fields — `name`.

### `cad_run`

On a supported confined host, run a parameterized build123d or mesh job using one supplied script/source path and a permitted output directory. Returns revision paths and validation data. Inspect geometry and physical dimensions separately. Use FreeCAD for this workflow on Windows.

Required fields — `output_dir`, `name`. Optional fields — `inputs`, `mode`, `script`, `script_path`, `parameters`, `role`, `final`, `timeout_ms`.

### `cad_check_fit`

On a supported engine host, compare two allowed, watertight mm meshes at an explicit reference transform and requested clearance. Inspect contacts, distances and assumptions. Use FreeCAD intersections/distances or Blender measurements on Windows.

Required fields — `model`, `reference`. Optional fields — `transform`, `clearance_mm`, `timeout_ms`.

### `blender_mcp_status`

Inspect the Bambu server's optional Blender bridge configuration. `connect=true` additionally discovers its remote tools. A successful direct Blender connection is a separate path. Use the direct registered server by default.

Required fields — none. Optional fields — `connect`, `timeout_ms`.

### `blender_mcp_call`

Forward a named tool and arguments through a configured Blender bridge. Effects and result follow the underlying method, including scene mutations. Discover that schema first and inspect the scene before retrying any edit.

Required fields — `tool_name`. Optional fields — `arguments`, `timeout_ms`.

### `blender_mcp_edit_model`

Import, edit and export an STL through the optional bridge using its supported operations. Requires shared files and an Object Mode Blender scene. Verify the reported export and its actual bounds, topology and bore/slot sizes.

Required fields — `stl_path`, `operations`. Optional fields — `output_path`, `user_prompt`, `timeout_ms`, `bridge_command`, `execute`.

### `blender_mcp_setup`

Read bridge/add-on setup status. `update=true` can change installed files. Use version-matched local components. Check for unsaved scene work before reloading an add-on.

Required fields — none. Optional fields — `update`.

### `fusion_mcp_status`

Probe the separately configured Autodesk Fusion bridge. Launching is an optional side effect. Returns readiness for that application. It is outside the three-app installation.

Required fields — none. Optional fields — `launch`, `timeout_ms`.

### `fusion_mcp_setup`

Inspect or provision the optional macOS Fusion add-in/bridge. `install=true` changes the separate setup. No Fusion dependency is needed to use this skill on Windows.

Required fields — none. Optional fields — `install`.

### `fusion_mcp_call`

Forward a discovered Fusion method and arguments, with document binding where supported. Results and mutations depend on that method. Verify document identity and inspect state after an interrupted edit.

Required fields — `tool_name`. Optional fields — `document_id`, `arguments`, `timeout_ms`.

### `fusion_mcp_new_design`

Create a Fusion design, optionally using a source F3D and document binding. This changes the active Fusion document. Separate prerequisites apply. Use an FCStd revision for a native Windows FreeCAD task.

Required fields — none. Optional fields — `bind_document`, `source_f3d`, `timeout_ms`.

### `fusion_mcp_export`

Export a bound Fusion design/body to the chosen directory, including available STL, F3D and parameter data. Verify selection and units. An unavailable bridge is not a reason to install another CAD system.

Required fields — `output_dir`, `name`. Optional fields — `document_id`, `body_name`, `timeout_ms`.

## Printer and filament observations

Requires an authorized, configured and reachable device for live observations. The model name, static profile or cached slot color alone cannot establish what is loaded. Use Studio or the operator when the device connection is unavailable.

### `get_printer_status`

Read the configured device's current reported state. Match its identity and job, inspect freshness and active errors. An offline or stale reply leaves the physical state unknown.

Required fields — none. Optional fields — `host`, `bambu_serial`, `bambu_token`.

### `get_printer_filaments`

Read loaded AMS/external spool inventory, IDs and any profile matches/confidence. Verify an uncertain match in Studio. An empty slot differs from an unavailable reading.

Required fields — none. Optional fields — `host`, `bambu_serial`, `bambu_token`, `bambu_model`, `nozzle_diameter`.

### `resolve_3mf_ams_slots`

Compare the selected sliced plate's material requirements against live AMS trays and return proposed mappings. This is a lookup. Confirm material, color, nozzle and physical tray before the final review.

Required fields — `three_mf_path`. Optional fields — `plate_index`, `bambu_model`, `nozzle_diameter`, `host`, `bambu_serial`, `bambu_token`.

### `counterpart_propose_filaments`

Compare requested colors/materials with the live AMS inventory, including user choices or painted inputs. Inspect ambiguities and possible manual changes. Return a proposed map for review.

Required fields — `filaments`. Optional fields — `painted`, `chosen`, `sliced`, `bambu_model`, `nozzle_diameter`, `host`, `bambu_serial`, `bambu_token`.

### `counterpart_print_progress`

Read the current reported job, time remaining, stage, temperatures and problems using cached/fresh reports. Verify job identity. FINISH describes firmware execution. A fitted part still needs inspection.

Required fields — none. Optional fields — `bambu_model`, `host`, `bambu_serial`, `bambu_token`.

### `counterpart_print_record`

Read persistent records for specific observed jobs/artifacts and any saved frames. Match job and artifact IDs. Missing history is unknown. A Studio-launched job may lack this server's dispatch record.

Required fields — none. Optional fields — `view`, `frame_format`, `frame_ids`, `list_jobs`, `job_id`, `include_frames`, `measurements`, `host`, `bambu_serial`.

### `counterpart_print_assess`

Store a client visual observation against an existing job, artifact, frame and image hash. Writes evidence locally. Label visibility and uncertainty honestly. An observation does not control the printer or prove finished geometry.

Required fields — `job_id`, `artifact_sha256`, `frame_id`, `image_sha256`, `visibility`, `footprint_visible`, `deposition`, `attempted`. Optional fields — `reference_frame_id`, `reference_visibility`, `reference_empty`, `host`, `bambu_serial`.

### `camera_snapshot`

Acquire one JPEG, optionally write it to a local path. X2D requires the RTSP route and available ffmpeg plus camera access. Check timestamp and visibility. Report a blocked view as unknown.

Required fields — none. Optional fields — `save_path`, `timeout_ms`, `bambu_model`, `experimental`, `ffmpeg_path`, `host`, `bambu_serial`, `bambu_token`.

### `camera_stream_start`

Start or renew an optional shared camera session for an active viewer. Configure frame rate and idle timeout to suit actual review. It uses a device connection.

Required fields — none. Optional fields — `host`, `bambu_serial`, `bambu_token`, `bambu_model`, `fps`, `idle_timeout_ms`.

### `camera_frame`

Read a new/changed frame using a sequence marker and bounded wait. An unchanged frame or timeout is not evidence of a print fault. Retain the last valid frame and its observation time.

Required fields — none. Optional fields — `host`, `bambu_serial`, `bambu_token`, `since_seq`, `wait_ms`, `max_width`, `max_bytes`, `changed_only`, `min_change`.

### `camera_stream_stop`

Close the shared camera connection and release cached frames. Consider other active viewers. The normal idle timeout can close an unused stream.

Required fields — none. Optional fields — `host`, `bambu_serial`, `bambu_token`.

## Printer files and launch routes

These tools advertise transfer, submission or control for multiple Bambu models. Windows X2D direct native dispatch and legacy remote-file/FTPS starts are unsupported in the pinned release. For this printer use the reviewed Studio workflow. No alternate server name, raw call or model substitution changes that fact.

### `list_printer_files`

Enumerate files on supported printer storage. Requires a compatible file transport. X2D storage is not a generic legacy SD/FTPS target. A missing listing does not mean the device is empty.

Required fields — none. Optional fields — `host`, `bambu_serial`, `bambu_token`.

### `delete_printer_file`

Delete an eligible remote storage file via supported FTPS with explicit confirmation. Check exact path, device and user intent. Never use deletion to repair missing local geometry.

Required fields — `filename`. Optional fields — `confirm`, `host`, `bambu_serial`, `bambu_token`.

### `upload_gcode`

Inspect a provided local G-code file/text and transfer a unique checked copy over a supported route. Check upload outcome independently of job start. This is not a Windows X2D dispatch mechanism.

Required fields — `filename`. Optional fields — `gcode`, `gcode_path`, `bambu_model`, `host`, `bambu_serial`, `bambu_token`.

### `upload_file`

Upload a local file to compatible device storage. Its optional `print` switch can start hardware. Treat these effects separately and keep this route out of the Windows X2D handoff.

Required fields — `file_path`, `filename`. Optional fields — `print`, `connection_mode`, `bambu_model`, `project_name`, `preset_name`, `bed_type`, `plate_index`, `host`, `bambu_serial`, `bambu_token`.

### `start_print`

Alias for starting a compatible printer's previously stored checked G-code file. This is a physical start and is unsupported for legacy X2D remote-file routing.

Required fields — `filename`, `bambu_model`. Optional fields — `host`, `bambu_serial`, `bambu_token`.

### `start_print_job`

Start an eligible existing file on a supported printer. A path string alone cannot establish identity of its current bytes. Use Studio for the approved Windows X2D plate.

Required fields — `filename`, `bambu_model`. Optional fields — `host`, `bambu_serial`, `bambu_token`.

### `print_3mf`

Prepare/check and submit a 3MF through an available model-specific route. An unsliced input can trigger automatic slicing. X2D's optional native helper does not implement Windows dispatch. Preserve file review and let Studio send the exact plate.

Required fields — `three_mf_path`, `bambu_model`. Optional fields — `pause_at_layers`, `connection_mode`, `try_emmc_print`, `connection_type`, `bambu_network_method`, `dev_id`, `dev_ip`, `bridge_command`, `bambu_network_config_dir`, `country_code`, `user_info`, `bed_type`, `nozzle_type`, `nozzle_volume_type`, `host`, `bambu_serial`, `bambu_token`, `plate_index`, `slicer_type`, `slicer_path`, `use_ams`, `ams_mapping`, `ams_slots`, `auto_match_ams`, `bed_leveling`, `flow_calibration`, `vibration_calibration`, `timelapse`, `slicer_profile`, `template_3mf_path`, `template_name`, `template_dir`, `nozzle_diameter`, `nozzle_diameters`.

### `print_collar_charm`

Submit a specialized two-part charm job with a fixed black/white tray policy. This is a real start action for a narrow project and makes assumptions about the AMS. It has no role as a connectivity test or generic print command.

Required fields — `bambu_model`. Optional fields — `source_path`, `template_name`, `template_dir`, `host`, `bambu_serial`, `bambu_token`, `bed_type`, `bed_leveling`, `flow_calibration`, `vibration_calibration`, `timelapse`, `slicer_profile`, `nozzle_diameter`.

### `bambu_connect_import_file`

Pass a local file to the signed-in Bambu Connect app for operator review on the documented macOS handoff. Opening it does not start a job. The Windows skill stages the plate in Bambu Studio.

Required fields — `file_path`. Optional fields — `name`, `version`.

### `bambu_network_bridge_status`

Read configuration for the optional FULU/BambuNetwork bridge. `connect=true` can launch/initialize the optional runtime. Probe only a configured route when investigating that integration.

Required fields — none. Optional fields — `connect`, `bridge_command`, `bambu_network_config_dir`, `country_code`, `user_info`, `timeout_ms`.

### `bambu_network_call`

Forward a raw, supported method on a separately configured bridge. Its side effects depend on the method. Raw mutation routes are restricted upstream. Use the named file inspection and Studio handoff here.

Required fields — `method`. Optional fields — `payload`, `with_agent`, `bridge_command`, `bambu_network_config_dir`, `country_code`, `user_info`, `timeout_ms`.

### `print_3mf_bambu_network`

Submit a job via the optional FULU BambuNetwork transport on supported configurations. It can transfer data and start hardware. It is outside this Windows X2D release route.

Required fields — `three_mf_path`, `bambu_model`. Optional fields — `connection_type`, `bambu_network_method`, `dev_id`, `dev_ip`, `host`, `bambu_serial`, `bambu_token`, `username`, `password`, `bed_type`, `nozzle_type`, `nozzle_volume_type`, `plate_index`, `project_name`, `preset_name`, `task_name`, `config_filename`, `bridge_command`, `bambu_network_config_dir`, `country_code`, `user_info`, `timeout_ms`, `slicer_type`, `slicer_path`, `slicer_profile`, `nozzle_diameter`, `nozzle_diameters`, `use_ams`, `ams_mapping`, `ams_slots`, `ams_mapping_bridge`, `ams_mapping2`, `ams_mapping_info`, `nozzle_mapping`, `nozzles_info`, `bed_leveling`, `flow_calibration`, `vibration_calibration`, `layer_inspect`, `timelapse`, `use_ssl_for_ftp`, `use_ssl_for_mqtt`, `external_change_assist`, `try_emmc_print`, `extra_options`, `client_job_id`.

## Live controls

All entries in this group concern device operations. They require an explicit task for the actual device, suitable hardware/firmware and a supported transport. No live command in this group was exercised during release testing. After a timeout read the device state before retrying. Prefer Studio's supported controls for the Windows X2D.

### `cancel_print`

Request cancellation of the current job. Identify the actual job and effect first. Cancellation can discard the current print. Verify the new firmware state.

Required fields — none. Optional fields — `host`, `bambu_serial`, `bambu_token`, `connection_mode`, `connection_type`.

### `pause_print`

Request a pause on the identified job. Check it reaches the paused state and record which job was paused. A missing reply is not permission to issue another command.

Required fields — none. Optional fields — `host`, `bambu_serial`, `bambu_token`, `connection_mode`, `connection_type`.

### `resume_print`

Resume a previously checked, eligible paused job on supported routes. Verify same job, artifact, setup and reason for the pause. A Studio-started job may not satisfy this helper's provenance checks.

Required fields — none. Optional fields — `host`, `bambu_serial`, `bambu_token`, `connection_mode`, `connection_type`.

### `x2d_native_control`

Read permitted calibration data or change supported AMS metadata through the native X2D plugin where available. Its restricted message vocabulary is not a general printer interface. The native path is unavailable on Windows.

Required fields — `message_json`. Optional fields — `qos`, `flag`, `host`, `bambu_serial`, `bambu_token`.

### `clear_hms_errors`

Request clearing supported printer error state. Read the original HMS condition and confirm its cause has been addressed. Clearing an indicator does not repair the physical issue.

Required fields — none. Optional fields — `host`, `bambu_serial`, `bambu_token`.

### `set_print_speed`

Change live print speed mode on compatible firmware. Record prior/requested mode and observe the response. Recheck print quality if the operator changes the speed.

Required fields — `mode`. Optional fields — `host`, `bambu_serial`, `bambu_token`.

### `set_airduct_mode`

Select the supported H2/P2 duct mode. Check the named model before using this interface.

Required fields — `mode`. Optional fields — `host`, `bambu_serial`, `bambu_token`.

### `reread_ams_rfid`

Ask the supported AMS unit and slot to reread its RFID. It can move filament. Verify the slot and resulting inventory. The X2D native route is platform dependent.

Required fields — `ams_id`, `slot_id`. Optional fields — `host`, `bambu_serial`, `bambu_token`.

### `set_temperature`

Request a checked heater target in degrees Celsius on a supported device. Positive targets require fresh compatible telemetry and nozzle material where applicable. A heater action is separate from preparing a sliced plate.

Required fields — `component`, `temperature`. Optional fields — `bambu_model`, `material`, `nozzle_diameter`, `host`, `bambu_serial`, `bambu_token`.

### `set_fan_speed`

Change the selected fan speed as a percentage where supported. The X2D native path and in-print confirmations are transport dependent. Verify physical state on the device.

Required fields — `fan`, `speed`. Optional fields — `confirm_during_print`, `host`, `bambu_serial`, `bambu_token`.

### `set_light`

Change a supported named light and mode. This is a device write, sometimes useful for requested visual inspection. Read back the observed result where available.

Required fields — `light`, `mode`. Optional fields — `host`, `bambu_serial`, `bambu_token`.

### `skip_objects`

Exclude specified IDs during a running compatible multi-object plate. Identify each printed copy via the sliced plate inventory. Skipping can permanently change what the current job produces.

Required fields — `object_ids`. Optional fields — `host`, `bambu_serial`, `bambu_token`.

### `set_ams_drying`

Start or stop drying on the selected supported AMS unit. Check unit identity, filament and current use. Operation can run heaters. This is outside ordinary slicing or job approval.

Required fields — `action`, `ams_id`. Optional fields — `host`, `bambu_serial`, `bambu_token`.

Version-pinned behavior. [Repository](https://github.com/DMontgomery40/bambu-printer-mcp) · [Slicing and model restrictions](https://github.com/DMontgomery40/bambu-printer-mcp/blob/v1.1.98/docs/SLICING.md) · [Optional code CAD](https://github.com/DMontgomery40/bambu-printer-mcp/blob/v1.1.98/docs/CAD.md)
