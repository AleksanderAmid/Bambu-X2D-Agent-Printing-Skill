# FreeCAD MCP tools

Applies to freecad-mcp 0.1.32. Default server name is `freecad`. The live GUI tools require the version-matched workbench RPC listener. Length geometry uses mm. Rotation in object-property input/output uses degrees in this protocol. For unambiguous feature values use a typed quantity. Internal names, including document names, can differ from display labels. For numeric work set `include_screenshot=false` where offered.

All entries were discovered on Windows. Entries marked **Exercised** also have a local execution result. For other entries the installed schema and upstream implementation describe the expected behavior.

## Discover and inspect

Read the live document and choose a target before mutation. Optional screenshots can reframe the view. An unavailable document is an error. Rediscover the open documents.

### `get_rpc_status`

Read listener, GUI dispatch, job activity and add-on/protocol status. Check `gui_dispatch` before a GUI call. After a timeout this can still answer even when the GUI is blocked.

Takes an empty argument object. Exercised on the Windows reference setup.

### `list_documents`

Get the open internal document names. Use this to select the owner of an object and avoid editing an unrelated active window. If the intended file is absent, open its revision explicitly.

Takes an empty argument object.

### `get_objects`

Enumerate objects in the named document to identify final bodies, operands and helpers. Use returned internal names when fetching details. Large documents benefit from text-only feedback.

Required fields — `doc_name`. Optional fields — `include_screenshot`, `view_name`.

### `get_object`

Inspect one named object's properties, links and placement. Use it to compare before/after parameter values. Then measure the evaluated shape to verify geometric effect.

Required fields — `doc_name`, `obj_name`. Optional fields — `include_screenshot`, `view_name`.

### `get_view`

Return an image of a named view, optionally focused and sized in pixels. Choose front/side/top for feature placement or isometric for overall form. A blank or occluded frame calls for another view or geometric inspection.

Required fields — `view_name`. Optional fields — `width`, `height`, `focus_object`.

## Create and edit

These calls change the live FreeCAD document. Work on a named revision. On failure inspect the returned mutation outcome and the actual object tree. Preserve dependent objects and user edits.

### `create_document`

Create a document using the requested name. Read back the actual name before further calls, particularly if a similarly named tab already exists. Save explicitly to retain it.

Required fields — `name`. Optional fields — none.

### `create_object`

Create a registered FreeCAD type with named properties in a specific document. Use links or a separate script for constructions the typed tool cannot express. Check recompute status and the returned object name.

Required fields — `doc_name`, `obj_type`, `obj_name`. Optional fields — `analysis_name`, `obj_properties`, `include_screenshot`, `view_name`.

### `edit_object`

Change properties on the named existing object. Read the original type, unit and expression binding first. Verify downstream recompute, body validity and protected dimensions.

Required fields — `doc_name`, `obj_name`, `obj_properties`. Optional fields — `include_screenshot`, `view_name`.

### `delete_object`

Remove the specified object from the document. Trace dependencies and ensure the deletion is part of the requested edit. Reinspect downstream features or restore the last good revision on failure.

Required fields — `doc_name`, `obj_name`. Optional fields — `include_screenshot`, `view_name`.

### `reload_document`

Close and reopen a saved document after an external change. Protect unsaved GUI work first. A reopen failure can leave the old tab closed. Check the file and open-document list before retrying.

Required fields — `doc_name`. Optional fields — none.

## Python, execution and recovery

GUI scripts have application privileges and can partially mutate state before raising. A timeout can mean the code is still running. Capture the job or task ID and inspect the actual outcome.

### `execute_code`

Execute a Python block on the FreeCAD GUI thread and return printed output, optional image and status. Use for modeling, explicit file I/O, selected exports and numeric checks. Include recompute and verification, and use document transactions for grouped edits.

Required fields — `code`. Optional fields — `include_screenshot`, `view_name`, `timeout`. Exercised on the Windows reference setup.

### `execute_code_async`

Submit long independent computations to a background job. Return its job ID immediately. Use the supported `commit()` mechanism for document/GUI access. Poll the existing job after disconnects.

Required fields — `code`. Optional fields — none.

### `get_async_status`

Read state, result or traceback for the async job ID. Omit the ID for known job history. Inspect partial work after failure before starting another computation.

Required fields — none. Optional fields — `job_id`.

### `get_task_status`

Read a GUI operation's retained outcome by task ID, including after admission or execution timeouts. Omission lists recent work. A running task can still change geometry. An evicted record leaves the outcome unknown.

Required fields — none. Optional fields — `task_id`.

### `execute_code_headless`

Run Python in a separate FreeCADCmd process, with timeout in seconds. Use absolute paths and scratch documents for crash-prone solid operations. Return process output/exit status. Reopen and measure the resulting file before replacing a working revision.

Required fields — `code`. Optional fields — `timeout`.

## Library and analysis

These functions have additional prerequisites. A missing parts library or CalculiX installation does not block ordinary CAD work.

### `get_parts_list`

List relative library entries from the installed FreeCAD parts library. Verify the exact entry and its revision before inserting a standard component.

Takes an empty argument object.

### `insert_part_from_library`

Insert a selected library-relative part into the active document. Check the active target, resulting placement, scale and asset license. Use measured interface dimensions for fit.

Required fields — `relative_path`. Optional fields — `include_screenshot`, `view_name`.

### `run_fem_analysis`

Run CalculiX for the named existing analysis. Requires a suitable mesh, material, constraints, loads and solver. Returns extrema, node count, applied load summary and result objects. Check force units, axes and fixtures. A solve changes analysis results. An isotropic simulation alone cannot certify the strength of a layered print.

Required fields — `doc_name`, `analysis_name`. Optional fields — `timeout`, `include_screenshot`, `view_name`.

Upstream implementation and failure semantics. [Tools](https://github.com/neka-nat/freecad-mcp/blob/246f608d5de49089aadc41d2d91cfce2ad8a44cd/docs/tools.md) · [Execution](https://github.com/neka-nat/freecad-mcp/blob/246f608d5de49089aadc41d2d91cfce2ad8a44cd/docs/execution.md)
