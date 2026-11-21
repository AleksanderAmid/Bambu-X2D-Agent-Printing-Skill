import argparse
import json
import sys

from . import jobs, runtime


def main():
    parser = argparse.ArgumentParser(description="Local TRELLIS.2 reference meshes for Blender and Bambu Studio.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("install", help="Download and verify the Windows Vulkan engine and geometry weights.")
    commands.add_parser("doctor", help="Report missing or incomplete installed files.")
    commands.add_parser("mcp", help="Serve local generation tools over stdio.")
    generate = commands.add_parser("generate", help="Create a mesh from one local reference image.")
    generate.add_argument("image")
    generate.add_argument("job_dir", help="New directory for the reference, result, and log.")
    generate.add_argument("--resolution", type=int, choices=(512, 1024), default=512)
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--height-mm", type=float, help="Also export an STL at this chosen height.")
    generate.add_argument("--detach", action="store_true", help="Return after launch. Poll with job.")
    check = commands.add_parser("job", help="Read job state and output measurements.")
    check.add_argument("job_dir")
    wrap = commands.add_parser("wrap", help="Create a separate watertight STL from a completed sized estimate.")
    wrap.add_argument("source_job")
    wrap.add_argument("job_dir", help="New directory for this revision.")
    wrap.add_argument("--detach", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "mcp":
            from .server import server
            server.run(transport="stdio")
            return 0
        if args.command == "install":
            result = runtime.install()
        elif args.command == "doctor":
            result = runtime.status()
        elif args.command == "job":
            result = jobs.job_status(args.job_dir)
        elif args.command == "wrap":
            result = jobs.wrap(args.source_job, args.job_dir, wait=not args.detach)
        else:
            result = jobs.generate(args.image, args.job_dir, args.resolution, args.seed,
                                   args.height_mm, wait=not args.detach)
    except Exception as exc:
        result = {"state": "failed", "error": str(exc)}
    print(json.dumps(result, indent=2))
    return int(result.get("state") in {"failed", "interrupted"} or result.get("installed") is False)
