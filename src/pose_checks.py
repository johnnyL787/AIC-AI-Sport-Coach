import argparse
import csv
import math

from rules import POSE_RULES


JOINTS = (
    "left_shoulder",
    "right_shoulder",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
)


def read_point(row, joint):
    x = float(row[f"{joint}_x"])
    y = float(row[f"{joint}_y"])
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("Invalid landmark coordinates")
    return x, y


def midpoint(first, second):
    return (first[0] + second[0]) / 2, (first[1] + second[1]) / 2


def measure_pose(row, facing):
    points = {joint: read_point(row, joint) for joint in JOINTS}

    left_hip = points["left_hip"]
    right_hip = points["right_hip"]
    hip_x, hip_y = midpoint(left_hip, right_hip)
    shoulder_x, shoulder_y = midpoint(
        points["left_shoulder"], points["right_shoulder"]
    )

    dx = shoulder_x - hip_x
    up = hip_y - shoulder_y  # Image y increases downward.
    torso_length = math.hypot(dx, up)
    if torso_length == 0:
        raise ValueError("Zero torso length")

    # Make positive values mean forward for either screen direction.
    forward = 1 if facing == "right" else -1
    left = forward * (points["left_knee"][0] - left_hip[0]) / torso_length
    right = forward * (points["right_knee"][0] - right_hip[0]) / torso_length

    left_lead = left - right
    lean = math.degrees(math.atan2(abs(dx), up))

    return left, right, left_lead, lean


def check_range(rule_name, *values):
    limits = POSE_RULES[rule_name]
    minimum = limits["min"]
    maximum = limits["max"]

    if minimum is None and maximum is None:
        return "UNSET"

    for value in values:
        if minimum is not None and value < minimum:
            return "FAIL"
        if maximum is not None and value > maximum:
            return "FAIL"

    return "PASS"


def main():
    parser = argparse.ArgumentParser(
        description="Measure knee position and torso lean from a landmark CSV."
    )
    parser.add_argument("csv_path", help="Path to the landmark CSV")
    parser.add_argument(
        "--facing",
        choices=("left", "right"),
        required=True,
        help="Which direction the setter faces on screen",
    )
    args = parser.parse_args()

    with open(args.csv_path, newline="") as csv_file:
        rows = csv.DictReader(csv_file)

        required = {"frame"}
        required.update(
            f"{joint}_{axis}" for joint in JOINTS for axis in ("x", "y")
        )
        missing = required.difference(rows.fieldnames or [])
        if missing:
            parser.error("CSV is missing columns: " + ", ".join(sorted(missing)))

        for row in rows:
            frame = row["frame"]

            try:
                left, right, left_lead, lean = measure_pose(row, args.facing)
            except (TypeError, ValueError):
                print(f"Frame {frame}: skipped (missing or invalid coordinates)")
                continue

            knee_status = check_range("knee_forward_torso_lengths", left, right)
            lead_status = check_range("left_knee_lead_torso_lengths", left_lead)
            lean_status = check_range("torso_lean_deg", lean)

            print(
                f"Frame {frame}: "
                f"left knee={left:+.3f}, right knee={right:+.3f} "
                f"torso lengths [{knee_status}] | "
                f"left lead={left_lead:+.3f} torso lengths [{lead_status}] | "
                f"torso lean={lean:.1f} deg [{lean_status}]"
            )


if __name__ == "__main__":
    main()