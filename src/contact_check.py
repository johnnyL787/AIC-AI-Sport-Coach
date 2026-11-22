"""
contact_check.py
Checks the setter's hands at ball contact and on the follow-through.

Steps:
  1. Read the landmarks CSV made by pose_landmarks.py
  2. Draw a boundary line above the player's head (moves with the player)
  3. CONTACT: the ball comes DOWN through the boundary near the head
  4. RELEASE: the ball goes back UP through the boundary after contact
  5. Check the hands at contact, and that they're above the head at release
  6. Save the results in the shared team format (JSON) for the UI cards

If there's no ball data (or the ball never crosses the boundary), it falls
back to using the hands, so it still works.

Usage (run from the main repo folder):
    python src/contact_check.py out/clip_landmarks.csv data/clip.mp4 --ball ball_tracking.csv

Outputs:
    out/clip_contact.json   results in the shared format
    out/clip_contact.png    picture of the contact frame
"""

import argparse
import csv
import json
import math
import os

import cv2

from rules import (CONTACT_RULES, CONTACT_BOUNDARY_ABOVE_NOSE,
                   CONTACT_BALL_NEAR_HEAD)


# How many frames after contact to look for the follow-through
# if there is no ball data (about half a second at 60 fps)
FOLLOW_THROUGH_FRAMES = 30


# ---------------------------------------------------------------
# What each check is called on the UI card, its unit, and its tips.
# "low" = value below min, "high" = value above max.
# ---------------------------------------------------------------

CHECK_INFO = {
    "hands_level_torso_lengths": {
        "name": "Hands level",
        "unit": "torso lengths",
        "pass": "Both hands are at the same height. Nice.",
        "low": "Bring both hands to the same height.",
        "high": "Bring both hands to the same height.",
    },
    "hands_forward_torso_lengths": {
        "name": "Hands forward",
        "unit": "torso lengths",
        "pass": "Good, your hands are out in front of your forehead.",
        "low": "Reach your hands a little more in front of your forehead.",
        "high": "Your hands are too far out in front. Get under the ball more.",
    },
    "hands_above_head_torso_lengths": {
        "name": "Hand height at contact",
        "unit": "torso lengths",
        "pass": "Good contact height, just above your forehead.",
        "low": "Get your hands higher, just above your forehead.",
        "high": "Your hands are too high. Meet the ball at your forehead, not at full reach.",
    },
    "contact_to_face_torso_lengths": {
        "name": "Contact distance from face",
        "unit": "torso lengths",
        "pass": "Good spacing between the ball and your face.",
        "low": "The ball is too close to your face. Give yourself a little space.",
        "high": "The ball is too far from your face. Move your feet to get under it.",
    },
    "contact_angle_deg": {
        "name": "Contact angle",
        "unit": "deg",
        "pass": "The ball is above you at contact. Good positioning.",
        "low": "The ball is above you at contact. Good positioning.",
        "high": "Get your body under the ball so it's more above you.",
    },
    "follow_through_above_head_torso_lengths": {
        "name": "Follow-through",
        "unit": "torso lengths",
        "pass": "Good follow-through, your hands finish above your head.",
        "low": "Extend your arms up through the ball after you release it.",
        "high": "Extend your arms up through the ball after you release it.",
    },
}


# ---------------------------------------------------------------
# Small math helpers
# ---------------------------------------------------------------

def midpoint(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ---------------------------------------------------------------
# Reading the landmarks CSV
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


def bodies_by_frame(rows):
    """{frame number: body} for every frame where the player was found."""
    bodies = {}
    for row in rows:
        body = get_body(row)
        if body is not None:
            bodies[int(row["frame"])] = body
    return bodies


# ---------------------------------------------------------------
# Reading the ball data
# Accepts Pratyush's CSV (Frame, X, Y, VX, VY, ..., Detected)
# or the shared format (frame, x, y, vx, vy, detected).
# Missing frames are fine: they're just skipped.
# ---------------------------------------------------------------

def to_number(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def load_ball_csv(path):
    """Read ball positions into the shared format: a list of dicts."""
    balls = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            row = {k.strip().lower(): v for k, v in row.items() if k}
            frame = to_number(row.get("frame"))
            if frame is None:
                continue
            balls.append({
                "frame": int(frame),
                "x": to_number(row.get("x")),
                "y": to_number(row.get("y")),
                "vx": to_number(row.get("vx")),
                "vy": to_number(row.get("vy")),
                "detected": str(row.get("detected", "")).strip() in ("1", "True", "true"),
            })
    return balls


def ball_by_frame(balls):
    """{frame number: (x, y)} for frames where we know where the ball is."""
    found = {}
    for b in balls or []:
        if b.get("x") is not None and b.get("y") is not None:
            found[int(b["frame"])] = (b["x"], b["y"])
    return found


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
    """Midway between the two wrists."""
    return midpoint(body["left_wrist"], body["right_wrist"])


def hands_above_head(body):
    """How far the hands are above the nose, in torso lengths."""
    return (body["nose"][1] - hands_point(body)[1]) / torso_length(body)


def facing_direction(body):
    """+1 if the player faces the right of the screen, -1 if the left."""
    ears = [e for e in (body["left_ear"], body["right_ear"]) if e is not None]
    if not ears:
        return 1
    ear_x = sum(e[0] for e in ears) / len(ears)
    return 1 if body["nose"][0] >= ear_x else -1


def ball_near_head(ball, body):
    """Is the ball within CONTACT_BALL_NEAR_HEAD torso lengths sideways of the head?"""
    return abs(ball[0] - body["nose"][0]) <= CONTACT_BALL_NEAR_HEAD * torso_length(body)


# ---------------------------------------------------------------
# Finding contact and release
# ---------------------------------------------------------------

def find_ball_crossings(bodies, balls):
    """
    Contact = first frame the ball comes DOWN through the boundary near the head.
    Release = first frame after that the ball goes back UP through it.
    Returns (contact_frame, release_frame). Either can be None.
    """
    contact = None
    release = None
    was_above = None   # was the ball above the boundary last time we saw it?

    for frame in sorted(balls):
        body = bodies.get(frame)
        if body is None:
            continue
        ball = balls[frame]
        if not ball_near_head(ball, body):
            was_above = None
            continue

        above = ball[1] < boundary_y(body)

        if contact is None:
            if was_above is True and not above:
                contact = frame
        elif not was_above and above:
            release = frame
            break

        was_above = above

    return contact, release


def find_contact_by_hands(bodies):
    """Backup: first frame the hands reach the boundary, or the highest hands."""
    highest_frame = None
    highest_y = float("inf")
    for frame in sorted(bodies):
        body = bodies[frame]
        hands_y = hands_point(body)[1]
        if hands_y <= boundary_y(body):
            return frame
        if hands_y < highest_y:
            highest_y = hands_y
            highest_frame = frame
    return highest_frame


def find_release_by_hands(bodies, contact_frame):
    """Backup: the frame with the highest hands soon after contact."""
    best_frame = None
    best_height = -float("inf")
    for frame in sorted(bodies):
        if contact_frame < frame <= contact_frame + FOLLOW_THROUGH_FRAMES:
            height = hands_above_head(bodies[frame])
            if height > best_height:
                best_height = height
                best_frame = frame
    return best_frame


# ---------------------------------------------------------------
# The checks
# ---------------------------------------------------------------

def measure_contact(body):
    """Measurements at the contact frame, in torso lengths or degrees."""
    torso = torso_length(body)
    shoulders = midpoint(body["left_shoulder"], body["right_shoulder"])
    hands = hands_point(body)
    nose = body["nose"]

    # Up is a SMALLER y, so "how far up" = start y minus end y
    dx = hands[0] - shoulders[0]
    dy_up = shoulders[1] - hands[1]

    return {
        "hands_level_torso_lengths": abs(body["left_wrist"][1] - body["right_wrist"][1]) / torso,
        "hands_forward_torso_lengths": dx * facing_direction(body) / torso,
        "hands_above_head_torso_lengths": hands_above_head(body),
        "contact_to_face_torso_lengths": distance(hands, nose) / torso,
        "contact_angle_deg": math.degrees(math.atan2(abs(dx), dy_up)),
    }


def make_check(rule_name, value):
    """One check in the shared team format."""
    info = CHECK_INFO[rule_name]
    low = CONTACT_RULES[rule_name]["min"]
    high = CONTACT_RULES[rule_name]["max"]

    if low is not None and value < low:
        passed, tip = False, info["low"]
    elif high is not None and value > high:
        passed, tip = False, info["high"]
    else:
        passed, tip = True, info["pass"]

    return {
        "name": info["name"],
        "part": "contact",
        "value": round(value, 2),
        "unit": info["unit"],
        "min": low,
        "max": high,
        "passed": passed,
        "tip": tip,
    }


# ---------------------------------------------------------------
# The main function the UI (or anyone) can call
# ---------------------------------------------------------------

def analyze_contact(landmarks_csv, video_path=None, balls=None, image_path=None):
    """
    Run the contact checks and return results in the shared format.

    landmarks_csv: CSV from pose_landmarks.py
    video_path:    optional, needed to save the contact picture and read fps
    balls:         optional list of ball dicts (frame, x, y, vx, vy, detected)
    image_path:    where to save the contact picture
    """
    rows = load_rows(landmarks_csv)
    bodies = bodies_by_frame(rows)
    if not bodies:
        raise ValueError("No frame had the nose, shoulders, hips and wrists.")

    ball_positions = ball_by_frame(balls)

    # 1. Contact and release from the ball
    contact, release = find_ball_crossings(bodies, ball_positions)
    method = "ball"

    # 2. Backup: use the hands if the ball didn't give us a contact frame
    if contact is None:
        method = "hands"
        contact = find_contact_by_hands(bodies)
    if release is None:
        release = find_release_by_hands(bodies, contact)

    # 3. Checks at contact
    contact_body = bodies[contact]
    checks = [make_check(name, value)
              for name, value in measure_contact(contact_body).items()]

    # 4. Follow-through check at release
    if release is not None:
        checks.append(make_check("follow_through_above_head_torso_lengths",
                                 hands_above_head(bodies[release])))

    fps = None
    if video_path:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or None
        cap.release()
        if image_path:
            save_contact_image(video_path, contact, contact_body,
                               ball_positions.get(contact), checks, image_path)

    return {
        "video": {"fps": fps, "frames": len(rows)},
        "contact_frame": contact,
        "release_frame": release,
        "contact_method": method,
        "contact_image": image_path if video_path else None,
        "ball": balls or [],
        "checks": checks,
    }


# ---------------------------------------------------------------
# Picture of the contact frame
# ---------------------------------------------------------------

def save_contact_image(video_path, frame_num, body, ball, checks, out_path):
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

    # Hands, nose, shoulders, ball
    cv2.circle(frame, tuple(map(int, hands_point(body))), 8, (255, 0, 255), -1)
    cv2.circle(frame, tuple(map(int, body["nose"])), 6, (255, 255, 0), -1)
    for side in ("left_shoulder", "right_shoulder"):
        cv2.circle(frame, tuple(map(int, body[side])), 6, (255, 255, 0), -1)
    if ball is not None:
        cv2.circle(frame, tuple(map(int, ball)), 14, (0, 165, 255), 3)

    # Results at the bottom: green = pass, red = fail
    y = frame.shape[0] - 24 * len(checks) - 5
    for check in checks:
        color = (0, 200, 0) if check["passed"] else (0, 0, 255)
        text = (f"{check['name']}: {check['value']}  "
                f"[{check['min']} to {check['max']}]  "
                f"{'PASS' if check['passed'] else 'FAIL'}")
        cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        y += 24

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    cv2.imwrite(out_path, frame)


# ---------------------------------------------------------------
# Running it from the terminal
# ---------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Check hands at ball contact.")
    parser.add_argument("landmarks_csv", help="CSV from pose_landmarks.py")
    parser.add_argument("video", nargs="?", help="The video (for the picture)")
    parser.add_argument("--ball", help="Ball tracking CSV from ball_tracking.py")
    args = parser.parse_args()

    balls = load_ball_csv(args.ball) if args.ball else None
    base = args.landmarks_csv.replace("_landmarks.csv", "")
    image_path = base + "_contact.png"
    json_path = base + "_contact.json"

    result = analyze_contact(args.landmarks_csv, args.video, balls, image_path)

    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Contact frame: {result['contact_frame']} (found using the {result['contact_method']})")
    print(f"Release frame: {result['release_frame']}\n")
    for c in result["checks"]:
        status = "PASS" if c["passed"] else "FAIL"
        print(f"  {c['name']:28s} {c['value']:6.2f} {c['unit']:14s} "
              f"[{c['min']} to {c['max']}]  {status}")
        if not c["passed"]:
            print(f"      tip: {c['tip']}")

    passed = sum(c["passed"] for c in result["checks"])
    print(f"\n{passed}/{len(result['checks'])} checks passed")
    print(f"Results: {json_path}")
    if result["contact_image"]:
        print(f"Picture: {result['contact_image']}")


if __name__ == "__main__":
    main()