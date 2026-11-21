# Single-image 3D estimates with TRELLIS.2

Use this route when the user wants a 3D interpretation of one local photograph, render or concept image. A clean silhouette around one subject gives the model more information. The shape behind the subject and its physical size are inferred. Keep dimensioned drawings, mating interfaces and existing CAD on the [measured modeling route](solid-modeling.md).

Microsoft's four-billion-parameter TRELLIS.2 model can generate geometry and materials from a single image. Its reference implementation uses Linux and an NVIDIA GPU with at least 24 GB. This Windows backend runs the shape stages of the model through the community trellis.cpp Vulkan port. It uses converted weights, DINOv3 image conditioning and BiRefNet for opaque backgrounds. Generation runs locally after setup. [Microsoft implementation](https://github.com/microsoft/TRELLIS.2) · [Model card](https://huggingface.co/microsoft/TRELLIS.2-4B) · [Pinned port](https://github.com/pwilkin/trellis.cpp/tree/v0.8.1) · [Weight files and upstream terms](https://huggingface.co/ilintar/trellis2-gguf/tree/a57397bd3d351599d9729fc144b3f87c3f87d65b)

## Install once

Use Windows x64, a Vulkan-capable GPU and driver, uv, Python 3.12 and the Windows curl executable. Allow about 11 GB for the engine and both geometry resolutions, plus space for Python packages and jobs. From the skill directory (the directory containing `SKILL.md`) run the following PowerShell commands. They also work from a standalone copy of the skill.

```powershell
uv tool install --python 3.12 ./scripts/trellis2
$trellis = Join-Path (uv tool dir --bin) 'x2d-trellis.exe'
& $trellis install
& $trellis doctor
codex mcp add trellis2 --env "LOCALAPPDATA=$env:LOCALAPPDATA" -- $trellis mcp
```

`install` downloads the pinned runtime and weights into the user's local app-data directory and checks SHA-256 before publishing each file. Rerun it to resume a partial download or check the installed weights. The Git package contains the [command and MCP source](../scripts/trellis2/). The runtime, TRELLIS.2 weights and auxiliary models retain their upstream licenses. For an updated copy of this wrapper, repeat the uv command with `--force --reinstall-package x2d-trellis`.

## Generate from Codex or the terminal

Discover the optional `trellis2` registration in a fresh Codex session. `trellis_status` checks the required files. `trellis_generate` takes an absolute `image_path`, a new absolute `job_dir`, and optional `resolution`, `seed` and `height_mm`. Use the tested 512 default for rough estimates. Reserve 1024 for a requested detail pass when the display GPU can be busy for longer. The default seed is 42. The call returns promptly. Poll `trellis_job(job_dir)` until it reports `complete`, `failed` or `interrupted`. After reconnecting or losing a reply, check that same directory. The status and job log show engine progress.

Keep the originating MCP session open until the run finishes. The Windows Python MCP client closes its process tree on disconnect, which can interrupt an active generation. A new session can read its recorded state and completed files.

The installed terminal command uses the same worker. The following example chooses a **100 mm preview height**. Omit `--height-mm` for a GLB at the model's native, uncalibrated scale. The terminal waits by default. Pass `--detach` and use `job` for longer runs.

```powershell
& $trellis generate '.\bust.png' '.\bust-draft' --resolution 512 --seed 42 --height-mm 100
& $trellis job '.\bust-draft'
```

For a decorative body whose sized STL has open or non-manifold edges, `trellis_wrap(source_job, job_dir)` creates a separate watertight revision on the CPU. Pass the completed generation directory and a new output directory, then poll `trellis_job` as above. The terminal equivalent is below. It reuses the saved mesh and checks the height and topology of the resulting STL. Wrapping can close openings, round details or retain an internal cavity. Compare against the GLB when those features matter. [Surface reconstruction method](https://fwilliams.info/point-cloud-utils/sections/watertight_manifold/)

```powershell
& $trellis wrap '.\bust-draft' '.\bust-watertight'
```

## Continue in the workshop

The worker requests trellis.cpp’s cleaned surface with `--dump-post`, simplifies it toward 150,000 triangles at 512 or 300,000 at 1024, and writes a geometry-only GLB. This keeps large estimates practical to edit. Surface cleanup can change small gaps and disconnected details. [Pinned surface exporter](https://github.com/pwilkin/trellis.cpp/blob/v0.8.1/src/trellis_cli.cpp)

- Open the returned GLB in Blender for sculpting. Inspect the silhouette, profile, back, underside and loose geometry. Save an editable BLEND revision before making changes. Rebuild fitted features from independent dimensions in FreeCAD.
- With `height_mm`, the worker also exports a Z-up STL with raw coordinates in millimetres, uniformly scales it to the chosen height and places its lowest point at Z = 0. It reopens the file and reports XYZ spans. Open that STL in Bambu Studio at 100% scale. The GLB retains the original scale.
- Read the triangle, body, boundary-edge, overused-edge and winding checks before treating the mesh as a printable body. These describe the saved geometry. A flat contact surface, wall thickness, overhangs and likeness still need inspection. Continue with [mesh repair](mesh-modeling.md) or the [X2D slicing workflow](slicing.md) according to the requested stage.
