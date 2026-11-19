"""Check the three locally configured stdio MCP inventories. Never calls a modeling or printer tool."""
import argparse
import asyncio
from difflib import unified_diff
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "skills/bambu-x2d-printing/references"
BASELINE = Path(__file__).with_name("catalog-baseline.json")
GUIDES = {"freecad": "freecad-tools.md", "blender": "blender-tools.md", "bambu-studio": "bambu-tools.md"}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def resource_key(uri):
    # Printer authorities can contain a real hostname. Only publish the URI pattern.
    return re.sub(r"^printer://[^/]+/", "printer://{printer}/", str(uri))


def signature(tool):
    payload = tool.model_dump(mode="json", by_alias=True, exclude_none=True)
    # Hash interface facts and instructions. Avoid volatile server metadata and secret-bearing logs.
    fields = ("description", "inputSchema", "outputSchema", "annotations")
    return hashlib.sha256(canonical({k: payload[k] for k in fields if k in payload}).encode()).hexdigest()


def documentation_errors(catalog):
    errors = []
    hosts = (REFERENCE / "hosts.md").read_text(encoding="utf-8")
    for server, doc in GUIDES.items():
        headings = re.findall(r"^### `([a-z0-9_]+)`$", (REFERENCE / doc).read_text(encoding="utf-8"), re.M)
        found, expected = set(headings), set(catalog[server]["tools"])
        if len(found) != len(headings):
            errors.append(f"{doc}: duplicate entries")
        if found != expected:
            errors.append(f"{doc}: missing {sorted(expected-found)}, extra {sorted(found-expected)}")
        for kind in ("prompts", "resources", "templates"):
            for name in catalog[server][kind]:
                if f"`{name}`" not in hosts:
                    errors.append(f"hosts.md: missing {server} {kind} entry {name}")
    return errors


async def list_server(entry):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import get_default_environment, stdio_client
    from mcp.shared.exceptions import McpError
    if not entry.get("enabled", True) or "command" not in entry:
        raise ValueError("Expected an enabled, local stdio server")
    env = get_default_environment()
    for key in ("APPDATA", "LOCALAPPDATA", "USERPROFILE", "HOME", "TEMP", "TMP"):
        if key in os.environ:
            env[key] = os.environ[key]
    for spec in entry.get("env_vars", []):
        key = spec if isinstance(spec, str) else spec["name"]
        if key in os.environ:
            env[key] = os.environ[key]
    env.update(entry.get("env", {}))
    params = StdioServerParameters(command=entry["command"], args=entry.get("args", []), env=env, cwd=entry.get("cwd"))
    methods = {"tools": ("list_tools", "tools"), "prompts": ("list_prompts", "prompts"),
               "resources": ("list_resources", "resources"), "templates": ("list_resource_templates", "resourceTemplates")}
    result = {"tools": {}, "prompts": [], "resources": [], "templates": []}
    with open(os.devnull, "w") as stderr:
        async with stdio_client(params, errlog=stderr) as (read, write), ClientSession(read, write) as session:
            info = await session.initialize()
            for kind, (method, field) in methods.items():
                cap = "resources" if kind == "templates" else kind
                if getattr(info.capabilities, cap, None) is None:
                    continue
                cursor = None
                while True:
                    try:
                        page = await getattr(session, method)(cursor=cursor)
                    except McpError as exc:
                        if kind == "templates" and exc.error.code == -32601:
                            break
                        raise
                    for item in getattr(page, field):
                        if kind == "tools":
                            result[kind][item.name] = signature(item)
                        elif kind == "prompts":
                            result[kind].append(item.name)
                        else:
                            result[kind].append(resource_key(item.uri if kind == "resources" else item.uriTemplate))
                    cursor = page.nextCursor
                    if not cursor:
                        break
    for key in ("prompts", "resources", "templates"):
        result[key] = sorted(set(result[key]))
    return result


async def discover(args):
    with args.config.open("rb") as config:
        entries = tomllib.load(config)["mcp_servers"]
    names = [args.freecad, args.blender, args.bambu]
    for name in names:
        if name not in entries:
            raise ValueError(f"Missing local MCP registration: {name}")
    results = await asyncio.wait_for(asyncio.gather(*(list_server(entries[n]) for n in names)), timeout=90)
    return dict(zip(GUIDES, results))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(os.getenv("CODEX_HOME", Path.home()/".codex"))/"config.toml")
    parser.add_argument("--freecad", default="freecad")
    parser.add_argument("--blender", default="blender")
    parser.add_argument("--bambu", default="bambu-studio")
    parser.add_argument("--snapshot", action="store_true", help="Print current fingerprints for a reviewed baseline update")
    parser.add_argument("--offline", action="store_true", help="Compare checked-in entries to documentation without servers")
    args = parser.parse_args()
    try:
        if args.snapshot and args.offline:
            parser.error("--snapshot needs live discovery")
        baseline = None if args.snapshot else json.loads(BASELINE.read_text(encoding="utf-8-sig"))
        live = baseline if args.offline else asyncio.run(discover(args))
        if args.snapshot:
            print(json.dumps(live, sort_keys=True, indent=2))
            return
        errs = documentation_errors(baseline)
        if live != baseline:
            old, new = (json.dumps(c, sort_keys=True, indent=2).splitlines() for c in (baseline, live))
            errs.extend(unified_diff(old, new, "documented", "installed", lineterm=""))
        if errs:
            parser.exit(1, "\n".join(errs) + "\n")
        print("Catalog matches:", ", ".join(f"{k} {len(v['tools'])}" for k, v in live.items()))
    except (OSError, KeyError, ValueError, TimeoutError, ImportError, ExceptionGroup) as exc:
        print(f"Catalog check failed ({type(exc).__name__}). Check local stdio configuration, dependencies and server health.", file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
