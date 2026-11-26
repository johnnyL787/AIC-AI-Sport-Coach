import json
import math
import os
import sys

import cv2
import numpy as np
from ultralytics import YOLO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT, "models", "yolo11m.pt")
BALL_CLASSES = {"sports ball", "volleyball", "ball"}

max_distance = 120
max_lost = 6
min_track_points = 3
min_still_points = 10
min_score = 0.15
moving_score = 0.25
still_score = 0.45
max_size_ratio = 2.5
min_motion = 40
min_travel = 0.1
max_gravity = 0.01
full_imgsz = 1280
crop_imgsz = 640
person_score = 0.3
min_radius = 8
max_radius = 150
motion_scale = 0.5
motion_threshold = 12
motion_score = 0.3
max_moving_fraction = 0.1


def make_detector():
    """Load the YOLO model (downloaded on first use) and find its ball and person classes."""
    model = YOLO(MODEL_PATH)
    classes = [i for i, name in model.names.items() if name.lower() in BALL_CLASSES]
    if not classes:
        raise ValueError(f"{MODEL_PATH} has no ball class. Classes: {sorted(model.names.values())}")
    people = [i for i, name in model.names.items() if name.lower() == "person"]
    return {"model": model, "classes": classes, "people": people}


def run_detector(detector, image, imgsz, offset_x=0, offset_y=0):
    """Return balls as (x, y, r, score) and people as (x1, y1, x2, y2), in full-frame pixels."""
    if image.shape[0] < 2 or image.shape[1] < 2:
        return [], []
    result = detector["model"].predict(
        image, classes=detector["classes"] + detector["people"],
        conf=min_score, imgsz=imgsz, verbose=False)[0]
    balls = []
    people = []
    boxes = zip(result.boxes.xyxy.tolist(), result.boxes.conf.tolist(), result.boxes.cls.tolist())
    for (x1, y1, x2, y2), score, cls in boxes:
        x1, x2 = x1 + offset_x, x2 + offset_x
        y1, y2 = y1 + offset_y, y2 + offset_y
        if int(cls) in detector["people"]:
            if score >= person_score:
                people.append((x1, y1, x2, y2))
            continue
        w, h = x2 - x1, y2 - y1
        if w <= 0 or h <= 0 or not 0.5 <= w / h <= 2.0:
            continue
        r = (w + h) / 4
        balls.append((int(round((x1 + x2) / 2)), int(round((y1 + y2) / 2)),
                      max(1, int(round(r))), float(score)))
    return balls, people


def detect_balls(detector, image, imgsz=full_imgsz):
    return run_detector(detector, image, imgsz)


def detect_near(detector, image, x, y, r):
    """Search a zoomed-in window around where the ball should be. Cheaper than the full frame."""
    height, width = image.shape[:2]
    side = int(min(max(320, r * 10), width, height))
    x0 = int(min(max(x - side // 2, 0), max(width - side, 0)))
    y0 = int(min(max(y - side // 2, 0), max(height - side, 0)))
    crop = image[y0:y0 + side, x0:x0 + side]
    return run_detector(detector, crop, crop_imgsz, x0, y0)[0]


def small_gray(frame):
    small = cv2.resize(frame, None, fx=motion_scale, fy=motion_scale, interpolation=cv2.INTER_AREA)
    return cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (5, 5), 0)


def read_frames(video):
    """Yield each frame with the grayscale frames just before and after it."""
    ok, frame = video.read()
    if not ok:
        return
    prev_gray, gray = None, small_gray(frame)
    while True:
        ok, nxt = video.read()
        next_gray = small_gray(nxt) if ok else None
        yield frame, prev_gray, gray, next_gray
        if not ok:
            return
        frame, prev_gray, gray = nxt, gray, next_gray


def align(other, gray):
    """Warp other onto gray so camera panning and shaking cancel out.

    Returns the warped frame and a mask of the pixels that both frames cover.
    """
    height, width = gray.shape
    full = np.full_like(gray, 255)
    corners = cv2.goodFeaturesToTrack(gray, maxCorners=400, qualityLevel=0.01, minDistance=8)
    if corners is None or len(corners) < 10:
        return other, full
    moved, status, _ = cv2.calcOpticalFlowPyrLK(gray, other, corners, None)
    good = status.ravel() == 1
    if good.sum() < 10:
        return other, full
    matrix, _ = cv2.estimateAffinePartial2D(
        moved[good], corners[good], method=cv2.RANSAC, ransacReprojThreshold=2.0)
    if matrix is None:
        return other, full
    warped = cv2.warpAffine(other, matrix, (width, height), borderMode=cv2.BORDER_REPLICATE)
    covered = cv2.warpAffine(full, matrix, (width, height), borderValue=0)
    return warped, cv2.erode(covered, np.ones((9, 9), np.uint8))


def detect_moving(prev_gray, gray, next_gray):
    """Find compact moving blobs. Works in any light and for any ball color, even if the camera moves."""
    diffs = []
    covered = np.full_like(gray, 255)
    for other in (prev_gray, next_gray):
        if other is None:
            continue
        warped, mask = align(other, gray)
        diffs.append(cv2.absdiff(gray, warped))
        covered = cv2.bitwise_and(covered, mask)
    if not diffs:
        return []
    motion = diffs[0] if len(diffs) == 1 else cv2.min(diffs[0], diffs[1])
    _, mask = cv2.threshold(motion, motion_threshold, 255, cv2.THRESH_BINARY)
    mask = cv2.bitwise_and(mask, covered)
    if cv2.countNonZero(mask) > max_moving_fraction * mask.size:
        return []
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    count, _, stats, centers = cv2.connectedComponentsWithStats(mask)
    balls = []
    for i in range(1, count):
        w, h, area = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT], stats[i, cv2.CC_STAT_AREA]
        if not 0.4 <= w / h <= 2.5 or area < 0.3 * w * h:
            continue
        r = (w + h) / 4 / motion_scale
        if not min_radius <= r <= max_radius:
            continue
        x = centers[i][0] / motion_scale
        y = centers[i][1] / motion_scale
        balls.append((int(round(x)), int(round(y)), int(round(r)), motion_score))
    return balls


def combine(found, moving, people):
    """Add motion blobs that the model did not already report, skipping motion on a person's body."""
    balls = list(found)
    for blob in moving:
        x, y = blob[0], blob[1]
        if any(x1 <= x <= x2 and y1 <= y <= y2 for x1, y1, x2, y2 in people):
            continue
        if all(math.hypot(x - b[0], y - b[1]) > max(b[2], blob[2]) for b in found):
            balls.append(blob)
    return balls


def similar_size(r1, r2):
    return max(r1, r2) <= max_size_ratio * max(min(r1, r2), 1)


def predicted_center(track):
    points = track["points"]
    x, y = points[-1][1], points[-1][2]
    if len(points) >= 2:
        vx = points[-1][1] - points[-2][1]
        vy = points[-1][2] - points[-2][2]
        step = track["missed"] + 1
        x += vx * step
        y += vy * step
    return x, y


def update_tracks(tracks, balls, frame_index):
    unused = set(range(len(balls)))
    ordered = sorted(tracks, key=lambda track: len(track["points"]), reverse=True)
    for track in ordered:
        last = track["points"][-1]
        px, py = predicted_center(track)
        best_i = None
        best_d = min(max_distance + track["missed"] * 20, 200)
        for i in unused:
            x, y, r, _ = balls[i]
            if not similar_size(r, last[3]):
                continue
            dist = math.hypot(x - px, y - py)
            if dist < best_d:
                best_d = dist
                best_i = i
        if best_i is None:
            track["missed"] += 1
        else:
            track["points"].append((frame_index, *balls[best_i]))
            track["missed"] = 0
            unused.remove(best_i)
    for i in unused:
        tracks.append({"points": [(frame_index, *balls[i])], "missed": 0})
    return [track for track in tracks if track["missed"] <= max_lost]


def choose_ball(tracks, frame_index, travel):
    """Prefer the ball that is in play. A still ball only counts if nothing is moving.

    travel is how far, in pixels, a track must move to count as a ball in flight.
    """
    best_track = None
    best_key = None
    for track in tracks:
        points = track["points"]
        if len(points) < min_track_points or frame_index - points[-1][0] > 3:
            continue
        confidence = sum(point[4] for point in points) / len(points)
        motion = math.hypot(points[-1][1] - points[0][1], points[-1][2] - points[0][2])
        moving = motion >= travel
        if moving and confidence < moving_score:
            continue
        if not moving and (confidence < still_score or len(points) < min_still_points):
            continue
        key = (moving, motion if moving else confidence)
        if best_key is None or key > best_key:
            best_key = key
            best_track = track
    return best_track


def blank_row(frame_index):
    return [frame_index, "", "", "", "", "", "", "", 0]


def motion_row(frame_index, x, y, vx, vy, detected, fps):
    vx = round(float(vx), 1)
    vy = round(float(vy), 1)
    speed = math.hypot(vx, vy)
    angle = math.degrees(math.atan2(-vy, vx))
    return [frame_index, int(x), int(y), vx, vy,
            round(speed, 2), round(speed * fps, 2), round(angle, 1), detected]


def fill_window(track, start_frame, end_frame, fps):
    """Write every frame from the chosen track, and fill short gaps from its velocity."""
    points = [point for point in track["points"] if start_frame <= point[0] < end_frame]
    rows = []
    point_i = 0
    prev = None
    for frame_index in range(start_frame, end_frame):
        point = None
        if point_i < len(points) and points[point_i][0] == frame_index:
            point = points[point_i]
            point_i += 1
        if point is not None:
            nxt = points[point_i] if point_i < len(points) else None
            if prev is not None and 0 < frame_index - prev[0] <= max_lost:
                gap = frame_index - prev[0]
                vx = (point[1] - prev[1]) / gap
                vy = (point[2] - prev[2]) / gap
            elif nxt is not None and nxt[0] > frame_index:
                gap = nxt[0] - frame_index
                vx = (nxt[1] - point[1]) / gap
                vy = (nxt[2] - point[2]) / gap
            else:
                vx, vy = 0, 0
            rows.append(motion_row(frame_index, point[1], point[2], vx, vy, 1, fps))
            prev = point
            continue

        nxt = points[point_i] if point_i < len(points) else None
        if prev is not None and nxt is not None and 0 < nxt[0] - prev[0] <= max_lost:
            gap = nxt[0] - prev[0]
            step = frame_index - prev[0]
            vx = (nxt[1] - prev[1]) / gap
            vy = (nxt[2] - prev[2]) / gap
            rows.append(motion_row(
                frame_index,
                prev[1] + vx * step,
                prev[2] + vy * step,
                vx,
                vy,
                0,
                fps))
            continue

        earlier = [item for item in points if prev is not None and item[0] < prev[0]]
        if prev is not None and nxt is None and earlier and frame_index - prev[0] <= max_lost:
            gap = prev[0] - earlier[-1][0]
            if gap <= 0:
                rows.append(blank_row(frame_index))
                continue
            vx = (prev[1] - earlier[-1][1]) / gap
            vy = (prev[2] - earlier[-1][2]) / gap
            step = frame_index - prev[0]
            rows.append(motion_row(
                frame_index,
                prev[1] + vx * step,
                prev[2] + vy * step,
                vx,
                vy,
                0,
                fps))
            continue
        rows.append(blank_row(frame_index))
    radius = points[-1][3] if points else None
    return rows, radius


def state_from_rows(rows, radius):
    trailing = 0
    last = None
    for row in reversed(rows):
        if row[1] == "":
            trailing += 1
            continue
        last = row
        break
    if last is None or radius is None or trailing > max_lost:
        return None
    have_vel = last[3] != ""
    return {
        "x": int(last[1]),
        "y": int(last[2]),
        "vx": float(last[3]) if have_vel else 0.0,
        "vy": float(last[4]) if have_vel else 0.0,
        "r": int(radius),
        "lost": trailing,
        "have_vel": have_vel,
        "frame": int(last[0]),
        "ay": 0.0,
    }


def draw_ball(frame, x, y, r, detected, speed):
    color = (0, 255, 0) if detected else (0, 255, 255)
    x, y, r = int(x), int(y), int(r)
    cv2.circle(frame, (x, y), r, color, 4)
    text = f"x:{x}  y:{y}  {float(speed):.1f} px/s"
    cv2.putText(
        frame, text, (x + r + 8, y),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)


def predict(state):
    """Where the ball should be next frame, including the pull of gravity."""
    return state["x"] + state["vx"], state["y"] + state["vy"] + state["ay"]


def closest_ball(balls, state):
    px, py = predict(state)
    best = None
    best_d = min(max_distance + state["lost"] * 20, 200)
    for x, y, r, _ in balls:
        if not similar_size(r, state["r"]):
            continue
        dist = math.hypot(x - px, y - py)
        if dist < best_d:
            best_d = dist
            best = (x, y, r)
    return best


def track_video(video, fps, detector, show=False, progress=False):
    track_data = []
    tracks = []
    state = None
    mode = "lock"
    next_row = 0
    current_frame = 0
    total = int(video.get(cv2.CAP_PROP_FRAME_COUNT)) or "?"
    height = video.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0
    travel = max(min_motion, min_travel * height)

    for frame, prev_gray, gray, next_gray in read_frames(video):
        if progress:
            print(f"\rProcessing frame {current_frame + 1}/{total}", end="", flush=True)
        moving = detect_moving(prev_gray, gray, next_gray)
        if mode == "lock":
            found, people = detect_balls(detector, frame)
            balls = combine(found, moving, people)
            tracks = update_tracks(tracks, balls, current_frame)
            for x, y, r, _ in balls:
                cv2.circle(frame, (x, y), r, (0, 255, 255), 2)
            if current_frame + 1 >= min_track_points:
                chosen = choose_ball(tracks, current_frame, travel)
                if chosen is not None:
                    rows, radius = fill_window(chosen, next_row, current_frame + 1, fps)
                    state = state_from_rows(rows, radius)
                    if state is not None:
                        track_data.extend(rows)
                        next_row = current_frame + 1
                        mode = "track"
                        current = rows[-1]
                        if current[1] != "":
                            draw_ball(frame, current[1], current[2], radius, current[8], current[6])
        else:
            px, py = predict(state)
            found, people = detect_balls(detector, frame, crop_imgsz)
            best = closest_ball(combine(found, moving, people), state)
            if best is None:
                best = closest_ball(detect_near(detector, frame, px, py, state["r"]), state)
            if best is not None:
                x, y, r = best
                gap = max(current_frame - state["frame"], 1)
                vx = (x - state["x"]) / gap
                vy = (y - state["y"]) / gap
                track_data.append(motion_row(current_frame, x, y, vx, vy, 1, fps))
                vx = round(float(vx), 1)
                vy = round(float(vy), 1)
                if gap == 1 and state["have_vel"] and state["lost"] == 0:
                    pull = 0.5 * state["ay"] + 0.5 * (vy - state["vy"])
                    state["ay"] = min(max(pull, 0.0), max_gravity * height)
                state["vx"], state["vy"] = vx, vy
                state["have_vel"] = True
                state["x"], state["y"] = x, y
                state["r"] = int(round(0.7 * state["r"] + 0.3 * r))
                state["frame"] = current_frame
                state["lost"] = 0
                draw_ball(frame, x, y, r, 1, math.hypot(vx, vy) * fps)
            else:
                state["lost"] += 1
                frame_h, frame_w = frame.shape[:2]
                x, y = predict(state)
                x, y = int(x), int(y)
                inside = 0 <= x < frame_w and 0 <= y < frame_h
                if state["lost"] <= max_lost and state["have_vel"] and inside:
                    state["vy"] = round(state["vy"] + state["ay"], 1)
                    track_data.append(motion_row(
                        current_frame, x, y, state["vx"], state["vy"], 0, fps))
                    state["x"], state["y"] = x, y
                    state["frame"] = current_frame
                    draw_ball(frame, x, y, state["r"], 0, math.hypot(state["vx"], state["vy"]) * fps)
                else:
                    track_data.append(blank_row(current_frame))
                    if state["lost"] > max_lost:
                        mode = "lock"
                        tracks = []
                        state = None
            next_row = current_frame + 1

        if show:
            cv2.imshow("Ball Tracking", frame)
            if cv2.waitKey(25) & 0xFF == ord("q"):
                break
        current_frame += 1

    if progress:
        print()
    if mode == "lock" and current_frame > next_row:
        chosen = choose_ball(tracks, current_frame - 1, travel) if current_frame else None
        if chosen is not None:
            rows, radius = fill_window(chosen, next_row, current_frame, fps)
            if state_from_rows(rows, radius) is not None:
                track_data.extend(rows)
                next_row = current_frame
        while next_row < current_frame:
            track_data.append(blank_row(next_row))
            next_row += 1
    return track_data


def ball_record(row):
    """One frame for the UI. A missed frame has null numbers and detected false."""
    frame = int(row[0])
    if row[1] == "" or row[3] == "":
        return {"frame": frame, "x": None, "y": None, "vx": None, "vy": None, "detected": False}
    return {
        "frame": frame,
        "x": int(row[1]),
        "y": int(row[2]),
        "vx": round(float(row[3]), 1),
        "vy": round(float(row[4]), 1),
        "detected": bool(row[8]),
    }


def track_ball(video_path, show=False, progress=False):
    """Return the ball's position and speed for every frame.

    The result is {"ball": [{"frame", "x", "y", "vx", "vy", "detected"}, ...]}.
    Missed frames stay in the list with null x, y, vx, and vy.
    """
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        return None
    fps = video.get(cv2.CAP_PROP_FPS) or 30
    detector = make_detector()
    try:
        rows = track_video(video, fps, detector, show=show, progress=progress)
    finally:
        video.release()
        if show:
            cv2.destroyAllWindows()
    return {"ball": [ball_record(row) for row in rows]}


def clean_path(text):
    """Accept paths pasted with quotes, such as from File Explorer's Copy as path."""
    return os.path.expanduser(text.strip().strip('"').strip("'"))


def ask_for_video():
    while True:
        video_path = clean_path(input("Enter the path of the video file: "))
        if os.path.isfile(video_path):
            return video_path
        print(f"No file found at {video_path}. Try again, or press Ctrl+C to quit.")


def main():
    if len(sys.argv) > 1:
        video_path = clean_path(" ".join(sys.argv[1:]))
        if not os.path.isfile(video_path):
            print(f"No file found at {video_path}")
            sys.exit(1)
    else:
        video_path = ask_for_video()

    output_file = os.path.abspath("ball_tracking.json")
    print("Tracking the ball. Press q in the video window to stop early.")
    try:
        payload = track_ball(video_path, show=True, progress=True)
    except KeyboardInterrupt:
        print("\nStopped. No file was saved.")
        sys.exit(1)
    if payload is None:
        print(f"Could not open {video_path} as a video.")
        sys.exit(1)

    with open(output_file, "w") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")

    frames = payload["ball"]
    seen = sum(1 for f in frames if f["detected"])
    estimated = sum(1 for f in frames if f["x"] is not None and not f["detected"])
    missing = len(frames) - seen - estimated
    print(f"Done. {len(frames)} frames: ball seen in {seen}, estimated in {estimated}, missing in {missing}.")
    print(f"Tracking data has been saved to {output_file}")


if __name__ == "__main__":
    main()
