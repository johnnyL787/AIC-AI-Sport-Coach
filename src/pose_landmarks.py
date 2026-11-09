"""
pose_landmarks.py
Runs MediaPipe Pose on a volleyball setting video:
  - draws the skeleton on every frame
  - prints the x, y of tracked joints in the terminal and writes them on the video
  - saves a CSV with one row per frame
  - saves the annotated video

Usage:
    python src/pose_landmarks.py data/your_clip.mp4
pip install yt-dlp
Outputs go to the out/ folder.
"""

import csv
import os
import sys
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python import vision

# ---------------------------------------------------------------
# Joints to track: (name, MediaPipe landmark number)
# "left"/"right" means the PERSON's left/right, not the screen's.
# ---------------------------------------------------------------

# Praneet: arms
ARM_JOINTS = [
    ("left_shoulder", 11),
    ("right_shoulder", 12),
    ("left_elbow", 13),
    ("right_elbow", 14),
    ("left_wrist", 15),
    ("right_wrist", 16),
]

# Nilesh: add hips, knees, ankles, heels, feet here, e.g. ("left_knee", 25)
# Hips 23/24, knees 25/26, ankles 27/28, heels 29/30, feet 31/32
LEG_JOINTS = [
    ("left_hip", 23),
    ("right_hip", 24),
    ("left_knee", 25),
    ("right_knee", 26),
    ("left_ankle", 27),
    ("right_ankle", 28),
    ("left_heel", 29),
    ("right_heel", 30),
    ("left_foot_index", 31),
    ("right_foot_index", 32),
]

TRACKED_JOINTS = ARM_JOINTS + LEG_JOINTS

# Lines that make up the skeleton (pairs of landmark numbers)
SKELETON = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),   # shoulders + arms
    (11, 23), (12, 24), (23, 24),                       # torso
    (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),   # left leg
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32),   # right leg
]

MODEL_PATH = "models/pose_landmarker_full.task"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
             "pose_landmarker_full/float16/latest/pose_landmarker_full.task")
OUTPUT_DIR = "out"


def get_model():
    """Download the MediaPipe pose model the first time the script runs."""
    if not os.path.exists(MODEL_PATH):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        print("Downloading pose model (one time only)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    return MODEL_PATH


def make_landmarker():
    """Set up MediaPipe's pose detector for video."""
    options = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=get_model()),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
    )
    return vision.PoseLandmarker.create_from_options(options)


def draw_skeleton(frame, points):
    """Draw lines between joints and a dot on each joint. points = {id: (x_px, y_px)}"""
    for a, b in SKELETON:
        if a in points and b in points:
            cv2.line(frame, points[a], points[b], (255, 255, 255), 2)
    for p in points.values():
        cv2.circle(frame, p, 4, (0, 0, 255), -1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/pose_landmarks.py data/your_clip.mp4")
        sys.exit(1)

    video_path = sys.argv[1]
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Output files are named after the input video
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    name = os.path.splitext(os.path.basename(video_path))[0]
    csv_path = os.path.join(OUTPUT_DIR, f"{name}_landmarks.csv")
    video_out_path = os.path.join(OUTPUT_DIR, f"{name}_annotated.mp4")

    writer = cv2.VideoWriter(video_out_path, cv2.VideoWriter_fourcc(*"mp4v"),
                             fps, (width, height))

    # CSV header: frame, then x / y / vis for every tracked joint
    header = ["frame"]
    for joint_name, _ in TRACKED_JOINTS:
        header += [f"{joint_name}_x", f"{joint_name}_y", f"{joint_name}_vis"]

    landmarker = make_landmarker()

    with open(csv_path, "w", newline="") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(header)

        frame_num = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            # MediaPipe wants RGB; OpenCV gives BGR
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(frame_num * 1000 / fps)
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            row = [frame_num]

            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]   # first (only) person

                # Convert every landmark from 0-1 to pixels, for drawing
                points = {i: (int(lm.x * width), int(lm.y * height))
                          for i, lm in enumerate(landmarks)}
                draw_skeleton(frame, points)

                print(f"Frame {frame_num}:")
                text_y = 25
                for joint_name, idx in TRACKED_JOINTS:
                    lm = landmarks[idx]
                    x_px, y_px = points[idx]
                    vis = round(lm.visibility, 3)
                    row += [x_px, y_px, vis]

                    label = f"{joint_name}: ({x_px}, {y_px})"
                    print(f"  {label}  vis={vis}")
                    cv2.putText(frame, label, (10, text_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    text_y += 20
            else:
                # No person found: blank values so frame numbers stay lined up
                print(f"Frame {frame_num}: no person detected")
                row += [""] * (3 * len(TRACKED_JOINTS))

            cv2.putText(frame, f"frame {frame_num}", (10, height - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            csv_writer.writerow(row)
            writer.write(frame)
            frame_num += 1

    cap.release()
    writer.release()
    landmarker.close()

    print(f"\nDone. {frame_num} frames processed.")
    print(f"CSV:   {csv_path}")
    print(f"Video: {video_out_path}")


if __name__ == "__main__":
    main()