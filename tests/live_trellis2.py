"""Exercise the installed TRELLIS.2 stdio server with a caller-supplied image."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def call(session, tool, arguments):
    reply = await session.call_tool(tool, arguments)
    if reply.isError:
        raise RuntimeError(reply.content)
    return json.loads(reply.content[0].text)


async def run(args):
    params = StdioServerParameters(command=shutil.which("x2d-trellis") or "x2d-trellis",
                                   args=["mcp"], env={"LOCALAPPDATA": os.environ["LOCALAPPDATA"]})
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        names = {tool.name for tool in (await session.list_tools()).tools}
        assert {"trellis_status", "trellis_generate", "trellis_job", "trellis_wrap"} <= names, names

        status = await call(session, "trellis_status", {})
        print(json.dumps(status), flush=True)
        if not status["installed"]:
            raise RuntimeError("Run x2d-trellis install before the generation test.")
        folder = str(args.job_dir.resolve())
        job = await call(session, "trellis_generate", {"image_path": str(args.image.resolve()), "job_dir": folder,
                         "resolution": args.resolution, "seed": 42, "height_mm": args.height_mm})
        print(json.dumps(job), flush=True)
        while job["state"] in {"starting", "running"}:
            await asyncio.sleep(10)
            job = await call(session, "trellis_job", {"job_dir": folder})
    # The Windows SDK stops its process tree when the originating session
    # closes. Completed results must still be available to a fresh client.
    async with stdio_client(params) as (read, write), ClientSession(read, write) as fresh:
        await fresh.initialize()
        assert await call(fresh, "trellis_job", {"job_dir": folder}) == job
        if args.wrap_dir:
            wrapped_dir = str(args.wrap_dir.resolve())
            wrapped = await call(fresh, "trellis_wrap", {"source_job": folder, "job_dir": wrapped_dir})
            while wrapped["state"] in {"starting", "running"}:
                await asyncio.sleep(5)
                wrapped = await call(fresh, "trellis_job", {"job_dir": wrapped_dir})
            print(json.dumps(wrapped, indent=2))
            assert wrapped["state"] == "complete", wrapped
            assert wrapped["stl_mesh"]["watertight"] and wrapped["stl_mesh"]["consistent_winding"]
            assert Path(wrapped["stl"]).is_file() and abs(wrapped["stl_span_mm"][2] - args.height_mm) < 0.001
    print(json.dumps(job, indent=2))
    assert job["state"] == "complete", job
    assert Path(job["glb"]).is_file() and job["glb_mesh"]["triangles"] > 0
    assert Path(job["stl"]).is_file() and abs(job["stl_span_mm"][2] - args.height_mm) < 0.001


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("job_dir", type=Path)
    parser.add_argument("--resolution", type=int, choices=(512, 1024), default=512)
    parser.add_argument("--height-mm", type=float, default=100.0)
    parser.add_argument("--wrap-dir", type=Path, help="Also test wrapping a decorative body into this new directory.")
    asyncio.run(run(parser.parse_args()))
