# Windows hosts and MCP discovery

A skill supplies procedures. An MCP client separately starts the local servers and exposes their tools. Use a client with access to this Windows host and shared local files. Codex's desktop and CLI can share local configuration. In Claude Code configure the three stdio servers separately and install the same skill body in its skills directory. A plain cloud conversation does not acquire a local FreeCAD GUI, filesystem, or slicer when given a copy of these instructions. Check which tools the actual host exposes. [Codex MCP](https://developers.openai.com/codex/mcp/) · [Claude Code MCP](https://code.claude.com/docs/en/mcp) · [Claude Code skills](https://code.claude.com/docs/en/skills)

## Windows setup for a new workstation

Use the versions and repository pins in [research and tested versions](sources.md). Keep private server configuration outside the public skill source. The procedure below matches the three-application setup. Adjust paths to the actual installation. If a server is already configured, verify it before adding a duplicate.

### 1. Install the apps and development tools

The reference workstation used FreeCAD 1.1.4, Blender 5.3.0 and Bambu Studio 02.09.01.70. Open each app once. In Studio select the Bambu Lab X2D in the setup wizard and verify the 0.4 mm X2D machine, process and filament presets are available. [FreeCAD release](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.4) · [Blender 5.3 installers](https://download.blender.org/release/Blender5.3/) · [Bambu Studio release](https://github.com/bambulab/BambuStudio/releases/tag/v02.09.01.70)

Install Git for Windows, uv, Python 3.12, Node.js 24 with npm, and the Codex CLI for the Codex route. If Python 3.12 is missing, `uv python install 3.12` provides it for the server builds. Open a fresh PowerShell and confirm `git --version`, `uv --version`, `node --version`, `npm.cmd --version` and `codex --version` work. [Git](https://git-scm.com/downloads/win) · [uv](https://docs.astral.sh/uv/getting-started/installation/) · [Node.js](https://nodejs.org/en/download) · [Codex CLI](https://developers.openai.com/codex/cli/)

### 2. Build the three MCP servers

Run the following from the skill repository root. Keep using the same `$mcpRoot` in later commands. Pick another directory with `-InstallRoot` if desired. The [Windows installer](https://github.com/AleksanderAmid/Bambu-X2D-Agent-Printing-Skill/blob/main/tools/install-mcps.ps1) fetches each pinned upstream commit, runs `uv sync --locked --no-dev --python 3.12 --no-editable` for both Python servers, and runs `npm.cmd ci --include=dev` and `npm.cmd run build` for the Studio connector. It verifies all three entry points. A repeat run reuses matching clean checkouts. A different revision or local edits require a separate root.

```powershell
$mcpRoot = Join-Path $env:LOCALAPPDATA 'Bambu-X2D-MCP'
.\tools\install-mcps.ps1 -InstallRoot $mcpRoot
```

### 3. Enable the two application add-ons

In the FreeCAD Python console, run `App.getUserAppDataDir()`. Append `Mod` to that path and use the result as `$freecadMod` below. The example uses the tested 1.1 default. For Blender, the example targets the 5.3 user profile. Save open work before loading add-ons. These commands are for a first installation.

```powershell
$freecadMod = Join-Path $env:APPDATA 'FreeCAD\v1-1\Mod'
$workbench = Join-Path $freecadMod 'FreeCADMCP'
if (Test-Path -LiteralPath $workbench) { throw "Review the existing workbench before replacing it: $workbench" }
New-Item -ItemType Directory -Force -Path $freecadMod | Out-Null
Copy-Item -LiteralPath (Join-Path $mcpRoot 'freecad-mcp\addon\FreeCADMCP') -Destination $workbench -Recurse

$blenderAddons = Join-Path $env:APPDATA 'Blender Foundation\Blender\5.3\scripts\addons'
$env:PYTHONUTF8 = '1'
& (Join-Path $mcpRoot 'mcp-for-blender\.venv\Scripts\mcp-for-blender.exe') install-addon --addons-dir $blenderAddons
```

Restart FreeCAD, select the **MCP Addon** workbench, and start the RPC server. Enable Auto-Start if you want it on subsequent launches. Keep the listener on loopback. In Blender open **Edit → Preferences → Add-ons**, enable **MCP for Blender** and save preferences. If its listener is stopped, open the 3D Viewport sidebar with **N**, find **MCP for Blender**, and select **Connect to MCP server**. The upstream Blender installer can update an existing copy of the add-on in the selected directory.

### 4. Register the servers in Codex

Run once for a new Codex installation. Adjust the FreeCAD and Studio folders if the apps were installed elsewhere. Use the same PowerShell session as step 2 or set `$mcpRoot` again. If a name already exists, compare its configuration with the table below before making changes.

```powershell
$freecadServer = Join-Path $mcpRoot 'freecad-mcp\.venv\Scripts\freecad-mcp.exe'
$blenderServer = Join-Path $mcpRoot 'mcp-for-blender\.venv\Scripts\mcp-for-blender.exe'
$bambuServer = Join-Path $mcpRoot 'bambu-printer-mcp\dist\index.js'
$freecadCmd = Join-Path $env:ProgramFiles 'FreeCAD 1.1\bin\freecadcmd.exe'
$studioDir = Join-Path $env:ProgramFiles 'Bambu Studio'
$studioExe = Join-Path $studioDir 'bambu-studio.exe'
$studioProfiles = Join-Path $studioDir 'resources\profiles'
$nodeExe = (Get-Command node.exe -CommandType Application | Select-Object -First 1).Source

codex mcp add freecad -- $freecadServer --host 127.0.0.1 --freecadcmd $freecadCmd
codex mcp add blender --env BLENDER_HOST=127.0.0.1 --env PYTHONUTF8=1 --env DISABLE_TELEMETRY=true -- $blenderServer
codex mcp add bambu-studio --env BAMBU_MODEL=x2d --env SLICER_TYPE=bambustudio --env MCP_TRANSPORT=stdio --env "SLICER_PATH=$studioExe" --env "BAMBU_PROFILES_ROOT=$studioProfiles" -- $nodeExe $bambuServer
```

If you set an authentication token in the FreeCAD workbench, provide that same `FREECAD_MCP_TOKEN` privately to the server process. For example, set it in the environment that launches Codex and add `env_vars = ["FREECAD_MCP_TOKEN"]` to the existing `[mcp_servers.freecad]` section in your user Codex config. The offline Studio configuration above works without a printer address, serial number or LAN access code.

Copy the skill as shown in the [repository README](https://github.com/AleksanderAmid/Bambu-X2D-Agent-Printing-Skill#install-in-codex-on-windows), open a fresh Codex session and run `/mcp`. From the checkout, run both commands below using the Python environment just built. The first compares the installed interfaces with the release baseline. The second tests actual modeling and offline slicing. Save open work, keep FreeCAD open, and use Blender Object Mode for that check. The [verification report](https://github.com/AleksanderAmid/Bambu-X2D-Agent-Printing-Skill/blob/main/docs/validation.md) lists the expected results and the known two-color rejection.

```powershell
& (Join-Path $mcpRoot 'freecad-mcp\.venv\Scripts\python.exe') -B tools/catalog.py
& (Join-Path $mcpRoot 'freecad-mcp\.venv\Scripts\python.exe') -B tests/live_codex.py
```

For large slices increase that server's tool timeout in private client configuration as needed. On a timeout check for a running slicer before resubmitting.

### Server settings and Claude Code

| Registration | Executable and arguments | Local configuration |
|---|---|---|
| `freecad` | `<freecad-checkout>\.venv\Scripts\freecad-mcp.exe --host 127.0.0.1 --freecadcmd "<FreeCAD-bin>\freecadcmd.exe"` | Pass `FREECAD_MCP_TOKEN` privately when listener authentication is enabled. |
| `blender` | `<blender-checkout>\.venv\Scripts\mcp-for-blender.exe` | `BLENDER_HOST=127.0.0.1`, `PYTHONUTF8=1`, `DISABLE_TELEMETRY=true`. |
| `bambu-studio` | `<node.exe> "<bambu-checkout>\dist\index.js"` | `BAMBU_MODEL=x2d`, `SLICER_TYPE=bambustudio`, `MCP_TRANSPORT=stdio`, `SLICER_PATH=<bambu-studio.exe>`, `BAMBU_PROFILES_ROOT=<Studio>\resources\profiles`. |

For **Claude Code on Windows**, clone/copy the skill folder containing `SKILL.md` into `~/.claude/skills/bambu-x2d-printing` or the project's `.claude/skills/` directory. Use `claude mcp add --transport stdio --scope user [--env KEY=VALUE ...] NAME -- COMMAND ARG...` for each row with resolved paths. User scope keeps local settings out of project Git history. Use `claude mcp list` and `/mcp` to check connections. Invoke `/bambu-x2d-printing` in Claude Code. Product-specific web/Desktop MCP availability and permissions vary. This release tests Codex on Windows. [Claude's Windows stdio setup](https://code.claude.com/docs/en/mcp) · [Codex skills](https://developers.openai.com/codex/skills/)

## Health and optional capabilities

FreeCAD loopback normally listens on port 9875 and Blender on 9876. A listening socket proves only that a process bound a port. A healthy FreeCAD protocol handshake, a Blender scene read, and a real X2D local slice are stronger checks. A missing LAN access code blocks live printer observations, while offline slicing still works. A setup check or catalog entry is weaker evidence than exercising a real tool.

Use MCP discovery for `tools/list`, `prompts/list`, `resources/list` and `resources/templates/list` if exposed. Different clients can omit prompts or resources even when tools work. Keep the currently installed schema authoritative for names, required fields and units.

| Server | Item | Use |
|---|---|---|
| FreeCAD prompt | `asset_creation_strategy` | Upstream CAD asset planning. Apply relevant parts to the user's design. |
| Blender resource | `ui://mcp-for-blender/viewport-v2` | Client-rendered viewport companion where UI resources are supported. |
| Blender resource templates | `blender://object/{name}`, `blender://material/{name}`, `blender://collection/{name}` | Read the named scene element for targeted inspection. |
| Bambu prompts | `cad_design`, `fdm_design`, `fdm_slicing`, `fdm_after_slice` | Optional engine contract, design intent, slice planning and review. |
| Bambu prompts | `fdm_fit`, `fdm_flexures`, `fdm_assembly`, `fdm_multicolor` | Mating interfaces, bending features, joining/splitting, colors and material transitions. |
| Bambu resources | `guidance://fdm/capability-guidance`, `guidance://fdm/fit-by-function` | Read design recommendations on demand. Use `design_guidance` for supported topics when the host exposes only tools. |
| Bambu printer resources | `printer://{printer}/status`, `printer://{printer}/files`, `printer://{printer}/hms` | Live state, storage and machine messages. Discover the actual resource URI. Connection and model support apply to each resource. |

When upgrading, compare the maintained catalog with the live inventory and retest the cross-application handoff. For stdio server startup errors inspect the command, path quoting, versions and matching listener authentication. For a missing printer profile, resolve the local BBL preset tree before slicing. For a missing GUI, use the applicable headless or file-only path and label anything requiring visible review as pending.
