from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP

from . import jobs, runtime

server = FastMCP("trellis2")


@server.tool()
def trellis_status() -> dict:
    """Check local TRELLIS.2 runtime and model files. GPU execution is tested by generation."""
    return runtime.status()


@server.tool()
def trellis_generate(image_path: str, job_dir: str, resolution: Literal[512, 1024] = 512,
                     seed: int = 42, height_mm: float | None = None) -> dict:
    """Start a local image-to-GLB estimate. Use absolute paths and a new job directory.
    Optional height_mm also writes a Z-up STL. Poll trellis_job with the returned job_dir."""
    if not all(Path(path).is_absolute() for path in (image_path, job_dir)):
        raise ValueError("Supply absolute image_path and job_dir.")
    return jobs.generate(image_path, job_dir, resolution, seed, height_mm, wait=False)


@server.tool()
def trellis_job(job_dir: str) -> dict:
    """Read a job's state, log location and verified output paths, including after reconnecting."""
    if not Path(job_dir).is_absolute():
        raise ValueError("Supply the absolute job_dir returned by trellis_generate.")
    return jobs.job_status(job_dir)


@server.tool()
def trellis_wrap(source_job: str, job_dir: str) -> dict:
    """Start a watertight STL revision of a completed sized estimate. Wrapping can close openings.
    Use a new absolute job_dir. Poll trellis_job for the measured result."""
    if not all(Path(path).is_absolute() for path in (source_job, job_dir)):
        raise ValueError("Supply absolute source_job and job_dir paths.")
    return jobs.wrap(source_job, job_dir, wait=False)
