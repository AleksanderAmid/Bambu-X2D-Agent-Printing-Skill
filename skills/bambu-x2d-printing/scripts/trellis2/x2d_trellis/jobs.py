"""Run one local reconstruction per new directory and report its durable result."""

import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageOps
import psutil

from . import runtime


def write_json(path, data):
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    pending.replace(path)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def job_status(job_dir):
    folder = Path(job_dir).resolve()
    job = read_json(folder / "request.json")
    report = {"job_dir": str(folder), "log": str(folder / "run.log"), **job}
    result = folder / "result.json"
    if result.is_file():
        return {**report, **read_json(result)}
    worker_file = folder / "worker.json"
    if worker_file.is_file():
        worker = read_json(worker_file)
        try:
            if psutil.Process(worker["pid"]).create_time() == worker["created"]:
                log = folder / "run.log"
                if log.exists():
                    with log.open("rb") as stream:
                        end = stream.seek(0, io.SEEK_END)
                        stream.seek(max(0, end - 4096))
                        lines = stream.read(4096).decode("utf-8", errors="replace").strip().splitlines()
                    if lines:
                        report["progress"] = lines[-1].strip()[:400]
                return {**report, "state": worker.get("state", "running")}
        except psutil.NoSuchProcess:
            pass
        # The worker can publish the result between the first check and exiting.
        if result.is_file():
            return {**report, **read_json(result)}
        return {**report, "state": "interrupted", "error": "Worker exited before recording a result. Inspect run.log."}
    return {**report, "state": "interrupted", "error": "Missing worker record. Inspect the job directory."}


def generate(image_path, job_dir, resolution=512, seed=42, height_mm=None, *, wait=True):
    if resolution not in (512, 1024) or not 1 <= seed <= 2**31 - 1:
        raise ValueError("Use resolution 512 or 1024 and a seed between 1 and 2147483647.")
    if height_mm is not None and (not math.isfinite(height_mm) or height_mm <= 0):
        raise ValueError("height_mm must be a positive, finite number.")
    installed = runtime.status()
    if not installed["installed"]:
        raise ValueError("Run x2d-trellis install. Missing files: " + ", ".join(installed["missing_or_incomplete"]))
    image_path = Path(image_path).resolve(strict=True)
    folder = Path(job_dir).resolve()
    raw = image_path.read_bytes()
    with Image.open(io.BytesIO(raw)) as original:
        image = ImageOps.exif_transpose(original).convert("RGBA")
    alpha_min, alpha_max = image.getchannel("A").getextrema()
    if alpha_max == 0:
        raise ValueError("The image is fully transparent.")
    if alpha_min == 255:
        image = image.convert("RGB")
    request = {"model": installed["model"], "runtime": installed["runtime"],
               "weights_revision": installed["weights_revision"], "resolution": resolution,
               "seed": seed, "height_mm": height_mm, "source_name": image_path.name,
               "source_sha256": hashlib.sha256(raw).hexdigest(), "source_pixels": list(image.size)}
    return launch(folder, request, wait, image)


def wrap(source_job, job_dir, *, wait=True):
    parent = Path(source_job).resolve()
    record = job_status(parent)
    if record["state"] != "complete" or not record.get("glb") or not record.get("stl"):
        raise ValueError("Wrapping needs a completed generation with height_mm.")
    request = {"operation": "wrap", "source_job": str(parent), "height_mm": record["height_mm"],
               "resolution": record["resolution"], "source_sha256": runtime.sha256(parent / "estimate-mm.stl")}
    return launch(Path(job_dir).resolve(), request, wait)


def launch(folder, request, wait, image=None):
    try:
        folder.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        raise ValueError(f"Job path already exists. Check its status or choose a new directory: {folder}") from None
    submitter = psutil.Process()
    write_json(folder / "worker.json", {"pid": submitter.pid, "created": submitter.create_time(), "state": "starting"})
    write_json(folder / "request.json", request)
    try:
        if image is not None:
            image.save(folder / "reference.png")
        with (folder / "run.log").open("wb") as log:
            child = subprocess.Popen([sys.executable, "-m", "x2d_trellis.worker"],
                                     cwd=folder, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            created = psutil.Process(child.pid).create_time()
            write_json(folder / "worker.json", {"pid": child.pid, "created": created})
        except psutil.NoSuchProcess:
            if not (folder / "result.json").is_file():
                raise RuntimeError("Worker exited on startup. Inspect run.log.") from None
    except Exception as exc:
        write_json(folder / "result.json", {"state": "failed", "error": str(exc)})
        raise
    if wait:
        child.wait()
    return job_status(folder)
