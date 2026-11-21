"""Install the pinned Windows Vulkan CLI and the geometry pipeline weights."""

import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from zipfile import ZipFile

from filelock import FileLock

ENGINE = "v0.8.1"
REVISION = "a57397bd3d351599d9729fc144b3f87c3f87d65b"
ARCHIVE = "trellis-vulkan-windows-x64.zip"
RUNTIME_SHA = "d6c70678635f5367f9aa93261e9310e7c0c327ca8395399cf2ef869ccc2e72ba"
BINARIES = ("trellis-cli.exe", "ggml-base.dll", "ggml-cpu.dll", "ggml-vulkan.dll", "ggml.dll")
# Original-precision GGUFs, including the matte for opaque input. Byte lengths
# make preflight cheap. Installation checks the Hugging Face LFS SHA-256s.
WEIGHTS = {
    "birefnet.gguf": (882749024, "10c5dd4dcac904cf81c9a16180eb66f167dd52ab55867f54a44567b0b2babbc1"),
    "dinov3.gguf": (606773440, "b2e84087aebeb06440da4f5970413153f7f27f71ede7bab993e82accd839d936"),
    "ss_flow.gguf": (2586488480, "1dfbef1b80ddea422a6189ff9ac29a244c4482cfbaa01870a0c0ea76d3fb9ae6"),
    "ss_dec.gguf": (147379392, "2790b5eecb261cc877d9bf175ce2bd6dd48cd65be8c042c5f5bc023dfca01cf7"),
    "shape_flow_512.gguf": (2586636032, "fef397f3600e2fab327a98b3edd3cc8377e9741eef870f3ea3f40235875828fb"),
    "shape_dec.gguf": (948745344, "d3230b649031b55728da2d8818f092eab9ad6f1e72fd01f6cbff6bfada5d7d47"),
    "shape_flow_1024.gguf": (2586636032, "7d0e9903bf132a5d78f289eaa2fa4050bcd52c689716406cbf66b76cdfa4656c"),
}


def install_root():
    local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    return local / "Bambu-X2D-MCP" / "trellis2" / ENGINE


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fetch(url, path, digest):
    if path.is_file() and sha256(path) == digest:
        return
    partial = path.with_suffix(path.suffix + ".part")
    print(f"Downloading {path.name}", file=sys.stderr, flush=True)
    subprocess.run(["curl.exe", "--fail", "--location", "--silent", "--show-error",
                    "--retry", "3", "--connect-timeout", "30", "--speed-time", "120",
                    "--speed-limit", "1024", "--continue-at", "-", "--output", str(partial), url],
                   check=True)
    if sha256(partial) != digest:
        partial.unlink()
        raise ValueError(f"SHA-256 mismatch for {path.name}. Run install again.")
    partial.replace(path)


def status():
    root = install_root()
    missing = [name for name in BINARIES if not (root / "bin" / name).is_file()]
    for name, (size, _) in WEIGHTS.items():
        path = root / "models" / name
        if not path.is_file() or path.stat().st_size != size:
            missing.append(name)
    return {"installed": not missing, "runtime": f"trellis.cpp {ENGINE} Windows x64 Vulkan",
            "model": "microsoft/TRELLIS.2-4B", "weights_revision": REVISION,
            "install_dir": str(root), "missing_or_incomplete": missing}


def install():
    if sys.platform != "win32" or platform.machine().upper() not in {"AMD64", "X86_64"}:
        raise ValueError("This installer targets Windows x64 with a Vulkan-capable GPU.")
    root = install_root()
    models = root / "models"
    models.mkdir(parents=True, exist_ok=True)
    binaries = root / "bin"
    binaries.mkdir(exist_ok=True)
    with FileLock(root / "install.lock", timeout=1):
        bundle = root / ARCHIVE
        fetch(f"https://github.com/pwilkin/trellis.cpp/releases/download/{ENGINE}/{ARCHIVE}",
              bundle, RUNTIME_SHA)
        with ZipFile(bundle) as archive:
            for name in BINARIES:
                dest = binaries / name
                tmp = dest.with_suffix(".part")
                with archive.open(name) as src, tmp.open("wb") as out:
                    shutil.copyfileobj(src, out)
                if dest.is_file() and sha256(tmp) == sha256(dest):
                    tmp.unlink()
                else:
                    tmp.replace(dest)
        for name, (_, digest) in WEIGHTS.items():
            fetch(f"https://huggingface.co/ilintar/trellis2-gguf/resolve/{REVISION}/{name}?download=true",
                  models / name, digest)
    return status()
