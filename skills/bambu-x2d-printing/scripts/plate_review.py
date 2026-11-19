"""Bind an existing offline inspection receipt to the durable selected X2D plate. No printer I/O."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def reviewed_plate(artifact, receipt, studio_plate):
    if type(studio_plate) is not int or studio_plate < 1:
        raise ValueError("Studio plates start at 1")
    if receipt.get("receipt_version") != "1" or receipt.get("evidence") != "file-only" or receipt.get("dispatch_authorized") is not False:
        raise ValueError("Expected a v1 file-only inspect_print_file receipt")
    selection = receipt["selection"]
    if selection.get("bambu_model") != "x2d" or type(selection.get("plate_index")) is not int or selection["plate_index"] != studio_plate - 1:
        raise ValueError("Wrong target or selected plate")
    evidence, details = receipt["artifact"], receipt["inspection"]
    if evidence["file_format"] != "3mf" or details.get("model") != "x2d" or details.get("plateInternalPath") != f"Metadata/plate_{studio_plate}.gcode":
        raise ValueError("Expected X2D plate toolpaths in a sliced 3MF")
    with artifact.open("rb") as stream:
        before = os.fstat(stream.fileno())
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        after = os.fstat(stream.fileno())
    current = artifact.stat()
    if not os.path.samestat(after, current) or before.st_mtime_ns != after.st_mtime_ns or after.st_mtime_ns != current.st_mtime_ns:
        raise ValueError("File changed during review. Inspect the durable file again.")
    if before.st_size != current.st_size or current.st_size != evidence["byte_length"] or digest != evidence["sha256"] or digest != details["sha256"]:
        raise ValueError("File changed or receipt belongs to different bytes. Inspect the durable file again.")
    return {"sha256": digest, "studio_plate": studio_plate, "printer_model": details["model"],
            "nozzles_mm": details.get("nozzleDiameters"), "plate_type": details.get("bedType"),
            "materials": details.get("materials"), "file_filaments": details.get("projectFilaments"),
            "slicer": receipt.get("sliced"), "evidence": "file-only"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--studio-plate", type=int, required=True)
    args = parser.parse_args()
    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8-sig"))
        print(json.dumps(reviewed_plate(args.artifact, receipt, args.studio_plate), indent=2))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        parser.exit(2, f"Plate review failed: {exc}\n")


if __name__ == "__main__":
    main()
