"""
contact_check.py
Checks hand position at ball contact during a volleyball set.

Steps:
  1. Read the landmarks CSV made by pose_landmarks.py
  2. Draw a boundary line above the player's head
  3. Find the contact frame (when the hands reach the boundary)
  4. At that frame, measure the hands against the shoulders and face
  5. Compare each measurement to the ranges in rules.py

Usage (run from the main repo folder):
    python src/contact_check.py out/setting_landmarks.csv
    python src/contact_check.py out/setting_landmarks.csv data/setting.mp4

Adding the video also saves a picture of the contact frame to out/.
"""

import csv
import math
import sys

import cv2

from rules import CONTACT_RULES, CONTACT_BOUNDARY_ABOVE_NOSE


# ---------------------------------------------------------------
# Small math helpers
# ---------------------------------------------------------------

def midpoint(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ---------------------------------------------------------------
# Reading the CSV
# ---------------------------------------------------------------

def load_rows(csv_path):
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))


def get_point(row, name):
    """Return (x, y) for a joint, or None if it's blank in this frame."""
    x = row.get(f"{name}_x")
    y = row.get(f"{name}_y")
    if not x or not y:
        return None
    return (float(x), float(y))


NEEDED = ["nose", "left_shoulder", "right_shoulder", "left_hip", "right_hip",
          "left_wrist", "right_wrist"]


def get_body(row):
    """All the points we need for one frame, or None if any are missing."""
    body = {name: get_point(row, name) for name in NEEDED}
    if any(p is None for p in body.values()):
        return None
    body["left_ear"] = get_point(row, "left_ear")      # optional
    body["right_ear"] = get_point(row, "right_ear")    # optional
    return body


# ---------------------------------------------------------------
# Body measurements
# ---------------------------------------------------------------

def torso_length(body):
    """Shoulder midpoint to hip midpoint. Our unit for every distance."""
    shoulders = midpoint(body["left_shoulder"], body["right_shoulder"])
    hips = midpoint(body["left_hip"], body["right_hip"])
    return distance(shoulders, hips)


def boundary_y(body):
    """The y value of the boundary line above the head (smaller y = higher)."""
    return body["nose"][1] - CONTACT_BOUNDARY_ABOVE_NOSE * torso_length(body)


def hands_point(body):
    """Contact point: midway between the two wrists."""
    return midpoint(body["left_wrist"], body["right_wrist"])


def facing_direction(body):
    """
    +1 if the player faces the right side of the screen, -1 if the left.
    Works out which way the nose points compared to the ears.
    """
    ears = [e for e in (body["left_ear"], body["right_ear"]) if e is not None]
    if not ears:
        return 1
    ear_x = sum(e[0] for e in ears) / len(ears)
    return 1 if body["nose"][0] >= ear_x else -1


# ---------------------------------------------------------------
# Finding the contact frame
# ---------------------------------------------------------------

def find_contact_frame(rows):
    """
    For now: contact = the first frame where the hands reach the boundary.
    If they never reach it, use the frame where the hands are highest.

    Later, when ball tracking is connected, this becomes:
    the first frame where the BALL crosses the boundary.
    """
    highest_row = None
    highest_y = float("inf")

    for row in rows:
        body = get_body(row)
        if body is None:
            continue
        hands_y = hands_point(body)[1]

        if hands_y <= boundary_y(body):
            return row, "hands reached the boundary"

        if hands_y < highest_y:
            highest_y = hands_y
            highest_row = row

    return highest_row, "hands never reached the boundary, used highest hands"


# ---------------------------------------------------------------
# The checks
# ---------------------------------------------------------------

def measure(body):
    """Every contact measurement, in torso lengths or degrees."""
    torso = torso_length(body)
    shoulders = midpoint(body["left_shoulder"], body["right_shoulder"])
    hands = hands_point(body)
    nose = body["nose"]
    left_wrist = body["left_wrist"]
    right_wrist = body["right_wrist"]

    # Up is a SMALLER y, so "how far up" = start y minus end y
    dx = hands[0] - shoulders[0]
    dy_up = shoulders[1] - hands[1]

    return {
        "hands_level_torso_lengths": abs(left_wrist[1] - right_wrist[1]) / torso,
        "hands_forward_torso_lengths": dx * facing_direction(body) / torso,
        "hands_above_head_torso_lengths": (nose[1] - hands[1]) / torso,
        "contact_to_face_torso_lengths": distance(hands, nose) / torso,
        "contact_angle_deg": math.degrees(math.atan2(abs(dx), dy_up)),
    }


def run_checks(values):
    """
    Compare each value to its min/max in CONTACT_RULES (rules.py).
    A bound of None means it hasn't been set yet, so that side is skipped.
    """
    results = {}
    for name, bounds in CONTACT_RULES.items():
        if name not in values:
            print(f"Warning: rules.py has '{name}' but no calculation for it")
            continue
        value = values[name]
        low, high = bounds["min"], bounds["max"]
        passed = (low is None or value >= low) and (high is None or value <= high)
        results[name] = (value, low, high, passed)
    return results


# ---------------------------------------------------------------
# Picture of the contact frame (optional)
# ---------------------------------------------------------------

def save_contact_image(video_path, frame_num, body, results, out_path):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        print(f"Could not read frame {frame_num} from {video_path}")
        return

    # Boundary line across the frame
    by = int(boundary_y(body))
    cv2.line(frame, (0, by), (frame.shape[1], by), (0, 255, 255), 2)
    cv2.putText(frame, "boundary", (10, by - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    # Contact point, nose, shoulders
    hx, hy = map(int, hands_point(body))
    cv2.circle(frame, (hx, hy), 8, (255, 0, 255), -1)
    cv2.circle(frame, tuple(map(int, body["nose"])), 6, (255, 255, 0), -1)
    for side in ("left_shoulder", "right_shoulder"):
        cv2.circle(frame, tuple(map(int, body[side])), 6, (255, 255, 0), -1)

    # Results at the bottom: green = pass, red = fail
    y = frame.shape[0] - 24 * len(results) - 5
    for name, (value, low, high, passed) in results.items():
        color = (0, 200, 0) if passed else (0, 0, 255)
        text = f"{name}: {value:.2f}  [{low} to {high}]  {'PASS' if passed else 'FAIL'}"
        cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        y += 24

    cv2.imwrite(out_path, frame)
    print(f"Picture: {out_path}")


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python src/contact_check.py out/setting_landmarks.csv [data/setting.mp4]")
        sys.exit(1)

    csv_path = sys.argv[1]
    video_path = sys.argv[2] if len(sys.argv) > 2 else None

    rows = load_rows(csv_path)
    contact_row, how = find_contact_frame(rows)
    if contact_row is None:
        print("No frame had all the points needed (nose, shoulders, hips, wrists).")
        sys.exit(1)

    frame_num = int(contact_row["frame"])
    body = get_body(contact_row)
    results = run_checks(measure(body))

    print(f"Contact frame: {frame_num} ({how})")
    print(f"Torso length: {torso_length(body):.1f} px\n")
    for name, (value, low, high, passed) in results.items():
        print(f"  {name:32s} {value:6.2f}   range {low} to {high}   {'PASS' if passed else 'FAIL'}")

    passed = sum(r[3] for r in results.values())
    print(f"\n{passed}/{len(results)} checks passed")

    if video_path:
        out_path = csv_path.replace("_landmarks.csv", "_contact.png")
        save_contact_image(video_path, frame_num, body, results, out_path)


if __name__ == "__main__":
    main()
