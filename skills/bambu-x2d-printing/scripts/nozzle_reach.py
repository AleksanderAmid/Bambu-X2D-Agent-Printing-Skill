"""Check one feature's X2D bed-frame box against a resolved rectangular nozzle envelope."""
import argparse
import json
import math
from pathlib import Path
from zipfile import BadZipFile, ZipFile


def check(settings, nozzle, bounds):
    if settings.get("printer_model") != "Bambu Lab X2D":
        raise ValueError("Expected resolved Bambu Lab X2D project settings")
    if nozzle not in (0, 1) or len(bounds) != 6 or not all(math.isfinite(v) for v in bounds):
        raise ValueError("Supply one nozzle index and six finite bounds in mm")
    xmin, ymin, zmin, xmax, ymax, zmax = bounds
    if xmin > xmax or ymin > ymax or zmin > zmax:
        raise ValueError("A minimum exceeds its maximum")
    vertices = [tuple(map(float, p.split("x"))) for p in settings["extruder_printable_area"][nozzle].split(",")]
    if any(len(p) != 2 or not all(math.isfinite(v) for v in p) for p in vertices):
        raise ValueError("Invalid printable-area polygon")
    xs, ys = sorted({p[0] for p in vertices}), sorted({p[1] for p in vertices})
    if (len(vertices) != 4 or len(set(vertices)) != 4 or len(xs) != 2 or len(ys) != 2
            or any(a[0] != b[0] and a[1] != b[1] for a, b in zip(vertices, vertices[1:] + vertices[:1]))):
        raise ValueError("Use Studio's geometry checks for this non-rectangular nozzle area")
    profile_z = float(settings["extruder_printable_height"][nozzle])
    if not math.isfinite(profile_z) or profile_z <= 0:
        raise ValueError("Invalid printable height")
    # Apply both the profile and published physical Z limit for the named head.
    ceiling = min(profile_z, (260.0, 256.0)[nozzle])
    inside = xs[0] <= xmin <= xmax <= xs[1] and ys[0] <= ymin <= ymax <= ys[1] and 0 <= zmin <= zmax <= ceiling
    return {"inside_nozzle_envelope": inside, "nozzle_index": nozzle,
            "envelope_mm": [xs[0], ys[0], 0, xs[1], ys[1], ceiling],
            "feature_bounds_mm": list(bounds), "scope": "rectangular reach only; review exclusions, brim, tower and clearance in Studio"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Sliced Studio 3MF with resolved X2D settings")
    parser.add_argument("--nozzle", type=int, choices=(0, 1), required=True, help="Confirmed physical nozzle index")
    parser.add_argument("--bounds", type=float, nargs=6, required=True, metavar=("XMIN","YMIN","ZMIN","XMAX","YMAX","ZMAX"))
    args = parser.parse_args()
    try:
        with ZipFile(args.project) as archive:
            entry = archive.getinfo("Metadata/project_settings.config")
            if entry.file_size > 16 * 1024 * 1024:
                raise ValueError("Settings exceed this helper's read limit")
            info = check(json.loads(archive.read(entry)), args.nozzle, args.bounds)
        print(json.dumps(info, indent=2))
        if not info["inside_nozzle_envelope"]:
            parser.exit(1)
    except (OSError, KeyError, IndexError, ValueError, TypeError, BadZipFile) as exc:
        parser.exit(2, f"Unable to assess nozzle envelope: {exc}\n")


if __name__ == "__main__":
    main()
