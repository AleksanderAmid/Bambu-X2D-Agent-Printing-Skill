"""Dry decision check for a reviewed Studio job. Does not observe the GUI, grant consent, or click."""
import argparse
import json
import math
from pathlib import Path
import re
from plate_review import reviewed_plate


def next_step(review, visible, operator_action, previous_start):
    """review and visible describe independent observations, never fabricate either from the other."""
    if previous_start in {"unknown", "attempted", "accepted", "running"}:
        return "check_device_state"
    if previous_start != "none":
        return "request_new_review"
    if not isinstance(review, dict) or not isinstance(visible, dict):
        return "request_new_review"
    # File hash binds all settings inside the artifact. The remaining fields bind the live selection.
    fields = ("sha256", "studio_plate", "printer", "mapping", "quantity", "nozzles_mm", "plate_type", "print_options")
    for key in fields:
        if key not in review or key not in visible or type(review[key]) is not type(visible[key]) or review[key] != visible[key]:
            return "request_new_review"
    if not isinstance(review["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", review["sha256"]):
        return "request_new_review"
    if any(type(review[k]) is not int or review[k] < 1 for k in ("studio_plate", "quantity")):
        return "request_new_review"
    if not all(isinstance(review[k], str) and review[k].strip() for k in ("printer", "plate_type", "mapping")):
        return "request_new_review"
    for selection in (review, visible):
        diameters = selection["nozzles_mm"]
        if not isinstance(diameters, list) or len(diameters) != 2:
            return "request_new_review"
        if not all(type(d) in (int, float) and math.isfinite(d) and d > 0 for d in diameters):
            return "request_new_review"
    if not isinstance(review["print_options"], dict) or json.dumps(review["print_options"], sort_keys=True) != json.dumps(visible["print_options"], sort_keys=True):
        return "request_new_review"
    if operator_action == "human_click":
        return "leave_final_control_to_operator"
    if operator_action == "approved_and_delegated" and visible.get("final_control_verified") is True:
        return "one_studio_click_eligible"
    return "await_operator"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("context", type=Path, help="Reviewed summary, current independent observation, operator action, previous start")
    args = parser.parse_args()
    try:
        context = json.loads(args.context.read_text(encoding="utf-8-sig"))
        review = context["review"]
        receipt = json.loads(args.receipt.read_text(encoding="utf-8-sig"))
        plate = reviewed_plate(args.artifact, receipt, review["studio_plate"])
        if any(review[key] != plate[key] for key in ("sha256", "nozzles_mm", "plate_type")):
            raise ValueError("Reviewed summary disagrees with the inspected artifact")
        print(next_step(review, context["visible"], context["operator_action"], context["previous_start"]))
    except (OSError, KeyError, ValueError, TypeError, AttributeError) as exc:
        parser.exit(2, f"Cannot verify this review: {exc}\n")


if __name__ == "__main__":
    main()
