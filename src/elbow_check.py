import argparse
import math

from rules import ELBOW_RULES, MIN_VISIBILITY, ELBOW_AVERAGE_FRAMES
from contact_check import (load_rows, load_ball_csv, bodies_by_frame,
                           torso_length, analyze_contact, FOLLOW_THROUGH_FRAMES)


CHECK_INFO = {
    "elbow_angle_deg": {
        "name": "Elbow bend",
        "unit": "deg",
        "pass": "Nice elbows, bent and ready to push.",
        "low": "Lift your elbows so your hands make a window.",
        "high": "Bend your elbows more to soak up the ball.",
    },
    "elbow_above_shoulder_torso_lengths": {
        "name": "Elbow height",
        "unit": "torso lengths",
        "pass": "Good, your elbows are up at shoulder height.",
        "low": "Raise your elbows to shoulder height or higher.",
        "high": "Raise your elbows to shoulder height or higher.",
    },
    "elbow_extension_deg": {
        "name": "Arms push through",
        "unit": "deg",
        "pass": "Good push, your arms extend through the ball.",
        "low": "Push through the ball by straightening your arms.",
        "high": "Push through the ball by straightening your arms.",
    },
    "elbow_symmetry_deg": {
        "name": "Both arms even",
        "unit": "deg",
        "pass": "Both arms are working evenly.",
        "low": "Use both arms evenly.",
        "high": "Use both arms evenly.",
    },
}

NOT_MEASURED_TIP = "Film from the side with your arms in view through the end of the set."


def angle(a, b, c):
    ab = (a[0] - b[0], a[1] - b[1])
    cb = (c[0] - b[0], c[1] - b[1])
    size = math.hypot(*ab) * math.hypot(*cb)
    if size == 0:
        return None
    dot = ab[0] * cb[0] + ab[1] * cb[1]
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / size))))


def average(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def visible_point(row, name):
    x, y, vis = row.get(f"{name}_x"), row.get(f"{name}_y"), row.get(f"{name}_vis")
    if not x or not y:
        return None
    if vis not in (None, "") and float(vis) < MIN_VISIBILITY:
        return None
    return (float(x), float(y))


def arm(row, side):
    points = [visible_point(row, f"{side}_{joint}")
              for joint in ("shoulder", "elbow", "wrist")]
    return None if None in points else points


def elbow_angle(row, side):
    points = arm(row, side)
    return angle(*points) if points else None


def elbow_height(row, side, torso):
    points = arm(row, side)
    if not points or not torso:
        return None
    shoulder, elbow, _ = points
    return (shoulder[1] - elbow[1]) / torso   # smaller y = higher on screen


def make_check(rule_name, value, phase, missing_tip=NOT_MEASURED_TIP):
    info = CHECK_INFO[rule_name]
    low = ELBOW_RULES[rule_name]["min"]
    high = ELBOW_RULES[rule_name]["max"]

    if value is None:
        passed, tip = None, missing_tip
    elif low is not None and value < low:
        passed, tip = False, info["low"]
    elif high is not None and value > high:
        passed, tip = False, info["high"]
    else:
        passed, tip = True, info["pass"]

    return {
        "name": info["name"],
        "category": "elbows",
        "phase": phase,
        "value": None if value is None else round(value, 2),
        "unit": info["unit"],
        "min": low,
        "max": high,
        "passed": passed,
        "tip": tip,
    }


def check_elbows(rows, contact_frame, release_frame=None):
    by_frame = {int(r["frame"]): r for r in rows}
    bodies = bodies_by_frame(rows)

    near = range(contact_frame - ELBOW_AVERAGE_FRAMES,
                 contact_frame + ELBOW_AVERAGE_FRAMES + 1)
    near_rows = [by_frame[f] for f in near if f in by_frame]
    torso = average([torso_length(bodies[f]) for f in near if f in bodies])

    left = average([elbow_angle(r, "left") for r in near_rows])
    right = average([elbow_angle(r, "right") for r in near_rows])
    bend = average([left, right])

    height = average([elbow_height(r, side, torso)
                      for r in near_rows for side in ("left", "right")])

    symmetry = abs(left - right) if left is not None and right is not None else None

    end = release_frame if release_frame is not None else contact_frame + FOLLOW_THROUGH_FRAMES
    end = max(end, contact_frame + 1)
    later = [average([elbow_angle(by_frame[f], "left"), elbow_angle(by_frame[f], "right")])
             for f in range(contact_frame + 1, end + 1) if f in by_frame]
    later = [a for a in later if a is not None]
    extension = max(later) - bend if later and bend is not None else None

    return [
        make_check("elbow_angle_deg", bend, "contact"),
        make_check("elbow_above_shoulder_torso_lengths", height, "contact"),
        make_check("elbow_extension_deg", extension, "follow"),
        make_check("elbow_symmetry_deg", symmetry, "contact",
                   "Only one arm was visible from the side, so this wasn't scored."),
    ]


def main():
    parser = argparse.ArgumentParser(description="Check the elbows at contact.")
    parser.add_argument("landmarks_csv", help="CSV from pose_landmarks.py")
    parser.add_argument("video", nargs="?", help="The video (optional)")
    parser.add_argument("--ball", help="Ball tracking CSV from ball_tracking.py")
    args = parser.parse_args()

    balls = load_ball_csv(args.ball) if args.ball else None
    contact = analyze_contact(args.landmarks_csv, args.video, balls)
    checks = check_elbows(load_rows(args.landmarks_csv),
                          contact["contact_frame"], contact["release_frame"])

    print(f"Contact frame: {contact['contact_frame']}  "
          f"Release frame: {contact['release_frame']}\n")
    for c in checks:
        status = {True: "PASS", False: "FAIL", None: "NOT MEASURED"}[c["passed"]]
        value = "-" if c["value"] is None else f"{c['value']:.1f}"
        print(f"  {c['name']:18s} {value:>7s} {c['unit']:14s} "
              f"[{c['min']} to {c['max']}]  {status}")
        if c["passed"] is not True:
            print(f"      tip: {c['tip']}")


if __name__ == "__main__":
    main()
